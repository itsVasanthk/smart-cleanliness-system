from flask import Blueprint, render_template, session, redirect, url_for
from app import mysql

volunteer_bp = Blueprint('volunteer', __name__)

@volunteer_bp.route("/volunteer")
def volunteer_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT volunteer_id FROM volunteers WHERE user_id=%s", (user_id,))
    volunteer = cur.fetchone()

    total_points = 0

    if volunteer:
        cur.execute(
            "SELECT COALESCE(SUM(points),0) FROM carbon_credits WHERE volunteer_id=%s",
            (volunteer[0],)
        )
        total_points = cur.fetchone()[0]

    cur.close()

    return render_template(
        "volunteer_dashboard.html",
        is_volunteer=bool(volunteer),
        total_points=total_points
    )


@volunteer_bp.route("/volunteer/join")
def join_volunteer():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM volunteers WHERE user_id=%s", (user_id,))
    exists = cur.fetchone()

    if not exists:
        cur.execute("INSERT INTO volunteers (user_id) VALUES (%s)", (user_id,))
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('volunteer.volunteer_dashboard'))


@volunteer_bp.route("/volunteer/earn")
def earn_credits():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Get volunteer ID
    cur.execute("SELECT volunteer_id FROM volunteers WHERE user_id=%s", (user_id,))
    volunteer = cur.fetchone()

    if not volunteer:
        cur.close()
        return redirect(url_for('volunteer.volunteer_dashboard'))

    volunteer_id = volunteer[0]

    # Simulation: fixed points for one clean-up activity
    points = 10
    activity = "Community Clean-up Drive"

    cur.execute(
        """
        INSERT INTO carbon_credits (volunteer_id, points, activity)
        VALUES (%s, %s, %s)
        """,
        (volunteer_id, points, activity)
    )

    mysql.connection.commit()
    cur.close()

    return redirect(url_for('volunteer.volunteer_dashboard'))


@volunteer_bp.route("/volunteer/events")
def view_events():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Fetch upcoming events
    cur.execute(
        """
        SELECT event_id, title, area, event_date, credit_points
        FROM cleaning_events
        WHERE status = 'Upcoming'
        ORDER BY event_date ASC
        """
    )
    events = cur.fetchall()

    # Events already joined by this user
    cur.execute(
        "SELECT event_id FROM event_participants WHERE user_id=%s",
        (user_id,)
    )
    joined = [row[0] for row in cur.fetchall()]

    cur.close()

    return render_template(
        "volunteer_events.html",
        events=events,
        joined_events=joined
    )


@volunteer_bp.route("/volunteer/join_event/<int:event_id>")
def join_event(event_id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    user_id = session['user_id']

    cur = mysql.connection.cursor()

    # Prevent duplicate join
    cur.execute(
        """
        SELECT * FROM event_participants
        WHERE event_id=%s AND user_id=%s
        """,
        (event_id, user_id)
    )
    exists = cur.fetchone()

    if not exists:
        cur.execute(
            """
            INSERT INTO event_participants (event_id, user_id)
            VALUES (%s, %s)
            """,
            (event_id, user_id)
        )
        mysql.connection.commit()

    cur.close()
    return redirect(url_for('volunteer.view_events'))

