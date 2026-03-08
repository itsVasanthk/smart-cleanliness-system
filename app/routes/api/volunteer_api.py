from flask import Blueprint, jsonify, request
from app import mysql

api_volunteer_bp = Blueprint('api_volunteer', __name__)

# ---------------- VOLUNTEER STATS & HISTORY ----------------
@api_volunteer_bp.route("/volunteer/stats/<int:user_id>", methods=["GET"])
def get_volunteer_stats(user_id):
    cur = mysql.connection.cursor()
    
    # Get volunteer details
    cur.execute("""
        SELECT volunteer_id, has_vehicle, vehicle_type, vehicle_number, 
               vehicle_area, vehicle_status
        FROM volunteers
        WHERE user_id=%s
    """, (user_id,))
    volunteer = cur.fetchone()
    
    if not volunteer:
        cur.close()
        return jsonify({
            "has_volunteer_profile": False,
            "total_points": 0,
            "credit_history": [],
            "transport_assignments": []
        })

    volunteer_id = volunteer[0]
    has_vehicle = bool(volunteer[1])
    
    # Get total carbon credits
    cur.execute("SELECT SUM(points) FROM carbon_credits WHERE volunteer_id=%s", (volunteer_id,))
    total_points = cur.fetchone()[0] or 0
    
    # Get credit history
    cur.execute("""
        SELECT points, activity, created_at 
        FROM carbon_credits 
        WHERE volunteer_id=%s 
        ORDER BY created_at DESC
    """, (volunteer_id,))
    credits = cur.fetchall()
    credit_history = [
        {"points": c[0], "activity": c[1], "date": c[2].strftime("%Y-%m-%d %H:%M:%S")} 
        for c in credits
    ]
    
    # Get transport assignments
    cur.execute("""
        SELECT complaint_id, area, landmark, transport_status
        FROM complaints
        WHERE vehicle_volunteer_id=%s
        ORDER BY created_at DESC
    """, (volunteer_id,))
    assignments = cur.fetchall()
    transport_assignments = [
        {
            "complaint_id": a[0], 
            "area": a[1], 
            "landmark": a[2], 
            "status": a[3]
        } for a in assignments
    ]
    
    cur.close()
    return jsonify({
        "has_volunteer_profile": True,
        "volunteer_id": volunteer_id,
        "has_vehicle": has_vehicle,
        "vehicle_details": {
            "type": volunteer[2],
            "number": volunteer[3],
            "area": volunteer[4],
            "status": volunteer[5]
        } if has_vehicle else None,
        "total_points": total_points,
        "credit_history": credit_history,
        "transport_assignments": transport_assignments
    })

# ---------------- LIST CLEANING EVENTS ----------------
@api_volunteer_bp.route("/volunteer/events", methods=["GET"])
def get_events():
    user_id = request.args.get('user_id', type=int)
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT event_id, title, area, description, event_date, credit_points, status
        FROM cleaning_events
        ORDER BY event_date DESC
    """)
    events_data = cur.fetchall()
    
    joined_event_ids = []
    if user_id:
        cur.execute("SELECT event_id FROM event_participants WHERE user_id=%s", (user_id,))
        joined = cur.fetchall()
        joined_event_ids = [e[0] for e in joined]
    
    events = [
        {
            "id": e[0],
            "title": e[1],
            "area": e[2],
            "description": e[3],
            "date": e[4].strftime("%Y-%m-%d"),
            "points": e[5],
            "status": e[6],
            "is_joined": e[0] in joined_event_ids
        } for e in events_data
    ]
    
    cur.close()
    return jsonify(events)

# ---------------- JOIN EVENT ----------------
@api_volunteer_bp.route("/volunteer/join", methods=["POST"])
def join_event():
    data = request.json
    user_id = data.get('user_id')
    event_id = data.get('event_id')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT participant_id FROM event_participants WHERE event_id=%s AND user_id=%s", (event_id, user_id))
    if cur.fetchone():
        cur.close()
        return jsonify({"success": False, "message": "Already joined"}), 400
        
    cur.execute("INSERT INTO event_participants (event_id, user_id) VALUES (%s, %s)", (event_id, user_id))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"success": True, "message": "Joined successfully"})

# ---------------- REGISTER VEHICLE ----------------
@api_volunteer_bp.route("/volunteer/register_vehicle", methods=["POST"])
def register_vehicle():
    data = request.json
    user_id = data.get('user_id')
    v_type = data.get('type')
    v_number = data.get('number')
    v_area = data.get('area')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT volunteer_id FROM volunteers WHERE user_id=%s", (user_id,))
    volunteer = cur.fetchone()
    
    if volunteer:
        cur.execute("""
            UPDATE volunteers 
            SET has_vehicle = TRUE, vehicle_type = %s, vehicle_number = %s, 
                vehicle_area = %s, vehicle_status = 'available'
            WHERE user_id = %s
        """, (v_type, v_number, v_area, user_id))
    else:
        cur.execute("""
            INSERT INTO volunteers (user_id, has_vehicle, vehicle_type, vehicle_number, vehicle_area, vehicle_status)
            VALUES (%s, TRUE, %s, %s, %s, 'available')
        """, (user_id, v_type, v_number, v_area))
        
    mysql.connection.commit()
    cur.close()
    return jsonify({"success": True})

# ---------------- MARK TRANSPORT COMPLETE ----------------
@api_volunteer_bp.route("/volunteer/transport_complete", methods=["POST"])
def transport_complete():
    data = request.json
    complaint_id = data.get('complaint_id')
    
    cur = mysql.connection.cursor()
    cur.execute("SELECT vehicle_volunteer_id FROM complaints WHERE complaint_id=%s", (complaint_id,))
    volunteer = cur.fetchone()
    
    if volunteer:
        volunteer_id = volunteer[0]
        cur.execute("UPDATE complaints SET transport_status='completed', status='Resolved' WHERE complaint_id=%s", (complaint_id,))
        cur.execute("UPDATE volunteers SET vehicle_status='available' WHERE volunteer_id=%s", (volunteer_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True})
    
    cur.close()
    return jsonify({"success": False, "message": "Assignment not found"}), 404

# ---------------- LEADERBOARD ----------------
@api_volunteer_bp.route("/volunteer/leaderboard", methods=["GET"])
def get_leaderboard():
    cur = mysql.connection.cursor()
    
    # Aggregate total points per user from carbon_credits table
    cur.execute("""
        SELECT u.name, COALESCE(SUM(cc.points), 0) as total_points
        FROM users u
        JOIN volunteers v ON u.user_id = v.user_id
        LEFT JOIN carbon_credits cc ON v.volunteer_id = cc.volunteer_id
        GROUP BY u.user_id, u.name
        ORDER BY total_points DESC
        LIMIT 10
    """)
    leaderboard_data = cur.fetchall()
    cur.close()

    leaderboard = [
        {"name": row[0], "points": int(row[1]), "rank": i + 1}
        for i, row in enumerate(leaderboard_data)
    ]
    
    return jsonify(leaderboard)
