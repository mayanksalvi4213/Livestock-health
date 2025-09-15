"""
Refresh farm locations automatically using enhanced geocoding
This script attempts to geocode farm addresses using the Google Maps API
and updates the database with accurate coordinates
"""
from app import app, db
from models import Farm
from utils import geocode_address
import time

def refresh_farm_location():
    """
    Attempt to geocode farm addresses using the Google Maps API
    and update the database with accurate coordinates
    """
    with app.app_context():
        # Get all farms
        farms = Farm.query.all()
        
        if not farms:
            print("No farms found in the database!")
            return
        
        print(f"Found {len(farms)} farm(s) to refresh")
        
        updated_count = 0
        for farm in farms:
            print(f"\nProcessing farm #{farm.id}: {farm.name}")
            print(f"Address: {farm.address}, {farm.district}, {farm.state}, {farm.pincode}")
            
            # Skip if already has coordinates (optional - comment this out to force refresh)
            # if farm.latitude and farm.longitude:
            #     print(f"Farm already has coordinates: ({farm.latitude}, {farm.longitude})")
            #     continue
            
            # Create a better formatted address for geocoding
            address_parts = []
            
            # Extract the main area/landmark from the address
            if farm.address:
                # Split address by commas, spaces, or other common separators
                address_parts.append(farm.address.strip())
            
            if farm.district:
                address_parts.append(farm.district.strip())
            
            if farm.state:
                address_parts.append(farm.state.strip())
            
            if farm.pincode:
                address_parts.append(farm.pincode.strip())
            
            address_parts.append("India")
            
            # Join all parts with commas for better geocoding
            formatted_address = ", ".join(address_parts)
            print(f"Formatted address: {formatted_address}")
            
            try:
                # Get coordinates using geocode function with retry
                for attempt in range(3):  # Try up to 3 times
                    try:
                        lat, lng = geocode_address(
                            farm.address, 
                            farm.district, 
                            farm.state, 
                            pincode=farm.pincode
                        )
                        break
                    except Exception as e:
                        print(f"Error on attempt {attempt+1}: {str(e)}")
                        if attempt < 2:  # Don't sleep on the last attempt
                            time.sleep(2)  # Wait before retrying
                
                if lat and lng:
                    # Update farm coordinates
                    old_lat, old_lng = farm.latitude, farm.longitude
                    farm.latitude = lat
                    farm.longitude = lng
                    
                    updated_count += 1
                    print(f"Updated coordinates from ({old_lat}, {old_lng}) to ({lat}, {lng})")
                else:
                    print(f"Could not determine coordinates for farm #{farm.id}")
            except Exception as e:
                print(f"Error updating farm #{farm.id}: {str(e)}")
        
        # Commit changes to database only once at the end
        db.session.commit()
        print(f"\nUpdated {updated_count} out of {len(farms)} farms")

if __name__ == "__main__":
    refresh_farm_location()
    print("Done! Restart the application to see changes.") 