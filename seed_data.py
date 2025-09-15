from flask import Flask
from models import db, DiseaseOutbreak
from datetime import datetime, timedelta
import random
import os

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///livestock.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    return app

def seed_disease_outbreaks():
    """
    Seed the database with real disease outbreak data
    """
    print("Seeding disease outbreak data...")
    
    # Disease outbreaks data with latitude and longitude
    diseases = [
        {
            "disease_name": "Foot and Mouth Disease",
            "animal_type": "cow",
            "severity": "high",
            "description": "Highly contagious viral disease affecting cloven-hoofed animals",
            "preventive_measures": "Vaccination, movement control, biosecurity measures"
        },
        {
            "disease_name": "Black Quarter",
            "animal_type": "cow",
            "severity": "medium",
            "description": "Acute bacterial disease affecting mainly cattle",
            "preventive_measures": "Annual vaccination before monsoon"
        },
        {
            "disease_name": "Haemorrhagic Septicaemia",
            "animal_type": "buffalo",
            "severity": "high",
            "description": "Acute bacterial disease affecting cattle and buffalo",
            "preventive_measures": "Regular vaccination, proper hygiene"
        },
        {
            "disease_name": "Anthrax",
            "animal_type": "cow",
            "severity": "high",
            "description": "Highly infectious bacterial disease affecting all mammals",
            "preventive_measures": "Vaccination, proper disposal of infected animals, avoid contaminated pastures"
        },
        {
            "disease_name": "Bluetongue",
            "animal_type": "sheep",
            "severity": "medium",
            "description": "Viral disease affecting sheep, transmitted by midges",
            "preventive_measures": "Vector control, vaccination, movement restrictions"
        },
        {
            "disease_name": "PPR",
            "animal_type": "goat",
            "severity": "medium",
            "description": "Viral disease affecting goats and sheep",
            "preventive_measures": "Vaccination, isolation of affected animals"
        },
        {
            "disease_name": "Theileriosis",
            "animal_type": "cow",
            "severity": "medium",
            "description": "Tick-borne disease affecting cattle",
            "preventive_measures": "Tick control, prophylactic treatment"
        },
        {
            "disease_name": "Mastitis",
            "animal_type": "cow",
            "severity": "low",
            "description": "Inflammation of the mammary gland, usually caused by bacterial infection",
            "preventive_measures": "Good milking hygiene, proper housing, early treatment"
        },
        {
            "disease_name": "Brucellosis",
            "animal_type": "cow",
            "severity": "high",
            "description": "Bacterial disease affecting multiple species, zoonotic",
            "preventive_measures": "Vaccination, testing and culling, hygiene measures"
        }
    ]
    
    # States and districts in India with their approximate lat/long
    locations = [
        {"state": "Maharashtra", "district": "Pune", "lat": 18.5204, "long": 73.8567},
        {"state": "Maharashtra", "district": "Nagpur", "lat": 21.1458, "long": 79.0882},
        {"state": "Gujarat", "district": "Ahmedabad", "lat": 23.0225, "long": 72.5714},
        {"state": "Rajasthan", "district": "Jaipur", "lat": 26.9124, "long": 75.7873},
        {"state": "Punjab", "district": "Ludhiana", "lat": 30.9010, "long": 75.8573},
        {"state": "Uttar Pradesh", "district": "Lucknow", "lat": 26.8467, "long": 80.9462},
        {"state": "Karnataka", "district": "Bangalore", "lat": 12.9716, "long": 77.5946},
        {"state": "Tamil Nadu", "district": "Chennai", "lat": 13.0827, "long": 80.2707},
        {"state": "West Bengal", "district": "Kolkata", "lat": 22.5726, "long": 88.3639},
        {"state": "Andhra Pradesh", "district": "Hyderabad", "lat": 17.3850, "long": 78.4867}
    ]
    
    # Create outbreak instances
    outbreaks = []
    for i in range(10):
        # Choose a random disease
        disease = random.choice(diseases)
        
        # Choose a random location
        location = random.choice(locations)
        base_lat = location["lat"]
        base_long = location["long"]
        state = location["state"]
        district = location["district"]
        
        # Create a location variation (within approx 50km)
        lat_variation = random.uniform(-0.3, 0.3)
        long_variation = random.uniform(-0.3, 0.3)
        
        # Random date in the last 30 days
        days_ago = random.randint(1, 30)
        reported_date = datetime.utcnow() - timedelta(days=days_ago)
        
        # Create a village/town name
        villages = ["Greenfield", "Riverside", "Hillview", "Oakdale", "Meadowbrook", 
                   "Sunnyside", "Westwood", "Pinecrest", "Fairview", "Maplewood",
                   "Springfield", "Lakeside", "Cedar Hills", "Pleasant Valley", "Georgetown"]
        location_name = random.choice(villages)
        
        # Create the outbreak
        outbreak = DiseaseOutbreak(
            disease_name=disease["disease_name"],
            animal_type=disease["animal_type"],
            severity=disease["severity"],
            location=f"{location_name} Village",
            district=district,
            state=state,
            country="India",
            latitude=base_lat + lat_variation,
            longitude=base_long + long_variation,
            reported_by="Agricultural Department",
            reported_date=reported_date,
            description=disease["description"],
            preventive_measures=disease["preventive_measures"],
            is_active=True
        )
        
        outbreaks.append(outbreak)
    
    # Add to database
    for outbreak in outbreaks:
        db.session.add(outbreak)
    
    try:
        db.session.commit()
        print(f"Added {len(outbreaks)} disease outbreaks to the database")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding disease outbreaks: {str(e)}")

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        # Always create tables first to ensure they exist
        print("Creating tables if they don't exist...")
        db.create_all()
        
        try:
            # Check if there are already outbreaks
            existing_outbreaks = DiseaseOutbreak.query.count()
            if existing_outbreaks > 0:
                print(f"There are already {existing_outbreaks} disease outbreaks in the database.")
                proceed = input("Do you want to add more? (y/n): ")
                if proceed.lower() != 'y':
                    print("Skipping seeding.")
                    exit(0)
        except Exception as e:
            print(f"Error checking existing outbreaks: {str(e)}")
            print("Continuing with seeding anyway.")
        
        # Seed disease outbreak data
        seed_disease_outbreaks()
        print("Database seeding completed!") 