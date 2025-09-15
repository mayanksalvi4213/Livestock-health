# app.py
from flask import Flask, render_template, session, g, request, redirect, url_for, jsonify
from flask_migrate import Migrate
from routes.health import health_bp
from routes.vaccine import vaccine_bp
from routes.disease import disease_bp
from routes.disease_alerts import disease_alerts_bp
from routes.auth import auth_bp
from routes.breed import breed_bp
from routes.language import language_bp, set_language_for_request, AVAILABLE_LANGUAGES
from routes.dashboard import dashboard_bp
from routes.profile import profile_bp
from routes.notifications import notifications_bp
from routes.animals import animals_bp
from routes.services import services_bp
from models import db, User, Language, AnimalType
from utils.translator_flask import Translator, translate_blueprint
from utils.translator import translate_text, translate_dict
import os
from datetime import timedelta, datetime
import locale

# Create Flask application
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'agrihealth_secret_key'  # Change this in production!
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agrihealth.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'tmp_uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days
app.config['DEFAULT_LANGUAGE'] = 'en'  # Default language
app.config['AVAILABLE_LANGUAGES'] = AVAILABLE_LANGUAGES  # Available languages
app.config['AUTH_REQUIRED_ENDPOINTS'] = ['dashboard.index', 'health.health_page', 'vaccine.vaccine_page', 
                                        'disease_alerts.index', 'breed.breed_form', 'profile.index', 
                                        'notifications.index']

# Initialize SQLAlchemy with the app
db.init_app(app)
migrate = Migrate(app, db)

# Initialize translator
translator = Translator(app)
print("✨ Translator extension initialized ✨")

# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Ensure static folder exists
if not os.path.exists('static'):
    os.makedirs('static')

# Translation dictionary - only used for static content that isn't sent to Google Translate
# For dynamic content, we use the Google Translate API through utils.translator
translations = {
    # English translations (default)
    'en': {
        'welcome': 'Welcome to Livestock Health',
        'language_select': 'Select Language',
        'login': 'Login',
        'register': 'Register',
        'dashboard': 'Dashboard',
        'animal_health': 'Animal Health',
        'breed_identification': 'Breed Identification',
        'vaccines': 'Vaccines',
        'disease_alerts': 'Disease Alerts',
        'profile': 'Profile',
        'logout': 'Logout',
        'notifications': 'Notifications',
        # Animal Health page
        'animal_health_analysis': 'Animal Health Analysis',
        'upload_image': 'Upload an image for AI-powered health assessment',
        'ai_powered_assessment': 'AI-Powered Health Assessment',
        'upload_photo': 'Upload a photo of your animal to receive an AI-powered health assessment. Our system will analyze the image and identify potential health issues.',
        'best_results': 'For best results, upload a clear image of the affected area or full body shot in good lighting.',
        'upload_animal_image': 'Upload Animal Image',
        'animal_type': 'Animal Type',
        'drop_image': 'Drop your image here',
        'or': 'or',
        'browse_files': 'Browse Files',
        'analyze_image': 'Analyze Image',
        'change_image': 'Change Image',
        'analyzing_image': 'Analyzing image...',
        'health_analysis_results': 'Health Analysis Results',
        'detection_results': 'Detection Results:',
        'detected_condition': 'Detected Condition:',
        'detected_features': 'Detected Features:',
        'recommendations': 'Recommendations:',
        'all_predictions': 'All Predictions:',
        'confidence': 'Confidence',
        
        # Dashboard page
        'welcome_back': 'Welcome back,',
        'settings': 'Settings',
        'disease_alerts': 'Disease Alerts',
        'active': 'active',
        'no_disease_outbreaks': 'No disease outbreaks reported in your area!',
        'view_all_alerts': 'View All Alerts',
        'nearby_veterinary_services': 'Nearby Veterinary Services',
        'no_veterinary_services': 'No veterinary services found in your area.',
        'recent_activities': 'Recent Activities',
        'no_recent_activities': 'No recent activities',
        'farm_location': 'Farm Location',
        'farm_info_not_available': 'Farm information not available',
        'address': 'Address',
        'district': 'District',
        'state': 'State',
        'pincode': 'PIN Code',
        'km_away': 'km away',
        
        # Vaccine page
        'vaccine_information': 'Vaccine Information',
        'essential_vaccines': 'Essential vaccines for your livestock health management',
        'search_vaccines': 'Search vaccines...',
        'all': 'All',
        'cows': 'Cows',
        'goats': 'Goats',
        'sheep': 'Sheep',
        'chicken': 'Chicken',
        'understanding_livestock_vaccines': 'Understanding Livestock Vaccines',
        'vaccines_description': 'Vaccines are an essential part of preventive health care for your animals. They help prevent diseases that can cause illness, decreased productivity, and even death. Regular vaccination according to recommended schedules is crucial for maintaining healthy livestock.',
        'vaccine_reminder': 'Remember to consult with your veterinarian to develop a vaccination program tailored to your specific farm conditions and regional disease risks.',
        'available_vaccines': 'Available Vaccines',
        'check_another_animal': 'Check Another Animal',
        'view_vaccine_information': 'View Vaccine Information',
        
        # Disease alerts page
        'disease_alert_center': 'Disease Alert Center',
        'monitor_outbreaks': 'Monitor disease outbreaks and keep your livestock safe',
        'current_outbreaks': 'Current Outbreaks',
        'no_current_outbreaks': 'No current outbreaks reported.',
        'disease_monitoring_description': 'Our disease tracking system monitors outbreaks and health risks for livestock in your region. Stay updated on potential threats and take preventive measures to protect your animals.',
        'monitoring_details': 'We analyze data from local veterinary reports, weather patterns, and historical disease trends to provide you with timely alerts.',
        'severity': 'Severity:',
        'location': 'Location:',
        'reported_on': 'Reported on:',
        'reported_by': 'Reported by:',
        'preventive_measures': 'Preventive Measures',
        'filter_alerts': 'Filter Alerts',
        
        # Breed identification page
        'breed_identification_service': 'Breed Identification Service',
        'upload_animal_photo': 'Upload an animal photo for AI-powered breed identification',
        'breed_identification_description': 'Our advanced AI system can help identify the breed of your animal from a photo. This can help you understand breed-specific traits, care requirements, and potential health issues.',
        'upload_breed_image': 'Upload Breed Image',
        'analyzing_breed': 'Analyzing breed...',
        'breed_results': 'Breed Identification Results',
        'breed_detected': 'Breed Detected:',
        'breed_details': 'Breed Details',
        'breed_characteristics': 'Breed Characteristics:',
        'care_recommendations': 'Care Recommendations:',
        'other_possible_breeds': 'Other Possible Breeds:',
        
        # Disease alerts page (additional)
        'by_location': 'By Location',
        'by_animal': 'By Animal',
        'by_risk_level': 'By Risk Level',
        'all_animals': 'All Animals',
        'high_risk': 'High Risk',
        'medium_risk': 'Medium Risk',
        'low_risk': 'Low Risk',
        'informational': 'Informational',
        'total_alerts': 'Total Alerts',
        'view_details': 'View Details',
        'local': 'Local',
        'nearby': 'Nearby',
        'disease_information': 'Disease Information',
        'prevention_guide': 'Download Prevention Guide',
        
        # Vaccine page (additional)
        'schedule': 'Schedule',
        'administration': 'Administration',
        'age_first_dose': 'Age for First Dose',
        'every_6_months': 'Every 6 months',
        'one_time_heifers': 'One-time for heifers',
        'annual': 'Annual',
        'subcutaneous_injection': 'Subcutaneous injection',
        'four_months': '4 months and above',
        'four_to_eight_months': '4-8 months of age',
        'three_months': '3 months and above',
        'fmd_vaccine_description': 'Protects against Foot and Mouth Disease, a highly contagious viral disease that affects cloven-hoofed animals.',
        'brucellosis_vaccine_description': 'Prevents Brucellosis, a bacterial disease causing abortion, infertility, and reduced milk production.',
        'hs_bq_vaccine_description': 'Combined vaccine against two fatal bacterial diseases: Haemorrhagic Septicaemia and Black Quarter.',
        'more_information': 'More Information',
        'set_reminder': 'Set Reminder',
        'vaccine_information': 'Vaccine Information',
        'download_schedule': 'Download Schedule',
        'set_vaccination_reminder': 'Set Vaccination Reminder',
        'animal': 'Animal',
        'select_animal': 'Select animal',
        'date': 'Date',
        'notes': 'Notes',
        'cancel': 'Cancel',
        'save_reminder': 'Save Reminder',
        
        # Health analysis (additional)
        'health_analysis_result': 'Health Analysis Result',
        'detection_result': 'Detection Result',
        'confidence': 'Confidence',
        'detected_patterns': 'Detected Patterns',
        'recommendations': 'Recommendations',
        'consult_vet': 'Consult a veterinarian',
        'isolate_animal': 'Isolate the affected animal',
        'follow_treatment': 'Follow prescribed treatment',
        'monitor_symptoms': 'Monitor for additional symptoms',
        
        # Disease names
        'foot_and_mouth': 'Foot and Mouth Disease',
        'brucellosis': 'Brucellosis',
        'black_quarter': 'Black Quarter',
        'mastitis': 'Mastitis',
        'ringworm': 'Ringworm',
        'theileriosis': 'Theileriosis',
        
        # Health analysis specific elements
        'circular_lesions': 'Circular lesions on skin',
        'hair_loss': 'Hair loss in affected areas',
        'skin_inflammation': 'Skin inflammation and redness',
        'back': 'Back',
        'save_analysis': 'Save Analysis',
        'share_with_vet': 'Share with Veterinarian',
        
        # Breed page specific elements
        'breed_identification_results': 'Breed Identification Results',
        'breed_image': 'Breed Image',
        'identification_result': 'Identification Result',
        'loading_results': 'Loading results...',
        'breed_characteristics': 'Breed Characteristics',
        'loading_breed_information': 'Loading breed information...',
        'try_another': 'Try Another',
        'save_results': 'Save Results',
        'more_breed_info': 'More Breed Info',
        'other_possible_breeds': 'Other Possible Breeds',
    },
    # Hindi translations
    'hi': {
        'welcome': 'एग्रीहेल्थ में आपका स्वागत है',
        'language_select': 'भाषा चुनें',
        'login': 'लॉग इन करें',
        'register': 'पंजीकरण करें',
        'dashboard': 'डैशबोर्ड',
        'animal_health': 'पशु स्वास्थ्य',
        'breed_identification': 'नस्ल पहचान',
        'vaccines': 'टीके',
        'disease_alerts': 'रोग अलर्ट',
        'profile': 'प्रोफ़ाइल',
        'logout': 'लॉग आउट',
        'notifications': 'सूचनाएं',
        # Animal Health page
        'animal_health_analysis': 'पशु स्वास्थ्य विश्लेषण',
        'upload_image': 'AI-संचालित स्वास्थ्य मूल्यांकन के लिए एक छवि अपलोड करें',
        'ai_powered_assessment': 'AI-संचालित स्वास्थ्य मूल्यांकन',
        'upload_photo': 'AI-संचालित स्वास्थ्य मूल्यांकन प्राप्त करने के लिए अपने पशु की एक तस्वीर अपलोड करें। हमारी प्रणाली छवि का विश्लेषण करेगी और संभावित स्वास्थ्य समस्याओं की पहचान करेगी।',
        'best_results': 'सर्वोत्तम परिणामों के लिए, प्रभावित क्षेत्र या पूरे शरीर का स्पष्ट चित्र अच्छी रोशनी में अपलोड करें।',
        'upload_animal_image': 'पशु छवि अपलोड करें',
        'animal_type': 'पशु प्रकार',
        'drop_image': 'अपनी छवि यहां छोड़ें',
        'or': 'या',
        'browse_files': 'फ़ाइलें ब्राउज़ करें',
        'analyze_image': 'छवि विश्लेषण करें',
        'change_image': 'छवि बदलें',
        'analyzing_image': 'छवि का विश्लेषण हो रहा है...',
        'health_analysis_results': 'स्वास्थ्य विश्लेषण परिणाम',
        'detection_results': 'पहचान परिणाम:',
        'detected_condition': 'पहचानी गई स्थिति:',
        'detected_features': 'पहचानी गई विशेषताएं:',
        'recommendations': 'सिफारिशें:',
        'all_predictions': 'सभी भविष्यवाणियां:',
        'confidence': 'विश्वास',
        
        # Dashboard page
        'welcome_back': 'वापसी पर स्वागत है,',
        'settings': 'सेटिंग्स',
        'disease_alerts': 'रोग अलर्ट',
        'active': 'सक्रिय',
        'no_disease_outbreaks': 'आपके क्षेत्र में कोई रोग प्रकोप की सूचना नहीं है!',
        'view_all_alerts': 'सभी अलर्ट देखें',
        'nearby_veterinary_services': 'आस-पास की पशु चिकित्सा सेवाएं',
        'no_veterinary_services': 'आपके क्षेत्र में कोई पशु चिकित्सा सेवा नहीं मिली।',
        'recent_activities': 'हाल की गतिविधियां',
        'no_recent_activities': 'कोई हालिया गतिविधि नहीं',
        'farm_location': 'फार्म स्थान',
        'farm_info_not_available': 'फार्म की जानकारी उपलब्ध नहीं है',
        'address': 'पता',
        'district': 'जिला',
        'state': 'राज्य',
        'pincode': 'पिन कोड',
        'km_away': 'किलोमीटर दूर',
        
        # Vaccine page
        'vaccine_information': 'टीका जानकारी',
        'essential_vaccines': 'आपके पशुधन स्वास्थ्य प्रबंधन के लिए आवश्यक टीके',
        'search_vaccines': 'टीके खोजें...',
        'all': 'सभी',
        'cows': 'गायें',
        'goats': 'बकरियां',
        'sheep': 'भेड़',
        'chicken': 'मुर्गी',
        'understanding_livestock_vaccines': 'पशुधन टीकों को समझना',
        'vaccines_description': 'टीके आपके पशुओं के लिए निवारक स्वास्थ्य देखभाल का एक आवश्यक हिस्सा हैं। वे ऐसे रोगों को रोकने में मदद करते हैं जो बीमारी, कम उत्पादकता, और यहां तक कि मृत्यु का कारण बन सकते हैं। स्वस्थ पशुधन बनाए रखने के लिए अनुशंसित कार्यक्रमों के अनुसार नियमित टीकाकरण महत्वपूर्ण है।',
        'vaccine_reminder': 'अपनी विशिष्ट फार्म स्थितियों और क्षेत्रीय रोग जोखिमों के अनुरूप एक टीकाकरण कार्यक्रम विकसित करने के लिए अपने पशु चिकित्सक से परामर्श करने के लिए याद रखें।',
        'available_vaccines': 'उपलब्ध टीके',
        'check_another_animal': 'एक और पशु की जांच करें',
        'view_vaccine_information': 'टीका जानकारी देखें',
        
        # Disease alerts page
        'disease_alert_center': 'रोग अलर्ट केंद्र',
        'monitor_outbreaks': 'रोग प्रकोप की निगरानी करें और अपने पशुधन को सुरक्षित रखें',
        'current_outbreaks': 'वर्तमान प्रकोप',
        'no_current_outbreaks': 'कोई वर्तमान प्रकोप की सूचना नहीं है।',
        'disease_monitoring_description': 'हमारी रोग ट्रैकिंग प्रणाली आपके क्षेत्र में पशुधन के लिए प्रकोप और स्वास्थ्य जोखिमों की निगरानी करती है। संभावित खतरों पर अपडेट रहें और अपने पशुओं की सुरक्षा के लिए निवारक उपाय करें।',
        'monitoring_details': 'हम आपको समय पर अलर्ट प्रदान करने के लिए स्थानीय पशु चिकित्सा रिपोर्ट, मौसम पैटर्न और ऐतिहासिक रोग रुझानों से डेटा का विश्लेषण करते हैं।',
        'severity': 'गंभीरता:',
        'location': 'स्थान:',
        'reported_on': 'रिपोर्ट किया गया:',
        'reported_by': 'रिपोर्ट किया:',
        'preventive_measures': 'निवारक उपाय',
        'filter_alerts': 'अलर्ट फिल्टर करें',
        
        # Breed identification page
        'breed_identification_service': 'नस्ल पहचान सेवा',
        'upload_animal_photo': 'AI-संचालित नस्ल पहचान के लिए एक पशु फोटो अपलोड करें',
        'breed_identification_description': 'हमारी उन्नत AI प्रणाली एक फोटो से आपके पशु की नस्ल की पहचान करने में मदद कर सकती है। यह आपको नस्ल-विशिष्ट गुणों, देखभाल आवश्यकताओं और संभावित स्वास्थ्य समस्याओं को समझने में मदद कर सकता है।',
        'upload_breed_image': 'नस्ल छवि अपलोड करें',
        'analyzing_breed': 'नस्ल का विश्लेषण हो रहा है...',
        'breed_results': 'नस्ल पहचान परिणाम',
        'breed_detected': 'पहचानी गई नस्ल:',
        'breed_details': 'नस्ल विवरण',
        'breed_characteristics': 'नस्ल विशेषताएं:',
        'care_recommendations': 'देखभाल की सिफारिशें:',
        'other_possible_breeds': 'अन्य संभावित नस्लें:',
        
        # Disease alerts page (additional)
        'by_location': 'स्थान के अनुसार:',
        'by_animal': 'पशु के अनुसार:',
        'by_risk_level': 'जोखिम स्तर के अनुसार:',
        'all_animals': 'सभी पशु',
        'high_risk': 'उच्च जोखिम',
        'medium_risk': 'मध्यम जोखिम',
        'low_risk': 'कम जोखिम',
        'informational': 'जानकारीपूर्ण',
        'total_alerts': 'कुल अलर्ट',
        'view_details': 'विवरण देखें',
        'local': 'स्थानीय',
        'nearby': 'आस-पास',
        'disease_information': 'रोग की जानकारी',
        'prevention_guide': 'रोकथाम गाइड डाउनलोड करें',
        
        # Vaccine page (additional)
        'schedule': 'कार्यक्रम:',
        'administration': 'प्रशासन:',
        'age_first_dose': 'पहली खुराक की उम्र:',
        'every_6_months': 'हर 6 महीने',
        'one_time_heifers': 'बछियों के लिए एक बार',
        'annual': 'वार्षिक',
        'subcutaneous_injection': 'त्वचा के नीचे इंजेक्शन',
        'four_months': '4 महीने और उससे अधिक',
        'four_to_eight_months': '4-8 महीने की उम्र',
        'three_months': '3 महीने और उससे अधिक',
        'fmd_vaccine_description': 'खुरपका-मुंहपका रोग से बचाता है, यह एक अत्यधिक संक्रामक वायरल रोग है जो खुरदार पशुओं को प्रभावित करता है।',
        'brucellosis_vaccine_description': 'ब्रूसेलोसिस से बचाता है, यह एक जीवाणु रोग है जो गर्भपात, बांझपन और दूध उत्पादन में कमी का कारण बनता है।',
        'hs_bq_vaccine_description': 'दो घातक जीवाणु रोगों के खिलाफ संयुक्त टीका: हेमोरेजिक सेप्टीसीमिया और ब्लैक क्वार्टर।',
        'more_information': 'अधिक जानकारी',
        'set_reminder': 'रिमाइंडर सेट करें',
        'vaccine_information': 'टीका जानकारी',
        'download_schedule': 'अनुसूची डाउनलोड करें',
        'set_vaccination_reminder': 'टीकाकरण रिमाइंडर सेट करें',
        'animal': 'पशु',
        'select_animal': 'पशु चुनें',
        'date': 'तारीख',
        'notes': 'नोट्स',
        'cancel': 'रद्द करें',
        'save_reminder': 'रिमाइंडर सहेजें',
        
        # Health analysis (additional)
        'health_analysis_result': 'स्वास्थ्य विश्लेषण परिणाम',
        'detection_result': 'पहचान परिणाम:',
        'confidence': 'विश्वास स्तर',
        'detected_patterns': 'पहचाने गए पैटर्न',
        'recommendations': 'सिफारिशें',
        'consult_vet': 'पशु चिकित्सक से परामर्श करें',
        'isolate_animal': 'प्रभावित पशु को अलग रखें',
        'follow_treatment': 'निर्धारित उपचार का पालन करें',
        'monitor_symptoms': 'अतिरिक्त लक्षणों पर नज़र रखें',
        
        # Disease names
        'foot_and_mouth': 'खुरपका-मुंहपका रोग',
        'brucellosis': 'ब्रूसेलोसिस',
        'black_quarter': 'ब्लैक क्वार्टर',
        'mastitis': 'थनैला',
        'ringworm': 'दाद',
        'theileriosis': 'थेइलेरिओसिस',
        
        # Health analysis specific elements
        'circular_lesions': 'त्वचा पर गोलाकार घाव',
        'hair_loss': 'प्रभावित क्षेत्रों में बालों का झड़ना',
        'skin_inflammation': 'त्वचा की सूजन और लालिमा',
        'back': 'वापस',
        'save_analysis': 'विश्लेषण सहेजें',
        'share_with_vet': 'पशु चिकित्सक के साथ साझा करें',
        
        # Breed page specific elements
        'breed_identification_results': 'नस्ल पहचान परिणाम',
        'breed_image': 'नस्ल छवि',
        'identification_result': 'पहचान परिणाम',
        'loading_results': 'परिणाम लोड हो रहे हैं...',
        'breed_characteristics': 'नस्ल विशेषताएं',
        'loading_breed_information': 'नस्ल जानकारी लोड हो रही है...',
        'try_another': 'दूसरा प्रयास करें',
        'save_results': 'परिणाम सहेजें',
        'more_breed_info': 'अधिक नस्ल जानकारी',
        'other_possible_breeds': 'अन्य संभावित नस्लें',
    },
    # Placeholder for other languages - these will be dynamically translated
}

# Add other languages to the translations dictionary
for lang_code in AVAILABLE_LANGUAGES:
    if lang_code not in translations:
        # Create empty dictionaries for other languages
        # They will be filled via Google Translate API
        translations[lang_code] = {}

# Function to get translations for a specific language
def get_translations(lang_code):
    """
    Get translations for a specific language
    If translation doesn't exist, create it dynamically
    """
    if lang_code not in translations:
        # Default to English
        lang_code = 'en'
    
    # If language exists but is empty, translate from English
    if not translations[lang_code] and lang_code != 'en':
        # Get English translations
        en_translations = translations['en']
        
        # Translate all keys to the target language
        translations[lang_code] = translate_dict(en_translations, lang_code, 'en')
    
    return translations.get(lang_code, translations['en'])

# Set up translations in the global template context
@app.context_processor
def inject_translations():
    lang = g.language if hasattr(g, 'language') else request.cookies.get('language', 'en')
    
    # Get translations for the language
    t = get_translations(lang)
    
    # Function to translate text on the fly
    def translate(text):
        # If key exists in translations dictionary, use it
        if text in t:
            return t[text]
        
        # Otherwise translate dynamically
        return translate_text(text, lang)
    
    return {'t': t, 'translate': translate}

# Set locale based on language for date and number formatting
@app.before_request
def before_request():
    # Set user in g
    user_id = session.get('user_id')
    if user_id:
        g.user = User.query.get(user_id)
    else:
        g.user = None
        
    # Set language for request
    set_language_for_request()
    
    # Skip for static files
    if request.path.startswith('/static'):
        return
        
    # Check if user is authenticated for protected routes
    if request.endpoint in app.config.get('AUTH_REQUIRED_ENDPOINTS', []):
        if not g.user:
            return redirect(url_for('auth.login', next=request.url))
            
    # Set the current timestamp for the request
    g.now = datetime.utcnow()

# Register blueprints
app.register_blueprint(language_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(health_bp)
app.register_blueprint(vaccine_bp)
app.register_blueprint(disease_bp)
app.register_blueprint(disease_alerts_bp)
app.register_blueprint(breed_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(notifications_bp)
app.register_blueprint(animals_bp)
app.register_blueprint(services_bp)

@app.route('/')
def home():
    """Home page route"""
    # If user is logged in, redirect to dashboard
    if g.user:
        return redirect(url_for('dashboard.index'))
    
    # Check if language has been set
    lang = request.cookies.get('language')
    if not lang:
        # If language not set, redirect to language selection
        return redirect(url_for('language.select', next=url_for('auth.login')))
    
    # If language is set but user is not logged in, show welcome page
    return render_template('welcome.html')

@app.route('/ping')
def ping():
    """Simple endpoint to check if the server is available"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat()
    })

# Create database tables within application context
with app.app_context():
    db.create_all()

# Register error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', 
                          error_code=404, 
                          error_message="The page you're looking for doesn't exist."), 404

@app.errorhandler(500)
def server_error(e):
    # Log the error
    app.logger.error(f"500 error: {str(e)}")
    return render_template('error.html', 
                          error_code=500, 
                          error_message="Internal server error. Our team has been notified."), 500

@app.errorhandler(Exception)
def handle_exception(e):
    # Log the error
    app.logger.error(f"Unhandled exception: {str(e)}")
    
    # Only show error details in debug mode
    error_details = str(e) if app.debug else None
    
    return render_template('error.html',
                          error_code="Error",
                          error_message="An unexpected error occurred.",
                          error_details=error_details), 500

# Set up response after-request handler for JSON translation
@app.after_request
def process_response(response):
    if response.mimetype == 'application/json':
        return translator.translate_response(response)
    return response

# Context processor for global template variables
@app.context_processor
def inject_globals():
    return {
        'now': datetime.utcnow(),
        'app_name': 'Livestock Health',
        'app_version': '1.0.0'
    }

if __name__ == '__main__':
    app.run(debug=True)