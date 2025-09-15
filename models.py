from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()

# User model
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=True)
    phone_number = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(20), default='farmer')
    is_active = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    preferred_language_id = db.Column(db.Integer, db.ForeignKey('languages.id'), nullable=True)
    
    # Relationships
    farm = db.relationship('Farm', backref='owner', uselist=False)
    notifications = db.relationship('Notification', backref='user', lazy='dynamic')
    otp_verifications = db.relationship('OTPVerification', backref='user', lazy='dynamic')
    animals = db.relationship('Animal', backref='owner', lazy='dynamic')
    health_records = db.relationship('HealthRecord', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

# Farm model
class Farm(db.Model):
    __tablename__ = 'farms'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    pincode = db.Column(db.String(10), nullable=True)
    country = db.Column(db.String(100), default='India')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    size_acres = db.Column(db.Float, nullable=True)
    animal_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    animals = db.relationship('Animal', backref='farm', lazy='dynamic')
    
    def __repr__(self):
        return f'<Farm {self.name}>'

# Animal Type model
class AnimalType(db.Model):
    __tablename__ = 'animal_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Relationships
    animals = db.relationship('Animal', backref='animal_type', lazy='dynamic')
    
    def __repr__(self):
        return f'<AnimalType {self.name}>'

# Animal model
class Animal(db.Model):
    __tablename__ = 'animals'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    animal_type_id = db.Column(db.Integer, db.ForeignKey('animal_types.id'), nullable=False)
    breed = db.Column(db.String(100), nullable=True)
    age_months = db.Column(db.Integer, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    farm_id = db.Column(db.Integer, db.ForeignKey('farms.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    health_records = db.relationship('HealthRecord', backref='animal', lazy='dynamic')
    
    def __repr__(self):
        return f'<Animal {self.name} - {self.breed}>'

# Health Record model
class HealthRecord(db.Model):
    __tablename__ = 'health_records'
    id = db.Column(db.Integer, primary_key=True)
    animal_id = db.Column(db.Integer, db.ForeignKey('animals.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    record_type = db.Column(db.String(20), nullable=False)  # checkup, treatment, vaccination, etc.
    diagnosis = db.Column(db.String(200), nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    medication = db.Column(db.Text, nullable=True)
    vet_name = db.Column(db.String(100), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    weight_kg = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    follow_up_date = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<HealthRecord {self.record_type} - {self.diagnosis}>'

# Disease Outbreak model
class DiseaseOutbreak(db.Model):
    __tablename__ = 'disease_outbreaks'
    id = db.Column(db.Integer, primary_key=True)
    disease_name = db.Column(db.String(100), nullable=False)
    animal_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high
    location = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), default='India')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    reported_by = db.Column(db.String(100), nullable=False)
    reported_date = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_date = db.Column(db.DateTime, nullable=True)
    description = db.Column(db.Text, nullable=True)
    preventive_measures = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DiseaseOutbreak {self.disease_name} in {self.location}>'

# Veterinary Service model
class VeterinaryService(db.Model):
    __tablename__ = 'veterinary_services'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    district = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), default='India')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    website = db.Column(db.String(200), nullable=True)
    service_hours = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<VeterinaryService {self.name}>'

# OTP Verification model
class OTPVerification(db.Model):
    __tablename__ = 'otp_verifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    mobile_number = db.Column(db.String(20), nullable=False)
    otp = db.Column(db.String(6), nullable=False)
    purpose = db.Column(db.String(20), default='registration')  # registration, reset_password
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self):
        return f'<OTPVerification {self.otp}>'

# Language model
class Language(db.Model):
    __tablename__ = 'languages'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(5), unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    native_name = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship
    users = db.relationship('User', backref='preferred_language', lazy='dynamic')
    
    def __repr__(self):
        return f'<Language {self.code}>'

# Notification model
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # disease_alert, reminder, system
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    is_action_required = db.Column(db.Boolean, default=False)
    action_url = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'

# Analysis Result model (for storing breed and disease analysis results)
class AnalysisResult(db.Model):
    __tablename__ = 'analysis_results'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    animal_type = db.Column(db.String(50), nullable=False)  # cow, goat, chicken
    analysis_type = db.Column(db.String(20), nullable=False)  # breed, disease
    result = db.Column(db.String(100), nullable=False)  # detected breed or disease
    confidence = db.Column(db.Float, nullable=False)
    image_path = db.Column(db.String(255), nullable=True)
    recommendations = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref='analysis_results')
    
    def __repr__(self):
        return f'<AnalysisResult {self.analysis_type} - {self.result}>' 