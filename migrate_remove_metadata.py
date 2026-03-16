"""
Migration Script: Remove old 'metadata' column from messages table
Keep only 'meta_data' column
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL

def migrate():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("🔄 Starting migration to remove 'metadata' column...")
        
        # Check if metadata column exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'messages' 
            AND column_name = 'metadata'
        """))
        
        if result.fetchone():
            print("📋 Found 'metadata' column, removing it...")
            
            # Drop metadata column
            try:
                conn.execute(text("""
                    ALTER TABLE messages 
                    DROP COLUMN IF EXISTS metadata
                """))
                conn.commit()
                print("✅ 'metadata' column removed successfully")
            except Exception as e:
                print(f"❌ Error removing metadata column: {e}")
        else:
            print("⚠️ 'metadata' column not found, nothing to remove")
        
        print("\n✅ Migration completed!")
        print("\n📝 Summary:")
        print("   - Old 'metadata' column removed")
        print("   - Only 'meta_data' column remains")

if __name__ == "__main__":
    migrate()
