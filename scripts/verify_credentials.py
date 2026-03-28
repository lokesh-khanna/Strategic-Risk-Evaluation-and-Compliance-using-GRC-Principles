
import mysql.connector
from mysql.connector import errorcode
import socket
import sys

PASSWORD = "Grc2026!"

def check_port(host, port):
    print(f"Checking {host}:{port}...", end=" ")
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((host, port))
        s.close()
        print("OPEN")
        return True
    except:
        print("CLOSED/UNREACHABLE")
        return False

def try_connect(host):
    print(f"\nAttempting MySQL connection to host='{host}', user='root'...")
    try:
        cnx = mysql.connector.connect(user='root', password=PASSWORD, host=host)
        print(f"✅ SUCCESS! Connected to {host} with provided password.")
        cnx.close()
        return True
    except mysql.connector.Error as err:
        print(f"❌ FAILED: Code={err.errno}, State={err.sqlstate}")
        print(f"   Message: {err.msg}")
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print("   -> Access denied (Password incorrect or user not allowed from this host)")
        elif err.errno == errorcode.CR_CONN_HOST_ERROR:
            print("   -> Can't connect to MySQL server")
        return False

if __name__ == "__main__":
    print(f"Verifying credentials for password: '{PASSWORD}'")
    print("-" * 50)
    
    port_open = check_port("127.0.0.1", 3306)
    
    if port_open:
        success_ip = try_connect("127.0.0.1")
        success_localhost = try_connect("localhost")
        
        if success_ip or success_localhost:
            print("\n🎉 Connection Verified!")
            sys.exit(0)
        else:
            print("\n⚠️  Credentials rejected by server.")
            sys.exit(1)
    else:
        print("\n⚠️  MySQL port 3306 is not open. Is the service running?")
        sys.exit(1)
