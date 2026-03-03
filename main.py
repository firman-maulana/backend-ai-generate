from fastapi import FastAPI, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests

from database import engine, Base, SessionLocal
import models
from models import Chat, Message, User
from fastapi import HTTPException
import bcrypt
from auth import get_current_user_id, verify_chat_ownership

# ==============================
# Create Tables
# ==============================
Base.metadata.create_all(bind=engine)

app = FastAPI()

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
    chat_id: int
    # user_id dihapus dari request body, akan diambil dari auth header

class CreateChatRequest(BaseModel):
    pass  # user_id akan diambil dari auth header

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


# ==============================
# Create New Chat
# ==============================
@app.post("/create-chat")
def create_chat(
    request: CreateChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"💬 Creating new chat for user_id: {user_id}")
    
    new_chat = Chat(title="New Chat", user_id=user_id)
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    print(f"✅ Chat created: ID {new_chat.id} for user {user_id}")
    
    return {"chat_id": new_chat.id}


# ==============================
# Get All Chats by User
# ==============================
@app.get("/chats")
def get_chats(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"📋 Fetching chats for user_id: {user_id}")
    
    chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.id.desc()).all()
    
    print(f"✅ Found {len(chats)} chats for user {user_id}")
    
    return chats


# ==============================
# Get Messages by Chat
# ==============================
# Get Messages by Chat
# ==============================
@app.get("/messages/{chat_id}")
def get_messages(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    print(f"📨 Fetching messages for chat_id: {chat_id}, user_id: {user_id}")
    
    # Validasi bahwa chat milik user (WAJIB)
    verify_chat_ownership(chat_id, user_id, db)
    
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    
    print(f"✅ Found {len(messages)} messages for chat {chat_id}")
    
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
    print(f"🤖 Generate request from user {user_id} for chat {request.chat_id}")

    # Validasi chat milik user (WAJIB)
    chat = verify_chat_ownership(request.chat_id, user_id, db)

    # Jika title masih default → ubah pakai potongan prompt pertama
    if chat.title == "New Chat":
        chat.title = request.prompt[:25] + "..."
        db.commit()

    # 1️⃣ Save User Message
    user_msg = Message(
        role="user",
        content=request.prompt,
        chat_id=request.chat_id,
        user_id=user_id
    )
    db.add(user_msg)
    db.commit()

    # 2️⃣ Call AI Engine
    response = requests.post(
        "http://localhost:9000/generate",
        json={"prompt": request.prompt}
    )

    ai_text = response.json()["result"]

    # 3️⃣ Save AI Message
    ai_msg = Message(
        role="ai",
        content=ai_text,
        chat_id=request.chat_id,
        user_id=user_id
    )
    db.add(ai_msg)
    db.commit()

    print(f"✅ Generated response for chat {request.chat_id}")

    return {"result": ai_text}

@app.post("/register")
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
