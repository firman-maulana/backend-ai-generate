import os
import requests
from utils import download_and_upload_video
from dotenv import load_dotenv

load_dotenv()

def verify_upload():
    print("🎬 Verifying Supabase Video Upload...")
    
    # Use a small sample video URL for testing
    test_video_url = "https://www.w3schools.com/html/mov_bbb.mp4"
    
    try:
        print(f"🔄 Attempting to download and upload: {test_video_url}")
        public_url = download_and_upload_video(test_video_url)
        
        print(f"🏁 Function returned: {public_url}")
        
        if public_url and "supabase.co" in public_url:
            print(f"✅ SUCCESS! Video uploaded to Supabase.")
            print(f"🔗 Public URL: {public_url}")
        elif public_url == test_video_url:
            print("⚠️ FAILED: Function returned the original URL. This means an exception occurred and was caught in download_and_upload_video.")
        else:
            print(f"❌ FAILED: Unexpected result: {public_url}")
            
    except Exception as e:
        print(f"❌ CRITICAL ERROR during verification: {e}")

if __name__ == "__main__":
    verify_upload()
