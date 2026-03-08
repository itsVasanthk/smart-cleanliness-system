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
                   area, pincode, created_at
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
                "created_at": c[7].strftime("%Y-%m-%d %H:%M:%S") if c[7] else None
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
        # To avoid overwriting existing images with the same name, better to prepend something unique if needed.
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

@api_complaints_bp.route("/citizen/dashboard/<int:user_id>", methods=["GET"])
def api_citizen_dashboard(user_id):
    try:
        # Re-using the logic from the web app for calculating logic
        cur = mysql.connection.cursor()
        cur.execute("SELECT COUNT(*) FROM complaints")
        total_reports = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'resolved'")
        resolved_reports = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM complaints WHERE status = 'pending'")
        pending_reports = cur.fetchone()[0]
        cur.close()

        if total_reports > 0:
            resolved_percent = (resolved_reports / total_reports) * 100
        else:
            resolved_percent = 0

        if resolved_percent >= 70:
            emotion = "happy"
            slogan = "Madurai is becoming cleaner! Your contribution is amazing!"
        elif resolved_percent >= 40:
            emotion = "neutral"
            slogan = "Together, we can make Madurai cleaner!"
        else:
            emotion = "sad"
            slogan = "Madurai needs your help! Act now!"

        return jsonify({
            "success": True, 
            "total_reports": total_reports,
            "resolved_reports": resolved_reports,
            "pending_reports": pending_reports,
            "emotion": emotion,
            "slogan": slogan
        })
    except Exception as e:
         return jsonify({"success": False, "message": str(e)}), 500
