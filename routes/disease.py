from flask import Blueprint, render_template, request, jsonify, url_for, redirect
import os
from werkzeug.utils import secure_filename
from disease_predict import predict_disease
from utils.vaccine_data import get_vaccines_for_disease

disease_bp = Blueprint('disease', __name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'disease'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@disease_bp.route('/disease')
def disease_page():
    """Redirect to the disease alerts page"""
    return redirect(url_for('disease_alerts.index'))

@disease_bp.route('/disease/predict', methods=['POST'])
def predict():
    """Handle disease prediction request"""
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
        
        # Get animal type (default to cow)
        animal_type = request.form.get('animalType', 'cow')
        
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, 'disease', filename)
        file.save(filepath)
        
        # Check if the image is valid (not corrupted)
        try:
            with open(filepath, 'rb') as f:
                img_data = f.read()
                if img_data.startswith(b'\x00'):
                    return jsonify({
                        'error': 'Uploaded image is corrupted or contains null bytes',
                        'status': 'error'
                    }), 400
        except Exception:
            return jsonify({
                'error': 'Unable to read the uploaded image',
                'status': 'error'
            }), 400
        
        # Analyze the image with our implementation that now includes animal verification
        try:
            result = predict_disease(
                filepath, 
                animal_type=animal_type,
                auto_create_minimal=True
            )
        except ValueError as e:
            return jsonify({
                'error': str(e),
                'image_url': url_for('static', filename=f'uploads/disease/{filename}'),
                'status': 'error'
            }), 400
        
        # Check if the image contains the claimed animal type
        if not result.get('animal_verified', False):
            # Get the detected animal if available
            detected_animal = result.get('detected_animal', 'different animal')
            
            return jsonify({
                'error': f'This does not appear to be a {animal_type}. We detected {detected_animal} instead.',
                'image_url': url_for('static', filename=f'uploads/disease/{filename}'),
                'status': 'error',
                'animal_mismatch': True,
                'detected_animal': detected_animal
            }), 400
        
        # Get vaccine information for the predicted disease
        vaccine_info = get_vaccines_for_disease(result['disease'])
        
        # Format confidence scores for template
        formatted_predictions = []
        for prediction in result['all_predictions']:
            formatted_predictions.append({
                'disease': prediction['disease'],
                'confidence': f"{prediction['confidence']:.1f}%"
            })
        
        # Format the result for the template
        template_data = {
            'disease': result['disease'],
            'confidence': f"{result['confidence']:.1f}%",
            'confidence_value': result['confidence'],
            'image_url': url_for('static', filename=f'uploads/disease/{filename}'),
            'status': 'success',
            'features': result.get('detected_features', []),
            'top_predictions': formatted_predictions,
            'recommendations': result.get('recommendations', []),
            'animal_type': animal_type,
            'vaccine': vaccine_info
        }
        
        return jsonify(template_data)
        
    except Exception as e:
        print("Error in disease prediction:")
        print(str(e))
        return jsonify({
            'error': f"Error analyzing the image: {str(e)}",
            'status': 'error'
        }), 500

def get_disease_info(disease, animal_type='cow'):
    """Get detailed information about a disease"""
    
    # Common disease information for all animals
    common_info = {
        'Healthy': 'No disease detected. The animal appears to be in good health.',
    }
    
    # Cow-specific disease information
    cow_disease_info = {
        'Lumpy Skin Disease': 'A viral disease characterized by fever and multiple nodules on the skin. Requires immediate veterinary attention.',
        'Mastitis': 'An inflammation of the udder tissue, usually caused by bacterial infection. Common in dairy animals.',
        'Foot and Mouth Disease': 'A highly contagious viral disease affecting cloven-hoofed animals. Causes fever and blisters on the mouth and feet.',
        'Ringworm': 'A fungal infection causing circular patches of hair loss and scaly skin. Contagious to other animals and humans.',
        'Theileriosis': 'A tick-borne disease caused by Theileria parasites. Symptoms include high fever, enlarged lymph nodes, and anemia.'
    }
    
    # Goat-specific disease information
    goat_disease_info = {
        'CCPP': 'Contagious Caprine Pleuropneumonia - A highly contagious respiratory disease in goats with high mortality rate.',
        'Orf': 'A viral skin disease that causes scabs and lesions, usually around the mouth. Can be transmitted to humans.',
        'Mastitis': 'Inflammation of the udder tissue, causing reduced milk production and altered milk quality.',
        'Foot Rot': 'A bacterial infection causing lameness, typically occurs in wet conditions.',
        'Enterotoxemia': 'Also known as "overeating disease," caused by Clostridium perfringens. Often affects well-fed animals.'
    }
    
    # Chicken-specific disease information
    chicken_disease_info = {
        'Newcastle Disease': 'A highly contagious viral infection affecting respiratory, nervous, and digestive systems.',
        'Avian Pox': 'A viral disease causing wartlike skin lesions on unfeathered parts of the body.',
        'Infectious Coryza': 'A bacterial disease causing swelling of the face, nasal discharge, and reduced egg production.',
        'Fowl Cholera': 'A bacterial disease causing sudden deaths, respiratory issues, and diarrhea.',
        'Coccidiosis': 'A parasitic disease affecting the intestinal tract, common in young birds.'
    }
    
    # Select the appropriate disease information based on animal type
    if animal_type == 'cow':
        disease_info = {**common_info, **cow_disease_info}
    elif animal_type == 'goat':
        disease_info = {**common_info, **goat_disease_info}
    elif animal_type == 'chicken':
        disease_info = {**common_info, **chicken_disease_info}
    else:
        disease_info = common_info
    
    return disease_info.get(disease, 'Information not available for this condition.')

# Add other disease-related routes here