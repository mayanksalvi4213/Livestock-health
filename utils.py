import os
import random
import string
import requests
from datetime import datetime, timedelta
from flask import current_app, g, request
from math import radians, cos, sin, asin, sqrt

def generate_otp(length=6):
    """Generate a random OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

def get_current_language():
    """Get the current language from request cookie or session"""
    # First try from g (global context)
    if hasattr(g, 'language'):
        return g.language
    
    # Then try from request cookies
    lang = request.cookies.get('language', 'en')
    
    # Validate language code (only allow supported languages)
    if lang not in ['en', 'hi', 'mr', 'gu', 'pa', 'ta', 'te', 'bn', 'kn', 'ml']:
        lang = 'en'  # Default to English if unsupported
    
    # Store in g for future use in this request
    g.language = lang
    return lang

def geocode_address(address, district, state, country='India', pincode=None):
    """
    Geocode an address to get latitude and longitude using Google Maps API
    Returns the coordinates or None if geocoding fails
    """
    try:
        # Build the complete address string for better geocoding results
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
        
        # First try Google Maps Geocoding API - most accurate method
        try:
            # Prepare the API request
            api_key = "AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM"
            formatted_address = requests.utils.quote(full_address)
            url = f"https://maps.googleapis.com/maps/api/geocode/json?address={formatted_address}&key={api_key}"
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
                print("Falling back to alternative geocoding methods...")
        except Exception as e:
            print(f"Error during Google API geocoding: {str(e)}")
            print("Falling back to alternative geocoding methods...")
        
        # Fall back to pincode mapping if Google API fails
        if pincode:
            # Location database by pincode - can be expanded for all locations
            pincode_mapping = {
                # Maharashtra
                '415616': (16.991, 73.299),  # Pawas, Ratnagiri
                '415639': (16.9902, 73.3129),  # Ratnagiri
                '416604': (16.7042, 74.2433),  # Kolhapur
                '444303': (20.9320, 77.7523),  # Amravati
                '431001': (19.8762, 75.3433),  # Aurangabad
                '413713': (17.6599, 74.0089),  # Satara
                '422101': (19.9975, 73.7898),  # Nashik
                '400615': (19.2350, 72.9674),  # Kasarvadavli, Ghodbunder Road, Thane West
                
                # Gujarat
                '370201': (23.2472, 69.6682),  # Kutch
                '380015': (23.0225, 72.5714),  # Ahmedabad
                '390001': (22.3072, 73.1812),  # Vadodara
                '395003': (21.1702, 72.8311),  # Surat
                
                # Punjab
                '143001': (31.6340, 74.8723),  # Amritsar
                '144001': (31.3260, 75.5762),  # Jalandhar
                '160022': (30.7333, 76.7794),  # Chandigarh
                
                # Rajasthan
                '302001': (26.9124, 75.7873),  # Jaipur
                '313001': (24.5854, 73.7125),  # Udaipur
                '342001': (26.2389, 73.0243),  # Jodhpur
            }
            
            if pincode in pincode_mapping:
                print(f"Using pincode mapping for {pincode}")
                return pincode_mapping[pincode]
        
        # Fall back to location database by district and location keywords
        if district and state:
            district_key = district.lower()
            state_key = state.lower()
            
            # Location database by district and state
            location_mapping = {
                ('ratnagiri', 'maharashtra'): {
                    'pawas': (16.991, 73.299),
                    'default': (16.9902, 73.3129)  # Ratnagiri city coordinates
                },
                ('thane', 'maharashtra'): {
                    'vartak nagar': (19.2220, 72.9614),
                    'thane west': (19.2183, 72.9781),
                    'kasarvadavli': (19.2350, 72.9674),  # Kasarvadavli, Ghodbunder Road
                    'ghodbunder': (19.2370, 72.9680),    # Ghodbunder Road area
                    'default': (19.2183, 72.9781)
                },
                ('mumbai', 'maharashtra'): {
                    'andheri': (19.1136, 72.8697),
                    'bandra': (19.0596, 72.8295),
                    'default': (19.0760, 72.8777)
                },
                ('pune', 'maharashtra'): {
                    'default': (18.5204, 73.8567)
                },
                ('nashik', 'maharashtra'): {
                    'default': (19.9975, 73.7898)
                },
                ('kolhapur', 'maharashtra'): {
                    'default': (16.7042, 74.2433)
                },
                ('amravati', 'maharashtra'): {
                    'default': (20.9320, 77.7523)
                },
                ('ahmedabad', 'gujarat'): {
                    'default': (23.0225, 72.5714)
                },
                ('vadodara', 'gujarat'): {
                    'default': (22.3072, 73.1812)
                },
                ('jaipur', 'rajasthan'): {
                    'default': (26.9124, 75.7873)
                },
                ('amritsar', 'punjab'): {
                    'default': (31.6340, 74.8723)
                }
            }
            
            if (district_key, state_key) in location_mapping:
                district_map = location_mapping[(district_key, state_key)]
                
                # Check for specific location within district
                if address:
                    address_lower = address.lower()
                    for location, coords in district_map.items():
                        if location != 'default' and location in address_lower:
                            print(f"Using mapping for {location} in {district}, {state}")
                            return coords
                
                # Use district default if specific location not found but district is known
                if 'default' in district_map:
                    print(f"Using default mapping for {district}, {state}")
                    return district_map['default']
        
        # As a last resort, fall back to state-level geocoding
        print("Falling back to state-level geocoding")
        state_mapping = {
            'maharashtra': (19.7515, 75.7139),
            'gujarat': (22.2587, 71.1924),
            'rajasthan': (27.0238, 74.2179),
            'punjab': (31.1471, 75.3412),
            'haryana': (29.0588, 76.0856),
            'uttar pradesh': (26.8467, 80.9462),
            'madhya pradesh': (22.9734, 78.6569),
            'bihar': (25.0961, 85.3131),
            'west bengal': (22.9868, 87.8550),
            'tamil nadu': (11.1271, 78.6569),
            'karnataka': (15.3173, 75.7139),
            'kerala': (10.8505, 76.2711),
            'andhra pradesh': (15.9129, 79.7400),
            'telangana': (18.1124, 79.0193),
            'odisha': (20.9517, 85.0985),
            'assam': (26.2006, 92.9376),
            'chhattisgarh': (21.2787, 81.8661)
        }
        
        if state:
            state_key = state.lower()
            if state_key in state_mapping:
                print(f"Using pre-defined coordinates for {state}")
                return state_mapping[state_key]
        
        # If all else fails, return None
        return None, None
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return None, None

def get_nearby_veterinarians(lat, lng, radius=20):
    """
    Get nearby veterinarians based on coordinates using Google Places API
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        radius (int): Radius in kilometers to search
    
    Returns:
        list: List of veterinary services with location details
    """
    # Define haversine function locally to avoid dependency issues
    def haversine(lon1, lat1, lon2, lat2):
        # Convert decimal degrees to radians 
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula 
        dlon = lon2 - lon1 
        dlat = lat2 - lat1 
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a)) 
        r = 6371  # Radius of earth in kilometers
        return c * r
    
    api_key = "AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM"
    
    # Convert radius from km to meters
    radius_meters = radius * 1000
    
    # Prepare the request URL for Google Places API - use keyword for broader search
    # Indian veterinary services may not be categorized properly, so using multiple keywords
    url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={lat},{lng}&radius={radius_meters}&keyword=veterinary|animal|cattle|clinic|hospital&key={api_key}"
    
    print(f"Fetching veterinary services from Google Places API: {url}")
    
    try:
        # Make the request with proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://livestock-app.com/'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()
        
        # Log the response status and count
        if data['status'] == 'OK':
            print(f"Found {len(data['results'])} veterinary services nearby")
            vets = []
            for place in data['results']:
                # Filter out non-veterinary places (like human hospitals)
                place_name = place['name'].lower()
                
                # Include common English and Indian terms for veterinary services
                vet_terms = [
                    'vet', 'animal', 'cattle', 'livestock', 'pet', 'dairy', 
                    'pashu', 'prani', 'janwar', 'pashupalak', 'gau', 'goshala',
                    'veterinary', 'chicksa', 'chikitsalaya', 'chikitsak'
                ]
                
                if not any(term in place_name for term in vet_terms):
                    # Skip places that don't seem to be animal-related
                    if 'hospital' in place_name and not any(term in place_name for term in ['veterinary', 'pashu', 'prani', 'animal']):
                        print(f"Skipping non-veterinary place: {place['name']}")
                        continue
                
                # Calculate distance in km (simplified)
                place_lat = place['geometry']['location']['lat']
                place_lng = place['geometry']['location']['lng']
                
                # Use haversine formula to calculate distance
                distance = haversine(place_lng, place_lat, lng, lat)
                
                # Format the vet data
                vet = {
                    'name': place['name'],
                    'address': place.get('vicinity', 'Address not available'),
                    'latitude': place_lat,
                    'longitude': place_lng,
                    'distance': round(distance, 1),
                    'rating': place.get('rating', None),
                    'place_id': place['place_id']
                }
                
                # Try to get phone number and website from place details
                if 'place_id' in place:
                    try:
                        details_url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place['place_id']}&fields=formatted_phone_number,website&key={api_key}"
                        details_response = requests.get(details_url, headers=headers, timeout=5)
                        details_data = details_response.json()
                        
                        if details_data['status'] == 'OK':
                            result = details_data['result']
                            vet['phone'] = result.get('formatted_phone_number', '')
                            vet['website'] = result.get('website', '')
                    except Exception as e:
                        print(f"Error fetching place details: {str(e)}")
                
                vets.append(vet)
            
            return vets
        else:
            print(f"Google Places API error: {data['status']}")
            if 'error_message' in data:
                print(f"Error message: {data['error_message']}")
            
            # Fall back to mock data if API call fails
            return get_mock_veterinarians(lat, lng)
    except Exception as e:
        print(f"Error fetching nearby veterinarians: {str(e)}")
        # Fall back to mock data if request fails
        return get_mock_veterinarians(lat, lng)

def get_mock_veterinarians(lat, lng, count=3):
    """
    Get mock veterinarian data as fallback
    """
    vets = [
        {
            'name': 'District Veterinary Hospital',
            'address': 'Main Road, City Center',
            'distance': round(random.uniform(1.5, 5.0), 1),
            'latitude': lat + 0.01,
            'longitude': lng + 0.015,
            'rating': round(random.uniform(3.5, 5.0), 1),
            'phone': '+91 9876543210',
            'website': 'http://example.com/vet1'
        },
        {
            'name': 'Animal Care Center',
            'address': 'Near Bus Stand, Green Avenue',
            'distance': round(random.uniform(2.0, 6.0), 1),
            'latitude': lat - 0.008,
            'longitude': lng + 0.012,
            'rating': round(random.uniform(3.5, 5.0), 1),
            'phone': '+91 9876543211',
            'website': 'http://example.com/vet2'
        },
        {
            'name': 'Livestock Health Center',
            'address': 'Rural Area, Farm Road',
            'distance': round(random.uniform(3.0, 8.0), 1),
            'latitude': lat - 0.015,
            'longitude': lng - 0.01,
            'rating': round(random.uniform(3.5, 5.0), 1),
            'phone': '+91 9876543212',
            'website': 'http://example.com/vet3'
        }
    ]
    
    return vets[:count]

def get_disease_alerts(district=None, state=None, animal_type=None):
    """
    Get disease alerts based on location and animal type
    This is a placeholder function that would normally fetch data from a database or API
    For now, it returns mock data
    """
    # In a real application, you would query a database or API
    
    # For now, return mock data
    all_alerts = [
        {
            'id': 1,
            'disease': 'Foot and Mouth Disease',
            'animal_type': 'cow',
            'severity': 'high',
            'location': 'Anand, Gujarat',
            'district': 'Anand',
            'state': 'Gujarat',
            'reported_date': datetime.now() - timedelta(days=random.randint(1, 10)),
            'reported_by': 'District Veterinary Officer',
            'description': 'Multiple cases of FMD detected in dairy farms.',
            'preventive_measures': [
                'Isolate affected animals',
                'Implement biosecurity measures',
                'Vaccinate healthy animals',
                'Restrict movement of animals'
            ]
        },
        {
            'id': 2,
            'disease': 'Newcastle Disease',
            'animal_type': 'chicken',
            'severity': 'medium',
            'location': 'Nashik, Maharashtra',
            'district': 'Nashik',
            'state': 'Maharashtra',
            'reported_date': datetime.now() - timedelta(days=random.randint(1, 15)),
            'reported_by': 'Poultry Farm Association',
            'description': 'Several cases reported in backyard poultry.',
            'preventive_measures': [
                'Vaccinate healthy birds',
                'Improve sanitation',
                'Control wild bird access',
                'Proper disposal of dead birds'
            ]
        },
        {
            'id': 3,
            'disease': 'Brucellosis',
            'animal_type': 'goat',
            'severity': 'medium',
            'location': 'Jaipur, Rajasthan',
            'district': 'Jaipur',
            'state': 'Rajasthan',
            'reported_date': datetime.now() - timedelta(days=random.randint(1, 20)),
            'reported_by': 'State Veterinary Department',
            'description': 'Cases detected in multiple goat farms.',
            'preventive_measures': [
                'Test and cull positive animals',
                'Vaccinate young animals',
                'Proper disposal of aborted fetuses',
                'Maintain good hygiene during milking'
            ]
        }
    ]
    
    # Filter based on parameters
    filtered_alerts = all_alerts
    
    if district:
        filtered_alerts = [alert for alert in filtered_alerts if alert['district'].lower() == district.lower()]
    
    if state:
        filtered_alerts = [alert for alert in filtered_alerts if alert['state'].lower() == state.lower()]
    
    if animal_type:
        filtered_alerts = [alert for alert in filtered_alerts if alert['animal_type'].lower() == animal_type.lower()]
    
    # Decide randomly if we should return alerts or not
    if random.random() < 0.7:  # 70% chance to return alerts
        return filtered_alerts
    else:
        return []

def format_date(date, format='%d %b %Y'):
    """Format a date object to string"""
    if date:
        return date.strftime(format)
    return ''

def calculate_distance(lat1, lng1, lat2, lng2):
    """
    Calculate distance between two coordinates using Haversine formula
    This is simplified and doesn't account for Earth's curvature
    """
    # In a real application, you would use a more accurate formula
    # For now, return an approximate distance
    return round(((lat1 - lat2) ** 2 + (lng1 - lng2) ** 2) ** 0.5 * 111, 1)  # Approx km 