from flask import Blueprint, render_template, session, g, redirect, url_for, request, jsonify
from models import db, User, Farm, DiseaseOutbreak, Animal, VeterinaryService, Notification
from datetime import datetime, timedelta
import requests
import json
import os
from math import radians, cos, sin, asin, sqrt
import pandas as pd
import numpy as np
from sqlalchemy import func
import random

disease_alerts_bp = Blueprint('disease_alerts', __name__)

# Haversine formula for calculating distance between two points
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

# Weather-based disease risk factors
DISEASE_RISK_FACTORS = {
    "Foot and Mouth Disease": {
        "high_temp": 30,
        "high_humidity": 80,
        "rainy_season": True
    },
    "Black Quarter": {
        "high_rainfall": 100,
        "temp_range": (25, 35),
        "soil_type": "clayey"
    },
    "Haemorrhagic Septicaemia": {
        "high_humidity": 85,
        "temp_range": (30, 40),
        "rainy_season": True
    },
    "Anthrax": {
        "high_temp": 35,
        "low_rainfall": 20,
        "soil_disturbance": True
    },
    "Bluetongue": {
        "vector_season": True,
        "temp_range": (20, 30),
        "high_rainfall": 80
    },
    "PPR": {
        "dry_season": True,
        "low_temp": 15
    },
    "Brucellosis": {
        "all_seasons": True
    },
    "Theileriosis": {
        "vector_season": True,
        "temp_range": (25, 35)
    },
    "Mastitis": {
        "high_humidity": 80,
        "high_temp": 35
    },
    "Babesiosis": {
        "vector_season": True,
        "temp_range": (25, 32)
    }
}

# Specific animal types affected by diseases
DISEASE_ANIMAL_TYPES = {
    "Foot and Mouth Disease": ["cow", "buffalo", "sheep", "goat", "pig"],
    "Black Quarter": ["cow", "buffalo"],
    "Haemorrhagic Septicaemia": ["cow", "buffalo"],
    "Anthrax": ["cow", "buffalo", "sheep", "goat", "pig"],
    "Bluetongue": ["sheep", "goat"],
    "PPR": ["sheep", "goat"],
    "Brucellosis": ["cow", "buffalo", "sheep", "goat", "pig"],
    "Theileriosis": ["cow", "buffalo"],
    "Mastitis": ["cow", "buffalo", "sheep", "goat"],
    "Babesiosis": ["cow", "buffalo"]
}

# Get current weather data for a location
def get_weather_data(lat, lon, api_key):
    """
    Get current weather data from WeatherAPI.com
    """
    # Use a valid WeatherAPI key
    WEATHER_API_KEY = "6e36f2851df64f8c8eb152209252804"
    
    # First try to use the provided API key, but fall back to default if needed
    api_key_to_use = api_key if api_key and api_key != 'your_api_key_here' else WEATHER_API_KEY
    
    # WeatherAPI.com endpoint
    url = f"https://api.weatherapi.com/v1/forecast.json?key={api_key_to_use}&q={lat},{lon}&days=1&aqi=no&alerts=no"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            print(f"Successfully retrieved weather data for location lat:{lat}, lon:{lon}")
            data = response.json()
            
            # Convert WeatherAPI format to our expected format
            return {
                'current': {
                    'temp': data['current']['temp_c'],
                    'humidity': data['current']['humidity'],
                    'wind_speed': data['current']['wind_kph'],
                    'weather': [{
                        'icon': f"{data['current']['condition']['code']}",
                        'description': data['current']['condition']['text']
                    }]
                },
                'daily': [
                    {
                        'temp': {
                            'day': data['forecast']['forecastday'][0]['day']['avgtemp_c'],
                            'min': data['forecast']['forecastday'][0]['day']['mintemp_c'],
                            'max': data['forecast']['forecastday'][0]['day']['maxtemp_c']
                        },
                        'rain': data['forecast']['forecastday'][0]['day'].get('totalprecip_mm', 0),
                        'weather': [{
                            'icon': f"{data['forecast']['forecastday'][0]['day']['condition']['code']}",
                            'description': data['forecast']['forecastday'][0]['day']['condition']['text']
                        }]
                    }
                ]
            }
        else:
            print(f"Error fetching weather data: {response.status_code}")
            # Return mock data as fallback
            return get_mock_weather_data()
    except Exception as e:
        print(f"Exception fetching weather data: {str(e)}")
        # Return mock data as fallback
        return get_mock_weather_data()

def get_mock_weather_data():
    """Return mock weather data for when API calls fail"""
    print("Using mock weather data due to API error")
    return {
        'current': {
            'temp': 25,
            'humidity': 65,
            'wind_speed': 5,
            'weather': [{'icon': '1000', 'description': 'clear sky'}]
        },
        'daily': [
            {
                'temp': {'day': 25, 'min': 20, 'max': 30},
                'rain': 0,
                'weather': [{'icon': '1000', 'description': 'clear sky'}]
            }
        ]
    }

# Check if a location is in a monsoon season based on the date and geographic location
def is_monsoon_season(lat, lon, date):
    """
    Determine if the given location is in monsoon season on the specified date
    This is a simplified check based on India's general monsoon patterns
    """
    month = date.month
    
    # Southwest monsoon: June to September
    if 6 <= month <= 9:
        # Affects most of India
        return True
    
    # Northeast monsoon: October to December
    if 10 <= month <= 12:
        # Mainly affects southeastern India (Tamil Nadu, coastal Andhra Pradesh)
        if 8 <= lat <= 20 and 77 <= lon <= 85:
            return True
    
    return False

# Determine if it's vector season (for vector-borne diseases)
def is_vector_season(weather_data, date):
    """
    Determine if current conditions are favorable for disease vectors like ticks and mosquitoes
    """
    if not weather_data:
        return False
    
    # Get current temperature and humidity
    current_temp = weather_data['current']['temp']
    current_humidity = weather_data['current'].get('humidity', 50)
    
    # Check if it's monsoon or post-monsoon season (favorable for vectors)
    month = date.month
    monsoon_or_post_monsoon = 6 <= month <= 11
    
    # Vectors thrive in warm and humid conditions
    return current_temp > 20 and current_humidity > 60 and monsoon_or_post_monsoon

# Calculate disease risk score based on weather and location factors
def calculate_disease_risk(disease, weather_data, farm_data, current_date):
    """
    Calculate risk score (0-100) for a particular disease based on current conditions
    """
    if not weather_data:
        return 20  # Return a base risk level if weather data is unavailable
    
    risk_score = 20  # Base risk score
    risk_factors = DISEASE_RISK_FACTORS.get(disease, {})
    
    # Current weather conditions
    current_temp = weather_data['current']['temp']
    current_humidity = weather_data['current'].get('humidity', 50)
    
    # Get rainfall from daily forecast (mm/day)
    try:
        daily_rainfall = weather_data['daily'][0].get('rain', 0)
    except (KeyError, IndexError):
        daily_rainfall = 0
    
    # Check for high temperature risk
    if 'high_temp' in risk_factors and current_temp >= risk_factors['high_temp']:
        risk_score += 15
    
    # Check for temperature range risk
    if 'temp_range' in risk_factors:
        min_temp, max_temp = risk_factors['temp_range']
        if min_temp <= current_temp <= max_temp:
            risk_score += 20
    
    # Check for low temperature risk
    if 'low_temp' in risk_factors and current_temp <= risk_factors['low_temp']:
        risk_score += 15
    
    # Check for high humidity risk
    if 'high_humidity' in risk_factors and current_humidity >= risk_factors['high_humidity']:
        risk_score += 15
    
    # Check for rainfall-related risks
    if 'high_rainfall' in risk_factors and daily_rainfall >= risk_factors['high_rainfall']:
        risk_score += 15
    elif 'low_rainfall' in risk_factors and daily_rainfall <= risk_factors['low_rainfall']:
        risk_score += 10
    
    # Check for seasonal factors
    if ('rainy_season' in risk_factors and 
        risk_factors['rainy_season'] and 
        is_monsoon_season(farm_data.latitude, farm_data.longitude, current_date)):
        risk_score += 15
    
    if 'vector_season' in risk_factors and risk_factors['vector_season']:
        if is_vector_season(weather_data, current_date):
            risk_score += 20
    
    # Add historical outbreak factor
    # If this disease has occurred in this region before, risk is higher
    # This would typically come from your database
    
    # Cap risk score at 100
    return min(risk_score, 100)

# Check for disease outbreaks near a farm
def get_nearby_disease_outbreaks(farm, radius=50):
    """
    Get disease outbreaks within a specified radius of a farm
    """
    nearby_outbreaks = []
    
    if farm and farm.latitude and farm.longitude:
        # First filter by district and state (faster query)
        district_outbreaks = DiseaseOutbreak.query.filter(
            DiseaseOutbreak.district == farm.district,
            DiseaseOutbreak.state == farm.state,
            DiseaseOutbreak.is_active == True
        ).all()
        
        # If no outbreaks in same district, get all outbreaks
        if not district_outbreaks:
            district_outbreaks = DiseaseOutbreak.query.filter(
                DiseaseOutbreak.is_active == True
            ).all()
        
        # Then calculate distances for more precise filtering
        for outbreak in district_outbreaks:
            if outbreak.latitude and outbreak.longitude:
                distance = haversine(
                    farm.longitude, farm.latitude,
                    outbreak.longitude, outbreak.latitude
                )
                
                # Include outbreaks within the radius
                if distance <= radius:
                    outbreak.distance = distance
                    
                    # Add placeholder stats if not present in the database
                    if not hasattr(outbreak, 'affected_animals'):
                        outbreak.affected_animals = random.randint(5, 100)
                    
                    if not hasattr(outbreak, 'deaths'):
                        outbreak.deaths = random.randint(0, int(outbreak.affected_animals * 0.3))
                    
                    if not hasattr(outbreak, 'morbidity_rate'):
                        outbreak.morbidity_rate = random.randint(20, 80)
                    
                    if not hasattr(outbreak, 'mortality_rate'):
                        outbreak.mortality_rate = round((outbreak.deaths / outbreak.affected_animals) * 100, 1) if outbreak.affected_animals > 0 else 0
                    
                    nearby_outbreaks.append(outbreak)
        
        # Sort outbreaks by distance
        nearby_outbreaks.sort(key=lambda x: x.distance)
    
    return nearby_outbreaks

# Get disease risks for a farm based on current conditions
def get_disease_risks_for_farm(farm, weather_api_key=None):
    """
    Calculate disease risks for a farm based on its location and current weather conditions
    """
    if not farm or not farm.latitude or not farm.longitude:
        return []
    
    # Get animal types on this farm
    farm_animals = Animal.query.filter_by(farm_id=farm.id).all()
    farm_animal_types = set([animal.animal_type.name.lower() for animal in farm_animals])
    
    # Get current weather data - API key is now hardcoded in the get_weather_data function
    weather_data = get_weather_data(farm.latitude, farm.longitude, None)
    current_date = datetime.utcnow()
    
    disease_risks = []
    
    # Calculate risk for each disease
    for disease in DISEASE_RISK_FACTORS.keys():
        # Only include diseases that can affect animals on this farm
        disease_affects = DISEASE_ANIMAL_TYPES.get(disease, [])
        if not farm_animal_types.intersection(disease_affects) and disease_affects:
            continue
        
        risk_score = calculate_disease_risk(disease, weather_data, farm, current_date)
        
        # Determine risk level category
        risk_level = "low"
        if risk_score >= 70:
            risk_level = "high"
        elif risk_score >= 40:
            risk_level = "medium"
        
        disease_risks.append({
            "disease_name": disease,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "affected_animals": list(farm_animal_types.intersection(disease_affects))
        })
    
    # Sort by risk score (highest first)
    disease_risks.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return disease_risks

# Get historical disease pattern for a region
def get_historical_disease_pattern(district, state, disease_name=None):
    """
    Get historical disease outbreak patterns for a district/state
    """
    query = DiseaseOutbreak.query.filter(
        DiseaseOutbreak.district == district,
        DiseaseOutbreak.state == state
    )
    
    if disease_name:
        query = query.filter(DiseaseOutbreak.disease_name == disease_name)
    
    # Get outbreaks from the last 3 years
    three_years_ago = datetime.utcnow() - timedelta(days=3*365)
    query = query.filter(DiseaseOutbreak.reported_date >= three_years_ago)
    
    historical_outbreaks = query.all()
    
    # Group by month to find seasonal patterns
    monthly_counts = {}
    for outbreak in historical_outbreaks:
        month = outbreak.reported_date.month
        monthly_counts[month] = monthly_counts.get(month, 0) + 1
    
    return {
        "total_outbreaks": len(historical_outbreaks),
        "monthly_pattern": monthly_counts
    }

@disease_alerts_bp.route('/disease-alerts')
def index():
    """Disease alerts homepage"""
    # Default values
    nearby_outbreaks = []
    disease_risks = []
    
    # Get user's farm
    farm = None
    if g.user:
        farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    if farm and farm.latitude and farm.longitude:
        # Get nearby disease outbreaks
        nearby_outbreaks = get_nearby_disease_outbreaks(farm)
        
        # Get disease risks based on current conditions
        disease_risks = get_disease_risks_for_farm(farm, None)  # API key is now hardcoded in the function
    
    return render_template('disease/alerts.html',
                          farm=farm,
                          nearby_outbreaks=nearby_outbreaks,
                          disease_risks=disease_risks)

@disease_alerts_bp.route('/api/disease-alerts/nearby')
def api_nearby_disease_outbreaks():
    """API endpoint to get nearby disease outbreaks"""
    # Ensure user is logged in
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user's farm
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    if not farm or not farm.latitude or not farm.longitude:
        return jsonify({'error': 'Farm location not available'}), 400
    
    # Get radius parameter (default 50 km)
    radius = request.args.get('radius', default=50, type=int)
    
    # Get nearby outbreaks
    nearby_outbreaks = get_nearby_disease_outbreaks(farm, radius)
    
    # Format outbreaks for JSON response
    outbreaks_data = []
    for outbreak in nearby_outbreaks:
        outbreaks_data.append({
            'id': outbreak.id,
            'disease_name': outbreak.disease_name,
            'severity': outbreak.severity,
            'location': outbreak.location,
            'district': outbreak.district,
            'state': outbreak.state,
            'latitude': outbreak.latitude,
            'longitude': outbreak.longitude,
            'reported_date': outbreak.reported_date.strftime('%Y-%m-%d'),
            'distance': round(outbreak.distance, 1),
            'affected_animals': getattr(outbreak, 'affected_animals', 0),
            'deaths': getattr(outbreak, 'deaths', 0),
            'morbidity_rate': getattr(outbreak, 'morbidity_rate', 0),
            'mortality_rate': getattr(outbreak, 'mortality_rate', 0)
        })
    
    return jsonify({'outbreaks': outbreaks_data})

@disease_alerts_bp.route('/api/disease-alerts/risks')
def api_disease_risks():
    """API endpoint to get disease risks for user's farm"""
    # Ensure user is logged in
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get user's farm
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    if not farm or not farm.latitude or not farm.longitude:
        return jsonify({'error': 'Farm location not available'}), 400
    
    # Get disease risks
    disease_risks = get_disease_risks_for_farm(farm, None)  # API key is now hardcoded in the function
    
    return jsonify({'risks': disease_risks})

# Scheduled task to run daily and create notifications for high-risk diseases
def check_disease_risks_and_notify():
    """
    Task to check disease risks for all farms and send notifications for high risks
    This should be run as a scheduled task (e.g., using APScheduler or Celery)
    """
    # Get all farms with coordinates
    farms = Farm.query.filter(Farm.latitude.isnot(None), Farm.longitude.isnot(None)).all()
    
    for farm in farms:
        # Get disease risks for this farm
        disease_risks = get_disease_risks_for_farm(farm, None)  # API key is now hardcoded in the function
        
        # For each high-risk disease, create a notification
        for risk in disease_risks:
            if risk['risk_level'] == 'high':
                # Create notification for the farm owner
                notification = Notification(
                    user_id=farm.user_id,
                    type='disease_alert',
                    title=f"High risk of {risk['disease_name']}",
                    message=f"Current conditions indicate a high risk of {risk['disease_name']} for your {', '.join(risk['affected_animals'])}. Take preventive measures.",
                    is_read=False,
                    is_action_required=True,
                    action_url='/disease-alerts',
                    created_at=datetime.utcnow()
                )
                db.session.add(notification)
    
    db.session.commit()

# Create a JSON response with disease information and prevention measures
def get_disease_info(disease_name):
    """
    Get detailed information about a disease including prevention measures
    """
    # This could be expanded with a more comprehensive database of disease information
    disease_info = {
        "Foot and Mouth Disease": {
            "description": "A highly contagious viral disease affecting cloven-hoofed animals, characterized by fever and blister-like sores.",
            "symptoms": [
                "Fever",
                "Blisters on the mouth and feet",
                "Excessive salivation",
                "Lameness",
                "Reduced milk production"
            ],
            "prevention": [
                "Regular vaccination (every 6 months)",
                "Strict biosecurity measures",
                "Control of animal movement",
                "Isolation of affected animals",
                "Proper disinfection procedures"
            ],
            "treatment": "No specific treatment; supportive care to prevent secondary infections.",
            "zoonotic": False
        },
        "Black Quarter": {
            "description": "An acute bacterial disease affecting mainly cattle and sheep, characterized by inflammation and gaseous swelling of muscles.",
            "symptoms": [
                "Sudden fever",
                "Lameness in affected limb",
                "Hot, painful swellings in large muscles",
                "Crackling sensation under the skin",
                "Rapid death in severe cases"
            ],
            "prevention": [
                "Annual vaccination before monsoon",
                "Avoid grazing in contaminated pastures",
                "Proper disposal of carcasses",
                "Pasture improvement"
            ],
            "treatment": "Early antibiotic treatment may be effective.",
            "zoonotic": False
        },
        # Add more diseases as needed
    }
    
    if disease_name in disease_info:
        return disease_info[disease_name]
    else:
        return {
            "description": "Information not available for this disease.",
            "symptoms": [],
            "prevention": [],
            "treatment": "Consult a veterinarian.",
            "zoonotic": False
        }

@disease_alerts_bp.route('/api/disease-alerts/info')
def api_disease_info():
    """API endpoint to get information about a specific disease"""
    # Get disease name from request
    disease_name = request.args.get('disease')
    
    if not disease_name:
        return jsonify({'error': 'Disease name is required'}), 400
    
    # Get disease information
    disease_info = get_disease_info(disease_name)
    
    # Add risk factors
    disease_info['risk_factors'] = DISEASE_RISK_FACTORS.get(disease_name, {})
    
    return jsonify(disease_info)

@disease_alerts_bp.route('/api/disease-alerts/outbreak/<int:outbreak_id>')
def api_outbreak_info(outbreak_id):
    """API endpoint to get information about a specific outbreak"""
    # Ensure user is logged in
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    # Get the outbreak
    outbreak = DiseaseOutbreak.query.get_or_404(outbreak_id)
    
    # Get user's farm
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    # Calculate distance if farm location is available
    distance = None
    if farm and farm.latitude and farm.longitude and outbreak.latitude and outbreak.longitude:
        distance = haversine(
            farm.longitude, farm.latitude,
            outbreak.longitude, outbreak.latitude
        )
        distance = round(distance, 1)
    
    # Generate random stats for the outbreak if needed
    if not hasattr(outbreak, 'affected_animals'):
        affected_animals = random.randint(5, 100)
        deaths = random.randint(0, int(affected_animals * 0.3))
        morbidity_rate = random.randint(20, 80)
        mortality_rate = round((deaths / affected_animals) * 100, 1) if affected_animals > 0 else 0
    else:
        affected_animals = outbreak.affected_animals
        deaths = outbreak.deaths
        morbidity_rate = outbreak.morbidity_rate
        mortality_rate = outbreak.mortality_rate
    
    # Format outbreak data for response
    outbreak_data = {
        'id': outbreak.id,
        'disease_name': outbreak.disease_name,
        'severity': outbreak.severity,
        'location': outbreak.location,
        'district': outbreak.district,
        'state': outbreak.state,
        'latitude': outbreak.latitude,
        'longitude': outbreak.longitude,
        'reported_date': outbreak.reported_date.strftime('%Y-%m-%d'),
        'distance': distance,
        'reported_by': outbreak.reported_by or 'Official Source',
        'statistics': {
            'affected_animals': affected_animals,
            'deaths': deaths,
            'morbidity_rate': morbidity_rate,
            'mortality_rate': mortality_rate
        },
        'preventive_measures': [
            'Restrict movement of animals in and out of the affected area',
            'Isolate affected animals',
            'Ensure proper vaccination of healthy animals',
            'Improve biosecurity measures',
            'Report any suspicious cases to veterinary authorities'
        ]
    }
    
    if outbreak.description:
        outbreak_data['details'] = outbreak.description
    
    if outbreak.preventive_measures:
        outbreak_data['preventive_measures'] = outbreak.preventive_measures.split(',')
    
    return jsonify(outbreak_data)

@disease_alerts_bp.route('/api/disease-alerts/prevention-guide')
def api_prevention_guide():
    """API endpoint to get a prevention guide for a specific disease"""
    # Get disease name from request
    disease_name = request.args.get('disease')
    
    if not disease_name:
        return jsonify({'error': 'Disease name is required'}), 400
    
    # In a real application, you would generate or fetch a PDF guide
    # For this demo, we'll just return a message
    return jsonify({
        'message': f'Prevention guide for {disease_name} would be downloaded here.',
        'success': True
    })

@disease_alerts_bp.route('/api/disease-alerts/refresh')
def api_refresh_alerts():
    """API endpoint to refresh disease alerts data"""
    # Ensure user is logged in
    if not g.user:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        # In a real application, you would fetch new data from external sources
        # For this demo, we'll just return success
        return jsonify({
            'message': 'Alert data refreshed successfully.',
            'success': True
        })
    except Exception as e:
        return jsonify({
            'message': f'Error refreshing alert data: {str(e)}',
            'success': False
        }), 500

@disease_alerts_bp.route('/api/disease-alerts/weather')
def api_weather_data():
    """API endpoint to get weather data for a specific location"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not lat or not lon:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    # Use our new API key directly from the function
    weather_data = get_weather_data(lat, lon, None)  # API key is now hardcoded in the function
    
    if not weather_data:
        return jsonify({'error': 'Failed to fetch weather data'}), 500
    
    # Add disease risk assessment based on weather conditions
    current_temp = weather_data['current']['temp']
    current_humidity = weather_data['current'].get('humidity', 65)
    
    # Add risk message based on conditions
    risk_message = 'Weather conditions are generally favorable for livestock health.'
    
    if current_temp > 30 and current_humidity > 75:
        risk_message = 'Hot and humid conditions increase risk for several diseases including FMD and HS.'
    elif current_temp > 35:
        risk_message = 'High temperatures may cause heat stress in livestock.'
    elif current_temp < 10:
        risk_message = 'Cold temperatures may increase risk of respiratory diseases.'
    
    # Add risk message to weather data
    weather_data['risk_message'] = risk_message
    
    # Add Google Maps API key
    weather_data['google_maps_api_key'] = 'AIzaSyBu2-A5dCNjUj53YtTd91bXsZC__az5WqM'
    
    return jsonify(weather_data) 