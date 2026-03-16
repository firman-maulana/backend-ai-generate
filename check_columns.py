from database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('messages')

print("\n=== Columns in 'messages' table ===")
for col in columns:
    print(f"- {col['name']}: {col['type']}")
