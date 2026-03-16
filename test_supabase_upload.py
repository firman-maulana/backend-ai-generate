import requests
import json
import time

def test_supabase_upload():
    print("🚀 Starting end-to-end test for Supabase integration...")
    
    url = "http://localhost:8000/generate"
    headers = {
        "Content-Type": "application/json",
        "X-User-Email": "firmanjabbar6@gmail.com"
    }
    payload = {
        "prompt": "A futuristic city in the clouds, cyberpunk style, neon lights, flying cars, volumetric lighting, highly detailed, 8k resolution.",
        "duration": 5,
        "resolution": "720p",
        "aspect_ratio": "16:9",
        "model": "minimax"
    }

    try:
        print("⏳ Sending request to backend (this will take 1-3 minutes for Replicate)...")
        start_time = time.time()
        
        # Timeout diset 8 menit menyesuaikan backend
        response = requests.post(url, headers=headers, json=payload, timeout=480)
        
        elapsed_time = time.time() - start_time
        print(f"⏱️ Request completed in {elapsed_time:.2f} seconds.")
        
        response.raise_for_status()
        data = response.json()
        
        print("\n📥 Backend Response:")
        print(json.dumps(data, indent=2))
        
        video_url = data.get("video_url")
        if video_url:
            print(f"\n✅ SUCCESS: Video URL generated: {video_url}")
            if "supabase.co" in video_url:
                print("🎉 VERIFIED: URL is a Supabase Storage URL!")
            else:
                print("⚠️ WARNING: URL is NOT a Supabase URL, fallback might have occurred.")
        else:
            print("\n❌ ERROR: No video URL in response.")
            if "error" in data:
                print(f"Error detail: {data['error']}")
                
    except requests.exceptions.Timeout:
         print("❌ Request timed out! Generation took too long.")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        try:
            print(f"Detail: {response.json()}")
        except:
             print(f"Raw response: {response.text}")
    except Exception as e:
        print(f"❌ Error during test: {e}")

if __name__ == "__main__":
    # Note: Requires both ai-engine (port 9000) and backend (port 8000) to be running
    test_supabase_upload()
