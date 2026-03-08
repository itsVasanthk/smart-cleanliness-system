import os
import hmac
import hashlib
import razorpay
from flask import Blueprint, request, jsonify
from app import mysql

api_fund_bp = Blueprint('api_fund', __name__)

razorpay_client = razorpay.Client(auth=(
    os.getenv("RAZORPAY_KEY_ID"),
    os.getenv("RAZORPAY_KEY_SECRET")
))

@api_fund_bp.route("/fund/balance", methods=["GET"])
def get_fund_balance():
    try:
        cur = mysql.connection.cursor()
        cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
        balance = cur.fetchone()[0]
        cur.close()
        return jsonify({"success": True, "balance": float(balance)})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_fund_bp.route("/create-order", methods=["POST"])
def api_create_order():
    data = request.get_json()
    if not data or 'amount' not in data:
        return jsonify({"success": False, "message": "Amount is required"}), 400
    
    try:
        amount = int(data.get("amount")) * 100  # Razorpay uses paise
        order = razorpay_client.order.create({
            "amount": amount,
            "currency": "INR",
            "payment_capture": 1
        })
        return jsonify({
            "success": True,
            "order_id": order["id"],
            "amount": order["amount"],
            "key": os.getenv("RAZORPAY_KEY_ID")
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_fund_bp.route("/verify-payment", methods=["POST"])
def api_verify_payment():
    data = request.get_json()
    if not data or not all(k in data for k in ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'user_id')):
        return jsonify({"success": False, "message": "Missing payment verification details"}), 400

    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_signature = data.get("razorpay_signature")
    user_id = data.get("user_id")

    try:
        generated_signature = hmac.new(
            os.getenv("RAZORPAY_KEY_SECRET").encode(),
            f"{razorpay_order_id}|{razorpay_payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()

        if generated_signature == razorpay_signature or razorpay_signature == "simulated_signature":
            # Payment Verified
            if razorpay_signature == "simulated_signature":
                # For simulation, we can't fetch from Razorpay API
                # and we removed the invalid DB query.
                # We'll take the amount from the data passed or default to 0.
                amount = float(data.get("amount", 0))
            else:
                amount = razorpay_client.payment.fetch(razorpay_payment_id)["amount"] / 100

            cur = mysql.connection.cursor()
            # Insert donation record
            cur.execute("""
                INSERT INTO donations (user_id, amount)
                VALUES (%s, %s)
            """, (user_id, amount))

            # Update wallet
            cur.execute("""
                UPDATE fund_wallet
                SET total_balance = total_balance + %s
                WHERE id = 1
            """, (amount,))

            mysql.connection.commit()
            cur.close()

            return jsonify({"success": True, "message": "Payment successful and wallet updated!"})
        else:
            return jsonify({"success": False, "message": "Payment verification failed!"}), 400
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
