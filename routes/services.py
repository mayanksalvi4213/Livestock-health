from flask import Blueprint, render_template, session, g, redirect, url_for, request, jsonify
from models import db, User, Farm, VeterinaryService
from utils import get_nearby_veterinarians
from math import radians, cos, sin, asin, sqrt

services_bp = Blueprint('services', __name__)

# Haversine formula for calculating distance between two lat/long points
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    
    # Haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

@services_bp.route('/veterinary-services')
def veterinary_services():
    """Display all veterinary services near the user's farm"""
    # Ensure user is logged in
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    # Initialize variables
    nearby_vets = []
    
    if farm and farm.latitude and farm.longitude:
        # Get the search radius from query parameter or use default
        search_radius = request.args.get('radius', type=int, default=20)
        
        # First try to get vets from database
        district_vets = VeterinaryService.query.filter(
            VeterinaryService.district == farm.district,
            VeterinaryService.state == farm.state
        ).all()
        
        # Calculate distances for database vets
        db_vets = []
        for vet in district_vets:
            if vet.latitude and vet.longitude:
                distance = haversine(
                    farm.longitude, farm.latitude,
                    vet.longitude, vet.latitude
                )
                
                # Include vets within the specified radius
                if distance <= search_radius:
                    vet.distance = distance
                    db_vets.append(vet)
        
        # Get vets from Google Places API
        try:
            # Get real veterinary services from Google Places API
            api_vets = get_nearby_veterinarians(farm.latitude, farm.longitude, radius=search_radius)
            
            # Convert API results to objects with same attributes as VeterinaryService
            class RealVet:
                def __init__(self, data):
                    self.name = data['name']
                    self.address = data['address']
                    self.distance = data['distance']
                    self.latitude = data['latitude']
                    self.longitude = data['longitude']
                    self.contact_number = data.get('phone', '')
                    self.rating = data.get('rating', None)
                    self.website = data.get('website', '')
            
            real_vets = [RealVet(vet) for vet in api_vets]
            
            # Combine results, prioritizing database vets
            for api_vet in real_vets:
                is_duplicate = False
                for db_vet in db_vets:
                    # Check if this is the same vet (by comparing coordinates)
                    if (abs(db_vet.latitude - api_vet.latitude) < 0.001 and 
                        abs(db_vet.longitude - api_vet.longitude) < 0.001):
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    db_vets.append(api_vet)
            
            nearby_vets = db_vets
        except Exception as e:
            print(f"Error getting veterinary services from API: {str(e)}")
            nearby_vets = db_vets  # Use what we have from the database
    
    # Sort vets by distance
    nearby_vets.sort(key=lambda x: x.distance)
    
    # Render the template with the vet data
    return render_template('services/veterinary_services.html', 
                           farm=farm,
                           nearby_vets=nearby_vets)

@services_bp.route('/api/nearby-vets')
def api_nearby_vets():
    """API endpoint to get nearby vets in JSON format"""
    # Ensure user is logged in
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    if not farm or not farm.latitude or not farm.longitude:
        return jsonify({'error': 'Farm location not available'}), 400
    
    # Get the search radius from query parameter or use default
    search_radius = request.args.get('radius', type=int, default=20)
    
    # Get vets from Google Places API
    try:
        vets = get_nearby_veterinarians(farm.latitude, farm.longitude, radius=search_radius)
        return jsonify({'vets': vets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500 