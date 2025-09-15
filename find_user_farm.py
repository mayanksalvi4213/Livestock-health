from app import app 
from models import User, Farm

def find_user_and_farm(username):
    """Find a user by username and their associated farm"""
    with app.app_context():
        print(f"Looking for user with username '{username}'...")
        
        # Find the user
        user = User.query.filter_by(username=username).first()
        
        if not user:
            print(f"User '{username}' not found")
            return
            
        print(f"User found: ID={user.id}, Name={user.full_name}")
        
        # Find the farm
        farm = Farm.query.filter_by(user_id=user.id).first()
        
        if farm:
            print(f"Farm found for user '{username}':")
            print(f"  Farm ID: {farm.id}")
            print(f"  Farm Name: {farm.name}")
            print(f"  Address: {farm.address}")
            print(f"  District: {farm.district}, State: {farm.state}")
            print(f"  Coordinates: Lat={farm.latitude}, Lng={farm.longitude}")
        else:
            print(f"No farm found for user '{username}'")

if __name__ == "__main__":
    # Try to find both test users
    find_user_and_farm('testfarmer')
    print("\n" + "-" * 50 + "\n")
    find_user_and_farm('mayank') 