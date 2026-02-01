import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from app import mysql

auth_bp = Blueprint('auth', __name__)

@auth_bp.route("/")
def home():
    return render_template("home.html")


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
        cur.execute(
            "SELECT user_id, name, password, role FROM users WHERE email=%s",
            (email,)
        )
        user = cur.fetchone()
        cur.close()

        if user and check_password_hash(user[2], password):
            role = user[3].strip().lower()   # 🔥 IMPORTANT LINE

            print("DEBUG ROLE VALUE ->", repr(role))  # 🔍 DEBUG

            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = role

            if role == 'citizen':
                return redirect(url_for('auth.citizen_dashboard'))
            elif role == 'authority':
                return redirect(url_for('auth.authority_dashboard'))
            elif role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))
            else:
                return "Unknown role: " + role

        return "Invalid email or password"

    return render_template("login.html")

@auth_bp.route("/citizen")
def citizen_dashboard():
    return render_template("citizen_dashboard.html")

@auth_bp.route("/citizen/reports")
def my_reports():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT complaint_id, garbage_type, description, status, image, created_at
        FROM complaints
        WHERE user_id = %s
        ORDER BY created_at DESC
        """,
        (user_id,)
    )
    complaints = cur.fetchall()
    cur.close()

    return render_template("my_reports.html", complaints=complaints)


@auth_bp.route("/report", methods=["GET", "POST"])
def report():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        garbage_type = request.form['garbage_type']
        description = request.form['description']
        user_id = session['user_id']

        image = request.files.get('image')
        image_name = None

        if image and image.filename != "":
            filename = secure_filename(image.filename)
            image_path = os.path.join("app/static/uploads", filename)
            image.save(image_path)
            image_name = filename

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO complaints (user_id, garbage_type, description, status, image)
            VALUES (%s, %s, %s, 'Pending', %s)
            """,
            (user_id, garbage_type, description, image_name)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('auth.citizen_dashboard'))

    return render_template("report.html")



@auth_bp.route("/authority/update/<int:complaint_id>", methods=["POST"])
def update_complaint_status(complaint_id):
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    new_status = request.form['status']

    cur = mysql.connection.cursor()
    cur.execute(
        "UPDATE complaints SET status=%s WHERE complaint_id=%s",
        (new_status, complaint_id)
    )
    mysql.connection.commit()
    cur.close()

    return redirect(url_for('auth.authority_dashboard'))


@auth_bp.route("/authority/events", methods=["GET", "POST"])
def authority_events():
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        title = request.form['title']
        area = request.form['area']
        description = request.form['description']
        event_date = request.form['event_date']
        credit_points = request.form['credit_points']
        created_by = session['user_id']

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO cleaning_events
            (title, area, description, event_date, credit_points, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (title, area, description, event_date, credit_points, created_by)
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('auth.authority_events'))

    # Fetch events created by this authority
    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT event_id, title, area, event_date, credit_points, status
        FROM cleaning_events
        WHERE created_by = %s
        ORDER BY event_date DESC
        """,
        (session['user_id'],)
    )
    events = cur.fetchall()
    cur.close()

    return render_template("authority_events.html", events=events)


@auth_bp.route("/authority/event/<int:event_id>")
def view_event_participants(event_id):
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get event details
    cur.execute(
        "SELECT title, credit_points, status FROM cleaning_events WHERE event_id=%s",
        (event_id,)
    )
    event = cur.fetchone()

    # Get participants
    cur.execute(
        """
        SELECT ep.participant_id, u.name, u.email, ep.status
        FROM event_participants ep
        JOIN users u ON ep.user_id = u.user_id
        WHERE ep.event_id = %s
        """,
        (event_id,)
    )
    participants = cur.fetchall()

    cur.close()

    return render_template(
        "authority_event_participants.html",
        event=event,
        event_id=event_id,
        participants=participants
    )


@auth_bp.route("/authority/event/complete/<int:event_id>")
def complete_event(event_id):
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get event credit points
    cur.execute(
        "SELECT credit_points FROM cleaning_events WHERE event_id=%s",
        (event_id,)
    )
    points = cur.fetchone()[0]

    # Get participants
    cur.execute(
        "SELECT participant_id, user_id FROM event_participants WHERE event_id=%s",
        (event_id,)
    )
    participants = cur.fetchall()

    for p in participants:
        participant_id, user_id = p

        # Get volunteer_id
        cur.execute(
            "SELECT volunteer_id FROM volunteers WHERE user_id=%s",
            (user_id,)
        )
        volunteer = cur.fetchone()

        if volunteer:
            volunteer_id = volunteer[0]

            # Award credits
            cur.execute(
                """
                INSERT INTO carbon_credits (volunteer_id, points, activity)
                VALUES (%s, %s, %s)
                """,
                (volunteer_id, points, "Cleaning Event Participation")
            )

            # Update participant status
            cur.execute(
                "UPDATE event_participants SET status='Credited' WHERE participant_id=%s",
                (participant_id,)
            )

    # Mark event completed
    cur.execute(
        "UPDATE cleaning_events SET status='Completed' WHERE event_id=%s",
        (event_id,)
    )

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('auth.authority_events'))



@auth_bp.route("/admin")
def admin_dashboard():
    return "Admin Dashboard"
@auth_bp.route("/authority")
def authority_dashboard():
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT complaint_id, garbage_type, description, image, status, created_at
        FROM complaints
        ORDER BY created_at DESC
        """
    )
    complaints = cur.fetchall()
    cur.close()

    return render_template("authority_dashboard.html", complaints=complaints)

@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.home'))

