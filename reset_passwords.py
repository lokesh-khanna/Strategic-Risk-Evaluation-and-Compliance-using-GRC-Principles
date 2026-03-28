"""
Reset sample user passwords to 'Password123!' using proper bcrypt hashing
Run ONCE after database creation
"""
import sys
sys.path.insert(0, '.')

from app import create_app
from app.db import db
from flask_bcrypt import Bcrypt

app = create_app()
bcrypt = Bcrypt(app)

# Password to set for all sample users
NEW_PASSWORD = "Password123!"

def reset_passwords():
    print("Resetting sample user passwords to 'Password123!'...")
    
    # Get all sample users
    users = db.execute_query(
        "SELECT user_id, username FROM users WHERE username IN ('admin', 'riskmgr', 'compoff', 'auditor1')",
        fetch=True
    )
    
    if not users:
        print("❌ No sample users found. Did you run the database schema script?")
        return False
    
    # Update each user's password hash
    for user in users:
        hashed_pw = bcrypt.generate_password_hash(NEW_PASSWORD).decode('utf-8')
        db.execute_query(
            "UPDATE users SET password_hash = %s WHERE user_id = %s",
            (hashed_pw, user['user_id'])
        )
        print(f"✓ Updated password for user '{user['username']}' (ID: {user['user_id']})")
    
    print(f"\n✅ SUCCESS: All {len(users)} sample users now use password: '{NEW_PASSWORD}'")
    print("\nSample credentials:")
    print("  Username      Password")
    print("  --------      --------")
    for user in users:
        print(f"  {user['username']:<13} {NEW_PASSWORD}")
    
    return True

if __name__ == '__main__':
    with app.app_context():
        reset_passwords()