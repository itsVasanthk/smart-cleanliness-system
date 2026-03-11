import mysql.connector
from werkzeug.security import generate_password_hash

def create_admin():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root123',
            database='smart_cleanliness_db'
        )
        cursor = conn.cursor()
        
        # Check if already exists
        cursor.execute("SELECT * FROM users WHERE email='admin@gmail.com'")
        if cursor.fetchone():
            print("Admin user already exists.")
            return

        name = "System Admin"
        email = "admin@gmail.com"
        password = "admin123"
        role = "admin"
        hashed_password = generate_password_hash(password)
        
        cursor.execute(
            "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, role)
        )
        conn.commit()
        print(f"Admin user created: {email} / {password}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()
