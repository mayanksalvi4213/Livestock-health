from flask import Blueprint, render_template, request, redirect, url_for, make_response, g, session, flash, jsonify
from models import db, Language, User
from utils.translator import translate_text, SUPPORTED_LANGUAGES

language_bp = Blueprint('language', __name__)

# Available languages with their display names
AVAILABLE_LANGUAGES = {
    'en': 'English',
    'hi': 'हिंदी (Hindi)',
    'ta': 'தமிழ் (Tamil)',
    'te': 'తెలుగు (Telugu)',
    'mr': 'मराठी (Marathi)',
    'bn': 'বাংলা (Bengali)',
    'pa': 'ਪੰਜਾਬੀ (Punjabi)',
    'gu': 'ગુજરાતી (Gujarati)',
    'kn': 'ಕನ್ನಡ (Kannada)',
    'ml': 'മലയാളം (Malayalam)'
}

@language_bp.route('/language')
def select():
    """Show language selection page"""
    # Get the redirect URL after language selection
    next_url = request.args.get('next', url_for('dashboard.index'))
    
    # If next is the home page and we're coming from language selection,
    # redirect to dashboard to break the loop
    if next_url == url_for('home') and request.referrer and 'language' in request.referrer:
        next_url = url_for('dashboard.index')
        
    # Get current language
    current_language = get_current_language()
    
    return render_template('language_select.html', 
                        languages=AVAILABLE_LANGUAGES,
                        current_language=current_language,
                        next=next_url)

@language_bp.route('/language/set', methods=['POST'])
def set_language():
    """Set language preference in cookie, session and user profile if logged in"""
    language_code = request.form.get('language', 'en')
    next_url = request.form.get('next', url_for('dashboard.index'))
    
    # If next is the home page, redirect to dashboard to break the loop
    if next_url == url_for('home'):
        next_url = url_for('dashboard.index')
    
    print(f"[DEBUG] Language change requested: {language_code}, redirect to: {next_url}")
    
    # Handle empty language code
    if not language_code:
        print(f"[DEBUG] Empty language code received, defaulting to 'en'")
        language_code = 'en'
    
    # Validate language code
    if language_code not in AVAILABLE_LANGUAGES:
        print(f"[DEBUG] Invalid language code: {language_code}, defaulting to 'en'")
        language_code = 'en'  # Default to English if invalid
    
    # Store language in session for persistence
    session['language'] = language_code
    
    # If user is logged in, save language preference to their profile
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            print(f"[DEBUG] Updating language preference for user {user.id} to {language_code}")
            # Get or create the language record
            language = Language.query.filter_by(code=language_code).first()
            if not language:
                print(f"[DEBUG] Creating new language record for {language_code}")
                language = Language(
                    code=language_code,
                    name=AVAILABLE_LANGUAGES.get(language_code).split(' ')[0],
                    native_name=AVAILABLE_LANGUAGES.get(language_code)
                )
                db.session.add(language)
                db.session.commit()
            
            # Update user's preferred language
            user.preferred_language_id = language.id
            db.session.commit()
            print(f"[DEBUG] User language preference updated in database")
            
            # If user is logged in, always redirect to dashboard
            next_url = url_for('dashboard.index')
    else:
        # If user is not logged in, redirect to login page
        # This breaks the loop between language selection and home
        next_url = url_for('auth.login')
    
    # Create response with redirect
    response = make_response(redirect(next_url))
    
    # Set language cookie (expires in 1 year)
    response.set_cookie('language', language_code, max_age=31536000)
    
    # Clear any stale translation caches
    session.pop('translation_cache', None)
    
    # For debugging, let's add a flash message
    flash(f"Language changed to {AVAILABLE_LANGUAGES[language_code]}", "success")
    
    return response

# Add a method to reset language to default (English)
@language_bp.route('/language/reset')
def reset_language():
    """Reset language to default (English)"""
    # Create response for redirect to home
    response = make_response(redirect(url_for('home')))
    
    # Reset language in cookie
    response.set_cookie('language', 'en', max_age=31536000)
    
    # Reset language in session
    session['language'] = 'en'
    
    # Clear any translation caches
    session.pop('translation_cache', None)
    
    return response

@language_bp.route('/language-selector')
def language_selector():
    """Show the language selector component for inclusion in other pages"""
    return render_template('_language_selector.html', 
                        languages=AVAILABLE_LANGUAGES,
                        current_language=get_current_language())

@language_bp.route('/api/translate', methods=['POST'])
def translate_api():
    """API endpoint for client-side translation"""
    # Get JSON request data
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'Missing text parameter'}), 400
    
    text = data.get('text')
    target_language = data.get('target_language') or g.language
    source_language = data.get('source_language', 'en')
    
    # Validate languages
    if target_language not in SUPPORTED_LANGUAGES:
        return jsonify({'error': f'Unsupported target language: {target_language}'}), 400
    
    # Skip translation if target is same as source
    if target_language == source_language:
        return jsonify({
            'original': text,
            'translated': text,
            'source_language': source_language,
            'target_language': target_language
        })
    
    # Check translation cache in session
    cache_key = f"{source_language}:{target_language}:{text}"
    if 'translation_cache' in session and cache_key in session['translation_cache']:
        return jsonify({
            'original': text,
            'translated': session['translation_cache'][cache_key],
            'source_language': source_language,
            'target_language': target_language,
            'cached': True
        })
    
    # Translate text
    try:
        translated_text = translate_text(text, target_language, source_language)
        
        # Save to cache
        if 'translation_cache' not in session:
            session['translation_cache'] = {}
        session['translation_cache'][cache_key] = translated_text
        
        return jsonify({
            'original': text,
            'translated': translated_text,
            'source_language': source_language,
            'target_language': target_language
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper function to get current language
def get_current_language():
    """
    Get current language from:
    1. g.language if set
    2. User's preferred language (if logged in)
    3. Session
    4. Cookie
    5. Default to English
    """
    # First check if language is already set in g
    if hasattr(g, 'language'):
        return g.language
        
    # Next check if user is logged in and has preferred language
    if hasattr(g, 'user') and g.user and g.user.preferred_language:
        return g.user.preferred_language.code
    
    # Next check session
    if 'language' in session:
        return session['language']
    
    # Next check cookie
    return request.cookies.get('language', 'en')

# Function to be used in before_request to set g.language
def set_language_for_request():
    """Set g.language for the current request"""
    # Check for temporary language override first (highest priority)
    temp_language = request.cookies.get('temp_language')
    if temp_language and temp_language in AVAILABLE_LANGUAGES:
        g.language = temp_language
        print(f"[DEBUG] Using temporary language for request: {g.language}")
    else:
        # Follow normal language resolution chain
        g.language = get_current_language()
        print(f"[DEBUG] Language set for request: {g.language}")
    
    # Set available languages
    g.available_languages = AVAILABLE_LANGUAGES 
    
    # Set a translate function for convenience in templates
    def translate(text):
        if not text:
            return text
        
        # Check translation cache
        cache_key = f"en:{g.language}:{text}"
        if 'translation_cache' in session and cache_key in session['translation_cache']:
            return session['translation_cache'][cache_key]
        
        result = translate_text(text, g.language)
        
        # Save to cache
        if 'translation_cache' not in session:
            session['translation_cache'] = {}
        session['translation_cache'][cache_key] = result
        
        return result
    
    g.translate = translate

@language_bp.route('/example')
def example():
    """Show translation example page"""
    return render_template('translation_example.html') 