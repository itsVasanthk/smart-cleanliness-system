import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from PIL import Image
import imagehash
from app import mysql

api_complaints_bp = Blueprint('api_complaints', __name__)

UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api_complaints_bp.route("/citizen/reports/<int:user_id>", methods=["GET"])
def api_citizen_reports(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            """
            SELECT complaint_id, garbage_type, description, status, image,
                   area, pincode, created_at, authority_decision, authority_reason,
                   citizen_feedback, citizen_rating, escalated_to_admin, landmark
            FROM complaints
            WHERE user_id = %s
            ORDER BY created_at DESC
            """,
            (user_id,)
        )
        complaints = cur.fetchall()
        cur.close()

        complaints_list = []
        for c in complaints:
            complaints_list.append({
                "complaint_id": c[0],
                "garbage_type": c[1],
                "description": c[2],
                "status": c[3],
                "image": c[4],
                "area": c[5],
                "pincode": c[6],
                "created_at": c[7].strftime("%Y-%m-%d %H:%M:%S") if c[7] else None,
                "authority_decision": c[8],
                "authority_reason": c[9],
                "citizen_feedback": c[10],
                "citizen_rating": c[11],
                "escalated_to_admin": bool(c[12]),
                "landmark": c[13]
            })

        return jsonify({"success": True, "reports": complaints_list})
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500


@api_complaints_bp.route("/report", methods=["POST"])
def api_report():
    user_id = request.form.get('user_id')
    if not user_id:
        return jsonify({"success": False, "message": "user_id is required"}), 400

    garbage_type = request.form.get('garbage_type')
    other_description = request.form.get('other_description')
    area = request.form.get('area')
    pincode = request.form.get('pincode')
    landmark = request.form.get('landmark')

    if garbage_type == "Other":
        if other_description and other_description.strip() != "":
            description = other_description.strip()
        else:
            description = "Other waste reported"
    else:
        description = garbage_type

    image = request.files.get('image')
    image_name = None
    image_hash_value = None

    if image and image.filename != "":
        filename = secure_filename(image.filename)
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        
        try:
            img = Image.open(image)
            image_hash_value = str(imagehash.phash(img))
            image.stream.seek(0)
            
            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT complaint_id FROM complaints WHERE image_hash=%s",
                (image_hash_value,)
            )
            duplicate = cur.fetchone()
            
            if duplicate:
                cur.close()
                return jsonify({
                    "success": False,
                    "message": "This image was already used in another report."
                }), 400
                
            image.save(image_path)
            image_name = filename
            cur.close()
        except Exception as e:
            return jsonify({
                "success": False, 
                "message": f"Error processing image: {str(e)}"
            }), 500

    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            INSERT INTO complaints
            (user_id, garbage_type, description, image, area, pincode, landmark, status, image_hash)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'Pending',%s)
        """, (
            user_id,
            garbage_type,
            description,
            image_name,
            area,
            pincode,
            landmark,
            image_hash_value
        ))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Complaint submitted successfully!"})
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500

@api_complaints_bp.route("/report/edit/<int:complaint_id>", methods=["PUT"])
def api_edit_report(complaint_id):
    try:
        cur = mysql.connection.cursor()
        # Verify status - can only edit if Pending and Authority hasn't decided
        cur.execute("SELECT status, authority_decision FROM complaints WHERE complaint_id=%s", (complaint_id,))
        result = cur.fetchone()
        if not result:
            return jsonify({"success": False, "message": "Report not found"}), 404
            
        if result[0] != 'Pending' or result[1] != 'pending':
            return jsonify({"success": False, "message": "Cannot edit a report that is already under process or decided by authority"}), 400

        garbage_type = request.form.get('garbage_type')
        other_description = request.form.get('other_description')
        area = request.form.get('area')
        pincode = request.form.get('pincode')
        landmark = request.form.get('landmark')
        
        if garbage_type == "Other":
            description = other_description.strip() if other_description else "Other waste reported"
        else:
            description = garbage_type

        image = request.files.get('image')
        image_name = None
        
        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            image.save(image_path)
            image_name = filename
            
        if image_name:
            cur.execute("""
                UPDATE complaints 
                SET garbage_type=%s, description=%s, area=%s, pincode=%s, landmark=%s, image=%s
                WHERE complaint_id=%s
            """, (garbage_type, description, area, pincode, landmark, image_name, complaint_id))
        else:
            cur.execute("""
                UPDATE complaints 
                SET garbage_type=%s, description=%s, area=%s, pincode=%s, landmark=%s
                WHERE complaint_id=%s
            """, (garbage_type, description, area, pincode, landmark, complaint_id))
            
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Report updated successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_complaints_bp.route("/report/feedback", methods=["POST"])
def api_submit_feedback():
    data = request.json
    complaint_id = data.get('complaint_id')
    feedback = data.get('feedback')
    rating = data.get('rating')
    
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            UPDATE complaints 
            SET citizen_feedback=%s, citizen_rating=%s 
            WHERE complaint_id=%s
        """, (feedback, rating, complaint_id))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Feedback submitted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_complaints_bp.route("/citizen/dashboard/<int:user_id>", methods=["GET"])
def api_citizen_dashboard(user_id):
    try:
        cur = mysql.connection.cursor()
        
        # Global Stats (Madurai Status)
        cur.execute("SELECT COUNT(*) FROM complaints")
        total_reports = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Resolved'")
        resolved_reports = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'Pending'")
        pending_reports = cur.fetchone()[0]

        # User Specific Stats (Optional for future use)
        cur.execute("SELECT COUNT(*) FROM complaints WHERE user_id = %s", (user_id,))
        user_total = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM complaints WHERE user_id = %s AND status = 'Resolved'", (user_id,))
        user_resolved = cur.fetchone()[0]

        cur.close()

        # Emotion/Slogan based on GLOBAL Madurai performance
        resolved_percent = (resolved_reports / total_reports * 100) if total_reports > 0 else 0
        emotion = "happy" if resolved_percent >= 70 else "neutral" if resolved_percent >= 40 else "sad"
        slogan = "Madurai is looking great!" if emotion == "happy" else "Let's keep Madurai clean!" if emotion == "neutral" else "Madurai needs our help!"

        return jsonify({
            "success": True, 
            "total_reports": total_reports, # Global
            "resolved_reports": resolved_reports, # Global
            "pending_reports": pending_reports, # Global
            "user_total": user_total,
            "user_resolved": user_resolved,
            "emotion": emotion,
            "slogan": slogan
        })
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500
