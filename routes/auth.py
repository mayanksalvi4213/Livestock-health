from flask import Blueprint, render_template, redirect, url_for, request, flash, session, g, jsonify, make_response
from models import db, User, OTPVerification, Farm, Language
import random
import string
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from utils import geocode_address
from routes.language import AVAILABLE_LANGUAGES

auth_bp = Blueprint('auth', __name__)

# Helper function to generate OTP
def generate_otp(length=6):
    """Generate a random numeric OTP of specified length"""
    return ''.join(random.choices(string.digits, k=length))

# Helper function to send OTP (mock implementation)
def send_otp_sms(mobile_number, otp):
    """Send OTP via SMS - in a real app, this would use a SMS gateway provider"""
    # In a real app, you would integrate with an SMS gateway like Twilio, MSG91, etc.
    print(f"SMS sent to {mobile_number} with OTP: {otp}")
    return True

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to dashboard
    if g.user:
        return redirect(url_for('dashboard.index'))
    
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        password = request.form.get('password')
        
        # Validate input
        user = User.query.filter_by(mobile_number=mobile_number).first()
        
        if user and user.check_password(password):
            # Set user ID in session to log them in
            session.clear()
            session['user_id'] = user.id
            
            # Set language preference from user's profile
            if user.preferred_language:
                language_code = user.preferred_language.code
                response = make_response(redirect(url_for('dashboard.index')))
                response.set_cookie('language', language_code, max_age=31536000)
                return response
                
            return redirect(url_for('dashboard.index'))
        else:
            flash('Invalid mobile number or password', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to dashboard
    if g.user:
        return redirect(url_for('dashboard.index'))
    
    # For GET request, simply display registration form
    if request.method == 'GET':
        return render_template('register.html')
    
    # Handle POST request (form submission)
    mobile_number = request.form.get('mobile_number')
    
    # Check if mobile number is already registered
    existing_user = User.query.filter_by(mobile_number=mobile_number).first()
    if existing_user:
        flash('This mobile number is already registered. Please login instead.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Generate OTP and store it
    otp = generate_otp()
    expiry_time = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
    
    # Save OTP in database
    otp_verification = OTPVerification(
        mobile_number=mobile_number,
        otp=otp,
        expires_at=expiry_time,
        purpose='registration'
    )
    db.session.add(otp_verification)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error creating verification: {str(e)}', 'danger')
        return render_template('register.html')
    
    # Send OTP via SMS (mock implementation for now)
    send_otp_sms(mobile_number, otp)
    
    # Store mobile number in session for the verification step
    session['registration_mobile'] = mobile_number
    
    # Redirect to OTP verification page
    return redirect(url_for('auth.verify_otp'))

@auth_bp.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    # Check if we have a mobile number in session
    mobile_number = session.get('registration_mobile')
    if not mobile_number:
        flash('Please start the registration process again', 'danger')
        return redirect(url_for('auth.register'))
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        
        # Validate OTP
        otp_record = OTPVerification.query.filter_by(
            mobile_number=mobile_number,
            purpose='registration'
        ).order_by(OTPVerification.created_at.desc()).first()
        
        if not otp_record:
            flash('OTP verification failed. Please try again.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if OTP has expired
        if datetime.utcnow() > otp_record.expires_at:
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('auth.register'))
        
        # Check if OTP matches
        if otp_record.otp != entered_otp:
            flash('Invalid OTP. Please try again.', 'danger')
            return render_template('verify_otp.html', mobile_number=mobile_number)
        
        # OTP is valid, mark it as verified (we'll delete it actually)
        db.session.delete(otp_record)
        db.session.commit()
        
        # Store verification status in session
        session['otp_verified'] = True
        
        # Redirect to complete registration
        return redirect(url_for('auth.complete_registration'))
    
    # GET request - show OTP verification form
    return render_template('verify_otp.html', mobile_number=mobile_number)

@auth_bp.route('/complete-registration', methods=['GET', 'POST'])
def complete_registration():
    # Check if mobile verification was done
    mobile_number = session.get('registration_mobile')
    otp_verified = session.get('otp_verified')
    
    if not mobile_number or not otp_verified:
        flash('Please complete the OTP verification first', 'danger')
        return redirect(url_for('auth.register'))
    
    if request.method == 'GET':
        # Pass available languages to the template
        return render_template('complete_registration.html', languages=AVAILABLE_LANGUAGES)
    
    if request.method == 'POST':
        # Get form data
        full_name = request.form.get('name')
        password = request.form.get('password')
        language_code = request.form.get('language', 'en')
        farm_address = request.form.get('farm_address')
        district = request.form.get('district')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        
        # Validate inputs
        if not full_name or not password or not farm_address or not district or not state or not pincode:
            flash('Please fill in all required fields', 'danger')
            return render_template('complete_registration.html', languages=AVAILABLE_LANGUAGES)
        
        # Check if mobile number already exists
        existing_user = User.query.filter_by(mobile_number=mobile_number).first()
        if existing_user:
            flash('This mobile number is already registered. Please login instead.', 'warning')
            # Clear registration session data
            session.pop('registration_mobile', None)
            session.pop('otp_verified', None)
            return redirect(url_for('auth.login'))
        
        # Get or create language entry
        language = Language.query.filter_by(code=language_code).first()
        if not language and language_code in AVAILABLE_LANGUAGES:
            language_name = AVAILABLE_LANGUAGES[language_code].split(' ')[0]
            language = Language(
                code=language_code,
                name=language_name,
                native_name=AVAILABLE_LANGUAGES[language_code]
            )
            db.session.add(language)
            db.session.commit()
        
        # Create new user - generate a username from the mobile number
        username = 'user_' + mobile_number.replace('+', '').replace(' ', '')
        email = f"{username}@example.com"  # temporary email
        
        try:
            new_user = User(
                username=username,
                email=email,
                mobile_number=mobile_number,
                full_name=full_name,
                role='farmer',
                is_active=True,
                preferred_language_id=language.id if language else None
            )
            new_user.set_password(password)
            
            # Save the user
            db.session.add(new_user)
            db.session.commit()
            
            # Get the user ID to create associated records
            user_id = new_user.id
            
            # Geocode the farm address
            farm_location = f"{farm_address}, {district}, {state}"
            lat, lng = geocode_address(farm_address, district, state)
            
            # Create farm record
            new_farm = Farm(
                user_id=new_user.id,
                name=f"{full_name}'s Farm",
                address=farm_address,
                district=district,
                state=state,
                pincode=pincode,
                country="India",
                latitude=lat,
                longitude=lng
            )
            db.session.add(new_farm)
            db.session.commit()
            
            # Clear registration session data
            session.pop('registration_mobile', None)
            session.pop('otp_verified', None)
            
            # Log the user in
            session['user_id'] = user_id
            
            flash('Registration successful! Welcome to AgriHealth.', 'success')
            return redirect(url_for('dashboard.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return render_template('complete_registration.html')

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    mobile_number = session.get('registration_mobile')
    if not mobile_number:
        return jsonify({'success': False, 'message': 'Mobile number not found in session'})
    
    # Generate new OTP
    otp = generate_otp()
    expiry_time = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
    
    # Save OTP in database
    otp_verification = OTPVerification(
        mobile_number=mobile_number,
        otp=otp,
        expires_at=expiry_time
    )
    db.session.add(otp_verification)
    db.session.commit()
    
    # Send OTP via SMS (mock implementation for now)
    send_otp_sms(mobile_number, otp)
    
    return jsonify({'success': True, 'message': 'OTP has been resent'})

@auth_bp.route('/logout')
def logout():
    # Clear all session data
    session.clear()
    
    # Create response with redirect to home
    response = make_response(redirect(url_for('home')))
    
    # Reset language cookie to English
    response.set_cookie('language', 'en', max_age=31536000)
    
    return response

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        mobile_number = request.form.get('mobile_number')
        
        # Validate mobile number
        if not mobile_number or len(mobile_number) != 10 or not mobile_number.isdigit():
            flash('Please enter a valid 10-digit mobile number', 'danger')
            return render_template('forgot_password.html')
        
        # Check if user exists
        user = User.query.filter_by(mobile_number=mobile_number).first()
        if not user:
            flash('No account found with this mobile number', 'danger')
            return render_template('forgot_password.html')
        
        # Generate and send OTP
        otp = generate_otp()
        expiry_time = datetime.utcnow() + timedelta(minutes=10)
        
        # Store OTP in database
        otp_verification = OTPVerification(
            mobile_number=mobile_number,
            otp=otp,
            purpose='reset_password',
            expires_at=expiry_time
        )
        
        # Delete any existing OTP for reset_password purpose
        OTPVerification.query.filter_by(
            mobile_number=mobile_number,
            purpose='reset_password'
        ).delete()
        
        db.session.add(otp_verification)
        db.session.commit()
        
        # Send OTP via SMS
        send_otp_sms(mobile_number, otp)
        
        # Store mobile number in session for the next step
        session['reset_mobile'] = mobile_number
        
        flash('An OTP has been sent to your mobile number', 'success')
        return redirect(url_for('auth.verify_forgot_password_otp'))
    
    return render_template('forgot_password.html')

@auth_bp.route('/verify-forgot-password-otp', methods=['GET', 'POST'])
def verify_forgot_password_otp():
    # Check if mobile number is in session
    if 'reset_mobile' not in session:
        flash('Please start the password reset process again', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    mobile_number = session['reset_mobile']
    
    if request.method == 'POST':
        entered_otp = request.form.get('otp')
        
        # Validate OTP
        if not entered_otp or len(entered_otp) != 6 or not entered_otp.isdigit():
            flash('Please enter a valid 6-digit OTP', 'danger')
            return render_template('verify_otp.html', 
                                  purpose='reset_password',
                                  mobile_number=mobile_number)
        
        # Check if OTP exists and is valid
        otp_verification = OTPVerification.query.filter_by(
            mobile_number=mobile_number,
            otp=entered_otp,
            purpose='reset_password'
        ).first()
        
        if not otp_verification:
            flash('Invalid OTP. Please try again', 'danger')
            return render_template('verify_otp.html', 
                                  purpose='reset_password',
                                  mobile_number=mobile_number)
        
        # Check if OTP is expired
        if datetime.utcnow() > otp_verification.expires_at:
            flash('OTP has expired. Please request a new one', 'danger')
            return render_template('verify_otp.html', 
                                  purpose='reset_password',
                                  mobile_number=mobile_number)
        
        # Delete the OTP record (equivalent to marking as used)
        db.session.delete(otp_verification)
        db.session.commit()
        
        # Store verification in session
        session['otp_verified_for_reset'] = True
        
        # Redirect to reset password page
        return redirect(url_for('auth.reset_password'))
    
    # For GET request, show the OTP verification form
    return render_template('verify_otp.html', 
                          purpose='reset_password',
                          mobile_number=mobile_number)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Check if user has verified OTP
    if 'otp_verified_for_reset' not in session or not session['otp_verified_for_reset']:
        flash('Please verify your identity first', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    # Check if mobile number is in session
    if 'reset_mobile' not in session:
        flash('Please start the password reset process again', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    mobile_number = session['reset_mobile']
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate passwords
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('reset_password.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html')
        
        # Find user and update password
        user = User.query.filter_by(mobile_number=mobile_number).first()
        if not user:
            flash('User not found', 'danger')
            return redirect(url_for('auth.login'))
        
        # Update password using user's set_password method
        user.set_password(password)
        db.session.commit()
        
        # Clear session data for password reset
        session.pop('reset_mobile', None)
        session.pop('otp_verified_for_reset', None)
        
        flash('Your password has been reset successfully. Please login with your new password', 'success')
        return redirect(url_for('auth.login'))
    
    # For GET request, show the reset password form
    return render_template('reset_password.html')

@auth_bp.route('/resend-forgot-password-otp', methods=['POST'])
def resend_forgot_password_otp():
    mobile_number = session.get('reset_mobile')
    if not mobile_number:
        return jsonify({'success': False, 'message': 'Mobile number not found in session'})
    
    # Generate new OTP
    otp = generate_otp()
    expiry_time = datetime.utcnow() + timedelta(minutes=10)  # OTP valid for 10 minutes
    
    # Delete any existing OTP for reset_password purpose
    OTPVerification.query.filter_by(
        mobile_number=mobile_number,
        purpose='reset_password'
    ).delete()
    
    # Save OTP in database
    otp_verification = OTPVerification(
        mobile_number=mobile_number,
        otp=otp,
        purpose='reset_password',
        expires_at=expiry_time
    )
    db.session.add(otp_verification)
    db.session.commit()
    
    # Send OTP via SMS (mock implementation for now)
    send_otp_sms(mobile_number, otp)
    
    return jsonify({'success': True, 'message': 'OTP has been resent'})