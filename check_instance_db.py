import sqlite3
import os

# Connect to the database in the instance folder
db_path = os.path.join('instance', 'agrihealth.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print(f"Connected to database: {db_path}")
if tables:
    print("Tables in the database:")
    for table in tables:
        print(f"  {table[0]}")
else:
    print("No tables found in the database")

# Check if user and farm tables exist
print("\nChecking for user data:")
if any(table[0] == 'user' for table in tables):
    cursor.execute("SELECT id, username, name, email FROM user;")
    users = cursor.fetchall()
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Name: {user[2]}, Email: {user[3]}")
else:
    print("No user table found")

print("\nChecking for farm data:")
if any(table[0] == 'farm' for table in tables):
    cursor.execute("SELECT id, user_id, name, address, latitude, longitude FROM farm;")
    farms = cursor.fetchall()
    print(f"Found {len(farms)} farms:")
    for farm in farms:
        print(f"  Farm ID: {farm[0]}, User ID: {farm[1]}, Name: {farm[2]}")
        print(f"  Address: {farm[3]}")
        print(f"  Coordinates: {farm[4]}, {farm[5]}")
        print("-" * 40)
else:
    print("No farm table found")

# Close the connection
conn.close() 