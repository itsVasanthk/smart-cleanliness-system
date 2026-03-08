from flask import Flask
from flask_mysqldb import MySQL
from flask_cors import CORS

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.secret_key = "smart_cleanliness_secret"

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root123'
    app.config['MYSQL_DB'] = 'smart_cleanliness_db'

    mysql.init_app(app)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.awareness_routes import awareness_bp
    app.register_blueprint(awareness_bp)

    from app.routes.volunteer_routes import volunteer_bp
    app.register_blueprint(volunteer_bp)

    from app.routes.api.auth_api import api_auth_bp
    app.register_blueprint(api_auth_bp, url_prefix='/api')

    from app.routes.api.complaints_api import api_complaints_bp
    app.register_blueprint(api_complaints_bp, url_prefix='/api')

    from app.routes.api.volunteer_api import api_volunteer_bp
    app.register_blueprint(api_volunteer_bp, url_prefix='/api')

    from app.routes.api.awareness_api import api_awareness_bp
    app.register_blueprint(api_awareness_bp, url_prefix='/api')

    from app.routes.api.authority_api import api_authority_bp
    app.register_blueprint(api_authority_bp, url_prefix='/api')

    from app.routes.api.fund_api import api_fund_bp
    app.register_blueprint(api_fund_bp, url_prefix='/api')

    from app.routes.api.emergency_api import api_emergency_bp
    app.register_blueprint(api_emergency_bp, url_prefix='/api')

    return app
