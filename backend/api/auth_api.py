from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from app import mysql

api_auth_bp = Blueprint('api_auth', __name__)

@api_auth_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json()
    if not data or 'email' not in data or 'password' not in data:
        return jsonify({"success": False, "message": "Email and password required"}), 400

    email = data.get('email')
    password = data.get('password')

    cur = mysql.connection.cursor()
    cur.execute(
        "SELECT user_id, name, password, role FROM users WHERE email=%s",
        (email,)
    )
    user = cur.fetchone()
    cur.close()

    if user and check_password_hash(user[2], password):
        # In a real production app, you would generate a JWT token here.
        # For simplicity and to match the current session structure, we return user details.
        user_data = {
            "user_id": user[0],
            "name": user[1],
            "role": user[3].strip().lower(),
            "email": email
        }
        return jsonify({
            "success": True, 
            "message": "Login successful",
            "user": user_data
            }), 200

    return jsonify({"success": False, "message": "Invalid email or password"}), 401


@api_auth_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'email', 'password', 'role')):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role')

    hashed_password = generate_password_hash(password)

    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Registration successful"}), 201
    except Exception as e:
        # e.g., duplicate email
        return jsonify({"success": False, "message": str(e)}), 500
