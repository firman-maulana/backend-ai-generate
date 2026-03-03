"""
Script untuk menambahkan kolom user_id ke tabel chats
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🔄 Starting migration: Add user_id to chats table")
    
    with engine.connect() as connection:
        try:
            # Cek apakah kolom user_id sudah ada
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='chats' AND column_name='user_id'
            """))
            
            if result.fetchone():
                print("✅ Column user_id already exists in chats table")
                return
            
            # Tambahkan kolom user_id
            print("📝 Adding user_id column to chats table...")
            connection.execute(text("""
                ALTER TABLE chats 
                ADD COLUMN user_id INTEGER REFERENCES users(id)
            """))
            connection.commit()
            
            print("✅ Migration completed successfully!")
            print("⚠️  Note: Existing chats will have NULL user_id")
            print("   You may want to assign them to a default user or delete them")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            connection.rollback()

if __name__ == "__main__":
    migrate()
