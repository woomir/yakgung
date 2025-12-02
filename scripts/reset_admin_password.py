import sqlite3
from pathlib import Path
import sys
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities.hasher import Hasher

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from app.db.database import UserDrugDB

def reset_admin_password():
    db = UserDrugDB()
    
    password = "1234"
    # Generate hash using the same method as the app
    # Based on app/streamlit_app.py usage: Hasher().hash(new_password)
    hashed_password = Hasher().hash(password)
    
    print(f"Generated new hash for '{password}': {hashed_password}")
    
    admin_id = "admin"
    
    # Update directly in DB
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (admin_id,))
    if not cursor.fetchone():
        print(f"User '{admin_id}' not found. Creating...")
        db.create_user(admin_id, "admin@example.com", "Admin", hashed_password)
    else:
        print(f"Updating password for '{admin_id}'...")
        cursor.execute("UPDATE users SET password = ? WHERE user_id = ?", (hashed_password, admin_id))
        conn.commit()
    
    conn.close()
    
    print("✅ Admin password reset successfully!")

if __name__ == "__main__":
    reset_admin_password()
