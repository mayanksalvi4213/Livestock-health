from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file
import os
import uuid
import shutil
import traceback
from werkzeug.utils import secure_filename
import json
import numpy as np
from PIL import Image
from datetime import datetime
import pdfkit  # For PDF generation

# Import both predictors with error handling
from simple_breed_predictor import predict_breed as simple_predict_breed, get_breed_characteristics

# Try to import the ML-based predictor, but don't fail if it's not available
try:
    from breed_predict import predict_breed as ml_predict_breed
    HAVE_ML_PREDICTOR = True
    print("TensorFlow ML-based breed predictor available")
except ImportError:
    HAVE_ML_PREDICTOR = False
    print("TensorFlow-based breed predictor not available, will use simple predictor only")

breed_bp = Blueprint('breed', __name__, url_prefix='/breed')

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.join(UPLOAD_FOLDER, 'breed'), exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@breed_bp.route('/', methods=['GET'])
def breed_form():
    return render_template('breed.html')

@breed_bp.route('/predict', methods=['POST'])
def predict():
    """Handle breed identification request"""
    temp_filepath = None
    try:
        # Check if image was uploaded
        if 'image' not in request.files:
            return jsonify({
                'error': 'No image file uploaded',
                'status': 'error'
            }), 400
        
        file = request.files['image']
        
        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'error': 'No file selected',
                'status': 'error'
            }), 400
            
        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'Invalid file type. Please upload an image (jpg, jpeg, png, gif).',
                'status': 'error'
            }), 400
        
        # Get animal type from form
        animal_type = request.form.get('animalType', 'cow').lower()
        print(f"DEBUG: Processing {animal_type} breed detection")
        
        # Generate a unique filename to avoid collisions
        unique_filename = f"{uuid.uuid4()}_{secure_filename(file.filename)}"
        filepath = os.path.join(UPLOAD_FOLDER, 'breed', unique_filename)
        temp_filepath = filepath  # Store the filepath for cleanup in case of errors
        
        # Save the uploaded file
        file.save(filepath)
        print(f"DEBUG: Saved file to {filepath}")
        
        try:
            # First try using the ML model if available
            prediction_method = 'rule-based'
            if HAVE_ML_PREDICTOR:
                try:
                    print(f"DEBUG: ML predictor is available, attempting ML prediction for {animal_type} breed")
                    prediction_result = ml_predict_breed(filepath, animal_type, auto_create_minimal=True)
                    prediction_method = 'tensorflow'
                    print(f"DEBUG: Successfully used ML model for {animal_type} breed prediction")
                    print(f"DEBUG: Prediction result: {prediction_result}")
                except Exception as ml_error:
                    print(f"DEBUG: ML prediction failed with error: {str(ml_error)}")
                    print(f"DEBUG: Full ML error traceback:")
                    traceback.print_exc()
                    print(f"DEBUG: Falling back to simple predictor")
                    prediction_result = simple_predict_breed(filepath, animal_type)
            else:
                print("DEBUG: ML predictor not available, using simple predictor")
                # Use simple predictor if ML is not available
                prediction_result = simple_predict_breed(filepath, animal_type)
            
            # Format confidence for display
            confidence_value = prediction_result['confidence']
            confidence_display = f"{confidence_value:.1f}%"
            
            # Prepare result for the template
            template_data = {
                'breed': prediction_result['breed'],
                'confidence': confidence_display,
                'confidence_value': confidence_value,
                'image_url': url_for('static', filename=f'uploads/breed/{unique_filename}'),
                'status': 'success',
                'features': prediction_result.get('physical_features', {}),
                'characteristics': prediction_result.get('characteristics', {}),
                'all_predictions': prediction_result['all_predictions'],
                'detected_features': prediction_result.get('physical_features', {}),
                'breed_characteristics': prediction_result.get('characteristics', {}),
                'animal_type': animal_type,
                'is_minimal_prediction': prediction_result.get('is_minimal_prediction', False),
                'prediction_method': prediction_method
            }
            
            print(f"DEBUG: Returning successful prediction: {template_data}")
            temp_filepath = None  # Don't delete the file on success
            return jsonify(template_data)
                        
        except Exception as e:
            print("Error in breed prediction:", str(e))
            traceback.print_exc()  # Print the full stack trace
            return jsonify({
                'error': f'Error analyzing the image: {str(e)}',
                'status': 'error'
            }), 500
        
    except Exception as e:
        print("Error in breed prediction endpoint:", str(e))
        print(traceback.format_exc())  # Print full traceback for debugging
        return jsonify({
            'error': f"Error analyzing the image: {str(e)}",
            'status': 'error'
        }), 500
    finally:
        # Only clean up the file if there was an error
        if temp_filepath and os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception as e:
                print(f"Error cleaning up file {temp_filepath}: {str(e)}")

@breed_bp.route('/')
def index():
    """Render the breed identification page"""
    return render_template('breed/index.html', 
                          result=None,
                          error=None,
                          all_predictions=[],
                          prediction_details={}) 

@breed_bp.route('/result')
def result():
    """Display the breed prediction result"""
    try:
        # Get the parameters from the query string
        breed = request.args.get('breed', '')
        confidence = request.args.get('confidence', '0%')
        animal_type = request.args.get('animal_type', 'cow')
        image_url = request.args.get('image_url', '')
        is_minimal = request.args.get('is_minimal', 'false').lower() == 'true'
        prediction_method = request.args.get('prediction_method', 'tensorflow')
        
        # Parse the JSON strings
        characteristics = json.loads(request.args.get('characteristics', '{}'))
        all_predictions = json.loads(request.args.get('all_predictions', '[]'))
        
        return render_template('breed_result.html',
                              result={
                                  'breed': breed,
                                  'confidence': confidence,
                                  'animal_type': animal_type,
                                  'image_url': image_url,
                                  'is_minimal_prediction': is_minimal,
                                  'prediction_method': prediction_method,
                                  'breed_characteristics': characteristics,
                                  'all_predictions': all_predictions,
                                  'detected_features': {}
                              })
    except Exception as e:
        print(f"Error displaying breed result: {str(e)}")
        return render_template('error.html', 
                              error_code=500, 
                              error_message="Error displaying breed result",
                              error_details=str(e) if os.environ.get('FLASK_ENV') == 'development' else None) 

@breed_bp.route('/save_results', methods=['POST'])
def save_results():
    """Save the breed prediction results as an HTML file with option for PDF if available"""
    try:
        data = request.json
        
        # Create a unique filename for the report
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_filename = f"breed_prediction_{timestamp}.html"
        html_output_path = os.path.join(UPLOAD_FOLDER, 'reports', html_filename)
        
        # Ensure reports directory exists
        os.makedirs(os.path.join(UPLOAD_FOLDER, 'reports'), exist_ok=True)
        
        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Breed Identification Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; color: #333; }}
                .header {{ text-align: center; padding: 20px; background-color: #157347; color: white; margin-bottom: 20px; border-radius: 5px; }}
                .result-section {{ margin: 20px 0; background-color: #f9f9f9; padding: 15px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .characteristics {{ margin-left: 20px; }}
                img {{ max-width: 100%; height: auto; margin: 20px auto; display: block; max-height: 400px; border-radius: 5px; }}
                h1, h2, h3 {{ color: #157347; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 0.8em; color: #777; }}
                table {{ width: 100%; border-collapse: collapse; }}
                td, th {{ padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                @media print {{
                    .no-print {{ display: none; }}
                    body {{ padding: 0; }}
                    .header {{ background-color: #f9f9f9 !important; color: #333 !important; }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Breed Identification Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="result-section">
                <h2>Identification Result</h2>
                <table>
                    <tr>
                        <th>Breed:</th>
                        <td>{data['breed']}</td>
                    </tr>
                    <tr>
                        <th>Confidence:</th>
                        <td>{data['confidence']}</td>
                    </tr>
                    <tr>
                        <th>Animal Type:</th>
                        <td>{data['animal_type'].capitalize()}</td>
                    </tr>
                </table>
            </div>
            
            <div class="result-section">
                <h2>Breed Characteristics</h2>
                <table>
        """
        
        # Add characteristics
        for key, value in data['characteristics'].items():
            if key != 'note':  # Skip notes
                html_content += f"""
                    <tr>
                        <th>{key.replace('_', ' ').title()}:</th>
                        <td>{value}</td>
                    </tr>
                """
        
        html_content += """
                </table>
            </div>
            
            <div class="footer">
                <p>© AgriHealth Livestock Identification System</p>
                <p>This report was automatically generated. For more information, please visit our website.</p>
            </div>
            
            <script class="no-print">
                // Auto-print when loaded
                window.onload = function() {
                    // Add a print button
                    var printBtn = document.createElement('button');
                    printBtn.innerHTML = 'Print Report';
                    printBtn.style.display = 'block';
                    printBtn.style.margin = '20px auto';
                    printBtn.style.padding = '10px 15px';
                    printBtn.style.backgroundColor = '#157347';
                    printBtn.style.color = 'white';
                    printBtn.style.border = 'none';
                    printBtn.style.borderRadius = '5px';
                    printBtn.style.cursor = 'pointer';
                    printBtn.onclick = function() { window.print(); };
                    
                    document.body.insertBefore(printBtn, document.querySelector('.footer'));
                }
            </script>
        </body>
        </html>
        """
        
        # Save HTML file
        with open(html_output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Try to generate PDF with pdfkit if available
        try:
            import pdfkit
            pdf_filename = f"breed_prediction_{timestamp}.pdf"
            pdf_output_path = os.path.join(UPLOAD_FOLDER, 'reports', pdf_filename)
            
            # Set configuration with found wkhtmltopdf path or default
            try:
                import subprocess
                wkhtmltopdf_path = subprocess.run(["where", "wkhtmltopdf"], 
                                                capture_output=True, 
                                                text=True, 
                                                check=False).stdout.strip()
                if not wkhtmltopdf_path:
                    wkhtmltopdf_path = r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"  # Default Windows path
                
                config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
                pdfkit.from_file(html_output_path, pdf_output_path, configuration=config)
                
                # Return the PDF file URL
                return jsonify({
                    'status': 'success',
                    'file_url': url_for('static', filename=f'uploads/reports/{pdf_filename}'),
                    'file_type': 'pdf',
                    'message': 'Results saved as PDF'
                })
            except Exception as pdf_error:
                print(f"PDF generation failed: {str(pdf_error)}")
                # Return the HTML file URL as fallback
                return jsonify({
                    'status': 'success',
                    'file_url': url_for('static', filename=f'uploads/reports/{html_filename}'),
                    'file_type': 'html',
                    'message': 'Results saved as HTML (PDF generation failed)'
                })
                
        except ImportError as e:
            print(f"pdfkit not available: {str(e)}")
            # Return the HTML file URL
            return jsonify({
                'status': 'success',
                'file_url': url_for('static', filename=f'uploads/reports/{html_filename}'),
                'file_type': 'html',
                'message': 'Results saved as HTML'
            })
        
    except Exception as e:
        print(f"Error saving results: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': 'Failed to save results'
        }), 500

@breed_bp.route('/more_info/<animal_type>/<breed>', methods=['GET'])
def more_info(animal_type, breed):
    """Get detailed information about a specific breed"""
    try:
        # Additional breed information including history, characteristics, and care tips
        additional_info = {
            'cow': {
                'jersey': {
                    'history': 'The Jersey breed originated on the British Channel Island of Jersey. Despite the small size of the breed, Jerseys are known for their high milk production and high butterfat content.',
                    'physical_traits': [
                        'Small to medium-sized breed',
                        'Fawn-colored coat that can vary from light tan to dark brown',
                        'Large, dark eyes',
                        'Dish-shaped face',
                        'Black nose with light-colored muzzle'
                    ],
                    'advantages': [
                        'Highest butterfat content among all breeds',
                        'Excellent feed conversion efficiency',
                        'Heat tolerant',
                        'Early maturity'
                    ],
                    'care_tips': [
                        'Regular hoof trimming required',
                        'Need balanced nutrition for high milk production',
                        'Regular veterinary check-ups recommended',
                        'Protect from extreme weather conditions'
                    ],
                    'resources': [
                        {'name': 'World Jersey Cattle Bureau', 'url': 'http://www.worldjerseycattle.com/'},
                        {'name': 'American Jersey Cattle Association', 'url': 'https://www.usjersey.com/'}
                    ]
                },
                'gir cow': {
                    'history': 'The Gir breed originated in the Gir forests of Gujarat, India. Known for its distinctive curved horns and gentle temperament.',
                    'physical_traits': [
                        'Distinctive curved horns',
                        'Pendulous ears',
                        'Red or spotted white coat',
                        'Gentle temperament',
                        'Strong build'
                    ],
                    'advantages': [
                        'Heat and disease resistant',
                        'Good milk production',
                        'Adaptable to various climates',
                        'Docile nature'
                    ],
                    'care_tips': [
                        'Regular grooming needed',
                        'Balanced diet essential',
                        'Adequate shade required',
                        'Regular health check-ups'
                    ],
                    'resources': [
                        {'name': 'Indian Council of Agricultural Research', 'url': 'https://www.icar.org.in/'},
                        {'name': 'Gir Cattle Breeding', 'url': '#'}
                    ]
                }
            },
            'goat': {
                'beetal': {
                    'history': 'The Beetal is a prominent dual-purpose breed from Punjab, known for its milk and meat production.',
                    'physical_traits': [
                        'Large, pendulous ears',
                        'Roman nose',
                        'Long legs',
                        'Brown coat with white spots'
                    ],
                    'advantages': [
                        'High milk yield',
                        'Good meat quality',
                        'Adaptable to various climates',
                        'Early maturity'
                    ],
                    'care_tips': [
                        'Regular deworming',
                        'Balanced feed supplementation',
                        'Clean housing',
                        'Regular health monitoring'
                    ],
                    'resources': [
                        {'name': 'Small Ruminant Info', 'url': '#'},
                        {'name': 'Goat Farming Guide', 'url': '#'}
                    ]
                }
            }
        }
        
        # Get breed info or return default info if breed not found
        animal_info = additional_info.get(animal_type.lower(), {})
        breed_info = animal_info.get(breed.lower(), {
            'history': f'Detailed history for {breed} breed of {animal_type}.',
            'physical_traits': ['Characteristic traits not available'],
            'advantages': ['Breed advantages not documented'],
            'care_tips': ['General care guidelines apply'],
            'resources': [{'name': 'General Resources', 'url': '#'}]
        })
        
        return jsonify({
            'status': 'success',
            'data': breed_info
        })
        
    except Exception as e:
        print(f"Error getting more info: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'error': 'Failed to get additional information'
        }), 500 