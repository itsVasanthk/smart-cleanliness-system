from flask import Blueprint, jsonify, request
from app import mysql
from datetime import datetime

api_authority_bp = Blueprint('api_authority', __name__)

# ---------------- AUTHORITY DASHBOARD STATS ----------------
@api_authority_bp.route("/authority/stats", methods=["GET"])
def get_authority_stats():
    cur = mysql.connection.cursor()
    
    cur.execute("SELECT COUNT(*) FROM complaints")
    total_complaints = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM complaints WHERE authority_decision='pending' AND status='pending'")
    pending_decisions = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM complaints WHERE authority_decision='agreed'")
    agreed_complaints = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM complaints WHERE authority_decision='disagreed'")
    disagreed_complaints = cur.fetchone()[0]
    
    cur.close()
    
    return jsonify({
        "total_complaints": total_complaints,
        "pending_decisions": pending_decisions,
        "agreed_complaints": agreed_complaints,
        "disagreed_complaints": disagreed_complaints
    })

# ---------------- MANAGE COMPLAINTS ----------------
@api_authority_bp.route("/authority/complaints", methods=["GET"])
def get_all_complaints():
    cur = mysql.connection.cursor()
    
    cur.execute("""
        SELECT complaint_id, garbage_type, description, image, area, 
               pincode, landmark, status, created_at, transport_status,
               authority_decision, authority_reason
        FROM complaints
        WHERE escalated_to_admin = FALSE
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
            "transport_status": c[9],
            "authority_decision": c[10],
            "authority_reason": c[11]
        } for c in complaints_data
    ]
    
    cur.close()
    return jsonify(complaints)

# ---------------- AUTHORITY DECISION ----------------
@api_authority_bp.route("/authority/decide", methods=["POST"])
def authority_decide():
    data = request.json
    complaint_id = data.get('complaint_id')
    decision = data.get('decision') # 'agreed' or 'disagreed'
    reason = data.get('reason', '')
    
    if decision not in ['agreed', 'disagreed']:
        return jsonify({"success": False, "message": "Invalid decision"}), 400
        
    cur = mysql.connection.cursor()
    
    try:
        if decision == 'agreed':
            # If agreed, it moves to 'Under Process' (or similar)
            cur.execute("""
                UPDATE complaints 
                SET authority_decision=%s, status='Under Process'
                WHERE complaint_id=%s
            """, (decision, complaint_id))
        else:
            # If disagreed, it describes reason and is escalated to admin
            cur.execute("""
                UPDATE complaints 
                SET authority_decision=%s, authority_reason=%s, escalated_to_admin=TRUE, escalated_at=NOW()
                WHERE complaint_id=%s
            """, (decision, reason, complaint_id))
            
        mysql.connection.commit()
        cur.close()
        return jsonify({"success": True, "message": f"Decision '{decision}' recorded successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

