from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from app import mysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
def home():
    return "Smart Cleanliness System is Running 🚀"

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        hashed_password = generate_password_hash(password)

        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('auth.home'))

    return render_template("register.html")

from werkzeug.security import check_password_hash
from flask import session

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']

        cur = mysql.connection.cursor()
        cur.execute("SELECT user_id, password, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['role'] = user[2]

            if user[2] == 'citizen':
                return redirect(url_for('auth.citizen_dashboard'))
            elif user[2] == 'authority':
                return redirect(url_for('auth.authority_dashboard'))
            else:
                return redirect(url_for('auth.admin_dashboard'))

        return "Invalid email or password"

    return render_template("login.html")

@auth_bp.route("/citizen")
def citizen_dashboard():
    return "Citizen Dashboard"

@auth_bp.route("/authority")
def authority_dashboard():
    return "Authority Dashboard"

@auth_bp.route("/admin")
def admin_dashboard():
    return "Admin Dashboard"

