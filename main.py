from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import requests

from database import engine, Base, SessionLocal
import models
from models import Chat, Message, User
from fastapi import HTTPException
import bcrypt

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
def create_chat(db: Session = Depends(get_db)):
    new_chat = Chat(title="New Chat")
    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    return {"chat_id": new_chat.id}


# ==============================
# Get All Chats
# ==============================
@app.get("/chats")
def get_chats(db: Session = Depends(get_db)):
    chats = db.query(Chat).all()
    return chats


# ==============================
# Get Messages by Chat
# ==============================
@app.get("/messages/{chat_id}")
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    messages = db.query(Message).filter(Message.chat_id == chat_id).all()
    return messages


# ==============================
# Generate + Save Messages
# ==============================
@app.post("/generate")
def generate(request: PromptRequest, db: Session = Depends(get_db)):

    # Ambil chat
    chat = db.query(Chat).filter(Chat.id == request.chat_id).first()

    # Jika title masih default → ubah pakai potongan prompt pertama
    if chat and chat.title == "New Chat":
        chat.title = request.prompt[:25] + "..."
        db.commit()

    # 1️⃣ Save User Message
    user_msg = Message(
        role="user",
        content=request.prompt,
        chat_id=request.chat_id
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
        chat_id=request.chat_id
    )
    db.add(ai_msg)
    db.commit()

    return {"result": ai_text}

    # 1️⃣ Save User Message
    user_msg = Message(
        role="user",
        content=request.prompt,
        chat_id=request.chat_id
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
        chat_id=request.chat_id
    )
    db.add(ai_msg)
    db.commit()

    # 4️⃣ Return Response
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