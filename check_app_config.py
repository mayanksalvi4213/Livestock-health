from app import app

print(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Check if database file exists on disk
import os
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
print(f"Full database path: {db_path}")
print(f"Does file exist: {os.path.exists(db_path)}")

# Also check for any instance folder
instance_path = os.path.join(os.getcwd(), 'instance')
if os.path.exists(instance_path):
    print(f"Instance folder exists: {instance_path}")
    print("Contents:")
    for item in os.listdir(instance_path):
        item_path = os.path.join(instance_path, item)
        print(f"  {item} ({'directory' if os.path.isdir(item_path) else 'file - ' + str(os.path.getsize(item_path)) + ' bytes'})")
else:
    print("Instance folder does not exist") 