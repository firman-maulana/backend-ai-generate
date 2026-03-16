import requests
import json

BASE_URL = "http://localhost:8000" # Backend URL

# Note: You need a valid auth token if get_current_user_id is active.
# For testing locally, it might be easier to bypass auth or use a test account.
# Assuming we can use a mock token or auth is handled.

def test_prompt(prompt, expected_intent):
    print(f"\n🧪 Testing prompt: '{prompt}'")
    payload = {
        "prompt": prompt
    }
    
    # In a real scenario, we'd need headers={"Authorization": "Bearer ..."}
    # But since I'm testing the logic, I'll check if the server is up first.
    try:
        response = requests.post(f"{BASE_URL}/generate", json=payload, timeout=20)
        if response.status_code == 401:
            print("❌ Unauthorized. Need auth token.")
            return
            
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        detected_type = data.get("type")
        if detected_type == expected_intent:
            print(f"✅ Success: Correctly identified as {expected_intent}")
        else:
            print(f"❌ Failed: Identified as {detected_type}, expected {expected_intent}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    # Test Chat
    test_prompt("Halo, siapa namamu?", "chat")
    
    # Test Video
    test_prompt("Buatkan video kucing sedang tidur", "video")
