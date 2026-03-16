"""
Script untuk cek isi database
Jalankan: python check_database.py
"""

from database import SessionLocal
from models import User, Message
from sqlalchemy import func

def check_database():
    db = SessionLocal()
    
    print("=" * 60)
    print("📊 DATABASE CHECK")
    print("=" * 60)
    
    # Count records
    user_count = db.query(User).count()
    user_count = db.query(User).count()
    message_count = db.query(Message).count()
    
    print(f"\n📈 Total Records:")
    print(f"   Users: {user_count}")
    print(f"   Messages: {message_count}")
    
    # Show users
    print(f"\n👥 Users:")
    users = db.query(User).all()
    for user in users:
        print(f"   ID: {user.id} | Email: {user.email} | Username: {user.username}")
    
    # Show recent messages
    print(f"\n📨 Recent Messages (Last 10):")
    messages = db.query(Message).order_by(Message.id.desc()).limit(10).all()
    for msg in messages:
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        meta_info = ""
        if msg.meta_data:
            if msg.meta_data.get("image_url"):
                meta_info = " [📷 Image]"
            if msg.meta_data.get("video_url"):
                meta_info += " [🎬 Video]"
            if msg.meta_data.get("model"):
                meta_info += f" [{msg.meta_data.get('model')}]"
        
        print(f"   ID: {msg.id} | Role: {msg.role} | Content: {content_preview}{meta_info}")
    
    # Check for messages with metadata
    print(f"\n🔍 Messages with Metadata:")
    messages_with_meta = db.query(Message).filter(Message.meta_data.isnot(None)).all()
    print(f"   Total: {len(messages_with_meta)}")
    for msg in messages_with_meta[:5]:  # Show first 5
        print(f"   ID: {msg.id} | Role: {msg.role} | Meta: {msg.meta_data}")
    
    print("\n" + "=" * 60)
    print("✅ Database check complete!")
    print("=" * 60)
    
    db.close()

if __name__ == "__main__":
    check_database()
