import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from deepface import DeepFace
from app import mysql

api_emergency_bp = Blueprint('api_emergency', __name__)

UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@api_emergency_bp.route("/emergency/request", methods=["POST"])
def api_emergency_request():
    user_id = request.form.get('user_id')
    reason = request.form.get('reason')
    amount_requested = request.form.get('amount')

    if not all([user_id, reason, amount_requested]):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        amount_requested = float(amount_requested)
        if amount_requested > 1000:
            return jsonify({"success": False, "message": "Maximum assistance allowed is ₹1000."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Invalid amount"}), 400

    # Check for active request
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT request_id FROM emergency_requests 
        WHERE user_id=%s AND status IN ('pending','paid')
    """, (user_id,))
    if cur.fetchone():
        cur.close()
        return jsonify({"success": False, "message": "You already have an active request."}), 400

    aadhaar_image = request.files.get("aadhaar_image")
    selfie_image = request.files.get("selfie_image")

    if not aadhaar_image or not selfie_image:
        cur.close()
        return jsonify({"success": False, "message": "Both Aadhaar and Selfie images are required."}), 400

    aadhaar_filename = secure_filename(aadhaar_image.filename)
    selfie_filename = secure_filename(selfie_image.filename)

    aadhaar_path = os.path.join(UPLOAD_FOLDER, aadhaar_filename)
    selfie_path = os.path.join(UPLOAD_FOLDER, selfie_filename)

    aadhaar_image.save(aadhaar_path)
    selfie_image.save(selfie_path)

    # DeepFace Verification
    try:
        result = DeepFace.verify(
            img1_path=aadhaar_path,
            img2_path=selfie_path,
            model_name="VGG-Face",
            enforce_detection=False
        )
        distance = result["distance"]
        if distance > 0.60:
            cur.close()
            return jsonify({"success": False, "message": "Face verification failed. Identity mismatch."}), 401
    except Exception as e:
        cur.close()
        return jsonify({"success": False, "message": f"AI verification error: {str(e)}"}), 500

    # Insert request
    try:
        cur.execute("""
            INSERT INTO emergency_requests 
            (user_id, reason, aadhaar_image, selfie_image, amount_requested, ai_distance, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())
        """, (user_id, reason, aadhaar_filename, selfie_filename, amount_requested, distance))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Emergency request submitted successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_emergency_bp.route("/emergency/status/<int:user_id>", methods=["GET"])
def api_emergency_status(user_id):
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT request_id, reason, amount_requested, status, created_at, approved_at
            FROM emergency_requests
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))
        row = cur.fetchone()
        cur.close()

        if not row:
            return jsonify({"success": True, "request": None})

        return jsonify({
            "success": True,
            "request": {
                "request_id": row[0],
                "reason": row[1],
                "amount": float(row[2]),
                "status": row[3],
                "created_at": row[4].strftime("%Y-%m-%d %H:%M:%S") if row[4] else None,
                "approved_at": row[5].strftime("%Y-%m-%d %H:%M:%S") if row[5] else None
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
@api_emergency_bp.route("/authority/emergency/requests", methods=["GET"])
def api_get_emergency_requests():
    try:
        cur = mysql.connection.cursor()
        cur.execute("""
            SELECT request_id, user_id, reason, aadhaar_image, selfie_image, 
                   amount_requested, ai_distance, status, created_at, approved_at 
            FROM emergency_requests 
            ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        
        cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
        wallet_balance = cur.fetchone()[0]
        
        cur.close()

        requests_list = []
        for r in rows:
            requests_list.append({
                "request_id": r[0],
                "user_id": r[1],
                "reason": r[2],
                "aadhaar_image": r[3],
                "selfie_image": r[4],
                "amount_requested": float(r[5]),
                "ai_distance": float(r[6]),
                "status": r[7],
                "created_at": r[8].strftime("%Y-%m-%d %H:%M:%S") if r[8] else None,
                "approved_at": r[9].strftime("%Y-%m-%d %H:%M:%S") if r[9] else None
            })
        return jsonify({
            "success": True, 
            "requests": requests_list,
            "wallet_balance": float(wallet_balance)
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_emergency_bp.route("/authority/emergency/approve", methods=["POST"])
def api_approve_emergency():
    data = request.get_json()
    request_id = data.get('request_id')
    priority = data.get('priority', 'normal')

    if not request_id:
        return jsonify({"success": False, "message": "Request ID is required"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT amount_requested, status FROM emergency_requests WHERE request_id=%s", (request_id,))
        result = cur.fetchone()

        if not result:
            cur.close()
            return jsonify({"success": False, "message": "Request not found"}), 404

        amount = float(result[0])
        status = result[1]

        if status != 'pending':
            cur.close()
            return jsonify({"success": False, "message": "Request already processed"}), 400

        # Check wallet
        cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
        wallet = float(cur.fetchone()[0])

        if wallet < amount:
            cur.close()
            return jsonify({"success": False, "message": "Insufficient fund balance"}), 400

        # Deduct and Update
        cur.execute("UPDATE fund_wallet SET total_balance = total_balance - %s WHERE id = 1", (amount,))
        cur.execute("UPDATE emergency_requests SET status='paid', approved_at=NOW() WHERE request_id=%s", (request_id,))
        mysql.connection.commit()
        cur.close()

        return jsonify({"success": True, "message": "Emergency request approved and paid."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
