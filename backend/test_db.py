# Create a test_db.py file
import psycopg2

try:
    conn = psycopg2.connect(
        dbname="password_vault",
        user="password_vault",
        password="devpassword",
        host="localhost"
    )
    print("Connection successful!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")