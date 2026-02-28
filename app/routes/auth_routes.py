from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from PIL import Image
import imagehash
import os
from app import mysql
from deepface import DeepFace


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

    import mysql.connector

    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root123",
        database="smart_cleanliness_db"
    )

    cursor = conn.cursor()

    # Total complaints
    cursor.execute("SELECT COUNT(*) FROM complaints")
    total_reports = cursor.fetchone()[0]

    # Resolved complaints
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'resolved'")
    resolved_reports = cursor.fetchone()[0]

    # Pending complaints
    cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'pending'")
    pending_reports = cursor.fetchone()[0]

    conn.close()

    # Calculate resolution percentage
    if total_reports > 0:
        resolved_percent = (resolved_reports / total_reports) * 100
    else:
        resolved_percent = 0

    # Select AI emotion image + Tamil + English slogan
    if resolved_percent >= 70:

        emotion_image = "images/happy_madurai.png"

        slogan_tamil = "மதுரை சுத்தமாக மாறுகிறது! உங்கள் பங்களிப்பு அருமை!"
        slogan_english = "Madurai is becoming cleaner! Your contribution is amazing!"

    elif resolved_percent >= 40:

        emotion_image = "images/neutral_madurai.png"

        slogan_tamil = "நாம் ஒன்றிணைந்து மதுரையை சுத்தமாக மாற்றலாம்!"
        slogan_english = "Together, we can make Madurai cleaner!"

    else:

        emotion_image = "images/sad_madurai.png"

        slogan_tamil = "மதுரைக்கு உங்கள் உதவி தேவை! இப்போதே செயல்படுங்கள்!"
        slogan_english = "Madurai needs your help! Act now!"

    return render_template(
        "citizen_dashboard.html",
        total_reports=total_reports,
        resolved_reports=resolved_reports,
        pending_reports=pending_reports,
        emotion_image=emotion_image,
        slogan_tamil=slogan_tamil,
        slogan_english=slogan_english
    )
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

        user_id = session['user_id']

        garbage_type = request.form.get('garbage_type')

        other_description = request.form.get('other_description')

        area = request.form.get('area')
        pincode = request.form.get('pincode')
        landmark = request.form.get('landmark')


        # FINAL CLEAN LOGIC
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

                flash(
                    "This image was already used in another report.",
                    "danger"
                )

                return redirect(url_for('auth.report'))

            image.save(image_path)

            image_name = filename

            cur.close()


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

        flash("Complaint submitted successfully!", "success")

        return redirect(url_for('auth.citizen_dashboard'))

    return render_template("report.html")







# ---------------- AUTHORITY DASHBOARD ----------------
@auth_bp.route("/authority")
def authority_dashboard():

    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='pending'")
    pending_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM complaints WHERE status='resolved'")
    resolved_complaints = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM cleaning_events")
    total_events = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM volunteers")
    total_volunteers = cur.fetchone()[0]

    cur.execute("SELECT COALESCE(SUM(points), 0) FROM carbon_credits")
    total_carbon_credits = cur.fetchone()[0]

    cur.close()

    return render_template(
        "authority_analytics.html",
        total_complaints=total_complaints,
        pending_complaints=pending_complaints,
        resolved_complaints=resolved_complaints,
        total_events=total_events,
        total_volunteers=total_volunteers,
        total_carbon_credits=total_carbon_credits
    )
@auth_bp.route("/authority/complaints")
def manage_complaints():

    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT complaint_id,
               garbage_type,
               description,
               image,
               area,
               pincode,
               landmark,
               status,
               created_at,
               vehicle_volunteer_id,
               transport_status
        FROM complaints
        ORDER BY created_at DESC
    """)

    complaints = cur.fetchall()

    cur.execute("""
        SELECT volunteer_id, vehicle_type, vehicle_number, vehicle_area
        FROM volunteers
        WHERE has_vehicle = TRUE AND vehicle_status = 'available'
    """)

    vehicle_volunteers = cur.fetchall()

    cur.close()

    return render_template(
        "authority_dashboard.html",
        complaints=complaints,
        vehicle_volunteers=vehicle_volunteers
    )

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

@auth_bp.route("/authority/assign_vehicle/<int:complaint_id>", methods=["POST"])
def assign_vehicle(complaint_id):

    if 'user_id' not in session or session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    volunteer_id = request.form["volunteer_id"]

    cur = mysql.connection.cursor()

    # Assign vehicle to complaint
    cur.execute("""
        UPDATE complaints
        SET vehicle_volunteer_id=%s,
            transport_status='assigned'
        WHERE complaint_id=%s
    """, (volunteer_id, complaint_id))

    # Mark vehicle as busy
    cur.execute("""
        UPDATE volunteers
        SET vehicle_status='busy'
        WHERE volunteer_id=%s
    """, (volunteer_id,))

    mysql.connection.commit()

    cur.close()

    flash("Vehicle assigned successfully!", "success")

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

    # Get volunteer info
    cur.execute("""
        SELECT volunteer_id, has_vehicle, vehicle_type, vehicle_number,
               vehicle_area, vehicle_status
        FROM volunteers
        WHERE user_id=%s
    """, (user_id,))

    volunteer = cur.fetchone()

    total_points = 0
    credit_history = []

    has_vehicle = False
    vehicle_type = None
    vehicle_number = None
    vehicle_area = None
    vehicle_status = None

    transport_assignments = []

    if volunteer:

        volunteer_id = volunteer[0]

        has_vehicle = volunteer[1]
        vehicle_type = volunteer[2]
        vehicle_number = volunteer[3]
        vehicle_area = volunteer[4]
        vehicle_status = volunteer[5]

        # Carbon credits
        cur.execute("""
            SELECT SUM(points)
            FROM carbon_credits
            WHERE volunteer_id=%s
        """, (volunteer_id,))

        result = cur.fetchone()

        total_points = result[0] if result[0] else 0

        # Credit history
        cur.execute("""
            SELECT points, activity, created_at
            FROM carbon_credits
            WHERE volunteer_id=%s
            ORDER BY created_at DESC
        """, (volunteer_id,))

        credit_history = cur.fetchall()

        # NEW: Transport assignments
        cur.execute("""
            SELECT complaint_id, area, landmark, transport_status
            FROM complaints
            WHERE vehicle_volunteer_id=%s
            ORDER BY created_at DESC
        """, (volunteer_id,))

        transport_assignments = cur.fetchall()

    cur.close()

    return render_template(
        "volunteer_dashboard.html",
        total_points=total_points,
        credit_history=credit_history,
        has_vehicle=has_vehicle,
        vehicle_type=vehicle_type,
        vehicle_number=vehicle_number,
        vehicle_area=vehicle_area,
        vehicle_status=vehicle_status,
        transport_assignments=transport_assignments
    )

@auth_bp.route("/volunteer/events")
def volunteer_events():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    cur = mysql.connection.cursor()

    # Get all events
    cur.execute("""
        SELECT event_id, title, area, event_date, credit_points, status
        FROM cleaning_events
        ORDER BY event_date DESC
    """)
    events = cur.fetchall()

    # Get events joined by this user
    cur.execute("""
        SELECT event_id FROM event_participants
        WHERE user_id=%s
    """, (user_id,))

    joined = cur.fetchall()

    joined_event_ids = [e[0] for e in joined]

    cur.close()

    return render_template(
        "volunteer_events.html",
        events=events,
        joined_event_ids=joined_event_ids
    )


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

@auth_bp.route("/register_vehicle", methods=["GET", "POST"])
def register_vehicle():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    if request.method == "POST":

        vehicle_type = request.form["vehicle_type"]
        vehicle_number = request.form["vehicle_number"]
        vehicle_area = request.form["vehicle_area"]

        user_id = session["user_id"]

        # Check if volunteer record exists
        cur.execute(
            "SELECT volunteer_id FROM volunteers WHERE user_id=%s",
            (user_id,)
        )

        volunteer = cur.fetchone()

        if volunteer:

            # Update existing volunteer
            cur.execute("""
                UPDATE volunteers
                SET has_vehicle = TRUE,
                    vehicle_type = %s,
                    vehicle_number = %s,
                    vehicle_area = %s,
                    vehicle_status = 'available'
                WHERE user_id = %s
            """, (vehicle_type, vehicle_number, vehicle_area, user_id))

        else:

            # Create volunteer record first
            cur.execute("""
                INSERT INTO volunteers
                (user_id, has_vehicle, vehicle_type, vehicle_number, vehicle_area, vehicle_status)
                VALUES (%s, TRUE, %s, %s, %s, 'available')
            """, (user_id, vehicle_type, vehicle_number, vehicle_area))

        mysql.connection.commit()
        cur.close()

        flash("Vehicle registered successfully!", "success")

        return redirect(url_for("auth.volunteer"))

    cur.close()

    return render_template("register_vehicle.html")

@auth_bp.route("/volunteer/transport_complete/<int:complaint_id>")
def transport_complete(complaint_id):

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get volunteer id first
    cur.execute("""
        SELECT vehicle_volunteer_id
        FROM complaints
        WHERE complaint_id=%s
    """, (complaint_id,))

    volunteer = cur.fetchone()

    if volunteer:

        volunteer_id = volunteer[0]

        # Update complaint
        cur.execute("""
            UPDATE complaints
            SET transport_status='completed',
                status='Resolved'
            WHERE complaint_id=%s
        """, (complaint_id,))

        # Make vehicle available again
        cur.execute("""
            UPDATE volunteers
            SET vehicle_status='available'
            WHERE volunteer_id=%s
        """, (volunteer_id,))

        mysql.connection.commit()

    cur.close()

    flash("Transport completed successfully!", "success")

    return redirect(url_for('auth.volunteer'))

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

    # Check if event already completed
    cur.execute(
        "SELECT status, credit_points FROM cleaning_events WHERE event_id=%s",
        (event_id,)
    )
    event = cur.fetchone()

    if not event:
        cur.close()
        flash("Event not found.", "danger")
        return redirect(url_for('auth.authority_events'))

    status, points = event

    # 🚨 SAFETY CHECK
    if status == "Completed":
        cur.close()
        flash("This event has already been completed and credits awarded.", "warning")
        return redirect(url_for('auth.authority_events'))

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

            # Insert credits
            cur.execute(
                """
                INSERT INTO carbon_credits
                (volunteer_id, points, activity)
                VALUES (%s, %s, %s)
                """,
                (
                    volunteer_id,
                    points,
                    "Cleaning Event Participation"
                )
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

    flash("Event completed and credits awarded successfully!", "success")

    return redirect(url_for('auth.authority_events'))


    

@auth_bp.route("/locate-waste")
def locate_waste():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    return render_template("locate_waste.html")

@auth_bp.route("/awareness/tourism")
def tourism():
    return render_template("awareness/tourism.html")


@auth_bp.route("/awareness/temples")
def temples():
    return render_template("awareness/temples.html")


@auth_bp.route("/awareness/food")
def food():
    return render_template("awareness/food.html")


@auth_bp.route("/awareness/guidelines")
def guidelines():
    return render_template("awareness/guidelines.html")

@auth_bp.route("/donate", methods=["GET", "POST"])
def donate():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    if request.method == "POST":

        try:
            amount = float(request.form['amount'])

            if amount <= 0:
                flash("Invalid donation amount.", "danger")
                return redirect(url_for('auth.donate'))

            # Insert donation
            cur.execute("""
                INSERT INTO donations (user_id, amount)
                VALUES (%s, %s)
            """, (session['user_id'], amount))

            # Update fund wallet
            cur.execute("""
                UPDATE fund_wallet
                SET total_balance = total_balance + %s
                WHERE id = 1
            """, (amount,))

            mysql.connection.commit()

            flash("Thank you for your donation ❤️", "success")

        except Exception as e:
            flash("Something went wrong.", "danger")

        return redirect(url_for('auth.donate'))

    # Get wallet balance
    cur.execute("SELECT total_balance FROM fund_wallet WHERE id = 1")
    result = cur.fetchone()
    total_balance = result[0] if result else 0

    cur.close()

    return render_template(
        "emergency/donate.html",
        total_balance=total_balance
    )

@auth_bp.route("/emergency/request", methods=["GET", "POST"])
def emergency_request():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # 🔒 Check if user already has active request
    cur.execute("""
        SELECT request_id, status
        FROM emergency_requests
        WHERE user_id=%s
        AND status IN ('pending','paid')
    """, (session['user_id'],))

    existing = cur.fetchone()

    if existing:
        cur.close()
        return redirect(url_for('auth.emergency_status'))

    if request.method == "POST":

        reason = request.form.get("reason")
        amount_requested = float(request.form.get("amount"))

        # 🚨 Cap amount to ₹1000
        if amount_requested > 1000:
            flash("Maximum assistance allowed is ₹1000.", "danger")
            return redirect(url_for('auth.emergency_request'))

        # Get uploaded images
        aadhaar_image = request.files.get("aadhaar_image")
        selfie_image = request.files.get("selfie_image")

        if not aadhaar_image or not selfie_image:
            flash("Both Aadhaar and Selfie images are required.", "danger")
            return redirect(url_for('auth.emergency_request'))

        # Save images
        aadhaar_filename = secure_filename(aadhaar_image.filename)
        selfie_filename = secure_filename(selfie_image.filename)

        aadhaar_path = os.path.join(UPLOAD_FOLDER, aadhaar_filename)
        selfie_path = os.path.join(UPLOAD_FOLDER, selfie_filename)

        aadhaar_image.save(aadhaar_path)
        selfie_image.save(selfie_path)

        # 🤖 AI Verification
        try:
            result = DeepFace.verify(
                img1_path=aadhaar_path,
                img2_path=selfie_path,
                model_name="VGG-Face",
                enforce_detection=False
            )

            distance = result["distance"]
            verified = result["verified"]

        except Exception as e:
            flash("Face verification failed. Try again.", "danger")
            return redirect(url_for('auth.emergency_request'))

        # 🔐 Threshold check (strict)
        if distance > 0.60:
            flash("Face verification failed. Identity mismatch.", "danger")
            return redirect(url_for('auth.emergency_request'))

        # Insert into DB
        cur.execute("""
            INSERT INTO emergency_requests
            (user_id, reason, aadhaar_image, selfie_image,
             amount_requested, ai_distance, status, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', NOW())
        """, (
            session['user_id'],
            reason,
            aadhaar_filename,
            selfie_filename,
            amount_requested,
            distance
        ))

        mysql.connection.commit()
        cur.close()

        flash("Emergency request submitted successfully.", "success")
        return redirect(url_for('auth.emergency_status'))

    cur.close()
    return render_template("emergency/request_help.html")

@auth_bp.route("/authority/emergency")
def view_emergency_requests():

    if session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get all emergency requests
    cur.execute("SELECT * FROM emergency_requests ORDER BY created_at DESC")
    requests = cur.fetchall()

    # Get current wallet balance
    cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
    wallet_balance = cur.fetchone()[0]

    cur.close()

    return render_template(
        "emergency/admin_requests.html",
        requests=requests,
        wallet_balance=wallet_balance
    )

@auth_bp.route("/authority/emergency/approve/<int:request_id>", methods=["POST"])
def approve_emergency(request_id):

    if session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get request details including status
    cur.execute("""
        SELECT amount_requested, status
        FROM emergency_requests
        WHERE request_id=%s
    """, (request_id,))
    result = cur.fetchone()

    if not result:
        flash("Request not found.", "danger")
        return redirect(url_for('auth.view_emergency_requests'))

    amount = float(result[0])
    status = result[1]

    # 🚨 Lock check
    if status != 'pending':
        flash("This request cannot be modified.", "danger")
        return redirect(url_for('auth.view_emergency_requests'))

    # Check wallet balance
    cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
    wallet = float(cur.fetchone()[0])

    if wallet < amount:
        flash("Insufficient fund balance.", "danger")
        return redirect(url_for('auth.view_emergency_requests'))

    # Deduct wallet
    cur.execute("""
        UPDATE fund_wallet
        SET total_balance = total_balance - %s
        WHERE id = 1
    """, (amount,))

    # Mark request as paid
    cur.execute("""
        UPDATE emergency_requests
        SET status='paid', approved_at=NOW()
        WHERE request_id=%s
    """, (request_id,))

    mysql.connection.commit()
    cur.close()

    flash("Emergency request approved and paid.", "success")
    return redirect(url_for('auth.view_emergency_requests'))

@auth_bp.route("/authority/emergency/reject/<int:request_id>", methods=["POST"])
def reject_emergency(request_id):

    if session.get('role') != 'authority':
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    # Get current status
    cur.execute("SELECT status FROM emergency_requests WHERE request_id=%s", (request_id,))
    result = cur.fetchone()

    if not result:
        flash("Request not found.", "danger")
        return redirect(url_for('auth.view_emergency_requests'))

    status = result[0]

    # 🚨 Prevent rejecting paid requests
    if status != 'pending':
        flash("This request cannot be modified.", "danger")
        return redirect(url_for('auth.view_emergency_requests'))

    cur.execute("""
        UPDATE emergency_requests
        SET status='rejected'
        WHERE request_id=%s
    """, (request_id,))

    mysql.connection.commit()
    cur.close()

    flash("Emergency request rejected.", "warning")
    return redirect(url_for('auth.view_emergency_requests'))

@auth_bp.route("/emergency/status")
def emergency_status():

    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    cur = mysql.connection.cursor()

    cur.execute("""
        SELECT request_id, reason, amount_requested,
               status, created_at, approved_at
        FROM emergency_requests
        WHERE user_id=%s
        ORDER BY created_at DESC
        LIMIT 1
    """, (session['user_id'],))

    request_data = cur.fetchone()
    cur.close()

    return render_template("emergency/status.html",
                           request_data=request_data)

