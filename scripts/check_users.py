"""
Diagnose login - check actual DB schema and user data.
"""
import mysql.connector, os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('MYSQL_HOST', 'localhost'),
    user=os.getenv('MYSQL_USER', 'root'),
    password=os.getenv('MYSQL_PASSWORD', ''),
    database=os.getenv('MYSQL_DB', 'grc_db')
)
cur = conn.cursor(dictionary=True)

# 1. Show table columns
print("=== users table columns ===")
cur.execute("DESCRIBE users")
for col in cur.fetchall():
    print(f"  {col['Field']:<25} {col['Type']:<20} {col['Null']}")

# 2. Show first 6 users
print("\n=== users rows ===")
cur.execute("SELECT * FROM users LIMIT 6")
rows = cur.fetchall()
for u in rows:
    ph = str(u.get('password_hash', 'MISSING') or 'NULL')
    print(f"  id={u.get('user_id')} user={u.get('username','?')} "
          f"active={u.get('is_active')} hash={ph[:35]}")

# 3. Verify bcrypt
print("\n=== Password verification ===")
try:
    import bcrypt
    for u in rows[:3]:
        ph = u.get('password_hash') or ''
        if not ph:
            print(f"  {u.get('username')}: NO HASH stored")
            continue
        for pwd in ['SecurePass@2025!', 'Grc2026!', 'Admin@2025!']:
            try:
                ok = bcrypt.checkpw(pwd.encode(), ph.encode())
                if ok:
                    print(f"  ✅ {u.get('username')} -> password is: {pwd}")
                    break
            except Exception as e:
                print(f"  ERROR: {e}")
        else:
            print(f"  ❌ {u.get('username')}: no tested password matched (hash={ph[:35]})")
except ImportError:
    print("  bcrypt not installed")

cur.close()
conn.close()
print("\nDone.")
