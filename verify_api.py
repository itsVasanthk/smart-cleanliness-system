import requests
import json

BASE_URL = "http://127.0.0.1:5000/api"

def test_api():
    print("--- Starting API Verification ---")
    
    # 1. Login as Citizen
    print("\n1. Testing Citizen Login...")
    citizen_payload = {"email": "citizen@test.com", "password": "pass123"}
    resp = requests.post(f"{BASE_URL}/login", json=citizen_payload)
    if resp.status_code == 200:
        citizen_data = resp.json()
        print("[OK] Citizen logged in.")
        citizen_id = citizen_data['user']['user_id']
    else:
        print(f"[FAIL] Citizen login failed: {resp.text}")
        return

    # 2. Login as Authority
    print("\n2. Testing Authority Login...")
    auth_payload = {"email": "authority@test.com", "password": "pass123"}
    resp = requests.post(f"{BASE_URL}/login", json=auth_payload)
    if resp.status_code == 200:
        print("[OK] Authority logged in.")
    else:
        print(f"[FAIL] Authority login failed: {resp.text}")
        return

    # 3. Login as Admin
    print("\n3. Testing Admin Login...")
    admin_payload = {"email": "admin@test.com", "password": "pass123"}
    resp = requests.post(f"{BASE_URL}/login", json=admin_payload)
    if resp.status_code == 200:
        print("[OK] Admin logged in.")
    else:
        print(f"[FAIL] Admin login failed: {resp.text}")
        return

    # 4. Check Citizen Dashboard (Stats)
    print("\n4. Checking Citizen Dashboard Stats...")
    resp = requests.get(f"{BASE_URL}/citizen_dashboard/{citizen_id}")
    if resp.status_code == 200:
        stats = resp.json()
        print(f"[OK] Stats received: {stats}")
        if 'emotion' in stats and 'slogan' in stats:
            print("[OK] Emotion/Slogan fields present.")
    else:
        print(f"[FAIL] Citizen dashboard failed: {resp.text}")

    # 5. Check Authority Stats
    print("\n5. Checking Authority Stats...")
    resp = requests.get(f"{BASE_URL}/authority/stats")
    if resp.status_code == 200:
        stats = resp.json()
        print(f"[OK] Authority Stats: {stats}")
        if 'pending_decisions' in stats:
            print("[OK] 'pending_decisions' field present.")
    else:
        print(f"[FAIL] Authority stats failed: {resp.text}")

    # 6. Check Admin Stats
    print("\n6. Checking Admin Stats...")
    resp = requests.get(f"{BASE_URL}/admin/stats")
    if resp.status_code == 200:
        stats = resp.json()
        print(f"[OK] Admin Stats: {stats}")
        if 'escalated_reports' in stats:
            print("[OK] 'escalated_reports' field present.")
    else:
        print(f"[FAIL] Admin stats failed: {resp.text}")

    print("\n--- API Verification Complete ---")

if __name__ == "__main__":
    test_api()
