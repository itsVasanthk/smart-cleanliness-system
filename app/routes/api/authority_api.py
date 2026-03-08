from flask import Blueprint, jsonify, request
from app import mysql

api_authority_bp = Blueprint('api_authority', __name__)

# ---------------- AUTHORITY DASHBOARD STATS ----------------
@api_authority_bp.route("/authority/stats", methods=["GET"])
def get_authority_stats():
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

    cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
    fund_balance = cur.fetchone()[0]
    
    cur.close()
    
    return jsonify({
        "total_complaints": total_complaints,
        "pending_complaints": pending_complaints,
        "resolved_complaints": resolved_complaints,
        "total_events": total_events,
        "total_volunteers": total_volunteers,
        "total_carbon_credits": total_carbon_credits,
        "fund_balance": float(fund_balance)
    })

# ---------------- MANAGE COMPLAINTS ----------------
@api_authority_bp.route("/authority/complaints", methods=["GET"])
def get_all_complaints():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT complaint_id, garbage_type, description, image, area, 
               pincode, landmark, status, created_at, transport_status
        FROM complaints
        ORDER BY created_at DESC
    """)
    complaints_data = cur.fetchall()
    
    complaints = [
        {
            "id": c[0],
            "type": c[1],
            "description": c[2],
            "image": c[3],
            "area": c[4],
            "pincode": c[5],
            "landmark": c[6],
            "status": c[7],
            "created_at": c[8].strftime("%Y-%m-%d %H:%M:%S"),
            "transport_status": c[9]
        } for c in complaints_data
    ]
    
    cur.close()
    return jsonify(complaints)

# ---------------- GET AVAILABLE VEHICLES ----------------
@api_authority_bp.route("/authority/vehicles/available", methods=["GET"])
def get_available_vehicles():
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT volunteer_id, vehicle_type, vehicle_number, vehicle_area, u.name
        FROM volunteers v
        JOIN users u ON v.user_id = u.user_id
        WHERE v.has_vehicle = TRUE AND v.vehicle_status = 'available'
    """)
    vehicles_data = cur.fetchall()
    
    vehicles = [
        {
            "id": v[0],
            "type": v[1],
            "number": v[2],
            "area": v[3],
            "volunteer_name": v[4]
        } for v in vehicles_data
    ]
    
    cur.close()
    return jsonify(vehicles)

# ---------------- ASSIGN VEHICLE ----------------
@api_authority_bp.route("/authority/assign_vehicle", methods=["POST"])
def assign_vehicle():
    data = request.json
    complaint_id = data.get('complaint_id')
    volunteer_id = data.get('volunteer_id')
    
    cur = mysql.connection.cursor()
    
    # Assign vehicle to complaint
    cur.execute("""
        UPDATE complaints 
        SET vehicle_volunteer_id=%s, transport_status='assigned' 
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
    
    return jsonify({"success": True})

# ---------------- CREATE EVENT ----------------
@api_authority_bp.route("/authority/events", methods=["POST"])
def create_event():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    area = data.get('area')
    date = data.get('date')
    points = data.get('points', 100)
    created_by = data.get('created_by')
    
    cur = mysql.connection.cursor()
    cur.execute("""
        INSERT INTO cleaning_events (title, description, area, event_date, credit_points, created_by, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'upcoming')
    """, (title, description, area, date, points, created_by))
    mysql.connection.commit()
    cur.close()
    
    return jsonify({"success": True, "message": "Event created successfully"})

# ---------------- GET EVENT PARTICIPANTS ----------------
@api_authority_bp.route("/authority/events/<int:event_id>/participants", methods=["GET"])
def get_event_participants(event_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT u.name, u.email, p.joined_at
        FROM event_participants p
        JOIN users u ON p.user_id = u.user_id
        WHERE p.event_id = %s
        ORDER BY p.joined_at DESC
    """, (event_id,))
    participants_data = cur.fetchall()
    cur.close()
    
    participants = [
        {
            "name": p[0],
            "email": p[1],
            "joined_at": p[2].strftime("%Y-%m-%d %H:%M:%S")
        } for p in participants_data
    ]
    
    return jsonify(participants)

