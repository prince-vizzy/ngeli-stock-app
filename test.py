import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host='sql8.freesqldatabase.com',
        user='sql8794024',
        password='uVCUIwx8Wy',  # Replace with password from your email
        database='sql8794024'
    )
    if connection.is_connected():
        print("✅ Connected to MySQL database")
except Error as e:
    print(f"❌ Error: {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()
