"""
Update farm location coordinates in the database
This script can be used to manually correct farm coordinates for existing farms
"""
from app import app, db
from models import Farm
from utils import geocode_address

def update_farm_location(farm_id=None, address=None, district=None, state=None, pincode=None):
    """
    Update coordinates for a specific farm or all farms
    
    Args:
        farm_id (int): Optional farm ID to update a specific farm
        address (str): Optional address to update for the farm
        district (str): Optional district to update for the farm
        state (str): Optional state to update for the farm
        pincode (str): Optional pincode to update for the farm
    """
    with app.app_context():
        if farm_id:
            farms = Farm.query.filter_by(id=farm_id).all()
        else:
            farms = Farm.query.all()
        
        print(f"Found {len(farms)} farm(s) to update")
        
        updated_count = 0
        for farm in farms:
            # Use provided values or existing values
            farm_address = address or farm.address
            farm_district = district or farm.district
            farm_state = state or farm.state
            farm_pincode = pincode or farm.pincode
            
            print(f"\nUpdating farm #{farm.id}: {farm.name}")
            print(f"Address: {farm_address}, {farm_district}, {farm_state}, {farm_pincode}")
            
            try:
                # Get coordinates using geocode function
                lat, lng = geocode_address(farm_address, farm_district, farm_state, pincode=farm_pincode)
                
                if lat and lng:
                    # Update farm coordinates
                    old_lat, old_lng = farm.latitude, farm.longitude
                    farm.latitude = lat
                    farm.longitude = lng
                    db.session.commit()
                    
                    updated_count += 1
                    print(f"Updated coordinates from ({old_lat}, {old_lng}) to ({lat}, {lng})")
                else:
                    print(f"Could not determine coordinates for farm #{farm.id}")
            except Exception as e:
                print(f"Error updating farm #{farm.id}: {str(e)}")
        
        print(f"\nUpdated {updated_count} out of {len(farms)} farms")
        
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Update farm locations in the database")
    parser.add_argument("--farm-id", type=int, help="Specific farm ID to update")
    parser.add_argument("--address", type=str, help="Address to update")
    parser.add_argument("--district", type=str, help="District to update")
    parser.add_argument("--state", type=str, help="State to update")
    parser.add_argument("--pincode", type=str, help="Pincode to update")
    
    args = parser.parse_args()
    
    update_farm_location(
        farm_id=args.farm_id,
        address=args.address,
        district=args.district,
        state=args.state,
        pincode=args.pincode
    ) 