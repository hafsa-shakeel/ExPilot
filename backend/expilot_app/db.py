import os
import pyodbc
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    try:
        conn = pyodbc.connect(
            f"DRIVER={os.getenv('DB_DRIVER')};"
            f"SERVER={os.getenv('DB_SERVER')};"
            f"DATABASE={os.getenv('DB_DATABASE')};"
            "Trusted_Connection=yes;"
        )
        print("Database connected")
        return conn
    except Exception as e:
        print("Database connection failed:", e)
        return None
        
if __name__ == "__main__":
    get_connection()

