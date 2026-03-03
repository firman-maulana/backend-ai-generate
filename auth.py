"""
Authentication and Authorization utilities
"""
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from models import User
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user_id(x_user_email: str = Header(None), db: Session = Depends(get_db)) -> int:
    """
    Get current user ID from email header
    Ini adalah simplified version. Di production, gunakan JWT token.
    """
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    user = db.query(User).filter(User.email == x_user_email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user.id

def verify_chat_ownership(chat_id: int, user_id: int, db: Session):
    """
    Verify that chat belongs to user
    """
    from models import Chat
    
    chat = db.query(Chat).filter(Chat.id == chat_id, Chat.user_id == user_id).first()
    
    if not chat:
        raise HTTPException(status_code=403, detail="Unauthorized access to chat")
    
    return chat
