"""Verify all key pages load correctly after fixes."""
import urllib.request, urllib.parse, http.cookiejar

jar    = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

# Login as admin
data = urllib.parse.urlencode({'username': 'sarah.chen', 'password': 'SecurePass@2025!'}).encode()
req  = urllib.request.Request('http://localhost:5000/auth/login', data=data, method='POST')
opener.open(req)
print("Logged in as sarah.chen\n")

pages = [
    ('Dashboard',           '/dashboard'),
    ('Risk Register',       '/risk/register'),
    ('Compliance Controls', '/compliance/controls'),
    ('Audit Trail',         '/audit/audit'),
    ('Map Risk #1',         '/compliance/map-risk/1'),
    ('Map Risk #3 (High)',  '/compliance/map-risk/3'),
]

all_ok = True
for name, url in pages:
    try:
        r    = opener.open('http://localhost:5000' + url)
        body = r.read().decode('utf-8', errors='ignore')
        ok   = r.status == 200
        if not ok:
            all_ok = False
        tag  = "OK  " if ok else "FAIL"
        print("[{}] {:26s} HTTP {}".format(tag, name, r.status))
    except urllib.error.HTTPError as e:
        print("[ERR] {:26s} HTTP {} - {}".format(name, e.code, e.reason))
        all_ok = False
    except Exception as e:
        print("[ERR] {:26s} {}".format(name, e))
        all_ok = False

print()
print("All pages OK!" if all_ok else "Some pages FAILED - see above")
