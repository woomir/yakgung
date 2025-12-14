import sqlite3
from pathlib import Path
import sys

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.db.database import UserDrugDB

def create_admin_user():
    db = UserDrugDB()
    
    # Admin credentials (same as in streamlit_app.py fallback)
    admin_id = "admin"
    admin_email = "admin@example.com"
    admin_name = "Admin"
    # Hash for "1234"
    admin_password = "$2b$12$qbGyuPnyvDaP1D7quPK36.bYGSFNWkqZS9wZExFpE3/Kc/IhdIefG"
    
    print(f"Creating/Updating admin user '{admin_id}'...")
    success = db.create_user(
        user_id=admin_id,
        email=admin_email,
        name=admin_name,
        password=admin_password
    )
    
    if success:
        print("✅ Admin user created successfully!")
        
        # Verify
        user = db.get_user(admin_id)
        print(f"Verified user: {user}")
    else:
        print("❌ Failed to create admin user.")

if __name__ == "__main__":
    create_admin_user()
