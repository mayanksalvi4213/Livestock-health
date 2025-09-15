from flask import Blueprint, render_template, session, g, redirect, url_for, jsonify
from models import db, User, DiseaseOutbreak, Animal, HealthRecord, VeterinaryService, Notification, Farm, AnimalType
from sqlalchemy.sql import func
from math import radians, cos, sin, asin, sqrt
from datetime import datetime, timedelta
from utils import get_nearby_veterinarians

dashboard_bp = Blueprint('dashboard', __name__)

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

@dashboard_bp.route('/dashboard')
def index():
    # Ensure user is logged in
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    # Get user's animals
    animals = Animal.query.filter_by(user_id=g.user.id).all()
    
    # Get recent health records
    recent_health_records = (HealthRecord.query
                            .filter_by(user_id=g.user.id)
                            .order_by(HealthRecord.created_at.desc())
                            .limit(5)
                            .all())
    
    # Get nearby disease outbreaks if farm coordinates are available
    nearby_outbreaks = []
    if farm and farm.latitude and farm.longitude:
        # First filter by district and state (faster query)
        district_outbreaks = DiseaseOutbreak.query.filter(
            DiseaseOutbreak.district == farm.district,
            DiseaseOutbreak.state == farm.state,
            DiseaseOutbreak.is_active == True
        ).all()
        
        # Then calculate distances for more precise filtering
        for outbreak in district_outbreaks:
            if outbreak.latitude and outbreak.longitude:
                distance = haversine(
                    farm.longitude, farm.latitude,
                    outbreak.longitude, outbreak.latitude
                )
                
                # Include outbreaks within 50km
                if distance <= 50:
                    outbreak.distance = distance
                    nearby_outbreaks.append(outbreak)
    
    # Sort outbreaks by distance
    nearby_outbreaks.sort(key=lambda x: x.distance)
    
    # Get nearby veterinary services
    nearby_vets = []
    if farm and farm.latitude and farm.longitude:
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
                
                # Include vets within 30km
                if distance <= 30:
                    vet.distance = distance
                    db_vets.append(vet)
        
        # If not enough vets found in database, get from Google Places API
        if len(db_vets) < 3:
            try:
                # Get real veterinary services from Google Places API
                api_vets = get_nearby_veterinarians(farm.latitude, farm.longitude, radius_km=20)
                
                # Convert API results to objects with same attributes as VeterinaryService
                class RealVet:
                    def __init__(self, data):
                        if isinstance(data, dict):
                            # Handle data from Google Places API format
                            self.name = data.get('name', 'Unknown')
                            self.address = data.get('address', 'Address not available')
                            self.distance = data.get('distance', 0)
                            self.latitude = data.get('latitude', 0)
                            self.longitude = data.get('longitude', 0)
                            self.contact_number = data.get('phone', '')
                            self.rating = data.get('rating')
                            self.website = data.get('website', '')
                        elif hasattr(data, 'service') and hasattr(data, 'distance'):
                            # Handle data from database format (in dictionary with 'service' key)
                            self.name = data['service'].name
                            self.address = data['service'].address
                            self.distance = data['distance']
                            self.latitude = data['service'].latitude
                            self.longitude = data['service'].longitude
                            self.contact_number = data['service'].phone
                            self.rating = data['service'].rating
                            self.website = data['service'].website
                
                real_vets = [RealVet(vet) for vet in api_vets]
                
                # Combine results, prioritizing database vets
                # Add API vets that aren't duplicates of database vets
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
                print(f"Error getting veterinary services: {str(e)}")
                nearby_vets = db_vets  # Use what we have from the database
        else:
            nearby_vets = db_vets
    
    # Sort vets by distance
    nearby_vets.sort(key=lambda x: x.distance)
    
    # Get unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=g.user.id, 
        is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    # Get animal count by type
    animal_counts = {}
    
    # Get animal type IDs from database
    animal_types = {
        'cow': AnimalType.query.filter_by(name='Cow').first(),
        'goat': AnimalType.query.filter_by(name='Goat').first(),
        'chicken': AnimalType.query.filter_by(name='Chicken').first()
    }
    
    # Count animals for each type
    for type_key, type_obj in animal_types.items():
        if type_obj:
            count = Animal.query.filter_by(user_id=g.user.id, animal_type_id=type_obj.id).count()
            animal_counts[type_key] = count
        else:
            animal_counts[type_key] = 0
    
    # Calculate alerts statistics
    alerts_count = len(nearby_outbreaks)
    high_severity_alerts = sum(1 for outbreak in nearby_outbreaks if outbreak.severity == 'high')
    
    return render_template('dashboard.html',
                          farm=farm,
                          animals=animals,
                          animal_counts=animal_counts,
                          health_records=recent_health_records,
                          nearby_outbreaks=nearby_outbreaks,
                          nearby_vets=nearby_vets,
                          unread_notifications=unread_notifications,
                          alerts_count=alerts_count,
                          high_severity_alerts=high_severity_alerts)

@dashboard_bp.route('/dashboard/mark-all-read')
def mark_all_read():
    """Mark all notifications as read"""
    if not g.user:
        return redirect(url_for('auth.login'))
    
    # Update all unread notifications
    unread_notifications = Notification.query.filter_by(
        user_id=g.user.id, 
        is_read=False
    ).all()
    
    for notification in unread_notifications:
        notification.is_read = True
    
    db.session.commit()
    return redirect(url_for('dashboard.index'))

@dashboard_bp.route('/api/nearby-vets')
def api_nearby_vets():
    """API endpoint to get nearby veterinarians in JSON format"""
    # Get user coordinates from session or use default
    lat = session.get('user_lat', 19.076)
    lon = session.get('user_lon', 72.877)
    radius = 20  # km
    
    # Get nearby vets
    print(f"[VETS] Getting nearby veterinarians at lat={lat}, lon={lon}, radius={radius}km")
    
    try:
        # Try to get veterinarians from database first
        radius_degrees = radius / 111  # Approximate conversion from km to degrees
        print(f"[VETS] Searching in DB with radius_degrees={radius_degrees}")
        
        services = VeterinaryService.query.filter(
            VeterinaryService.latitude.between(lat - radius_degrees, lat + radius_degrees),
            VeterinaryService.longitude.between(lon - radius_degrees, lon + radius_degrees)
        ).all()
        
        print(f"[VETS] Found {len(services)} services in database")
        
        # Filter by actual distance
        nearby_services = []
        for service in services:
            dist = haversine(lon, lat, service.longitude, service.latitude)
            if dist <= radius:
                nearby_services.append({
                    'name': service.name,
                    'distance': dist,
                    'address': service.address,
                    'phone': service.phone,
                    'website': service.website,
                    'latitude': service.latitude,
                    'longitude': service.longitude
                })
        
        print(f"[VETS] After distance filter, found {len(nearby_services)} services within {radius}km")
        
        # If not enough results from database, try Google Places API
        if len(nearby_services) < 3:
            print(f"[VETS] Not enough vets in DB, trying to get from Google Places API")
            google_results = get_nearby_veterinarians(lat, lon, radius_km=20)
            
            # Format Google results
            for place in google_results:
                # Skip if already in our results (by name)
                if any(s['name'] == place.get('name') for s in nearby_services):
                    continue
                    
                # Calculate distance
                place_lat = place.get('geometry', {}).get('location', {}).get('lat')
                place_lng = place.get('geometry', {}).get('location', {}).get('lng')
                
                if place_lat and place_lng:
                    dist = haversine(lon, lat, place_lng, place_lat)
                    
                    nearby_services.append({
                        'name': place.get('name', 'Unknown'),
                        'distance': dist,
                        'address': place.get('vicinity', ''),
                        'phone': place.get('formatted_phone_number', ''),
                        'website': place.get('website', ''),
                        'latitude': place_lat,
                        'longitude': place_lng,
                        'rating': place.get('rating'),
                        'place_id': place.get('place_id')
                    })
        
        # Sort by distance
        nearby_services.sort(key=lambda x: x['distance'])
        
        # Limit to top 5
        nearby_services = nearby_services[:5]
        
        return jsonify({
            'success': True,
            'vets': nearby_services
        })
        
    except Exception as e:
        print(f"Error getting nearby vets: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to get nearby veterinarians',
            'message': str(e)
        }) 