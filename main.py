from fastapi import FastAPI, Depends, Header, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests
import os
import uuid
from pathlib import Path

from database import engine, Base, SessionLocal
import models
from models import Message, User, VideoTemplate
from fastapi import HTTPException
import bcrypt
from auth import get_current_user_id
from utils import download_and_upload_video, upload_community_video

# ==============================
# Create Tables
# ==============================
Base.metadata.create_all(bind=engine)

app = FastAPI()

# ==============================
# Create uploads directory
# ==============================
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files untuk serve uploaded images
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ==============================
# CORS
# ==============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================
# Database Dependency
# ==============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==============================
# Request Model
# ==============================
class PromptRequest(BaseModel):
    prompt: str
    image_url: str = None  # URL gambar yang diupload (opsional)
    duration: int = 5  # Durasi video dalam detik (default 5)
    style: str = None  # Style video (cinematic, anime, realistic, dll)
    negative_prompt: str = None  # Hal yang ingin dihindari
    motion_strength: float = 0.5  # Untuk image-to-video (0.0-1.0)
    edit_message_id: int = None  # Existing user message ID to update instead of create

class CreateChatRequest(BaseModel):
    pass  # Deprecated - no longer needed

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class OAuthLoginRequest(BaseModel):
    email: str
    username: str
    provider: str

class VideoUpdateRequest(BaseModel):
    title: str = None
    description: str = None


# ==============================
# Get All Messages by User (Grouped by Date)
# ==============================
@app.get("/messages")
def get_messages(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"📨 Fetching messages for user_id: {user_id}")
    
    # Urutkan dari yang terlama ke terbaru (ascending)
    messages = db.query(Message).filter(Message.user_id == user_id).order_by(Message.date.asc(), Message.id.asc()).all()
    
    print(f"✅ Found {len(messages)} messages for user {user_id}")
    
    return messages


# ==============================
# Generate + Save Messages
# ==============================
@app.post("/generate")
def generate(
    request: PromptRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"🤖 Generate VIDEO request from user {user_id}")

    # 1️⃣ Save or Update User Message (dengan image jika ada)
    user_metadata = {}
    if request.image_url:
        user_metadata["image_url"] = request.image_url
        
    ai_msg = None  # To hold our placeholder AI message
    
    if request.edit_message_id:
        print(f"🔄 Editing existing request ID: {request.edit_message_id}")
        # Fetch existing user message
        user_msg = db.query(Message).filter(
            Message.id == request.edit_message_id, 
            Message.user_id == user_id
        ).first()
        
        if not user_msg:
            raise HTTPException(status_code=404, detail="Original message not found")
            
        # Update user message content
        user_msg.content = request.prompt
        if user_metadata:
            user_msg.meta_data = user_metadata
            
        # Find the sequential AI message (the first message after the user message, typically ID + 1 or the next closest AI message)
        ai_msg = db.query(Message).filter(
            Message.user_id == user_id,
            Message.role == "ai",
            Message.id > user_msg.id
        ).order_by(Message.id.asc()).first()
        
        if ai_msg:
            print(f"🔄 Updating existing AI message placeholder ID: {ai_msg.id}")
            ai_msg.meta_data = {"status": "generating"}
            ai_msg.content = "Generating video..."
        else:
            print("⚠️ No AI message found to update; creating a new placeholder.")
            ai_msg = Message(
                role="ai",
                content="Generating video...",
                user_id=user_id,
                meta_data={"status": "generating"}
            )
            db.add(ai_msg)
            
        db.commit()
    else:
        user_msg = Message(
            role="user",
            content=request.prompt,
            user_id=user_id,
            meta_data=user_metadata if user_metadata else None
        )
        db.add(user_msg)
        db.commit() # Commit to get ID
        
        # Create an upfront AI placeholder so it persists on page reload
        ai_msg = Message(
            role="ai",
            content="Generating video...",
            user_id=user_id,
            meta_data={"status": "generating"}
        )
        db.add(ai_msg)
        db.commit()
    
    print(f"✅ User message saved to database")

    # 2️⃣ Determine Intent (Chat vs Video)
    classify_endpoint = "http://localhost:9000/classify"
    try:
        classify_resp = requests.post(classify_endpoint, json={"prompt": request.prompt}, timeout=10)
        classify_resp.raise_for_status()
        intent = classify_resp.json().get("intent", "video")
    except Exception as e:
        print(f"⚠️ Classification failed, defaulting to video: {e}")
        intent = "video"

    print(f"🎯 Detected intent: {intent}")

    if intent == "chat":
        # Handle General Chat
        print(f"💬 Processing as CHAT request")
        
        # Update placeholder
        ai_msg.content = "Thinking..."
        db.commit()
        
        chat_endpoint = "http://localhost:9000/chat"
        try:
            # Get last few messages for context (optional but good)
            history = []
            recent_msgs = db.query(Message).filter(Message.user_id == user_id).order_by(Message.id.desc()).limit(6).all()
            for m in reversed(recent_msgs):
                if m.id != user_msg.id and m.id != ai_msg.id: # Don't include the current ones yet
                    # Map 'ai' role to 'assistant' for LLM compatibility
                    role = "assistant" if m.role == "ai" else m.role
                    history.append({"role": role, "content": m.content})

            chat_payload = {
                "prompt": request.prompt,
                "history": history
            }
            
            response = requests.post(chat_endpoint, json=chat_payload, timeout=60)
            response.raise_for_status()
            ai_response = response.json()
            
            ai_text = ai_response.get("result", "I'm sorry, I couldn't generate a response.")
            
            # Update AI Message
            ai_msg.content = ai_text
            ai_msg.meta_data = {
                "type": "chat",
                "model": ai_response.get("model", "llama-3.3-70b-versatile"),
                "status": "completed"
            }
            db.commit()
            
            print(f"✅ Chat response saved")
            return {
                "result": ai_text,
                "type": "chat",
                "status": "completed"
            }
            
        except Exception as e:
            print(f"❌ Chat processing error: {e}")
            error_msg = "Maaf, saya sedang mengalami kendala saat memproses chat Anda."
            ai_msg.content = error_msg
            ai_msg.meta_data = {"type": "chat", "status": "failed", "error": str(e)}
            db.commit()
            raise HTTPException(status_code=502, detail=str(e))

    # 3️⃣ Call AI Engine untuk generate VIDEO (Existing Logic)
    ai_endpoint = "http://localhost:9000/generate-video"
    
    # Kirim parameter ke AI Engine (resolution/aspect ratio removed)
    ai_payload = {
        "prompt": request.prompt,
        "duration": request.duration,
        "model": "minimax"  # Default model: minimax
    }
    
    # Tambahkan image_url jika ada (untuk image-to-video)
    if request.image_url:
        ai_payload["image_url"] = request.image_url
        ai_payload["motion_strength"] = request.motion_strength
    
    # Tambahkan optional parameters
    if request.style:
        ai_payload["style"] = request.style
    if request.negative_prompt:
        ai_payload["negative_prompt"] = request.negative_prompt
    
    print(f"🔗 Calling AI Engine (Video): {ai_endpoint}")
    
    try:
        # Replicate bisa memakan waktu 30-180 detik, set timeout lebih tinggi
        response = requests.post(ai_endpoint, json=ai_payload, timeout=480)  # 8 menit timeout
        response.raise_for_status()
        ai_response = response.json()
        
        print(f"📥 AI Engine response: {ai_response}")
        
    except requests.exceptions.Timeout:
        print(f"⏰ AI Engine timeout after 8 minutes")
        
        # Mark AI placeholder as failed
        ai_msg.meta_data = {
            "type": "video",
            "duration": request.duration,
            "status": "failed",
            "error": "Video generation timeout."
        }
        db.commit()
        
        raise HTTPException(
            status_code=504, 
            detail="Video generation timeout. Please try again."
        )
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to AI Engine")
        raise HTTPException(status_code=503, detail="AI Engine is not running.")
    except requests.exceptions.RequestException as e:
        print(f"❌ AI Engine error: {e}")
        error_detail = "AI Engine error."
        
        # Mark AI placeholder as failed
        ai_msg.meta_data = {
            "type": "video",
            "status": "failed",
            "error": str(e)
        }
        db.commit()
        raise HTTPException(status_code=502, detail=str(e))
    
    ai_text = ai_response.get("result", "Video sudah siap! 🎬")
    video_url = ai_response.get("video_url")
    
    if video_url:
        print(f"🔄 Processing video transfer to Supabase...")
        final_video_url = download_and_upload_video(video_url)
    else:
        final_video_url = None
    
    if not final_video_url:
        metadata = {
            "type": "video",
            "status": "failed",
            "error": "No video URL returned"
        }
    else:
        metadata = {
            "type": "video",
            "model": ai_response.get("model", "minimax"),
            "duration": request.duration,
            "status": "completed",
            "video_url": final_video_url
        }
    
    if request.image_url:
        metadata["source_image"] = request.image_url
    
    ai_msg.content = ai_text
    ai_msg.meta_data = metadata
    db.commit()
    
    return {
        "result": ai_text,
        **metadata
    }

# ==============================
# Upload Image
# ==============================
@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id)
):
    print(f"📤 Uploading image for user {user_id}: {file.filename}")
    
    # Validasi file type
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images allowed.")
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Return URL - gunakan 127.0.0.1 agar bisa diakses dari AI Engine
        # Atau bisa pakai IP address komputer
        image_url = f"http://127.0.0.1:8000/uploads/{unique_filename}"
        print(f"✅ Image uploaded: {image_url}")
        
        return {
            "success": True,
            "url": image_url,
            "filename": unique_filename,
            "local_path": str(file_path.absolute())  # Tambahkan local path untuk fallback
        }
    except Exception as e:
        print(f"❌ Upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")
def register(request: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = bcrypt.hashpw(
        request.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    new_user = User(
        username=request.username,
        email=request.email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"id": new_user.id, "email": new_user.email}

@app.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(
        request.password.encode("utf-8"),
        user.password.encode("utf-8")
    ):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.username
    }

@app.post("/oauth-login")
def oauth_login(request: OAuthLoginRequest, db: Session = Depends(get_db)):
    # Cek apakah user sudah ada
    user = db.query(User).filter(User.email == request.email).first()

    if user:
        # User sudah ada, return data user
        return {
            "id": user.id,
            "email": user.email,
            "name": user.username
        }
    else:
        # User baru, buat akun baru
        new_user = User(
            username=request.username,
            email=request.email,
            password=None  # OAuth user tidak punya password
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.username
        }

@app.get("/user-by-email")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    print(f"🔍 Looking up user by email: {email}")
    
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        print(f"❌ User not found: {email}")
        raise HTTPException(status_code=404, detail="User not found")
    
    print(f"✅ User found: {user.email} (ID: {user.id})")
    
    return {
        "id": user.id,
        "email": user.email,
        "name": user.username
    }

# ==============================
# Video Template CRUD
# ==============================

@app.get("/video-templates")
def get_video_templates(db: Session = Depends(get_db)):
    print("🎬 Fetching video templates")
    videos = db.query(VideoTemplate).order_by(VideoTemplate.id.desc()).all()
    
    # Map to frontend format
    result = []
    for v in videos:
        result.append({
            "id": v.id,
            "title": v.title,
            "description": v.description,
            "user": v.user.username if v.user else "Anonymous",
            "userId": v.user_id,
            "userEmail": v.user.email if v.user else None,
            "avatar": f"https://i.pravatar.cc/150?u={v.user_id}",
            "duration": v.duration,
            "thumbnail": v.video_url, # Use video URL as source for preview
            "videoUrl": v.video_url,
            "likes": v.likes
        })
    return result

@app.post("/video-templates")
async def post_video_template(
    title: str = Form(...),
    description: str = Form(...), # Mandatory now
    duration: str = Form("00:05"),
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"⬆️ User {user_id} posting video template: {title}")
    
    # 1. Read file
    contents = await file.read()
    
    # 2. Upload to Supabase (bucket: Video Template)
    video_url = upload_community_video(contents, file.filename)
    
    if not video_url:
        raise HTTPException(status_code=500, detail="Failed to upload video to storage")
    
    # 3. Save to database
    new_video = VideoTemplate(
        title=title,
        description=description,
        video_url=video_url,
        user_id=user_id,
        duration=duration
    )
    
    db.add(new_video)
    db.commit()
    db.refresh(new_video)
    
    print(f"✅ Video template posted: {new_video.id}")
    return {"success": True, "id": new_video.id, "video_url": video_url}

@app.delete("/video-templates/{video_id}")
def delete_video_template(
    video_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    video = db.query(VideoTemplate).filter(VideoTemplate.id == video_id, VideoTemplate.user_id == user_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or not authorized")
    
    db.delete(video)
    db.commit()
    return {"success": True}

@app.put("/video-templates/{video_id}")
async def update_video_template(
    video_id: int,
    title: str = Form(None),
    description: str = Form(None),
    duration: str = Form(None),
    file: UploadFile = File(None),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    video = db.query(VideoTemplate).filter(VideoTemplate.id == video_id, VideoTemplate.user_id == user_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found or not authorized")
    
    if title:
        video.title = title
    
    if description:
        video.description = description
        
    if file:
        contents = await file.read()
        video_url = upload_community_video(contents, file.filename)
        if video_url:
            video.video_url = video_url
            if duration:
                video.duration = duration
    elif duration:
        video.duration = duration
        
    db.commit()
    return {"success": True}
