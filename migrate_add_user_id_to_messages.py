"""
Script untuk menambahkan kolom user_id ke tabel messages
dan mengisi user_id dari tabel chats
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🔄 Starting migration: Add user_id to messages table")
    
    with engine.connect() as connection:
        try:
            # Cek apakah kolom user_id sudah ada
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='messages' AND column_name='user_id'
            """))
            
            if result.fetchone():
                print("✅ Column user_id already exists in messages table")
                return
            
            # Tambahkan kolom user_id
            print("📝 Adding user_id column to messages table...")
            connection.execute(text("""
                ALTER TABLE messages 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """))
            connection.commit()
            
            print("✅ Column added successfully!")
            
            # Update user_id dari tabel chats
            print("📝 Updating user_id from chats table...")
            result = connection.execute(text("""
                UPDATE messages 
                SET user_id = chats.user_id 
                FROM chats 
                WHERE messages.chat_id = chats.id
            """))
            connection.commit()
            
            rows_updated = result.rowcount
            print(f"✅ Updated {rows_updated} messages with user_id")
            
            print("✅ Migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            connection.rollback()

if __name__ == "__main__":
    migrate()
