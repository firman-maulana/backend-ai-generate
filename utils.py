import os
import uuid
import requests
from typing import Optional
from supabase import create_client, Client
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Inisialisasi Supabase client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

if url and key:
    supabase: Client = create_client(url, key)
else:
    supabase = None
    print("⚠️ Supabase credentials not found. Upload functionality will be disabled.")

def download_and_upload_video(video_url: str) -> str:
    """
    Downloads a video from a URL and uploads it to Supabase storage.
    Returns the public URL of the uploaded video.
    """
    if not supabase:
        print("⚠️ Supabase not configured. Returning original URL.")
        return video_url

    try:
        print(f"⬇️ Downloading video from Replicate: {video_url[:50]}...")
        # Download video content
        response = requests.get(video_url, stream=True)
        response.raise_for_status()

        # Generate unique filename
        filename = f"{uuid.uuid4()}.mp4"
        bucket_name = "videos"

        print(f"⬆️ Uploading video to Supabase as {filename}...")
        
        # Upload ke Supabase
        # Menggunakan response.content langsung (bytes)
        res = supabase.storage.from_(bucket_name).upload(
            path=filename,
            file=response.content,
            file_options={"content-type": "video/mp4"}
        )

        # Dapatkan public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(filename)
        print(f"✅ Video successfully uploaded to Supabase: {public_url[:50]}...")
        
        return public_url

    except requests.exceptions.RequestException as e:
        print(f"❌ Error downloading video from Replicate: {e}")
        # Kembalikan URL asli jika gagal download
        return video_url
    except Exception as e:
        print(f"❌ Error uploading to Supabase: {e}")
        # Kembalikan URL asli jika gagal upload
        return video_url

def upload_community_video(file_content: bytes, filename: str) -> Optional[str]:
    """
    Uploads a video file directly to the community-videos bucket.
    """
    if not supabase:
        print("⚠️ Supabase not configured.")
        return None

    try:
        bucket_name = "Video Template"
        
        # Ensure unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        print(f"⬆️ Uploading community video to Supabase: {unique_filename}...")
        
        # Upload ke Supabase
        res = supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": "video/mp4"}
        )

        # Dapatkan public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        return public_url

    except Exception as e:
        print(f"❌ Error uploading community video: {e}")
        return None

def upload_image_to_supabase(file_content: bytes, filename: str) -> Optional[str]:
    """
    Uploads an image file directly to the 'Upload Image' bucket.
    """
    if not supabase:
        print("⚠️ Supabase not configured.")
        return None

    try:
        bucket_name = "Upload Image"
        
        # Ensure unique filename
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        print(f"⬆️ Uploading image to Supabase: {unique_filename}...")
        
        # Get content type based on extension
        ext = filename.split(".")[-1].lower()
        content_type = f"image/{ext}" if ext in ["jpg", "jpeg", "png", "gif", "webp"] else "image/jpeg"
        
        # Upload ke Supabase
        res = supabase.storage.from_(bucket_name).upload(
            path=unique_filename,
            file=file_content,
            file_options={"content-type": content_type}
        )

        # Dapatkan public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)
        return public_url

    except Exception as e:
        print(f"❌ Error uploading image to Supabase: {e}")
        return None
