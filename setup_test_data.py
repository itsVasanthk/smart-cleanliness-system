import mysql.connector
from werkzeug.security import generate_password_hash

def setup_test_users():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root123',
            database='smart_cleanliness_db'
        )
        cursor = conn.cursor()
        
        users = [
            ("Test Citizen", "citizen@test.com", "pass123", "citizen"),
            ("Test Authority", "authority@test.com", "pass123", "authority"),
            ("Test Admin", "admin@test.com", "pass123", "admin")
        ]
        
        for name, email, password, role in users:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            if cursor.fetchone():
                cursor.execute("DELETE FROM users WHERE email=%s", (email,))
            
            hashed = generate_password_hash(password)
            cursor.execute(
                "INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                (name, email, hashed, role)
            )
        
        conn.commit()
        print("Test users setup complete.")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    setup_test_users()
