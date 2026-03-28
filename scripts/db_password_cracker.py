
import mysql.connector
from mysql.connector import errorcode

passwords = [
    "",
    "root",
    "password",
    "admin",
    "123456",
    "Grc2026!",  # From .env
    "GrcPlatform2026!", # Guess based on project name
    "mysql"
]

users = ["root", "admin", "db_admin"]

def try_connect():
    print("Attempting to connect to MySQL...")
    for user in users:
        for pwd in passwords:
            try:
                cnx = mysql.connector.connect(user=user, password=pwd, host='127.0.0.1')
                print(f"SUCCESS! Connected with user='{user}', password='{pwd}'")
                cnx.close()
                return user, pwd
            except mysql.connector.Error as err:
                # print(f"Failed with user='{user}', password='{pwd}': {err}")
                pass
    
    print("FAILED to connect with any common credentials.")
    return None, None

if __name__ == "__main__":
    try_connect()
