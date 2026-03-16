"""
Check if AI Engine is running on port 9000
"""
import requests

def check_ai_engine():
    try:
        response = requests.get("http://localhost:9000/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("✅ AI Engine is running!")
            print(f"   Status: {data.get('status')}")
            print(f"   Replicate: {data.get('replicate_status')}")
            print(f"   Free Credit: {data.get('free_credit')}")
            return True
        else:
            print(f"⚠️ AI Engine responded with status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ AI Engine is NOT running on port 9000")
        print("\n📝 To start AI Engine:")
        print("   1. cd ai-engine")
        print("   2. python main.py")
        return False
    except Exception as e:
        print(f"❌ Error checking AI Engine: {e}")
        return False

if __name__ == "__main__":
    check_ai_engine()
