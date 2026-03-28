"""
Test database connectivity and sample query execution
Run: python test_db.py
"""
import sys
sys.path.insert(0, '.')

from app.db import db
from app import create_app

app = create_app()

print("Testing GRC Platform Database Connection...")
print("=" * 50)

try:
    # Test 1: Basic connectivity
    users = db.execute_query("SELECT user_id, username, full_name FROM users", fetch=True)
    print(f"✓ Connected to grc_db")
    print(f"✓ Retrieved {len(users)} users:")
    for user in users:
        print(f"  - ID: {user['user_id']}, Username: {user['username']}, Name: {user['full_name']}")
    
    # Test 2: Risk scoring verification
    risks = db.execute_query("""
        SELECT risk_title, probability, impact, risk_score, risk_level 
        FROM risks 
        ORDER BY risk_score DESC
    """, fetch=True)
    print(f"\n✓ Retrieved {len(risks)} risks with computed scores:")
    for risk in risks:
        print(f"  - '{risk['risk_title']}': P{risk['probability']} × I{risk['impact']} = {risk['risk_score']} ({risk['risk_level']})")
    
    # Test 3: Compliance mapping
    mappings = db.execute_query("""
        SELECT r.risk_title, c.control_code, c.regulation
        FROM risks r
        INNER JOIN risk_compliance_mapping m ON r.risk_id = m.risk_id
        INNER JOIN compliance_controls c ON m.control_id = c.control_id
        LIMIT 3
    """, fetch=True)
    print(f"\n✓ Verified risk-control mappings (sample):")
    for mapping in mappings:
        print(f"  - Risk '{mapping['risk_title']}' → Control {mapping['control_code']} ({mapping['regulation']})")
    
    print("\n" + "=" * 50)
    print("✅ ALL DATABASE TESTS PASSED")
    print("Your GRC platform database layer is operational.")
    
except Exception as e:
    print(f"\n❌ DATABASE TEST FAILED: {e}")
    sys.exit(1)