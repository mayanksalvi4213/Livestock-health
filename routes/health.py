# Add breed prediction model and routes
from flask import Blueprint, render_template, request, jsonify, session, g, redirect, url_for, flash
import os
import uuid
import shutil
from werkzeug.utils import secure_filename
from disease_predict import predict_disease, get_disease_recommendations
from breed_predict import predict_breed
from utils.vaccine_data import get_vaccines_for_disease
import io
import sys
import numpy as np
import tensorflow as tf
import cv2
from PIL import Image
import json
from datetime import datetime
import base64
from flask_login import login_required, current_user
from utils import get_nearby_veterinarians
import requests
import traceback
from math import radians, cos, sin, asin, sqrt
from flask import g, session
from models import db, User, Farm

health_bp = Blueprint('health', __name__)

# Ensure user is set in g for all health routes
@health_bp.before_request
def set_user_in_g():
    # Get user from session
    user_id = session.get('user_id')
    if user_id:
        from models import User
        g.user = User.query.get(user_id)
    else:
        g.user = None
    print(f"Setting g.user from session in health blueprint: user_id={user_id}, g.user={g.user}")

# Configure image parameters
IMG_SIZE = (224, 224)

# Label mappings
disease_labels = {
    0: 'Healthy',
    1: 'Lumpy Skin Disease',
    2: 'Mastitis',
    3: 'Pinkeye',
    4: 'Ringworm'
}

breed_labels = {
    0: 'Ongole cow',
    1: 'Dangi',
    2: 'Gir cow',
    3: 'Jersey',
    4: 'Sahiwal'
}

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'health'), exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'breed'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@health_bp.route('/health')
def health_page():
    return render_template('health.html')

@health_bp.route('/analyze-health', methods=['POST'])
def analyze_health():
    """Analyze uploaded image for animal health"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file uploaded'
            }), 400
        
        file = request.files['image']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed'
            }), 400
        
        # Get animal type - accept both parameter names for compatibility
        animal_type = request.form.get('animalType', request.form.get('animal_type', 'cow'))
        print(f"DEBUG - Animal type from form: {animal_type}")
        print(f"DEBUG - All form data: {request.form}")
        
        # Create temporary uploads directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Try to create minimal models if needed and AUTO_CREATE_MODELS is enabled
            auto_create_model = bool(int(os.environ.get('AUTO_CREATE_MODELS', '0')))
            
            # Analyze the image with the specified animal type
            result = predict_disease(filepath, animal_type=animal_type, auto_create_minimal=auto_create_model)
            
            # Format confidence score to ensure it's a proper percentage
            confidence = min(result['confidence'] * 100, 100) if result['confidence'] <= 1.0 else min(result['confidence'], 100)
            
            # Get detailed recommendations based on the predicted disease from disease_predict module
            disease = result['disease']
            
            # Log the detected disease for debugging
            print(f"DEBUG - Detected disease: {disease} with confidence: {confidence} for animal type: {animal_type}")
            
            # Get comprehensive recommendations including medicine and diet info
            recommendations = get_disease_recommendations(animal_type, disease)
            
            # Format top predictions for display
            formatted_predictions = []
            for pred_disease, pred_conf in result.get('top_predictions', []):
                pred_conf_pct = pred_conf * 100 if pred_conf <= 1.0 else pred_conf
                formatted_predictions.append({
                    'disease': pred_disease,
                    'confidence': f"{min(pred_conf_pct, 100):.1f}%"
                })
            
            # Get vaccine information for the predicted disease
            vaccine_info = get_vaccines_for_disease(disease)
            
            # Log the formatted response for debugging
            response_data = {
                'success': True,
                'disease': disease,
                'confidence': f"{confidence:.1f}%",
                'recommendations': recommendations,
                'predictions': formatted_predictions,
                'detected_features': result.get('detected_features', []),
                'animal_type': animal_type,  # Include animal type in response
                'vaccine': vaccine_info  # Include vaccine information in response
            }
            print(f"DEBUG - Response data: {response_data}")
            
            # Return formatted results
            return jsonify(response_data)
        
        except FileNotFoundError as e:
            # Model not found - try to create minimal model
            error_message = str(e)
            if "No model found" in error_message:
                # Check if create_minimal_model.py exists
                if os.path.exists("create_minimal_model.py"):
                    # Offer to create a minimal model
                    return jsonify({
                        'error': f'The {animal_type} disease detection model is not available.',
                        'model_error': animal_type,
                        'create_option': True,
                        'create_message': f'You can create a minimal test model by running: python create_minimal_model.py {animal_type}'
                    }), 503  # Service Unavailable
                else:
                    return jsonify({
                        'error': f'The {animal_type} disease detection model is not available. Please run train_pipeline.py to create a model.',
                        'model_error': animal_type
                    }), 503  # Service Unavailable
            else:
                # Log the error for debugging
                print(f"Error analyzing image: {error_message}")
                return jsonify({
                    'error': f'Error analyzing image: {error_message}'
                }), 500
        except ValueError as e:
            # Check if this is a model loading error
            error_message = str(e)
            if "Chicken disease model is not available" in error_message:
                return jsonify({
                    'error': 'The chicken disease detection model is not available. Please try again later or select a different animal type.',
                    'model_error': 'chicken'
                }), 503  # Service Unavailable
            elif "Goat disease model is not available" in error_message:
                return jsonify({
                    'error': 'The goat disease detection model is not available. Please try again later or select a different animal type.',
                    'model_error': 'goat'
                }), 503  # Service Unavailable
            elif "Cow disease model is not available" in error_message:
                return jsonify({
                    'error': 'The cow disease detection model is not available. Please try again later or select a different animal type.',
                    'model_error': 'cow'
                }), 503  # Service Unavailable
            else:
                # Log the error for debugging
                print(f"Error analyzing image: {error_message}")
                return jsonify({
                    'error': f'Error analyzing image: {error_message}'
                }), 500
        except Exception as e:
            # Log the error for debugging
            print(f"Error analyzing image: {str(e)}")
            return jsonify({
                'error': f'Error analyzing image: {str(e)}'
            }), 500
        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@health_bp.route('/analyze-breed', methods=['POST'])
def analyze_breed():
    """Analyze uploaded image for animal breed"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file uploaded'
            }), 400
        
        file = request.files['image']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed'
            }), 400
        
        # Get animal type from form
        animal_type = request.form.get('animalType', request.form.get('animal_type', 'cow'))
        print(f"DEBUG - Animal type for breed analysis: {animal_type}")
        
        # Create temporary uploads directory if it doesn't exist
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save the uploaded file with a secure filename
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Try to create minimal models if needed and AUTO_CREATE_MODELS is enabled
            auto_create_model = bool(int(os.environ.get('AUTO_CREATE_MODELS', '0')))
            
            # Analyze the image with the specified animal type
            result = predict_breed(filepath, animal_type=animal_type, auto_create_minimal=auto_create_model)
            
            # Format response data
            breed = result.get('breed')
            confidence = result.get('confidence', 0) * 100
            
            # Format other possibilities
            other_possibilities = []
            for breed_name, breed_conf in result.get('top_predictions', [])[1:]:  # Skip the top one
                if breed_conf > 5:  # Only include predictions with >5% confidence
                    other_possibilities.append({
                        'name': breed_name,
                        'confidence': round(breed_conf * 100, 1)
                    })
            
            # Save the result image if available
            result_image_path = None
            if 'output_image_path' in result:
                result_image_path = result['output_image_path']
            
            # Return formatted results
            return jsonify({
                'success': True,
                'breed': breed,
                'confidence': round(confidence, 1),
                'other_possibilities': other_possibilities,
                'result_image': result_image_path
            })
        
        except FileNotFoundError as e:
            # Model not found - try to create minimal model
            error_message = str(e)
            if "No model found" in error_message:
                # Check if create_minimal_model.py exists
                if os.path.exists("create_minimal_model.py"):
                    # Offer to create a minimal model
                    return jsonify({
                        'error': f'The {animal_type} breed detection model is not available.',
                        'model_error': animal_type,
                        'create_option': True,
                        'create_message': f'You can create a minimal test model by running: python create_minimal_model.py {animal_type}'
                    }), 503  # Service Unavailable
                else:
                    return jsonify({
                        'error': f'The {animal_type} breed detection model is not available. Please run train_pipeline.py to create a model.',
                        'model_error': animal_type
                    }), 503  # Service Unavailable
            else:
                # Log the error for debugging
                print(f"Error analyzing image: {error_message}")
                return jsonify({
                    'error': f'Error analyzing image: {error_message}'
                }), 500
        except Exception as e:
            # Log the error for debugging
            print(f"Error analyzing image: {str(e)}")
            return jsonify({
                'error': f'Error analyzing image: {str(e)}'
            }), 500
        finally:
            # Clean up temporary file
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def get_vaccine_recommendation(disease):
    """Get vaccine/treatment recommendation based on disease"""
    recommendations = {
        'Healthy': 'No treatment needed. Continue regular preventive care including vaccinations against common diseases.',
        'Lumpy Skin Disease': 'Lumpy Skin Disease vaccine and antibiotics for secondary infections. Isolate affected animal.',
        'Mastitis': 'Antibiotic treatment, frequent milking of affected quarters. Consult a vet for proper medication.',
        'Pinkeye': 'Pinkeye vaccines, antibiotic ointment or injections. Keep affected eye clean and protect from sunlight.',
        'Ringworm': 'Topical antifungal treatments and oral medications in severe cases. Clean and disinfect housing areas.'
    }
    
    return recommendations.get(disease, 'Consult a veterinarian for proper diagnosis and treatment')

@health_bp.route('/disease-info/<disease>')
def disease_info(disease):
    """Display information about a specific disease"""
    # Normalize disease name
    disease = disease.replace('-', ' ').title()
    
    # Get disease information
    disease_info = {
        'Lumpy Skin Disease': {
            'name': 'Lumpy Skin Disease (LSD)',
            'description': 'Lumpy skin disease is a viral disease that affects cattle. It is characterized by fever, nodules on the skin, and can lead to death in severe cases.',
            'symptoms': [
                'Fever (40-41°C)',
                'Multiple firm nodules in the skin (2-5 cm in diameter)',
                'Nodules on the mucous membranes (especially in the mouth, nose, and eyes)',
                'Enlarged lymph nodes',
                'Edema in the limbs and brisket',
                'Reduced milk production',
                'Abortion in pregnant cows',
                'Emaciation'
            ],
            'transmission': 'Primarily spread by blood-feeding insects like mosquitoes and flies. Can also spread through contaminated equipment and materials.',
            'prevention': [
                'Vaccination is the most effective method of control',
                'Control of insect vectors',
                'Quarantine of infected animals',
                'Proper disposal of dead animals',
                'Disinfection of premises and equipment'
            ],
            'treatment': 'No specific treatment exists. Supportive care includes:',
            'treatment_options': [
                'Antibiotics to prevent secondary bacterial infections',
                'Anti-inflammatory drugs to reduce fever and inflammation',
                'Wound dressing for skin lesions',
                'Nutritional support'
            ],
            'severity': 'High',
            'zoonotic': 'No (does not affect humans)',
            'economic_impact': 'Very high due to reduced milk production, weight loss, abortion, infertility, and trade restrictions.'
        },
        'Mastitis': {
            'name': 'Mastitis',
            'description': 'Mastitis is an inflammation of the mammary gland and udder tissue in dairy animals. It is usually caused by bacterial infection and is one of the most common diseases in dairy cattle.',
            'symptoms': [
                'Swollen, hot, and painful udder',
                'Abnormal milk (watery, clotted, flaky, or bloody)',
                'Reduced milk production',
                'Fever in severe cases',
                'Loss of appetite',
                'Depression'
            ],
            'transmission': 'Primarily through contaminated milking equipment, hands of milkers, and the environment. The bacteria enter through the teat canal.',
            'prevention': [
                'Proper milking hygiene',
                'Regular teat dipping with disinfectant',
                'Proper maintenance of milking equipment',
                'Clean and dry housing',
                'Culling of chronically infected animals',
                'Dry cow therapy'
            ],
            'treatment': 'Treatment depends on the severity and causative agent:',
            'treatment_options': [
                'Intramammary antibiotics',
                'Systemic antibiotics in severe cases',
                'Anti-inflammatory drugs',
                'Frequent milking to remove infected milk',
                'Supportive care'
            ],
            'severity': 'Moderate to High',
            'zoonotic': 'Some causative bacteria can affect humans through milk consumption if not pasteurized.',
            'economic_impact': 'High due to reduced milk production, discarded milk, treatment costs, and premature culling.'
        },
        'Pinkeye': {
            'name': 'Infectious Bovine Keratoconjunctivitis (Pinkeye)',
            'description': 'Pinkeye is a highly contagious bacterial infection that affects the eyes of cattle. It is characterized by inflammation of the cornea and conjunctiva.',
            'symptoms': [
                'Excessive tearing',
                'Squinting or keeping the eye closed',
                'Redness and swelling of the conjunctiva',
                'Cloudy cornea',
                'Ulceration of the cornea in severe cases',
                'White spot or opacity in the center of the eye',
                'Temporary or permanent blindness in severe cases'
            ],
            'transmission': 'Spread by flies, direct contact, and fomites. UV radiation from sunlight, dust, and tall grass can predispose animals to infection.',
            'prevention': [
                'Fly control measures',
                'Vaccination',
                'Isolation of affected animals',
                'Providing shade',
                'Clipping pastures to reduce face irritation',
                'Early treatment of affected animals'
            ],
            'treatment': 'Treatment options include:',
            'treatment_options': [
                'Topical antibiotics (eye ointments)',
                'Subconjunctival antibiotic injections',
                'Systemic antibiotics in severe cases',
                'Eye patches to reduce light exposure',
                'Isolation of affected animals'
            ],
            'severity': 'Moderate',
            'zoonotic': 'No (does not affect humans)',
            'economic_impact': 'Moderate due to reduced weight gain, treatment costs, and potential blindness.'
        },
        'Ringworm': {
            'name': 'Ringworm (Dermatophytosis)',
            'description': 'Ringworm is a fungal infection of the skin and hair. Despite its name, it is not caused by a worm but by various species of fungi, primarily Trichophyton verrucosum in cattle.',
            'symptoms': [
                'Circular, raised, crusty lesions',
                'Hair loss in affected areas',
                'Lesions commonly found on the head, neck, and around the eyes',
                'Mild itching may be present',
                'Lesions may coalesce to form larger affected areas'
            ],
            'transmission': 'Highly contagious through direct contact with infected animals or contaminated equipment, brushes, fences, etc. Spores can survive in the environment for years.',
            'prevention': [
                'Isolation of affected animals',
                'Disinfection of equipment and housing',
                'Good nutrition to maintain skin health',
                'Avoiding overcrowding',
                'Quarantine of new animals'
            ],
            'treatment': 'Treatment options include:',
            'treatment_options': [
                'Topical antifungal treatments',
                'Systemic antifungal medications in severe cases',
                'Iodine solutions applied to affected areas',
                'Improving general hygiene and nutrition'
            ],
            'severity': 'Low to Moderate',
            'zoonotic': 'Yes (can be transmitted to humans)',
            'economic_impact': 'Low to moderate, mainly affecting show animals and causing reduced growth in young stock.'
        },
        'Healthy': {
            'name': 'Healthy Animal',
            'description': 'No disease detected. The animal appears to be in good health based on the visual assessment.',
            'symptoms': [
                'Normal body temperature',
                'Good appetite and normal water consumption',
                'Alert and responsive behavior',
                'Smooth coat with good shine',
                'Clear eyes without discharge',
                'Normal breathing pattern',
                'Regular rumination (in ruminants)',
                'Normal mobility'
            ],
            'prevention': [
                'Regular veterinary check-ups',
                'Proper nutrition and clean water',
                'Adequate housing with proper ventilation',
                'Regular vaccination according to schedule',
                'Parasite control',
                'Good biosecurity measures',
                'Proper waste management'
            ],
            'maintenance': 'To maintain good health:',
            'maintenance_options': [
                'Balanced diet appropriate for species, age, and production status',
                'Clean, fresh water available at all times',
                'Regular exercise and access to pasture when appropriate',
                'Stress reduction',
                'Regular monitoring for early disease detection',
                'Proper hoof/foot care',
                'Appropriate grooming'
            ],
            'severity': 'None',
            'zoonotic': 'Not applicable',
            'economic_impact': 'Positive - healthy animals have optimal production and require fewer interventions.'
        }
    }
    
    # Get information for the requested disease or return default message
    disease_data = disease_info.get(disease, {
        'name': disease,
        'description': 'Detailed information about this disease is not available in our database.',
        'symptoms': ['Information not available'],
        'prevention': ['Information not available'],
        'treatment': 'Information not available',
        'treatment_options': ['Consult a veterinarian for proper diagnosis and treatment'],
        'severity': 'Unknown',
        'zoonotic': 'Unknown',
        'economic_impact': 'Unknown'
    })
    
    return render_template('disease_info.html', disease=disease_data)

@health_bp.route('/health/recommendations/<animal_type>', methods=['GET'])
def animal_recommendations(animal_type):
    """Get food recommendations for a specific animal type"""
    recommendations = {
        'cow': [
            { 'name': 'Maize Silage', 'image': '/static/img/feed/maize_silage.jpg' },
            { 'name': 'Soybean Meal', 'image': '/static/img/feed/soybean_meal.jpg' },
            { 'name': 'Wheat Bran', 'image': '/static/img/feed/wheat_bran.jpg' },
            { 'name': 'Alfalfa Hay', 'image': '/static/img/feed/alfalfa_hay.jpg' }
        ],
        'goat': [
            { 'name': 'Grass', 'image': '/static/img/feed/grass.jpg' },
            { 'name': 'Legume Hay', 'image': '/static/img/feed/legume_hay.jpg' },
            { 'name': 'Barley', 'image': '/static/img/feed/barley.jpg' },
            { 'name': 'Mineral Mix', 'image': '/static/img/feed/mineral_mix.jpg' }
        ],
        'sheep': [
            { 'name': 'Pasture Grass', 'image': '/static/img/feed/pasture_grass.jpg' },
            { 'name': 'Alfalfa', 'image': '/static/img/feed/alfalfa.jpg' },
            { 'name': 'Grain Mix', 'image': '/static/img/feed/grain_mix.jpg' },
            { 'name': 'Mineral Block', 'image': '/static/img/feed/mineral_block.jpg' }
        ],
        'chicken': [
            { 'name': 'Corn', 'image': '/static/img/feed/corn.jpg' },
            { 'name': 'Soybean Meal', 'image': '/static/img/feed/soybean_meal.jpg' },
            { 'name': 'Wheat', 'image': '/static/img/feed/wheat.jpg' },
            { 'name': 'Fish Meal', 'image': '/static/img/feed/fish_meal.jpg' }
        ]
    }
    
    # Default to cow if animal type not found
    if animal_type not in recommendations:
        animal_type = 'cow'
    
    return jsonify({
        'recommendations': recommendations[animal_type]
    })

@health_bp.route('/health/analyze', methods=['POST'])
def health_analyze():
    """Analyze uploaded image for animal health (new endpoint)"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file uploaded'
            }), 400
        
        file = request.files['image']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed'
            }), 400
        
        # Get animal type - accept both parameter names for compatibility
        animal_type = request.form.get('animal_type', request.form.get('animalType', 'cow'))
        
        # Create temporary uploads directory if it doesn't exist
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'health'), exist_ok=True)
        
        # Save the uploaded file with a unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, 'health', unique_filename)
        file.save(filepath)
        
        try:
            # Analyze the image
            result = predict_disease(filepath)
            
            # Format confidence score to ensure it's a proper percentage
            confidence = min(result['confidence'] * 100, 100)
            
            # Generate recommendations based on the predicted disease
            recommendations = []
            disease = result['disease']
            
            if disease == 'Healthy':
                recommendations.append('No treatment needed. Continue regular preventive care including vaccinations against common diseases.')
            elif disease == 'Lumpy Skin Disease':
                recommendations.append('Lumpy Skin Disease vaccine and antibiotics for secondary infections. Isolate affected animal.')
            elif disease == 'Pinkeye':
                recommendations.append('Apply antibiotic eye ointment. Keep animal in shade and separate from herd.')
            elif disease == 'Ringworm':
                recommendations.append('Apply topical antifungal treatment. Disinfect environment. Monitor other animals.')
            elif disease == 'Mastitis':
                recommendations.append('Antibiotic treatment and frequent milking of affected quarters. Maintain good hygiene.')
            
            # Format for both old and new endpoints
            conditions = []
            conditions.append({
                'name': disease,
                'confidence': round(confidence, 1),
                'description': get_disease_description(disease)
            })
            
            # Include other predictions if available
            formatted_predictions = []
            if 'top_predictions' in result:
                for pred_disease, pred_conf in result.get('top_predictions', []):
                    pred_conf_pct = pred_conf * 100 if pred_conf <= 1.0 else pred_conf
                    formatted_predictions.append({
                        'disease': pred_disease,
                        'confidence': f"{min(pred_conf_pct, 100):.1f}%"
                    })
            
            # Get vaccine information for the predicted disease
            vaccine_info = get_vaccines_for_disease(disease)
            
            # Create a response that works with both old and new frontend code
            response_data = {
                'success': True,
                'disease': disease,  # For old endpoint
                'confidence': f"{confidence:.1f}%",  # For old endpoint
                'conditions': conditions,  # For new endpoint
                'recommendations': recommendations,
                'predictions': formatted_predictions,
                'detected_features': result.get('detected_features', []),
                'vaccine': vaccine_info  # Include vaccine information in response
            }
            
            print(f"DEBUG - Unified response: {response_data}")
            
            # Save the result image if available
            if 'output_image_path' in result:
                response_data['result_image'] = result['output_image_path']
            
            # Return formatted results
            return jsonify(response_data)
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error analyzing image: {str(e)}")
            return jsonify({
                'error': f'Error analyzing image: {str(e)}'
            }), 500
        finally:
            # Clean up file after analysis if needed
            try:
                if os.path.exists(filepath) and filepath.startswith(UPLOAD_FOLDER):
                    os.remove(filepath)
            except Exception as cleanup_error:
                print(f"Error cleaning up file: {str(cleanup_error)}")
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

@health_bp.route('/breed/analyze', methods=['POST'])
def breed_analyze():
    """Analyze uploaded image for breed identification (new endpoint)"""
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file uploaded'
            }), 400
        
        file = request.files['image']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'error': 'No file selected'
            }), 400
        
        # Check if file type is allowed
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed'
            }), 400
        
        # Get animal type
        animal_type = request.form.get('animal_type', 'cow')
        
        # Create upload directory if it doesn't exist
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'breed'), exist_ok=True)
        
        # Save the uploaded file with a unique name
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, 'breed', unique_filename)
        file.save(filepath)
        
        try:
            # Analyze the image
            result = predict_breed(filepath)
            
            # Format for the new endpoint
            breed = result.get('breed')
            confidence = result.get('confidence', 0) * 100
            
            # Format other possibilities
            other_possibilities = []
            for breed_name, breed_conf in result.get('top_predictions', [])[1:]:  # Skip the top one
                if breed_conf > 5:  # Only include predictions with >5% confidence
                    other_possibilities.append({
                        'name': breed_name,
                        'confidence': round(breed_conf * 100, 1)
                    })
            
            # Save the result image if available
            result_image_path = None
            if 'output_image_path' in result:
                result_image_path = result['output_image_path']
            
            # Return formatted results
            return jsonify({
                'success': True,
                'breed': breed,
                'confidence': round(confidence, 1),
                'other_possibilities': other_possibilities,
                'result_image': result_image_path
            })
            
        except Exception as e:
            # Log the error for debugging
            print(f"Error analyzing breed: {str(e)}")
            return jsonify({
                'error': f'Error analyzing breed: {str(e)}'
            }), 500
        
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

def get_disease_description(disease):
    """Get description for a disease"""
    descriptions = {
        'Healthy': 'No signs of disease detected. The animal appears to be in good health based on visual assessment.',
        'Lumpy Skin Disease': 'A viral disease characterized by fever and nodules on the skin and mucous membranes. Spread by biting insects.',
        'Mastitis': 'Inflammation of the mammary gland and udder tissue, usually due to bacterial infection. Common in dairy animals.',
        'Pinkeye': 'Infectious eye disease causing inflammation of the cornea and conjunctiva. Highly contagious among cattle.',
        'Ringworm': 'A fungal infection affecting the skin, characterized by circular lesions and hair loss. Can spread to other animals and humans.'
    }
    return descriptions.get(disease, 'No description available.')

@health_bp.route('/api/nearby-vets', methods=['GET'])
def nearby_vets():
    """API endpoint to get nearby veterinary services."""
    print("Accessed /api/nearby-vets API")
    
    # Get current user and their farm information
    user_id = session.get('user_id')
    print(f"Session user_id: {user_id}")
    
    # Explicit detailed logging for debugging
    if not user_id:
        print("ERROR: No user_id in session")
        return jsonify({
            'error': 'User not logged in',
            'farm': {
                'latitude': 19.076, 
                'longitude': 72.877,
                'address': 'Default location (Mumbai)'
            },
            'vets': []
        }), 200  # Return 200 with default data for graceful degradation
    
    # Query the user and farm directly - avoid g object which might not be set correctly
    user = db.session.query(User).filter_by(id=user_id).first()
    print(f"User query result: {user}")
    
    if not user:
        print(f"ERROR: User with ID {user_id} not found in database")
        return jsonify({
            'error': 'User not found in database',
            'farm': {
                'latitude': 19.076, 
                'longitude': 72.877,
                'address': 'Default location (Mumbai)'
            },
            'vets': []
        }), 200  # Return 200 with default data for graceful degradation
    
    # Now get the farm information
    farm = db.session.query(Farm).filter_by(user_id=user_id).first()
    print(f"Farm query result: {farm}")
    
    # Default coordinates (Mumbai)
    default_lat = 19.076
    default_lon = 72.877
    
    # If farm information is available, use it
    if farm and farm.latitude and farm.longitude:
        lat = float(farm.latitude)
        lon = float(farm.longitude)
        print(f"Using farm coordinates: lat={lat}, lon={lon}")
        farm_address = farm.address or "Your farm"
    else:
        print(f"WARNING: No farm coordinates available for user {user_id}, using defaults")
        lat = default_lat
        lon = default_lon
        farm_address = "Default location (Mumbai)"
    
    try:
        # Get nearby vets using Open Street Map (Nominatim)
        radius = 10000  # 10km radius
        overpass_url = "http://overpass-api.de/api/interpreter"
        overpass_query = f"""
        [out:json];
        node["amenity"="veterinary"](around:{radius},{lat},{lon});
        out body;
        """
        
        response = requests.post(overpass_url, data={"data": overpass_query})
        print(f"Overpass API response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: Overpass API returned {response.status_code}")
            vet_list = []
        else:
            data = response.json()
            vet_list = []
            
            for element in data.get('elements', []):
                vet_lat = element.get('lat')
                vet_lon = element.get('lon')
                vet_tags = element.get('tags', {})
                
                # Calculate distance from farm
                distance = haversine(lon, lat, vet_lon, vet_lat)
                
                vet_list.append({
                    'name': vet_tags.get('name', 'Unnamed Veterinary Clinic'),
                    'latitude': vet_lat,
                    'longitude': vet_lon,
                    'address': vet_tags.get('addr:full', 
                               vet_tags.get('addr:street', '') + ' ' + 
                               vet_tags.get('addr:city', '')).strip() or 'Address not available',
                    'phone': vet_tags.get('phone', 'Phone not available'),
                    'distance': round(distance, 2)
                })
            
            # Sort by distance
            vet_list.sort(key=lambda x: x['distance'])
        
        print(f"Found {len(vet_list)} veterinary services")
        
        # Return both farm and vet data
        return jsonify({
            'farm': {
                'latitude': lat,
                'longitude': lon,
                'address': farm_address
            },
            'vets': vet_list
        })
        
    except Exception as e:
        print(f"ERROR in nearby_vets API: {str(e)}")
        traceback.print_exc()
        
        # Return error with default location
        return jsonify({
            'error': str(e),
            'farm': {
                'latitude': default_lat,
                'longitude': default_lon,
                'address': 'Default location (Error occurred)'
            },
            'vets': []
        }), 200  # Return 200 with default data for graceful degradation

# Function to calculate distance between two geographical coordinates
def haversine(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
    
    # Haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371 * c
    return km