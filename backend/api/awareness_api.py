from flask import Blueprint, jsonify

api_awareness_bp = Blueprint('api_awareness', __name__)

AWARENESS_DATA = {
    "tourism": [
        {
            "id": 1,
            "name": "Meenakshi Amman Temple",
            "description": "One of the most iconic temples in India located at the heart of Madurai. Known for its magnificent gopurams and spiritual importance.",
            "timings": "5:00 AM – 12:30 PM, 4:00 PM – 9:30 PM",
            "duration": "2 – 3 Hours",
            "bus_routes": {
                "Periyar Bus Stand": "5A, 5B, 10A, 12B",
                "Mattuthavani": "70, 70A, 70B",
                "Arapalayam": "2B, 12B"
            },
            "cleanliness_tips": [
                "Avoid plastic carry bags",
                "Use designated dustbins",
                "Do not litter flowers or food waste"
            ],
            "image": "meenakshi_temple.jpg"
        },
        {
            "id": 2,
            "name": "Thirumalai Nayakkar Mahal",
            "description": "A 17th-century palace showcasing Indo-Saracenic architecture and one of Madurai’s major heritage attractions.",
            "timings": "10:00 AM – 5:00 PM",
            "duration": "1 – 1.5 Hours",
            "bus_routes": {
                "Periyar Bus Stand": "5A, 5B, 8A",
                "Mattuthavani": "70, 70B",
                "Arapalayam": "2B, 5A"
            },
            "cleanliness_tips": [
                "Maintain heritage cleanliness",
                "Do not damage public property",
                "Use dustbins provided"
            ],
            "image": "nayakkar_mahal.jpg"
        },
        {
            "id": 3,
            "name": "Gandhi Memorial Museum",
            "description": "A museum dedicated to Mahatma Gandhi preserving rare artifacts from India’s freedom movement.",
            "timings": "10:00 AM – 5:00 PM (Closed on Fridays)",
            "duration": "1.5 – 2 Hours",
            "bus_routes": {
                "Periyar Bus Stand": "4B, 7A, 9B",
                "Mattuthavani": "27C, 70",
                "Arapalayam": "2B, 7A"
            },
            "cleanliness_tips": [
                "Avoid littering inside campus",
                "Respect museum property",
                "Maintain silence and discipline"
            ],
            "image": "gandhi_museum.jpg"
        }
    ],
    "temples": [
        {
            "id": 4,
            "name": "Alagar Kovil",
            "description": "A scenic temple located in the Alagar Hills, known for its peaceful atmosphere and religious importance.",
            "timings": "6:00 AM – 12:30 PM, 4:00 PM – 8:00 PM",
            "duration": "1 – 2 Hours",
            "bus_routes": {
                "Periyar Bus Stand": "44, 44A",
                "Mattuthavani": "44A",
                "Arapalayam": "44"
            },
            "cleanliness_tips": [
                "Avoid littering in hill areas",
                "Carry reusable water bottles",
                "Maintain natural surroundings"
            ],
            "image": "alagar_kovil.jpg"
        },
        {
            "id": 5,
            "name": "Tirupparankundram Murugan Temple",
            "description": "One of the oldest and most revered Murugan temples in Tamil Nadu, located on the scenic Tirupparankundram Hill.",
            "timings": "5:30 AM – 12:30 PM, 4:00 PM – 8:30 PM",
            "duration": "1 – 1.5 Hours",
            "bus_routes": {
                "Periyar Bus Stand": "22, 23, 24",
                "Mattuthavani": "70, 70A",
                "Arapalayam": "2B"
            },
            "cleanliness_tips": [
                "Dispose offerings responsibly",
                "Avoid plastics/single-use items",
                "Respect the hill temple environment"
            ],
            "image": "tirupparankundram.jpg"
        },
        {
            "id": 6,
            "name": "Tallakulam Prasanna Venkatachalapathy Temple",
            "description": "A well-known Vishnu temple located in Tallakulam, Madurai. A peaceful spiritual destination.",
            "timings": "6:00 AM – 12:00 PM, 4:00 PM – 8:30 PM",
            "duration": "45 Minutes – 1 Hour",
            "bus_routes": {
                "Periyar Bus Stand": "7A, 9B",
                "Mattuthavani": "70, 70A",
                "Arapalayam": "2B"
            },
            "cleanliness_tips": [
                "Maintain silence and discipline",
                "Dispose temple offerings responsibly",
                "Avoid plastic usage inside premises"
            ],
            "image": "tallakulam_temple.jpg"
        }
    ],
    "food": [
        {
            "id": 7,
            "name": "Murugan Idli Shop",
            "description": "Famous vegetarian restaurant known for its soft idlis, chutneys, and traditional South Indian meals.",
            "timings": "6:00 AM – 10:30 PM",
            "must_try": ["Idli with 4 chutneys", "Ghee Podi Dosa", "Sweet Pongal"],
            "bus_routes": {
                "Periyar Bus Stand": "5A, 12B",
                "Mattuthavani": "70, 70A",
                "Arapalayam": "2B"
            },
            "hygiene_tips": [
                "Dispose food waste in bins",
                "Avoid littering outside restaurant",
                "Use eco-friendly packaging"
            ],
            "image": "murugan_idli.jpg"
        },
        {
            "id": 8,
            "name": "Amma Mess",
            "description": "Famous for authentic Chettinad-style non-vegetarian dishes. A must-visit for food lovers.",
            "timings": "11:00 AM – 4:00 PM & 7:00 PM – 11:00 PM",
            "must_try": ["Mutton Curry", "Brain Fry", "Chicken Chukka"],
            "bus_routes": {
                "Periyar Bus Stand": "5A, 8A",
                "Mattuthavani": "70",
                "Arapalayam": "2B"
            },
            "hygiene_tips": [
                "Do not waste food",
                "Use waste segregation bins",
                "Maintain cleanliness around dining area"
            ],
            "image": "amma_mess.jpg"
        },
        {
            "id": 9,
            "name": "Famous Jigarthanda (Vilakuthoon)",
            "description": "A signature Madurai cold beverage loved by tourists and locals. Best enjoyed in the evening.",
            "timings": "10:00 AM – 10:00 PM",
            "must_try": ["Special Jigarthanda", "Basundi Jigarthanda"],
            "bus_routes": {
                "Periyar Bus Stand": "5A, 10A",
                "Mattuthavani": "70",
                "Arapalayam": "2B"
            },
            "hygiene_tips": [
                "Dispose cups properly",
                "Avoid plastic waste",
                "Keep street food areas clean"
            ],
            "image": "jigarthanda.jpg"
        }
    ],
    "guidelines": {
        "dos": [
            "Segregate wet and dry waste",
            "Use public dustbins properly",
            "Participate in clean-up drives",
            "Report garbage via the app",
            "Use reusable bags",
            "Maintain temple & heritage cleanliness",
            "Encourage others to keep clean",
            "Dispose food waste properly",
            "Maintain sanitation practices",
            "Support eco-friendly initiatives"
        ],
        "donts": [
            "Do not litter in public places",
            "Avoid plastic dumping",
            "Do not spit in public areas",
            "Do not pollute water bodies",
            "Avoid burning garbage",
            "Do not damage public property",
            "Avoid food wastage",
            "Do not block drainage",
            "Do not ignore overflowing bins",
            "Avoid single-use plastics"
        ]
    }
}

@api_awareness_bp.route("/awareness/content", methods=["GET"])
def get_awareness_content():
    return jsonify({
        "success": True,
        "data": AWARENESS_DATA
    })
