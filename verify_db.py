import mysql.connector

def verify_schema():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root123',
            database='smart_cleanliness_db'
        )
        cursor = conn.cursor()
        
        cursor.execute("DESCRIBE complaints")
        columns = [row[0] for row in cursor.fetchall()]
        
        required_columns = [
            'authority_decision', 
            'authority_reason', 
            'escalated_to_admin', 
            'escalated_at', 
            'citizen_feedback', 
            'citizen_rating',
            'image_hash'
        ]
        
        print("Checking complaints table columns...")
        all_present = True
        for col in required_columns:
            if col in columns:
                print(f"[OK] {col}")
            else:
                print(f"[MISSING] {col}")
                all_present = False
        
        if all_present:
            print("\nSchema verification SUCCESSFUL!")
        else:
            print("\nSchema verification FAILED!")
            
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_schema()
