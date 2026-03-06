import sqlite3

# Connect to the database
conn = sqlite3.connect('agrihealth.db')
cursor = conn.cursor()

# Check if the farm table exists and its structure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='farm';")
if cursor.fetchone():
    print("Farm table exists")
    cursor.execute("PRAGMA table_info(farm);")
    columns = cursor.fetchall()
    print("Farm table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("Farm table does not exist")

# Check if the user table exists and its structure
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user';")
if cursor.fetchone():
    print("\nUser table exists")
    cursor.execute("PRAGMA table_info(user);")
    columns = cursor.fetchall()
    print("User table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
else:
    print("\nUser table does not exist")

# Close the connection
conn.close() 