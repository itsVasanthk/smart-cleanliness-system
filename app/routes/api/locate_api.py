from flask import Blueprint, jsonify
from app import mysql

api_locate_bp = Blueprint('api_locate', __name__)

# Official Madurai Waste Disposal & Transit Points
MADURAI_DISPOSAL_SITES = [
    {
        "id": 1,
        "name": "Vellaikkal Main Waste Yard",
        "type": "Primary Dump Yard & Processing",
        "latitude": 9.8732,
        "longitude": 78.1456,
        "description": "Main processing center for Madurai city waste.",
        "status": "Green"
    },
    {
        "id": 2,
        "name": "Anna Nagar Transit Point",
        "type": "Waste Collection Center",
        "latitude": 9.9189,
        "longitude": 78.1404,
        "description": "Secondary collection point for East Madurai.",
        "status": "Accessible"
    },
    {
        "id": 3,
        "name": "Sellur Collection Center",
        "type": "Regional Bin Point",
        "latitude": 9.9421,
        "longitude": 78.1189,
        "description": "Local disposal point for Sellur area.",
        "status": "Accessible"
    },
    {
        "id": 4,
        "name": "Simmakkal Central Micro-Center",
        "type": "Micro-Composting Center",
        "latitude": 9.9252,
        "longitude": 78.1194,
        "description": "Organic waste processing center near Central Market.",
        "status": "Green"
    },
    {
        "id": 5,
        "name": "Periyar Bus Stand Transit Point",
        "type": "Rapid Collection Bin",
        "latitude": 9.9174,
        "longitude": 78.1118,
        "description": "Temporary bin for high-traffic commuter waste.",
        "status": "Accessible"
    },
    {
        "id": 6,
        "name": "K.Pudur Micro-composting Center",
        "type": "MCC Center",
        "latitude": 9.9436,
        "longitude": 78.1487,
        "description": "Wastes are converted to manure here.",
        "status": "Green"
    }
]

@api_locate_bp.route("/locate-waste", methods=["GET"])
def get_waste_areas():
    try:
        # In a real app, we could also fetch resolved reports from the DB
        # for now, we provide the official official spots
        return jsonify({
            "success": True,
            "data": MADURAI_DISPOSAL_SITES
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
