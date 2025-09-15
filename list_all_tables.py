import sqlite3

# Connect to the database
conn = sqlite3.connect('agrihealth.db')
cursor = conn.cursor()

# Get list of all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

if tables:
    print("Tables in the database:")
    for table in tables:
        print(f"  {table[0]}")
else:
    print("No tables found in the database")

# Close the connection
conn.close() 