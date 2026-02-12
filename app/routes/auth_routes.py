from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import imagehash
import os
from app import mysql

auth_bp = Blueprint('auth', __name__)

# Upload folder setup
UPLOAD_FOLDER = os.path.join("app", "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ---------------- HOME ----------------
@auth_bp.route("/")
def home():
    return render_template("home.html")


# ---------------- REGISTER ----------------
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


# ---------------- LOGIN ----------------
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
            role = user[3].strip().lower()

            session['user_id'] = user[0]
            session['name'] = user[1]
            session['role'] = role

            if role == 'citizen':
                return redirect(url_for('auth.citizen_dashboard'))
            elif role == 'authority':
                return redirect(url_for('auth.authority_dashboard'))
            elif role == 'admin':
                return redirect(url_for('auth.admin_dashboard'))

        return "Invalid email or password"

    return render_template("login.html")


# ---------------- CITIZEN DASHBOARD ----------------
@auth_bp.route("/citizen")
def citizen_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template("citizen_dashboard.html")


# ---------------- MY REPORTS ----------------
@auth_bp.route("/citizen/reports")
def my_reports():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

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

    return render_template("my_reports.html", complaints=complaints)


# ---------------- REPORT (IMAGE HASH + AREA/PINCODE) ----------------
@auth_bp.route("/report", methods=["GET", "POST"])
def report():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    if request.method == "POST":
        garbage_type = request.form['garbage_type']
        description = request.form['description']
        area = request.form.get('area')
        pincode = request.form.get('pincode')
        user_id = session['user_id']

        image = request.files.get('image')
        image_name = None
        image_hash_value = None

        if image and image.filename:
            filename = secure_filename(image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, filename)

            # Generate perceptual hash
            img = Image.open(image)
            image_hash_value = str(imagehash.phash(img))

            # Reset stream before saving
            image.stream.seek(0)

            cur = mysql.connection.cursor()
            cur.execute(
                "SELECT complaint_id FROM complaints WHERE image_hash=%s",
                (image_hash_value,)
            )
            duplicate = cur.fetchone()

            if duplicate:
                cur.close()
                return render_template(
                    "report.html",
                    error="⚠️ This image was already used in a previous report. Please upload a new image taken at the location."
                )


            image.save(image_path)
            image_name = filename
            cur.close()

        cur = mysql.connection.cursor()
        cur.execute(
            """
            INSERT INTO complaints
            (user_id, garbage_type, description, status, image,
             area, pincode, image_hash)
            VALUES (%s, %s, %s, 'Pending', %s, %s, %s, %s)
            """,
            (
                user_id,
                garbage_type,
                description,
                image_name,
                area,
                pincode,
                image_hash_value
            )
        )
        mysql.connection.commit()
        cur.close()

        return redirect(url_for('auth.citizen_dashboard'))

    return render_template("report.html")


# ---------------- AUTHORITY DASHBOARD ----------------
@auth_bp.route("/authority")
def authority_dashboard():
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT complaint_id, garbage_type, description, image,
               area, pincode, status, created_at
        FROM complaints
        ORDER BY created_at DESC
        """
    )
    complaints = cur.fetchall()
    cur.close()

    return render_template("authority_dashboard.html", complaints=complaints)


# ---------------- UPDATE COMPLAINT STATUS ----------------
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


# ---------------- ADMIN ----------------
@auth_bp.route("/admin")
def admin_dashboard():
    return "Admin Dashboard"


# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('auth.home'))

@auth_bp.route("/awareness")
def awareness():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template("awareness/awareness_home.html")

@auth_bp.route("/volunteer")
def volunteer():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Get volunteer_id
    cur.execute(
        "SELECT volunteer_id FROM volunteers WHERE user_id=%s",
        (user_id,)
    )
    volunteer = cur.fetchone()

    total_points = 0
    credit_history = []

    if volunteer:
        volunteer_id = volunteer[0]

        # Total points
        cur.execute(
            "SELECT SUM(points) FROM carbon_credits WHERE volunteer_id=%s",
            (volunteer_id,)
        )
        result = cur.fetchone()
        total_points = result[0] if result[0] else 0

        # Credit history
        cur.execute(
            """
            SELECT points, activity, created_at
            FROM carbon_credits
            WHERE volunteer_id=%s
            ORDER BY created_at DESC
            """,
            (volunteer_id,)
        )
        credit_history = cur.fetchall()

    cur.close()

    return render_template(
        "volunteer_dashboard.html",
        total_points=total_points,
        credit_history=credit_history
    )


@auth_bp.route("/volunteer/events")
def volunteer_events():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()
    cur.execute(
        """
        SELECT event_id, title, area, event_date, credit_points, status
        FROM cleaning_events
        WHERE status = 'Upcoming'
        ORDER BY event_date ASC
        """
    )
    events = cur.fetchall()
    cur.close()

    return render_template("volunteer_events.html", events=events)

@auth_bp.route("/volunteer/join/<int:event_id>")
def join_event(event_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Check if already joined
    cur.execute(
        "SELECT participant_id FROM event_participants WHERE event_id=%s AND user_id=%s",
        (event_id, user_id)
    )
    existing = cur.fetchone()

    if existing:
        flash("You have already joined this event.", "warning")
    else:
        cur.execute(
            "INSERT INTO event_participants (event_id, user_id) VALUES (%s, %s)",
            (event_id, user_id)
        )
        mysql.connection.commit()
        flash("Successfully joined the event!", "success")

    cur.close()
    return redirect(url_for('auth.volunteer_events'))


@auth_bp.route("/authority/events", methods=["GET", "POST"])
def authority_events():
    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    # CREATE EVENT
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

    # FETCH EVENTS
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

    # Get credit points for this event
    cur.execute(
        "SELECT credit_points FROM cleaning_events WHERE event_id=%s",
        (event_id,)
    )
    result = cur.fetchone()

    if not result:
        cur.close()
        return redirect(url_for('auth.authority_events'))

    points = result[0]

    # Get participants
    cur.execute(
        "SELECT participant_id, user_id FROM event_participants WHERE event_id=%s",
        (event_id,)
    )
    participants = cur.fetchall()

    for participant_id, user_id in participants:

        # Get volunteer_id
        cur.execute(
            "SELECT volunteer_id FROM volunteers WHERE user_id=%s",
            (user_id,)
        )
        volunteer = cur.fetchone()

        if volunteer:
            volunteer_id = volunteer[0]

            # Insert carbon credits
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

    # Mark event as completed
    cur.execute(
        "UPDATE cleaning_events SET status='Completed' WHERE event_id=%s",
        (event_id,)
    )

    mysql.connection.commit()
    cur.close()

    flash("Event completed and credits awarded successfully!", "success")
    return redirect(url_for('auth.authority_events'))
