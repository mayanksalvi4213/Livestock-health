import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db
from models import (
    User, Farm, AnimalType, Animal, HealthRecord, DiseaseOutbreak,
    VeterinaryService, Language, Notification
)

def seed_languages():
    """Seed languages table with supported languages"""
    languages = [
        {'code': 'en', 'name': 'English', 'native_name': 'English'},
        {'code': 'hi', 'name': 'Hindi', 'native_name': 'हिन्दी'},
        {'code': 'mr', 'name': 'Marathi', 'native_name': 'मराठी'},
        {'code': 'gu', 'name': 'Gujarati', 'native_name': 'ગુજરાતી'},
        {'code': 'pa', 'name': 'Punjabi', 'native_name': 'ਪੰਜਾਬੀ'},
        {'code': 'ta', 'name': 'Tamil', 'native_name': 'தமிழ்'},
        {'code': 'te', 'name': 'Telugu', 'native_name': 'తెలుగు'},
        {'code': 'bn', 'name': 'Bengali', 'native_name': 'বাংলা'},
        {'code': 'kn', 'name': 'Kannada', 'native_name': 'ಕನ್ನಡ'},
        {'code': 'ml', 'name': 'Malayalam', 'native_name': 'മലയാളം'}
    ]
    
    for lang_data in languages:
        if not Language.query.filter_by(code=lang_data['code']).first():
            language = Language(
                code=lang_data['code'],
                name=lang_data['name'],
                native_name=lang_data['native_name'],
                is_active=True
            )
            db.session.add(language)
    
    db.session.commit()
    print(f"Added {len(languages)} languages")

def seed_animal_types():
    """Seed animal types table"""
    animal_types = [
        {'name': 'Cow', 'description': 'Cattle/bovines including cows and bulls'},
        {'name': 'Goat', 'description': 'Domestic goats'},
        {'name': 'Chicken', 'description': 'Domestic fowl including roosters and hens'},
        {'name': 'Sheep', 'description': 'Domestic sheep'},
        {'name': 'Buffalo', 'description': 'Water buffalo'},
        {'name': 'Pig', 'description': 'Domestic swine'}
    ]
    
    for type_data in animal_types:
        if not AnimalType.query.filter_by(name=type_data['name']).first():
            animal_type = AnimalType(
                name=type_data['name'],
                description=type_data['description']
            )
            db.session.add(animal_type)
    
    db.session.commit()
    print(f"Added {len(animal_types)} animal types")

def seed_test_user():
    """Create test user account"""
    test_user = User.query.filter_by(username='testfarmer').first()
    
    if not test_user:
        # Get English language
        english = Language.query.filter_by(code='en').first()
        
        # Create the user
        test_user = User(
            username='testfarmer',
            email='test@example.com',
            mobile_number='+911234567890',
            password_hash=generate_password_hash('password123'),
            full_name='Test Farmer',
            phone_number='+911234567890',
            role='farmer',
            is_active=True,
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow(),
            preferred_language_id=english.id if english else None
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Create a farm for the user
        farm = Farm(
            user_id=test_user.id,
            name='Test Farm',
            address='123 Farm Road, Village',
            district='Test District',
            state='Test State',
            country='India',
            latitude=random.uniform(8.0, 37.0),
            longitude=random.uniform(68.0, 97.0),
            size_acres=10.5,
            animal_count=25,
            created_at=datetime.utcnow()
        )
        db.session.add(farm)
        db.session.commit()
        
        print(f"Created test user: {test_user.username} with farm: {farm.name}")
    else:
        print(f"Test user {test_user.username} already exists")

def seed_animals():
    """Add sample animals to the test farm"""
    # Get test user and farm
    test_user = User.query.filter_by(username='testfarmer').first()
    if not test_user:
        print("Test user not found. Run seed_test_user() first.")
        return
    
    farm = Farm.query.filter_by(user_id=test_user.id).first()
    if not farm:
        print("Farm not found for test user.")
        return
    
    # Get animal types
    cow_type = AnimalType.query.filter_by(name='Cow').first()
    goat_type = AnimalType.query.filter_by(name='Goat').first()
    chicken_type = AnimalType.query.filter_by(name='Chicken').first()
    
    if not cow_type or not goat_type or not chicken_type:
        print("Animal types not found. Run seed_animal_types() first.")
        return
    
    # Create sample animals if they don't exist
    if not Animal.query.filter_by(user_id=test_user.id).first():
        animals = [
            {'name': 'Lakshmi', 'type_id': cow_type.id, 'breed': 'Gir', 'age_months': 36, 'weight_kg': 450, 'gender': 'female'},
            {'name': 'Shanti', 'type_id': cow_type.id, 'breed': 'Jersey', 'age_months': 48, 'weight_kg': 480, 'gender': 'female'},
            {'name': 'Gopal', 'type_id': cow_type.id, 'breed': 'Sahiwal', 'age_months': 30, 'weight_kg': 550, 'gender': 'male'},
            {'name': 'Meera', 'type_id': goat_type.id, 'breed': 'Beetal', 'age_months': 18, 'weight_kg': 45, 'gender': 'female'},
            {'name': 'Raja', 'type_id': goat_type.id, 'breed': 'Jamunapari', 'age_months': 24, 'weight_kg': 55, 'gender': 'male'},
            {'name': 'Kali', 'type_id': chicken_type.id, 'breed': 'Kadaknath', 'age_months': 8, 'weight_kg': 2.5, 'gender': 'female'},
            {'name': 'Lal', 'type_id': chicken_type.id, 'breed': 'Asil', 'age_months': 10, 'weight_kg': 3.0, 'gender': 'male'}
        ]
        
        for animal_data in animals:
            animal = Animal(
                name=animal_data['name'],
                animal_type_id=animal_data['type_id'],
                breed=animal_data['breed'],
                age_months=animal_data['age_months'],
                weight_kg=animal_data['weight_kg'],
                gender=animal_data['gender'],
                user_id=test_user.id,
                farm_id=farm.id,
                is_active=True,
                created_at=datetime.utcnow(),
                notes=f"Sample {animal_data['breed']} {animal_data['name']}"
            )
            db.session.add(animal)
        
        db.session.commit()
        print(f"Added {len(animals)} sample animals to test farm")
    else:
        print("Animals already exist for test user")

def seed_health_records():
    """Add sample health records for animals"""
    # Get test user
    test_user = User.query.filter_by(username='testfarmer').first()
    if not test_user:
        print("Test user not found. Run seed_test_user() first.")
        return
    
    # Get animals
    animals = Animal.query.filter_by(user_id=test_user.id).all()
    if not animals:
        print("No animals found. Run seed_animals() first.")
        return
    
    # Check if records already exist
    if not HealthRecord.query.filter_by(user_id=test_user.id).first():
        records = []
        
        # Create some random health records
        record_types = ['checkup', 'treatment', 'vaccination']
        diagnoses = ['Healthy', 'Mild infection', 'Parasites', 'Fever', 'Injury']
        treatments = ['None', 'Antibiotics', 'Anti-parasitic', 'Wound cleaning', 'Surgery']
        vets = ['Dr. Sharma', 'Dr. Patel', 'Dr. Singh', 'Dr. Kumar']
        
        for animal in animals:
            # Create 1-3 records per animal
            for _ in range(random.randint(1, 3)):
                record_type = random.choice(record_types)
                diagnosis = random.choice(diagnoses)
                
                # Create record
                record = HealthRecord(
                    animal_id=animal.id,
                    user_id=test_user.id,
                    record_type=record_type,
                    diagnosis=diagnosis,
                    treatment=random.choice(treatments) if diagnosis != 'Healthy' else 'None',
                    medication=f"Sample medication for {diagnosis}" if diagnosis != 'Healthy' else 'None',
                    vet_name=random.choice(vets),
                    temperature=random.uniform(37.5, 39.5) if diagnosis != 'Healthy' else random.uniform(38.0, 38.8),
                    weight_kg=animal.weight_kg + random.uniform(-5, 5),
                    notes=f"Sample health record for {animal.name}",
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 60)),
                    follow_up_date=datetime.utcnow() + timedelta(days=random.randint(7, 30)) if diagnosis != 'Healthy' else None
                )
                records.append(record)
                db.session.add(record)
        
        db.session.commit()
        print(f"Added {len(records)} health records for {len(animals)} animals")
    else:
        print("Health records already exist for test user")

def seed_disease_outbreaks():
    """Add sample disease outbreak data"""
    # Check if outbreaks already exist
    if not DiseaseOutbreak.query.first():
        outbreaks = [
            {
                'disease_name': 'Foot and Mouth Disease',
                'animal_type': 'cow',
                'severity': 'high',
                'location': 'Anand, Gujarat',
                'district': 'Anand',
                'state': 'Gujarat',
                'country': 'India',
                'latitude': 22.5645,
                'longitude': 72.9289,
                'reported_by': 'District Veterinary Officer',
                'days_ago': random.randint(1, 10),
                'is_resolved': False,
                'description': 'Multiple cases of FMD detected in dairy farms.',
                'preventive_measures': """
                    1. Isolate affected animals
                    2. Implement biosecurity measures
                    3. Vaccinate healthy animals
                    4. Restrict movement of animals
                """
            },
            {
                'disease_name': 'Newcastle Disease',
                'animal_type': 'chicken',
                'severity': 'medium',
                'location': 'Nashik, Maharashtra',
                'district': 'Nashik',
                'state': 'Maharashtra',
                'country': 'India',
                'latitude': 19.9975,
                'longitude': 73.7898,
                'reported_by': 'Poultry Farm Association',
                'days_ago': random.randint(1, 15),
                'is_resolved': False,
                'description': 'Several cases reported in backyard poultry.',
                'preventive_measures': """
                    1. Vaccinate healthy birds
                    2. Improve sanitation
                    3. Control wild bird access
                    4. Proper disposal of dead birds
                """
            },
            {
                'disease_name': 'Brucellosis',
                'animal_type': 'goat',
                'severity': 'medium',
                'location': 'Jaipur, Rajasthan',
                'district': 'Jaipur',
                'state': 'Rajasthan',
                'country': 'India',
                'latitude': 26.9124,
                'longitude': 75.7873,
                'reported_by': 'State Veterinary Department',
                'days_ago': random.randint(1, 20),
                'is_resolved': False,
                'description': 'Cases detected in multiple goat farms.',
                'preventive_measures': """
                    1. Test and cull positive animals
                    2. Vaccinate young animals
                    3. Proper disposal of aborted fetuses
                    4. Maintain good hygiene during milking
                """
            },
            {
                'disease_name': 'Lumpy Skin Disease',
                'animal_type': 'cow',
                'severity': 'high',
                'location': 'Amritsar, Punjab',
                'district': 'Amritsar',
                'state': 'Punjab',
                'country': 'India',
                'latitude': 31.6340,
                'longitude': 74.8723,
                'reported_by': 'Punjab Livestock Department',
                'days_ago': random.randint(30, 60),
                'is_resolved': True,
                'description': 'Outbreak now contained after vaccination campaign.',
                'preventive_measures': """
                    1. Mass vaccination
                    2. Insect control 
                    3. Movement restrictions
                    4. Isolation of affected animals
                """
            }
        ]
        
        for outbreak_data in outbreaks:
            outbreak = DiseaseOutbreak(
                disease_name=outbreak_data['disease_name'],
                animal_type=outbreak_data['animal_type'],
                severity=outbreak_data['severity'],
                location=outbreak_data['location'],
                district=outbreak_data['district'],
                state=outbreak_data['state'],
                country=outbreak_data['country'],
                latitude=outbreak_data['latitude'],
                longitude=outbreak_data['longitude'],
                reported_by=outbreak_data['reported_by'],
                reported_date=datetime.utcnow() - timedelta(days=outbreak_data['days_ago']),
                resolved_date=datetime.utcnow() - timedelta(days=5) if outbreak_data['is_resolved'] else None,
                description=outbreak_data['description'],
                preventive_measures=outbreak_data['preventive_measures'],
                is_active=not outbreak_data['is_resolved'],
                created_at=datetime.utcnow() - timedelta(days=outbreak_data['days_ago'])
            )
            db.session.add(outbreak)
        
        db.session.commit()
        print(f"Added {len(outbreaks)} disease outbreaks")
    else:
        print("Disease outbreaks already exist")

def seed_veterinary_services():
    """Add sample veterinary services"""
    # Check if vet services already exist
    if not VeterinaryService.query.first():
        services = [
            {
                'name': 'District Veterinary Hospital',
                'address': 'Main Road, City Center',
                'district': 'Test District', 
                'state': 'Test State',
                'country': 'India',
                'phone': '+91 9876543210',
                'email': 'district.vet@example.com',
                'website': 'http://example.com/dist-vet',
                'service_hours': 'Mon-Sat: 9 AM - 5 PM, Emergency: 24/7',
                'description': 'Government veterinary hospital with all facilities for livestock care.',
                'rating': 4.2
            },
            {
                'name': 'Animal Care Clinic',
                'address': 'Near Bus Stand, Green Avenue',
                'district': 'Test District',
                'state': 'Test State',
                'country': 'India',
                'phone': '+91 9876543211',
                'email': 'animalcare@example.com',
                'website': 'http://example.com/animalcare',
                'service_hours': 'Mon-Fri: 10 AM - 7 PM, Sat: 10 AM - 2 PM',
                'description': 'Private clinic specializing in cattle and goat treatments.',
                'rating': 4.5
            },
            {
                'name': 'Livestock Health Center',
                'address': 'Rural Area, Farm Road',
                'district': 'Another District',
                'state': 'Test State',
                'country': 'India',
                'phone': '+91 9876543212',
                'email': 'livestock.health@example.com',
                'website': 'http://example.com/livestock-health',
                'service_hours': 'Mon-Sun: 8 AM - 8 PM',
                'description': 'Mobile veterinary service covering rural areas.',
                'rating': 4.0
            }
        ]
        
        for service_data in services:
            # Get random coordinates near the test farm
            latitude = random.uniform(8.0, 37.0)
            longitude = random.uniform(68.0, 97.0)
            
            service = VeterinaryService(
                name=service_data['name'],
                address=service_data['address'],
                district=service_data['district'],
                state=service_data['state'],
                country=service_data['country'],
                latitude=latitude,
                longitude=longitude,
                phone=service_data['phone'],
                email=service_data['email'],
                website=service_data['website'],
                service_hours=service_data['service_hours'],
                description=service_data['description'],
                rating=service_data['rating'],
                is_verified=True,
                created_at=datetime.utcnow() - timedelta(days=random.randint(30, 365))
            )
            db.session.add(service)
        
        db.session.commit()
        print(f"Added {len(services)} veterinary services")
    else:
        print("Veterinary services already exist")

def seed_notifications():
    """Add sample notifications for test user"""
    # Get test user
    test_user = User.query.filter_by(username='testfarmer').first()
    if not test_user:
        print("Test user not found. Run seed_test_user() first.")
        return
    
    # Check if notifications already exist
    if not Notification.query.filter_by(user_id=test_user.id).first():
        notifications = [
            {
                'type': 'disease_alert',
                'title': 'Disease Alert: Foot and Mouth Disease',
                'message': 'Outbreak of Foot and Mouth Disease reported in your district. Take preventive measures.',
                'is_action_required': True,
                'action_url': '/disease',
                'days_ago': 2
            },
            {
                'type': 'reminder',
                'title': 'Vaccination Reminder',
                'message': 'Your cow Lakshmi is due for vaccination next week.',
                'is_action_required': True,
                'action_url': '/vaccine',
                'days_ago': 1
            },
            {
                'type': 'system',
                'title': 'Welcome to AgriHealth',
                'message': 'Thank you for joining AgriHealth. Complete your profile to get started.',
                'is_action_required': False,
                'action_url': None,
                'days_ago': 7
            }
        ]
        
        for notif_data in notifications:
            notification = Notification(
                user_id=test_user.id,
                type=notif_data['type'],
                title=notif_data['title'],
                message=notif_data['message'],
                is_read=False,
                is_action_required=notif_data['is_action_required'],
                action_url=notif_data['action_url'],
                created_at=datetime.utcnow() - timedelta(days=notif_data['days_ago'])
            )
            db.session.add(notification)
        
        db.session.commit()
        print(f"Added {len(notifications)} notifications for test user")
    else:
        print("Notifications already exist for test user")

if __name__ == '__main__':
    with app.app_context():
        print("Seeding database...")
        
        # Seed in proper order to maintain relationships
        seed_languages()
        seed_animal_types()
        seed_test_user()
        seed_animals()
        seed_health_records()
        seed_disease_outbreaks()
        seed_veterinary_services()
        seed_notifications()
        
        print("Database seeding complete!") 