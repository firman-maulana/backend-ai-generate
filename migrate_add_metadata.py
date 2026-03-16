"""
Script untuk menambahkan kolom meta_data ke tabel messages
"""
from database import engine
from sqlalchemy import text

def migrate():
    print("🔄 Starting migration: Add meta_data column to messages table")
    
    with engine.connect() as connection:
        try:
            # Cek apakah kolom meta_data sudah ada
            result = connection.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='messages' AND column_name='meta_data'
            """))
            
            if result.fetchone():
                print("✅ Column meta_data already exists in messages table")
                return
            
            # Tambahkan kolom meta_data (JSON type)
            print("📝 Adding meta_data column to messages table...")
            connection.execute(text("""
                ALTER TABLE messages 
                ADD COLUMN meta_data JSON
            """))
            connection.commit()
            
            print("✅ Migration completed successfully!")
            print("ℹ️  meta_data column can store: image_url, video_url, model, etc.")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            connection.rollback()

if __name__ == "__main__":
    migrate()
