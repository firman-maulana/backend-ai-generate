from dotenv import load_dotenv
load_dotenv()
from utils import download_and_upload_video
import sys

# Menggunakan sample video pendek
test_url = "https://www.w3schools.com/html/mov_bbb.mp4"

print(f"Starting test for download_and_upload_video...")
result = download_and_upload_video(test_url)
print(f"Result URL: {result}")
if "supabase.co" in result:
    print("✅ SUCCESS: Upload works!")
    sys.exit(0)
else:
    print("❌ FAILED: Did not get Supabase URL")
    sys.exit(1)
