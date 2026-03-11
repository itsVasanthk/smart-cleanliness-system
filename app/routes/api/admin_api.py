from flask import Blueprint, jsonify, request
from app import mysql
from datetime import datetime

api_admin_bp = Blueprint('api_admin', __name__)

# ---------------- ADMIN DASHBOARD STATS ----------------
@api_admin_bp.route("/admin/stats", methods=["GET"])
def get_admin_stats():
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT COUNT(*) FROM complaints WHERE escalated_to_admin = TRUE OR (status = 'pending' AND created_at < NOW() - INTERVAL 48 HOUR)")
    escalated_count = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM volunteers")
    total_volunteers = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM volunteers WHERE has_vehicle = TRUE")
    total_vehicles = cur.fetchone()[0]
    
    cur.execute("SELECT total_balance FROM fund_wallet WHERE id=1")
    fund_balance = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM cleaning_events")
    total_events = cur.fetchone()[0]

    cur.close()
    
    return jsonify({
        "escalated_reports": escalated_count,
        "total_volunteers": total_volunteers,
        "total_vehicles": total_vehicles,
        "fund_balance": float(fund_balance),
        "total_events": total_events
    })

# ---------------- GET ESCALATED COMPLAINTS ----------------
@api_admin_bp.route("/admin/complaints/escalated", methods=["GET"])
def get_escalated_complaints():
    cur = mysql.connection.cursor()
    
    # Logic: Explicitly escalated OR older than 48h and still pending
    # Also return the count of volunteers joined for each report
    cur.execute("""
        SELECT c.complaint_id, c.garbage_type, c.description, c.image, c.area, 
               c.pincode, c.landmark, c.status, c.created_at, c.transport_status,
               c.authority_decision, c.authority_reason, c.escalated_at,
               (SELECT COUNT(*) FROM complaint_volunteers cv WHERE cv.complaint_id = c.complaint_id) as volunteer_count
        FROM complaints c
        WHERE c.escalated_to_admin = TRUE 
           OR (c.status = 'pending' AND c.created_at < NOW() - INTERVAL 48 HOUR)
        ORDER BY c.created_at DESC
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
            "transport_status": c[9],
            "authority_decision": c[10],
            "authority_reason": c[11],
            "escalated_at": c[12].strftime("%Y-%m-%d %H:%M:%S") if c[12] else None,
            "volunteer_count": c[13]
        } for c in complaints_data
    ]
    
    cur.close()
    return jsonify(complaints)

@api_admin_bp.route("/admin/escalate_to_hub", methods=["POST"])
def escalate_to_hub():
    data = request.json
    complaint_id = data.get('complaint_id')
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("UPDATE complaints SET status='Awaiting Volunteers' WHERE complaint_id=%s", (complaint_id,))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Report escalated to Volunteer Hub"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_admin_bp.route("/admin/complaints/<int:complaint_id>/volunteers", methods=["GET"])
def get_joined_volunteers(complaint_id):
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT v.volunteer_id, u.name, cv.joined_at, v.vehicle_type, v.vehicle_number
        FROM complaint_volunteers cv
        JOIN users u ON cv.user_id = u.user_id
        JOIN volunteers v ON u.user_id = v.user_id
        WHERE cv.complaint_id = %s
        ORDER BY cv.joined_at DESC
    """, (complaint_id,))
    volunteers_data = cur.fetchall()
    
    volunteers = [
        {
            "volunteer_id": v[0],
            "name": v[1],
            "joined_at": v[2].strftime("%Y-%m-%d %H:%M:%S"),
            "vehicle_type": v[3],
            "vehicle_number": v[4]
        } for v in volunteers_data
    ]
    
    cur.close()
    return jsonify(volunteers)

# ---------------- MANAGE VEHICLES (Moved from Authority) ----------------
@api_admin_bp.route("/admin/vehicles/available", methods=["GET"])
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

@api_admin_bp.route("/admin/assign_vehicle", methods=["POST"])
def assign_vehicle():
    data = request.json
    complaint_id = data.get('complaint_id')
    volunteer_id = data.get('volunteer_id')
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            UPDATE complaints 
            SET vehicle_volunteer_id=%s, transport_status='assigned', status='Assigning Volunteer'
            WHERE complaint_id=%s
        """, (volunteer_id, complaint_id))
        
        cur.execute("""
            UPDATE volunteers 
            SET vehicle_status='busy' 
            WHERE volunteer_id=%s
        """, (volunteer_id,))
        
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Vehicle and volunteer assigned successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ---------------- MANAGE EVENTS (Moved from Authority) ----------------
@api_admin_bp.route("/admin/events", methods=["POST"])
def create_event():
    data = request.json
    title = data.get('title')
    description = data.get('description')
    area = data.get('area')
    date = data.get('date')
    points = data.get('points', 100)
    created_by = data.get('created_by')
    
    cur = mysql.connection.cursor()
    try:
        cur.execute("""
            INSERT INTO cleaning_events (title, description, area, event_date, credit_points, created_by, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'upcoming')
        """, (title, description, area, date, points, created_by))
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": "Event created successfully by Admin"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
