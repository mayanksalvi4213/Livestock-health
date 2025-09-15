from flask import Blueprint, render_template, redirect, url_for, request, flash, g, abort, make_response
from models import db, User, Farm, Animal, Language, AnimalType
from werkzeug.security import generate_password_hash, check_password_hash
from utils import geocode_address, get_current_language
from routes.language import AVAILABLE_LANGUAGES
import os
from datetime import datetime
import requests

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

@profile_bp.before_request
def check_login():
    if not g.user:
        flash('Please log in to access this page', 'warning')
        return redirect(url_for('auth.login'))

@profile_bp.route('/')
def index():
    """Show user profile"""
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    # Get user's animals
    animals = Animal.query.filter_by(user_id=g.user.id).all()
    
    # Get available languages
    available_languages = AVAILABLE_LANGUAGES
    
    return render_template('profile.html', user=g.user, farm=farm, animals=animals, languages=available_languages)

@profile_bp.route('/edit', methods=['GET', 'POST'])
def edit():
    """Edit user profile"""
    # Get user's farm details
    farm = Farm.query.filter_by(user_id=g.user.id).first()
    
    # Get available languages
    available_languages = AVAILABLE_LANGUAGES
    
    if request.method == 'POST':
        # Update user details
        full_name = request.form.get('name')
        language_code = request.form.get('language')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        # Update basic user info
        if full_name:
            g.user.full_name = full_name
        
        # Update language preference if provided
        if language_code and language_code in AVAILABLE_LANGUAGES.keys():
            language = Language.query.filter_by(code=language_code).first()
            if language:
                g.user.preferred_language_id = language.id
        
        # Update password if provided
        if current_password and new_password:
            if g.user.check_password(current_password):
                g.user.set_password(new_password)
                flash('Password updated successfully', 'success')
            else:
                flash('Current password is incorrect', 'danger')
                return render_template('edit_profile.html', user=g.user, farm=farm, languages=available_languages)
        
        # Update farm details
        farm_name = request.form.get('farm_name')
        farm_address = request.form.get('farm_address')
        district = request.form.get('district')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        
        # Ensure farm data is complete before updating
        if farm_address and district and state:
            # If farm doesn't exist, create a new one
            if not farm:
                farm = Farm(
                    user_id=g.user.id,
                    name=farm_name or "My Farm",
                    address=farm_address,
                    district=district,
                    state=state,
                    pincode=pincode,
                    country="India"
                )
                db.session.add(farm)
                print(f"Created new farm for user {g.user.id}")
            else:
                # Check if any location data has changed
                location_changed = (
                    farm.address != farm_address or
                    farm.district != district or
                    farm.state != state or
                    farm.pincode != pincode
                )
                
                # Update existing farm
                farm.name = farm_name if farm_name else farm.name
                farm.address = farm_address
                farm.district = district
                farm.state = state
                farm.pincode = pincode
                print(f"Updated farm {farm.id} for user {g.user.id}")
                
                # Only geocode if location data has changed
                if not location_changed:
                    print("Farm location data unchanged - skipping geocoding")
                    db.session.commit()
                    flash('Profile updated successfully', 'success')
                    
                    # Create response with redirect
                    response = make_response(redirect(url_for('profile.index')))
                    
                    # If language was changed, update the cookie
                    if language_code and language_code in AVAILABLE_LANGUAGES.keys():
                        response.set_cookie('language', language_code, max_age=31536000)
                    
                    return response
            
            # Update geocode using Google Maps API directly
            try:
                print(f"Geocoding farm location: {farm_address}, {district}, {state}, {pincode}")
                
                # Build the complete address string
                address_parts = []
                if farm_address:
                    address_parts.append(farm_address.strip())
                if district:
                    address_parts.append(district.strip())
                if state:
                    address_parts.append(state.strip())
                if pincode:
                    address_parts.append(pincode.strip())
                address_parts.append("India")
                
                full_address = ", ".join(address_parts)
                print(f"Full address for geocoding: {full_address}")
                
                # Call Google Maps API directly
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
                        
                        # Update farm coordinates
                        farm.latitude = lat
                        farm.longitude = lng
                        print(f"Updated farm coordinates to: {lat}, {lng}")
                        flash('Farm location successfully mapped', 'success')
                    else:
                        # Fallback to geocode_address function
                        print(f"Google Maps API error, falling back to geocode_address")
                        lat, lng = geocode_address(farm_address, district, state, pincode=pincode)
                        
                        if lat is not None and lng is not None:
                            farm.latitude = lat
                            farm.longitude = lng
                            print(f"Updated farm coordinates to: {lat}, {lng} (via fallback)")
                            flash('Farm location mapped (using fallback method)', 'success')
                        else:
                            flash('Could not determine exact coordinates for your farm location', 'warning')
                            print("Geocoding failed - no coordinates returned")
                except Exception as api_error:
                    print(f"Error calling Google Maps API: {str(api_error)}")
                    
                    # Fallback to geocode_address function
                    lat, lng = geocode_address(farm_address, district, state, pincode=pincode)
                    
                    if lat is not None and lng is not None:
                        farm.latitude = lat
                        farm.longitude = lng
                        print(f"Updated farm coordinates to: {lat}, {lng} (via fallback)")
                        flash('Farm location mapped (using fallback method)', 'success')
                    else:
                        flash('Could not determine exact coordinates for your farm location', 'warning')
            except Exception as e:
                print(f"Error geocoding farm location: {str(e)}")
                flash('Error mapping farm location. Basic information saved.', 'warning')
        
        # Save changes to database
        db.session.commit()
        
        flash('Profile updated successfully', 'success')
        
        # Create response with redirect
        response = make_response(redirect(url_for('profile.index')))
        
        # If language was changed, update the cookie
        if language_code and language_code in AVAILABLE_LANGUAGES.keys():
            response.set_cookie('language', language_code, max_age=31536000)
        
        return response
    
    return render_template('edit_profile.html', user=g.user, farm=farm, languages=available_languages)

@profile_bp.route('/change-password', methods=['GET', 'POST'])
def change_password():
    """Change user password"""
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate input
        if not current_password or not new_password or not confirm_password:
            flash('All fields are required', 'danger')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return render_template('change_password.html')
        
        if len(new_password) < 8:
            flash('New password must be at least 8 characters long', 'danger')
            return render_template('change_password.html')
        
        # Check if current password is correct
        if not g.user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return render_template('change_password.html')
        
        # Update password
        g.user.set_password(new_password)
        db.session.commit()
        
        flash('Password changed successfully', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('change_password.html')

@profile_bp.route('/add_animal', methods=['GET', 'POST'])
def add_animal():
    """Add a new animal"""
    # Get animal types for the form
    animal_types = AnimalType.query.all()
    
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        animal_type_id = request.form.get('animal_type_id')
        breed = request.form.get('breed')
        age_months = request.form.get('age_months')
        weight_kg = request.form.get('weight_kg')
        gender = request.form.get('gender')
        
        # Validate data
        if not animal_type_id or not AnimalType.query.get(animal_type_id):
            flash('Invalid animal type', 'danger')
            return render_template('add_animal.html', animal_types=animal_types)
        
        # Create new animal
        animal = Animal(
            name=name,
            animal_type_id=animal_type_id,
            breed=breed,
            age_months=int(age_months) if age_months else None,
            weight_kg=float(weight_kg) if weight_kg else None,
            gender=gender,
            user_id=g.user.id,
            farm_id=Farm.query.filter_by(user_id=g.user.id).first().id,
            is_active=True,
            notes=f"Added on {datetime.utcnow().strftime('%Y-%m-%d')}"
        )
        
        # Save to database
        db.session.add(animal)
        db.session.commit()
        
        flash('Animal added successfully', 'success')
        return redirect(url_for('profile.index'))
    
    return render_template('add_animal.html', animal_types=animal_types) 