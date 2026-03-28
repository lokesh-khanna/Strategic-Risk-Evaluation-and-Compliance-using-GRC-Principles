"""
Verify blueprint registration before running server
"""
import sys
sys.path.insert(0, '.')

from app import create_app

app = create_app()

print("=" * 60)
print("BLUEPRINT REGISTRATION VERIFICATION")
print("=" * 60)

print(f"\nRegistered Blueprints:")
for bp_name in app.blueprints.keys():
    print(f"  ✓ {bp_name}")

print(f"\nURL Endpoints (first 20):")
count = 0
for rule in app.url_map.iter_rules():
    print(f"  {rule.endpoint:40} {rule}")
    count += 1
    if count >= 20:
        break

print(f"\n" + "=" * 60)

required_blueprints = ['auth', 'dashboard', 'risk', 'compliance']
missing = [bp for bp in required_blueprints if bp not in app.blueprints]

if not missing:
    print("✅ SUCCESS: All blueprints registered!")
    print("   Endpoints available:")
    if 'compliance.controls' in [r.endpoint for r in app.url_map.iter_rules()]:
        print("   ✓ compliance.controls")
    else:
        print("   ✗ compliance.controls (route issue)")
else:
    print(f"❌ FAILURE: Missing blueprints: {', '.join(missing)}")
    print("\n⚠️  To fix missing blueprints:")
    print("   1. Create the blueprint package directory")
    print("   2. Create __init__.py with blueprint instance")
    print("   3. Create routes.py with route handlers")
    print("   4. Register in app/__init__.py")

print("=" * 60)