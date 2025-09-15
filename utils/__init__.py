"""
Utility functions for the AgriHealth application
"""
from flask import g, request
import requests
import json
import sys
import os

# Add parent directory to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Do not try to import geocode_address from utils module
# Instead, provide a fallback implementation that redirects to Google Maps API

def geocode_address(address, district=None, state=None, pincode=None, country="India"):
    """
    Geocode an address using Google Maps API directly
    This avoids circular imports and ensures consistent behavior
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
        
        # Call Google Maps Geocoding API directly
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
                
                # Log the formatted address that was returned
                formatted_address = data['results'][0].get('formatted_address', '')
                print(f"Successfully geocoded to: {lat}, {lng}")
                print(f"Google Maps returned: {formatted_address}")
                
                return lat, lng
            else:
                print(f"Google Maps API error: {data.get('status')}")
        except Exception as e:
            print(f"API geocoding error: {str(e)}")
        
        # Check for specific known locations as fallback
        if address and district:
            address_lower = address.lower()
            district_lower = district.lower()
            
            # Special case for Pawas, Ratnagiri
            if 'pawas' in address_lower and 'ratnagiri' in district_lower:
                return 16.991, 73.299
            
            # Special case for Kasarvadavli/Ghodbunder Road, Thane
            if ('kasarvadavli' in address_lower or 'ghodbunder' in address_lower) and 'thane' in district_lower:
                return 19.2350, 72.9674
            
            # Special case for Thane West
            if 'thane west' in address_lower and 'thane' in district_lower:
                return 19.2183, 72.9781
        
        # Final fallback - use state default
        if state:
            state_lower = state.lower()
            if state_lower == 'maharashtra':
                return 19.7515, 75.7139
        
        # Default to center of India if all else fails
        print("Using default coordinates (center of India)")
        return 21.7679, 78.8718
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return 21.7679, 78.8718  # Default to center of India

# Add the missing function that's being imported in profile.py
def get_current_language():
    """
    Get current language from:
    1. User's preferred language (if logged in)
    2. Cookie
    3. Default to English
    
    Returns:
        str: Language code (e.g., 'en', 'hi')
    """
    # First check if user is logged in and has preferred language
    if hasattr(g, 'user') and g.user and hasattr(g.user, 'preferred_language') and g.user.preferred_language:
        return g.user.preferred_language.code
    
    # Next check cookie
    return request.cookies.get('language', 'en')

# Add the missing function that's being imported in dashboard.py
def get_nearby_veterinarians(latitude, longitude, radius_km=10, limit=5, **kwargs):
    """
    Find nearby veterinary services based on coordinates
    
    Args:
        latitude (float): Latitude of the location
        longitude (float): Longitude of the location
        radius_km (int): Search radius in kilometers
        limit (int): Maximum number of results to return
        **kwargs: Additional parameters for backward compatibility
        
    Returns:
        list: List of veterinary services ordered by distance
    """
    from models import VeterinaryService
    from sqlalchemy import func, desc
    import math
    
    # Debug flag
    DEBUG = True
    
    if DEBUG:
        print(f"[VETS] Getting nearby veterinarians at lat={latitude}, lon={longitude}, radius={radius_km}km")
    
    # For backward compatibility with code that uses 'radius' parameter
    if 'radius' in kwargs:
        radius_km = kwargs['radius']
        if DEBUG:
            print(f"[VETS] Using radius from kwargs: {radius_km}km")
    
    if not latitude or not longitude:
        if DEBUG:
            print("[VETS] No coordinates provided, returning empty list")
        return []
    
    try:
        # Convert radius from km to degrees (approximate)
        # 1 degree of latitude is approximately 111 km
        radius_degrees = radius_km / 111.0
        
        if DEBUG:
            print(f"[VETS] Searching in DB with radius_degrees={radius_degrees}")
        
        # Get veterinary services within the radius
        # This is a simplified calculation and not precise for large distances
        services = VeterinaryService.query.filter(
            func.abs(VeterinaryService.latitude - latitude) <= radius_degrees,
            func.abs(VeterinaryService.longitude - longitude) <= radius_degrees
        ).all()
        
        if DEBUG:
            print(f"[VETS] Found {len(services)} services in database")
        
        # Calculate actual distance for each service
        result = []
        for service in services:
            # Haversine formula for distance calculation
            dlat = math.radians(service.latitude - latitude)
            dlon = math.radians(service.longitude - longitude)
            a = (math.sin(dlat/2) * math.sin(dlat/2) +
                 math.cos(math.radians(latitude)) * 
                 math.cos(math.radians(service.latitude)) *
                 math.sin(dlon/2) * math.sin(dlon/2))
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            distance = 6371 * c  # Earth radius in km
            
            if distance <= radius_km:
                result.append({
                    'service': service,
                    'distance': round(distance, 1)
                })
        
        if DEBUG:
            print(f"[VETS] After distance filter, found {len(result)} services within {radius_km}km")
        
        # If not enough vets found in DB, try to get some from Google Places API
        if len(result) < 3:
            if DEBUG:
                print(f"[VETS] Not enough vets in DB, trying to get from Google Places API")
            
            # Google Places API key (reuse the Google Maps API key)
            API_KEY = "AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM"
            
            # Google Places API - Nearby Search request
            url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            params = {
                'location': f"{latitude},{longitude}",
                'radius': radius_km * 1000,  # Convert km to meters
                'type': 'veterinary_care',
                'key': API_KEY
            }
            
            if DEBUG:
                print(f"[VETS] Making API request to Google Places API: {url}")
            
            try:
                response = requests.get(url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if DEBUG:
                        print(f"[VETS] API response status: {data.get('status')}")
                        print(f"[VETS] Found {len(data.get('results', []))} places")
                    
                    if data.get('status') == 'OK':
                        # Process results
                        places = data.get('results', [])
                        api_results = []
                        
                        for place in places:
                            place_lat = place['geometry']['location']['lat']
                            place_lng = place['geometry']['location']['lng']
                            
                            # Calculate distance using Haversine formula
                            dlat = math.radians(place_lat - latitude)
                            dlon = math.radians(place_lng - longitude)
                            a = (math.sin(dlat/2) * math.sin(dlat/2) +
                                math.cos(math.radians(latitude)) * 
                                math.cos(math.radians(place_lat)) *
                                math.sin(dlon/2) * math.sin(dlon/2))
                            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                            distance = 6371 * c  # Earth radius in km
                            
                            # Create a result object similar to VeterinaryService model
                            vet_result = {
                                'name': place.get('name', 'Unknown Vet'),
                                'address': place.get('vicinity', 'Address not available'),
                                'distance': round(distance, 1),
                                'latitude': place_lat,
                                'longitude': place_lng,
                                'rating': place.get('rating'),
                                'phone': place.get('phone', ''),
                                'website': place.get('website', '')
                            }
                            
                            # Add to results
                            api_results.append(vet_result)
                        
                        if DEBUG:
                            print(f"[VETS] Processed {len(api_results)} API results")
                        
                        # Combine results
                        result.extend(api_results)
                
                else:
                    if DEBUG:
                        print(f"[VETS] API error: {response.status_code} - {response.text}")
            
            except Exception as e:
                if DEBUG:
                    print(f"[VETS] Exception calling Google Places API: {str(e)}")
        
        # Sort by distance and limit results
        result.sort(key=lambda x: x['distance'])
        final_results = result[:limit]
        
        if DEBUG:
            print(f"[VETS] Returning {len(final_results)} nearby veterinarians")
        
        return final_results
    
    except Exception as e:
        print(f"Error finding nearby veterinarians: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return [] 