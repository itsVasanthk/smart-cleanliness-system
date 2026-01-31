from flask import Flask
from flask_mysqldb import MySQL

mysql = MySQL()

def create_app():
    app = Flask(__name__)
    app.secret_key = "smart_cleanliness_secret"

    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root123'
    app.config['MYSQL_DB'] = 'smart_cleanliness_db'

    mysql.init_app(app)

    from app.routes.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    return app
