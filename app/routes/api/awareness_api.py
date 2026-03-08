from flask import Blueprint, jsonify

api_awareness_bp = Blueprint('api_awareness', __name__)

@api_awareness_bp.route("/awareness/data", methods=["GET"])
def get_awareness_data():
    # In a real app, this might come from a DB, 
    # but based on the current website routes, it's static content.
    data = {
        "tourism": {
            "title": "Madurai Tourism",
            "content": "Explore the vibrant culture and history of Madurai. Keep our tourist spots clean!"
        },
        "temples": {
            "title": "Divine Temples",
            "content": "Madurai is the city of temples. Maintain the sanctity by avoiding littering."
        },
        "food": {
            "title": "Madurai Food Culture",
            "content": "From Jigarthanda to Parotta, enjoy Madurai's food responsibly. Dispose of waste properly."
        },
        "guidelines": {
            "title": "Cleanliness Guidelines",
            "content": "Follow these rules to keep Madurai smart and clean: Segregate waste, use bins, etc."
        }
    }
    return jsonify(data)
