import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
import matplotlib.pyplot as plt
import cv2

# Constants
IMG_SIZE = (224, 224)
MODELS_DIR = 'models'

def preprocess_image(img_path):
    """Preprocess the image for model prediction"""
    try:
        # First check if file exists and is not empty
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            raise ValueError("Image file does not exist or is empty")
        
        # Use PIL to open and validate the image
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
                # Check for null bytes at the beginning of the file
                if img_data.startswith(b'\x00'):
                    # Handle corrupt image
                    raise ValueError("Image file contains null bytes")
            
            img = Image.open(img_path).convert('RGB')
            img = img.resize(IMG_SIZE)
            img_array = image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = img_array / 255.0  # Normalize to [0,1]
            return img_array
        except (IOError, OSError) as e:
            raise ValueError(f"Could not open or process image: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error preprocessing image: {str(e)}")

def load_class_names(animal_type):
    """Load class names (diseases) for the specified animal type"""
    class_indices_path = os.path.join(MODELS_DIR, f"{animal_type}_diseases_classes.npy")
    
    if not os.path.exists(class_indices_path):
        raise FileNotFoundError(f"No model found for {animal_type} disease detection. Please train the model first.")
    
    # Load class indices (a dictionary mapping class names to indices)
    class_indices = np.load(class_indices_path, allow_pickle=True).item()
    
    # Invert the dictionary to map indices to class names
    class_names = {v: k for k, v in class_indices.items()}
    
    return class_names

def analyze_image_features(img_path, disease):
    """Analyze image for specific features related to the detected disease"""
    # Basic feature detection based on the disease
    try:
        # First check if file exists and is not empty
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            return []
        
        # Validate the image file
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
                # Check for null bytes at the beginning of the file
                if img_data.startswith(b'\x00'):
                    return []  # Skip feature analysis for corrupt images
            
            img = cv2.imread(img_path)
            if img is None:
                return []
            
            features = []
            
            # Convert to different color spaces for analysis
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            
            # Detect features based on disease
            disease_lower = disease.lower()
            
            if "ringworm" in disease_lower:
                # Look for circular patterns - Hough Circle Detection
                circles = cv2.HoughCircles(
                    gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=100,
                    param1=50, param2=30, minRadius=10, maxRadius=100
                )
                
                if circles is not None:
                    features.append("circular lesions")
                    features.append("defined borders")
            
            if "mastitis" in disease_lower:
                # Look for redness - using HSV color space
                red_mask = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
                red_ratio = np.sum(red_mask > 0) / (red_mask.shape[0] * red_mask.shape[1])
                
                if red_ratio > 0.1:  # If more than 10% of the image has red tones
                    features.append("inflammation")
                    features.append("redness")
            
            if "lumpy" in disease_lower:
                # Edge detection for lumps
                edges = cv2.Canny(gray, 50, 150)
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                if len(contours) > 10:  # If many contours detected
                    features.append("raised nodules")
                    features.append("skin lesions")
            
            if "pinkeye" in disease_lower:
                # Check for pink/red coloration in HSV
                pink_mask = cv2.inRange(hsv, (145, 50, 50), (175, 255, 255))
                pink_ratio = np.sum(pink_mask > 0) / (pink_mask.shape[0] * pink_mask.shape[1])
                
                if pink_ratio > 0.05:
                    features.append("eye redness")
                    features.append("inflammation around eye")
            
            # Generic features for other diseases
            if not features and "healthy" not in disease_lower:
                # Apply basic texture analysis
                texture_variance = np.var(gray)
                if texture_variance > 1000:  # High variance indicates irregular texture
                    features.append("irregular skin texture")
                
                # Basic color analysis
                color_variance = np.var(img, axis=(0, 1))
                if np.mean(color_variance) > 800:
                    features.append("abnormal coloration")
            
            return features
        except (IOError, OSError, cv2.error) as e:
            print(f"Warning: Could not process image for feature analysis: {str(e)}")
            return []
    
    except Exception as e:
        print(f"Warning: Could not analyze image features: {str(e)}")
        return []

def get_disease_recommendations(animal_type, disease):
    """Get comprehensive recommendations for treating specific diseases in animals, including medicinal and food recommendations"""
    
    # Dictionary of recommendations by animal type and disease
    recommendations = {
        "cow": {
            'healthy': [
                "No treatment required. Continue regular preventive care.",
                "Maintain regular deworming schedule every 3-4 months.",
                "Ensure vaccination against FMD, HS, and BQ as per schedule.",
                "DIET: Provide balanced diet with 60% dry fodder, 30% green fodder, and 10% concentrate.",
                "DIET: Include mineral mixture (100-150g daily) containing calcium and phosphorus.",
                "DIET: Feed locally available green fodder like berseem, oats, or napier grass."
            ],
            'lumpy skin disease': [
                "MEDICINE: Administer antipyretics like Paracetamol (10-20mg/kg) for fever.",
                "MEDICINE: Apply Himax ointment or neem oil on skin nodules to prevent secondary infections.",
                "MEDICINE: Give antibiotics like Oxytetracycline (10mg/kg) for 5-7 days as prescribed by vet.",
                "Isolate affected animals to prevent spread through biting insects.",
                "DIET: Provide soft, easily digestible green fodder like berseem or lucerne.",
                "DIET: Add jaggery water (गुड़ का पानी) to improve palatability and provide energy.",
                "DIET: Include turmeric powder (1-2 teaspoons) in feed for immunity and inflammation."
            ],
            'foot and mouth disease': [
                "MEDICINE: Contact veterinarian immediately as this is a notifiable disease.",
                "MEDICINE: Apply 1% potassium permanganate solution to mouth lesions.",
                "MEDICINE: For foot lesions, apply 10% copper sulfate solution and bandage.",
                "Isolate affected animals to prevent spread to healthy animals.",
                "DIET: Offer soft, green fodder that's easy to chew due to painful mouth lesions.",
                "DIET: Provide liquid or semi-solid feed like rice gruel (कांजी) for easier consumption.",
                "DIET: Add crushed banana with jaggery to improve appetite and provide energy."
            ],
            'mastitis': [
                "MEDICINE: Consult vet for appropriate intramammary antibiotics.",
                "MEDICINE: Apply hot fomentation to affected udder 3-4 times daily.",
                "MEDICINE: Milk the affected quarters frequently and completely.",
                "MEDICINE: Apply Himax or Zeet ointment after milking to soothe the udder.",
                "DIET: Reduce concentrate feed temporarily to decrease milk production.",
                "DIET: Provide easily digestible green fodder rich in Vitamin A.",
                "DIET: Add turmeric powder (10-15g daily) for its anti-inflammatory effects."
            ],
            'ringworm': [
                "MEDICINE: Apply topical antifungal preparations like 1% Terbinafine.",
                "MEDICINE: Wash affected areas with Betadine solution before medication.",
                "MEDICINE: Apply neem oil mixed with turmeric powder on affected areas.",
                "Disinfect all equipment and housing to prevent spread to other animals.",
                "DIET: Increase protein content in diet through additional oil cakes.",
                "DIET: Include garlic (2-3 cloves daily) in feed as a natural antifungal.",
                "DIET: Add linseed oil (1-2 tablespoons) to daily feed for skin health."
            ]
        },
        "goat": {
            'healthy': [
                "No treatment required. Continue regular preventive care.",
                "Maintain regular deworming every 3 months.",
                "Schedule vaccinations for PPR, FMD, and enterotoxemia as recommended.",
                "DIET: Provide browse and forage that makes up 60-70% of diet.",
                "DIET: Supplement with 150-200g concentrate feed for adult goats.",
                "DIET: Feed tree fodder like Subabul (सुबबूल) which is high in protein."
            ],
            'peste des petits ruminants': [
                "MEDICINE: Contact veterinarian immediately - this is a notifiable disease.",
                "MEDICINE: Administer antibiotics as prescribed to prevent secondary infections.",
                "MEDICINE: Give antipyretics (Paracetamol at 10mg/kg) to reduce fever.",
                "Isolate affected animals to prevent spread within the herd.",
                "DIET: Provide soft, easily consumable feeds due to mouth sores.",
                "DIET: Offer liquid feeds like rice gruel mixed with jaggery.",
                "DIET: Add honey (5-10ml) in drinking water to soothe throat irritation."
            ],
            'mastitis': [
                "MEDICINE: Consult vet for appropriate antibiotic treatment.",
                "MEDICINE: Apply warm compresses to affected udder 4-5 times daily.",
                "MEDICINE: Empty affected udder completely multiple times daily.",
                "Prevent kids from nursing on affected udder temporarily.",
                "DIET: Reduce grain intake temporarily to decrease milk production.",
                "DIET: Add turmeric powder and honey to feed for anti-inflammatory effects.",
                "DIET: Include fenugreek seeds (मेथी) in feed to help udder health."
            ],
            'foot rot': [
                "MEDICINE: Trim affected hooves to remove dead and diseased tissue.",
                "MEDICINE: Apply 10% zinc sulfate or copper sulfate footbath daily for 5-7 days.",
                "MEDICINE: Administer injectable antibiotics as prescribed by vet for severe cases.",
                "Keep affected animals in dry, clean area with fresh bedding.",
                "DIET: Supplement with zinc (15-20mg/day) to support hoof health.",
                "DIET: Provide adequate protein through concentrated feeds for tissue repair.",
                "DIET: Include neem leaves in feed for their antimicrobial properties."
            ]
        },
        "chicken": {
            'healthy': [
                "No treatment needed. Continue regular preventive care.",
                "Maintain vaccination schedule for Newcastle disease, Gumboro, and fowl pox.",
                "Deworm every 3 months with appropriate dewormer as per body weight.",
                "DIET: Feed age-appropriate commercial feed or balanced homemade mix.",
                "DIET: For desi chickens, provide 50-60g feed per bird daily (16-18% protein).",
                "DIET: Add crushed eggshells or limestone for calcium, especially for layers."
            ],
            'newcastle disease': [
                "MEDICINE: Contact veterinarian immediately - this is a notifiable disease.",
                "MEDICINE: Administer antibiotics to prevent secondary infections as prescribed.",
                "MEDICINE: Provide vitamins A, E and C as supportive therapy.",
                "Isolate affected birds and disinfect housing with 2% formalin or phenol.",
                "DIET: Ensure easy access to water with added electrolytes and glucose.",
                "DIET: Provide soft, easily digestible feed like boiled rice with crushed pulses.",
                "DIET: Add turmeric powder (0.5g/liter of water) for anti-inflammatory effects."
            ],
            'fowl pox': [
                "MEDICINE: Apply glycerin or neem oil to lesions to prevent secondary infections.",
                "MEDICINE: Remove scabs gently and apply 2% iodine solution for faster healing.",
                "MEDICINE: Administer vitamins A and E to support immune function.",
                "Isolate affected birds to prevent spread through direct contact.",
                "DIET: Provide soft feed that's easy to consume with mouth lesions.",
                "DIET: Include crushed garlic in water for natural antimicrobial effect.",
                "DIET: Ensure clean, fresh water with added vitamin C (100mg/liter)."
            ],
            'infectious coryza': [
                "MEDICINE: Consult vet for antibiotics like Erythromycin or Oxytetracycline.",
                "MEDICINE: Apply VapoRub or camphor oil near nostrils to relieve congestion.",
                "MEDICINE: Disinfect waterers and feeders daily during outbreak.",
                "Isolate affected birds to prevent spread in the flock.",
                "DIET: Provide easily digestible feed with higher protein content.",
                "DIET: Add garlic and ginger paste to feed for natural antimicrobial effects.",
                "DIET: Include warm water with honey and lemon to soothe throat irritation."
            ]
        }
    }
    
    # Convert animal type and disease name to lowercase for case-insensitive lookup
    animal_key = animal_type.lower()
    disease_key = disease.lower()
    
    # Default recommendations if specific ones are not available
    default_recs = [
        "Consult a local veterinarian for proper diagnosis and treatment.",
        "Isolate affected animal to prevent potential disease spread.",
        "Monitor temperature, feed intake, and water consumption daily.",
        "DIET: Provide fresh, clean water at all times.",
        "DIET: Offer easily digestible, high-quality feed appropriate for the animal.",
        "DIET: Include turmeric powder in feed for its anti-inflammatory properties."
    ]
    
    # Get specific recommendations if available, otherwise return general recommendations
    if animal_key in recommendations:
        animal_recs = recommendations[animal_key]
        
        # Direct match for disease
        if disease_key in animal_recs:
            return animal_recs[disease_key]
        
        # Check for partial matches (e.g., if "foot rot" should match "foot and mouth")
        for key in animal_recs:
            if disease_key in key or key in disease_key:
                return animal_recs[key]
    
    return default_recs

def find_best_model(animal_type, category_type="diseases"):
    """Find the best available model with priority: improved > keras > h5"""
    # Check for improved model (best)
    improved_path = os.path.join(MODELS_DIR, f"{animal_type}_{category_type}_improved_model.keras")
    if os.path.exists(improved_path):
        print(f"Using improved model: {improved_path}")
        return improved_path
    
    # Check for regular .keras format (second best)
    keras_path = os.path.join(MODELS_DIR, f"{animal_type}_{category_type}_model.keras")
    if os.path.exists(keras_path):
        print(f"Using keras model: {keras_path}")
        return keras_path
    
    # Fall back to .h5 format (legacy)
    h5_path = os.path.join(MODELS_DIR, f"{animal_type}_{category_type}_model.h5")
    if os.path.exists(h5_path):
        print(f"Using legacy h5 model: {h5_path}")
        return h5_path
    
    # No model found
    return None

def verify_animal_type(img_path, claimed_animal_type):
    """
    Verify that the image contains the claimed animal type
    Returns tuple of (is_verified, confidence, detected_animal)
    """
    # Import tensorflow here to avoid loading it unnecessarily
    import tensorflow as tf
    from tensorflow.keras.applications.mobilenet_v2 import MobileNetV2, preprocess_input, decode_predictions
    
    try:
        # First check if file exists and is not empty
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            raise ValueError("Image file does not exist or is empty")
        
        # Validate the image file first
        try:
            with open(img_path, 'rb') as f:
                img_data = f.read()
                # Check for null bytes at the beginning of the file
                if img_data.startswith(b'\x00'):
                    # Handle corrupt image
                    raise ValueError("Image file contains null bytes")
            
            # Load a pre-trained model for general image classification
            model = MobileNetV2(weights='imagenet')
            
            # Preprocess the image for MobileNetV2
            img = tf.keras.preprocessing.image.load_img(img_path, target_size=(224, 224))
            img_array = tf.keras.preprocessing.image.img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0)
            img_array = preprocess_input(img_array)
            
            # Make prediction
            predictions = model.predict(img_array)
            decoded_predictions = decode_predictions(predictions, top=5)[0]
            
            # Map the claimed animal type to potential ImageNet classes
            animal_classes = {
                'cow': ['ox', 'water_buffalo', 'bison', 'bull', 'cow'],
                'goat': ['goat', 'ram', 'sheep', 'ibex', 'antelope'],
                'chicken': ['hen', 'cock', 'bird', 'drake', 'peacock', 'ostrich', 'quail'],
            }
            
            relevant_classes = animal_classes.get(claimed_animal_type.lower(), [])
            
            # Check if any of the top predictions match the relevant classes
            is_verified = False
            confidence = 0.0
            detected_animal = None
            
            for _, class_name, pred_confidence in decoded_predictions:
                # If any prediction matches our expected classes
                if any(animal_class in class_name.lower() for animal_class in relevant_classes):
                    is_verified = True
                    confidence = float(pred_confidence) * 100
                    detected_animal = class_name
                    break
            
            return is_verified, confidence, detected_animal
        except (IOError, OSError) as e:
            raise ValueError(f"Could not open or process image: {str(e)}")
    except Exception as e:
        print(f"Error in animal verification: {str(e)}")
        # If verification fails, assume it's unverified but let the process continue
        return False, 0.0, None

def predict_disease(img_path, animal_type, auto_create_minimal=False):
    """Predict the disease from an image"""
    if animal_type not in ['cow', 'goat', 'chicken']:
        raise ValueError(f"Unsupported animal type: {animal_type}. Must be one of: cow, goat, chicken")
    
    # First verify if the image contains the claimed animal type
    is_verified, animal_confidence, detected_animal = verify_animal_type(img_path, animal_type)
    
    # Find the best available model
    model_path = find_best_model(animal_type, "diseases")
    
    # Check if any model exists
    if not model_path:
        # Try to create a minimal model if requested
        if auto_create_minimal and os.path.exists("create_minimal_model.py"):
            import create_minimal_model
            print(f"Creating minimal {animal_type} disease model...")
            create_minimal_model.create_minimal_model(animal_type, "diseases")
            # Check if model was created
            model_path = find_best_model(animal_type, "diseases")
            if model_path:
                print(f"Minimal {animal_type} disease model created.")
            else:
                raise FileNotFoundError(f"No model found for {animal_type} disease detection. Please train the model first.")
        else:
            raise FileNotFoundError(f"No model found for {animal_type} disease detection. Please train the model first.")
    
    try:
        # Preprocess the image
        img_array = preprocess_image(img_path)
        
        # Load the model
        model = load_model(model_path)
        
        # Get class names
        class_names = load_class_names(animal_type)
        
        # Make prediction
        predictions = model.predict(img_array)[0]
        
        # Get top 3 predictions
        top_indices = predictions.argsort()[-3:][::-1]
        top_predictions = [{'disease': class_names[i], 'confidence': float(predictions[i]) * 100} for i in top_indices]
        
        # Get the top prediction
        top_disease_index = np.argmax(predictions)
        disease_name = class_names[top_disease_index]
        confidence = float(predictions[top_disease_index]) * 100
        
        # Analyze image for specific features related to the detected disease
        detected_features = analyze_image_features(img_path, disease_name)
        
        # Get treatment recommendations
        recommendations = get_disease_recommendations(animal_type, disease_name)
        
        # Prepare result
        result = {
            'disease': disease_name,
            'confidence': confidence,
            'all_predictions': top_predictions,
            'detected_features': detected_features,
            'recommendations': recommendations,
            'animal_verified': is_verified,
            'animal_confidence': animal_confidence,
            'detected_animal': detected_animal
        }
        
        return result
    
    except Exception as e:
        raise ValueError(f"Error predicting disease: {str(e)}")

if __name__ == "__main__":
    # For testing purposes
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python disease_predict.py <image_path> <animal_type>")
        sys.exit(1)
    
    img_path = sys.argv[1]
    animal_type = sys.argv[2].lower()
    
    try:
        result = predict_disease(img_path, animal_type)
        print(f"\nPredicted Disease: {result['disease']}")
        print(f"Confidence: {result['confidence']:.2f}%")
        print("\nDetected Features:")
        for feature in result['detected_features']:
            print(f"- {feature}")
        
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"- {rec}")
        
        print("\nTop Predictions:")
        for disease in result['all_predictions']:
            print(f"{disease['disease']}: {disease['confidence']:.2f}%")
            
    except Exception as e:
        print(f"Error: {str(e)}") 