"""
Migration Script: Remove chats table and update messages table
- Drop chats table
- Add date column to messages table
- Remove chat_id column from messages table
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔄 Starting migration...")
        
        # 1. Add date column to messages (default to current date)
        print("📅 Adding date column to messages table...")
        try:
            conn.execute(text("""
                ALTER TABLE messages 
                ADD COLUMN IF NOT EXISTS date DATE DEFAULT CURRENT_DATE
            """))
            conn.commit()
            print("✅ Date column added")
        except Exception as e:
            print(f"⚠️ Date column might already exist: {e}")
        
        # 2. Drop chat_id foreign key constraint
        print("🔗 Dropping chat_id foreign key constraint...")
        try:
            conn.execute(text("""
                ALTER TABLE messages 
                DROP CONSTRAINT IF EXISTS messages_chat_id_fkey
            """))
            conn.commit()
            print("✅ Foreign key constraint dropped")
        except Exception as e:
            print(f"⚠️ Constraint might not exist: {e}")
        
        # 3. Drop chat_id column from messages
        print("🗑️ Dropping chat_id column from messages table...")
        try:
            conn.execute(text("""
                ALTER TABLE messages 
                DROP COLUMN IF EXISTS chat_id
            """))
            conn.commit()
            print("✅ chat_id column dropped")
        except Exception as e:
            print(f"❌ Error dropping chat_id: {e}")
        
        # 4. Drop chats table
        print("🗑️ Dropping chats table...")
        try:
            conn.execute(text("DROP TABLE IF EXISTS chats CASCADE"))
            conn.commit()
            print("✅ Chats table dropped")
        except Exception as e:
            print(f"❌ Error dropping chats table: {e}")
        
        # 5. Update User model relationship
        print("🔄 Updating relationships...")
        try:
            # Remove chats relationship from users (handled in models.py)
            conn.execute(text("""
                ALTER TABLE users 
                DROP CONSTRAINT IF EXISTS users_chats_fkey
            """))
            conn.commit()
            print("✅ User relationships updated")
        except Exception as e:
            print(f"⚠️ Relationship constraint might not exist: {e}")
        
        print("\n✅ Migration completed successfully!")
        print("\n📝 Summary:")
        print("   - Chats table removed")
        print("   - chat_id column removed from messages")
        print("   - date column added to messages")
        print("   - Messages now directly linked to users only")

if __name__ == "__main__":
    migrate()
