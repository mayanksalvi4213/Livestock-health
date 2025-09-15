"""
Dynamic location detection using Google Maps Geocoding API
This script will update farm coordinates by directly calling the Google Maps API
"""
import requests
import json
import time
from app import app
from models import db, Farm

# Google Maps API Key - you may need to replace this with your own key
API_KEY = "AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM"

def dynamic_geocode(address, district=None, state=None, pincode=None, country="India"):
    """
    Dynamically geocode an address using Google Maps API
    Returns (latitude, longitude) tuple or None if geocoding fails
    """
    # Build the complete address string
    address_parts = []
    if address:
        address_parts.append(address.strip())
    if district:
        address_parts.append(district.strip())
    if state:
        address_parts.append(state.strip())
    if pincode:
        address_parts.append(pincode.strip())
    address_parts.append(country)
    
    full_address = ", ".join(address_parts)
    print(f"Geocoding address: {full_address}")
    
    # Call Google Maps Geocoding API
    try:
        # Prepare the API request
        formatted_address = requests.utils.quote(full_address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={formatted_address}&key={API_KEY}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://livestock-app.com/'
        }
        
        # Make the API request
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Check if API call was successful
        if data['status'] == 'OK' and data['results']:
            location = data['results'][0]['geometry']['location']
            lat, lng = location['lat'], location['lng']
            
            # Log the full formatted address that was returned
            formatted_address = data['results'][0].get('formatted_address', '')
            print(f"Successfully geocoded to: {lat}, {lng}")
            print(f"Google Maps returned address: {formatted_address}")
            
            return lat, lng
        else:
            error_message = data.get('error_message', f"Status: {data['status']}")
            print(f"Google Maps API error: {error_message}")
            print(f"API response: {json.dumps(data, indent=2)}")
            return None
    except Exception as e:
        print(f"Error during geocoding: {str(e)}")
        return None

def update_farm_locations():
    """
    Update all farm locations using dynamic geocoding
    """
    with app.app_context():
        # Get all farms
        farms = Farm.query.all()
        
        if not farms:
            print("No farms found in database")
            return
        
        print(f"Found {len(farms)} farm(s) to update")
        
        updated_count = 0
        for farm in farms:
            print(f"\nUpdating farm #{farm.id}: {farm.name}")
            print(f"Address: {farm.address}, {farm.district}, {farm.state}, {farm.pincode}")
            print(f"Current coordinates: {farm.latitude}, {farm.longitude}")
            
            # Get coordinates using Google Maps API
            coordinates = dynamic_geocode(
                farm.address, 
                farm.district, 
                farm.state, 
                farm.pincode
            )
            
            if coordinates:
                lat, lng = coordinates
                
                # Only update if coordinates are different
                if farm.latitude != lat or farm.longitude != lng:
                    old_lat, old_lng = farm.latitude, farm.longitude
                    farm.latitude = lat
                    farm.longitude = lng
                    print(f"Updated coordinates from ({old_lat}, {old_lng}) to ({lat}, {lng})")
                    updated_count += 1
                else:
                    print(f"Coordinates already correct: ({lat}, {lng})")
            else:
                print(f"Could not determine coordinates for farm #{farm.id}")
            
            # Add a delay to avoid hitting API rate limits
            time.sleep(1)
        
        # Save all changes to database
        db.session.commit()
        print(f"\nUpdated {updated_count} out of {len(farms)} farms")

if __name__ == "__main__":
    update_farm_locations()
    print("\nDone! Please restart the application to see the changes.") 