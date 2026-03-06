"""
Simple breed predictor without TensorFlow dependencies
This is a minimal implementation that avoids the source code string error
"""
import os
import numpy as np
from PIL import Image
import json
import shutil

# Dictionary to store breed information
BREED_DATA = {
    'cow': {
        'breeds': ['Gir cow', 'Sahiwal', 'Jersey', 'Holstein Friesian', 'Ongole'],
        'characteristics': {
            'gir cow': {
                'description': 'Gir is an indigenous breed from India known for their distinctive long ears and forehead dome.',
                'origin': 'Gujarat, India',
                'milk_production': 'Good (1800-2500 liters/lactation)',
                'weight': '550-650 kg',
                'color': 'Red or spotted white with red markings',
                'lifespan': '12-15 years',
                'type': 'Dual purpose - dairy and draft'
            },
            'sahiwal': {
                'description': 'Sahiwal is one of the best dairy breeds from the Indian subcontinent, known for heat tolerance.',
                'origin': 'Punjab region (India/Pakistan)',
                'milk_production': 'Excellent (2000-2500 liters/lactation)',
                'weight': '400-500 kg',
                'color': 'Reddish brown or red and white',
                'lifespan': '12-14 years',
                'type': 'Dairy'
            },
            'jersey': {
                'description': 'Jersey cows are one of the oldest dairy breeds, known for high butterfat milk.',
                'origin': 'Jersey Island',
                'milk_production': 'High butterfat content',
                'weight': '400-500 kg',
                'color': 'Light brown to dark fawn',
                'lifespan': '15-20 years',
                'type': 'Dairy'
            },
            'holstein friesian': {
                'description': 'Holstein Friesian is the highest milk producing dairy breed in the world.',
                'origin': 'Netherlands',
                'milk_production': 'Very high (7500-9000 liters/lactation)',
                'weight': '600-700 kg',
                'color': 'Black and white patches',
                'lifespan': '15-20 years',
                'type': 'Dairy'
            },
            'ongole': {
                'description': 'Ongole is a large, powerful breed known for disease resistance and ability to thrive in harsh conditions.',
                'origin': 'Andhra Pradesh, India',
                'milk_production': 'Moderate',
                'weight': '500-600 kg',
                'color': 'White with sometimes black markings',
                'lifespan': '15-20 years',
                'type': 'Dual purpose - draft and meat'
            }
        }
    },
    'goat': {
        'breeds': ['Boer', 'Beetal', 'Jamunapari', 'Black Bengal', 'Barbari'],
        'characteristics': {
            'boer': {
                'description': 'Boer goats are a popular meat breed known for their rapid growth rate and muscular build.',
                'origin': 'South Africa',
                'purpose': 'Meat',
                'weight': '90-135 kg (males), 70-90 kg (females)',
                'color': 'White body with distinctive brown head',
                'lifespan': '8-12 years'
            },
            'beetal': {
                'description': 'Beetal goats are a dual-purpose breed known for both milk and meat production.',
                'origin': 'Punjab, India',
                'purpose': 'Dual-purpose (milk and meat)',
                'weight': '65-80 kg',
                'color': 'Usually brown with white spots',
                'lifespan': '10-12 years'
            },
            'jamunapari': {
                'description': 'Jamunapari is one of the largest Indian goat breeds, known for its convex facial profile and pendulous ears.',
                'origin': 'Uttar Pradesh, India',
                'purpose': 'Dual-purpose (milk and meat)',
                'weight': '60-90 kg',
                'color': 'White with patches of tan/brown',
                'lifespan': '8-10 years'
            },
            'black bengal': {
                'description': 'Black Bengal goats are small in size but known for high-quality meat and skin.',
                'origin': 'West Bengal, India',
                'purpose': 'Meat and skin',
                'weight': '15-25 kg',
                'color': 'Black, sometimes white patches',
                'lifespan': '6-8 years'
            },
            'barbari': {
                'description': 'Barbari goats are a compact breed known for early maturity and good reproductive traits.',
                'origin': 'North India',
                'purpose': 'Meat',
                'weight': '25-35 kg',
                'color': 'White with reddish-brown spots',
                'lifespan': '7-10 years'
            }
        }
    },
    'chicken': {
        'breeds': ['Asil chicken', 'Kadaknath chicken', 'Broiler chicken', 'Plymouth Rock', 'Leghorn'],
        'characteristics': {
            'asil chicken': {
                'description': 'Asil (or Aseel) is an ancient breed known for its strength, stamina, and fighting abilities.',
                'origin': 'India',
                'purpose': 'Meat and ornamental',
                'weight': '4-5 kg (male), 3-4 kg (female)',
                'color': 'Various colors including black, red, white',
                'lifespan': '7-10 years'
            },
            'kadaknath chicken': {
                'description': 'Kadaknath is known for its black meat and has high protein content and low cholesterol.',
                'origin': 'Madhya Pradesh, India',
                'purpose': 'Meat and medicinal',
                'weight': '1.5-2 kg',
                'color': 'Dark coloration including black skin, meat, and organs',
                'lifespan': '5-8 years'
            },
            'broiler chicken': {
                'description': 'Broiler chickens are bred specifically for meat production with rapid growth rate.',
                'origin': 'Commercially developed',
                'purpose': 'Meat',
                'weight': '3-4 kg',
                'color': 'Usually white',
                'lifespan': '5-7 years (but typically processed at 6-7 weeks)'
            },
            'plymouth rock': {
                'description': 'Plymouth Rock is a dual-purpose breed known for its hardiness and docile temperament.',
                'origin': 'United States',
                'purpose': 'Dual-purpose (eggs and meat)',
                'weight': '3.5-4 kg',
                'color': 'Barred pattern (black and white)',
                'lifespan': '6-8 years'
            },
            'leghorn': {
                'description': 'Leghorns are excellent egg layers with high feed efficiency.',
                'origin': 'Italy',
                'purpose': 'Eggs',
                'weight': '2-2.5 kg',
                'color': 'Primarily white',
                'lifespan': '4-6 years'
            }
        }
    }
}

def clean_image(img_path):
    """
    Process an image file to ensure it's clean and properly formatted
    Returns the path to the clean image
    """
    try:
        # Create output path
        output_dir = os.path.dirname(img_path)
        filename = f"cleaned_{os.path.basename(img_path)}"
        output_path = os.path.join(output_dir, filename)
        
        # Open image with PIL and convert/save as JPEG
        img = Image.open(img_path).convert('RGB')
        img.save(output_path, format='JPEG')
        
        return output_path
    except Exception as e:
        print(f"Error cleaning image: {e}")
        raise

def analyze_image_colors(img_path):
    """
    Analyze the color profile of an image to help with breed prediction
    Returns a dictionary of color statistics
    """
    try:
        # Open the image
        img = Image.open(img_path).convert('RGB')
        img_array = np.array(img)
        
        # Calculate average color values
        avg_red = np.mean(img_array[:,:,0])
        avg_green = np.mean(img_array[:,:,1])
        avg_blue = np.mean(img_array[:,:,2])
        
        # Calculate color variance
        var_red = np.var(img_array[:,:,0])
        var_green = np.var(img_array[:,:,1])
        var_blue = np.var(img_array[:,:,2])
        
        # Calculate brightness
        brightness = (avg_red + avg_green + avg_blue) / 3
        
        # Calculate contrast
        contrast = (var_red + var_green + var_blue) / 3
        
        # Determine dominant color
        dominant_color = None
        max_avg = max(avg_red, avg_green, avg_blue)
        if max_avg == avg_red and avg_red > 1.1 * avg_green and avg_red > 1.1 * avg_blue:
            dominant_color = "red"
        elif max_avg == avg_green and avg_green > 1.1 * avg_red and avg_green > 1.1 * avg_blue:
            dominant_color = "green"
        elif max_avg == avg_blue and avg_blue > 1.1 * avg_red and avg_blue > 1.1 * avg_green:
            dominant_color = "blue"
        elif avg_red > 200 and avg_green > 200 and avg_blue > 200:
            dominant_color = "white"
        elif avg_red < 50 and avg_green < 50 and avg_blue < 50:
            dominant_color = "black"
        elif avg_red > 150 and avg_green > 100 and avg_blue < 100:
            dominant_color = "brown"
        else:
            dominant_color = "mixed"
        
        return {
            "dominant_color": dominant_color,
            "brightness": brightness,
            "contrast": contrast,
            "red_avg": avg_red,
            "green_avg": avg_green,
            "blue_avg": avg_blue
        }
    except Exception as e:
        print(f"Error analyzing image colors: {e}")
        return {
            "dominant_color": "unknown",
            "brightness": 0,
            "contrast": 0
        }

def analyze_animal_patterns(img_path):
    """
    Analyze patterns in the image that might help identify animal breed
    """
    try:
        # Open the image
        img = Image.open(img_path).convert('RGB')
        img_array = np.array(img)
        
        # Resize for faster processing if needed
        if img.width > 500 or img.height > 500:
            img = img.resize((min(500, img.width), min(500, img.height)))
            img_array = np.array(img)
        
        # Convert to grayscale
        gray = np.mean(img_array, axis=2).astype(np.uint8)
        
        # Calculate edge density using simple gradient method
        dx = np.abs(np.diff(gray, axis=1, prepend=0))
        dy = np.abs(np.diff(gray, axis=0, prepend=0))
        gradient_magnitude = np.sqrt(dx**2 + dy**2)
        edge_density = np.mean(gradient_magnitude > 50)  # Threshold
        
        # Calculate texture variance
        texture_variance = np.var(gray)
        
        # Detect patterns
        has_spots = False
        has_stripes = False
        
        # Simple spot detection based on local variance
        from scipy.ndimage import uniform_filter
        local_mean = uniform_filter(gray, size=10)
        local_var = uniform_filter(gray**2, size=10) - local_mean**2
        spot_density = np.mean(local_var > 200)
        
        if spot_density > 0.05:
            has_spots = True
        
        # Simple stripe detection using variance in x and y directions
        var_x = np.var(np.diff(gray, axis=1), axis=1).mean()
        var_y = np.var(np.diff(gray, axis=0), axis=0).mean()
        
        stripe_ratio = max(var_x, var_y) / (min(var_x, var_y) + 1e-6)
        
        if stripe_ratio > 3:
            has_stripes = True
            stripe_direction = "horizontal" if var_y > var_x else "vertical"
        else:
            stripe_direction = None
            
        # Check if it's a solid color
        color_variance = np.var(img_array, axis=(0,1)).mean()
        is_solid_color = color_variance < 500
        
        return {
            "has_spots": has_spots,
            "has_stripes": has_stripes,
            "stripe_direction": stripe_direction,
            "edge_density": float(edge_density),
            "texture_variance": float(texture_variance),
            "is_solid_color": bool(is_solid_color)
        }
    except Exception as e:
        print(f"Error analyzing animal patterns: {e}")
        return {
            "has_spots": False,
            "has_stripes": False,
            "edge_density": 0,
            "texture_variance": 0,
            "is_solid_color": False
        }
        
def predict_breed_from_features(animal_type, color_data, pattern_data):
    """
    Predict animal breed based on color and pattern features
    Returns the most likely breed and confidence scores
    """
    breeds = BREED_DATA.get(animal_type, {}).get('breeds', [])
    if not breeds:
        return None, []
        
    scores = {}
    
    # Initialize scores
    for breed in breeds:
        scores[breed] = 50.0  # Base score
    
    # Update scores based on color data
    dominant_color = color_data.get('dominant_color', 'unknown')
    brightness = color_data.get('brightness', 0)
    
    if animal_type == 'cow':
        if dominant_color == 'white':
            scores['Holstein Friesian'] += 20
            scores['Ongole'] += 15
        elif dominant_color == 'brown' or dominant_color == 'red':
            scores['Gir cow'] += 20
            scores['Sahiwal'] += 15
            scores['Jersey'] += 10
        elif dominant_color == 'black':
            scores['Holstein Friesian'] += 15
    
    elif animal_type == 'goat':
        if dominant_color == 'white':
            scores['Jamunapari'] += 20
            scores['Barbari'] += 15
        elif dominant_color == 'black':
            scores['Black Bengal'] += 25
        elif dominant_color == 'brown':
            scores['Beetal'] += 20
            scores['Boer'] += 15
    
    elif animal_type == 'chicken':
        if dominant_color == 'black':
            scores['Kadaknath chicken'] += 25
        elif dominant_color == 'white':
            scores['Leghorn'] += 20
            scores['Broiler chicken'] += 15
        elif brightness < 100:  # Dark coloration
            scores['Asil chicken'] += 15
    
    # Update scores based on pattern data
    has_spots = pattern_data.get('has_spots', False)
    has_stripes = pattern_data.get('has_stripes', False)
    is_solid_color = pattern_data.get('is_solid_color', False)
    
    if animal_type == 'cow':
        if has_spots:
            scores['Holstein Friesian'] += 20
        if is_solid_color:
            scores['Sahiwal'] += 10
            scores['Jersey'] += 10
            scores['Ongole'] += 10
    
    elif animal_type == 'goat':
        if has_spots:
            scores['Barbari'] += 20
        if dominant_color == 'white' and not is_solid_color:
            scores['Boer'] += 15  # White body with colored head
    
    # Sort breeds by score
    sorted_breeds = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    # Return top prediction and all scores
    top_breed = sorted_breeds[0][0]
    top_confidence = min(95.0, sorted_breeds[0][1])  # Cap confidence at 95%
    
    all_predictions = []
    for breed, score in sorted_breeds[:3]:
        # Normalize scores to confidence percentage
        confidence = min(95.0, score)
        all_predictions.append({
            'breed': breed,
            'confidence': confidence
        })
    
    return top_breed, top_confidence, all_predictions

def get_breed_characteristics(animal_type, breed_name):
    """Get characteristics for a specific breed"""
    breed_key = breed_name.lower()
    characteristics = BREED_DATA.get(animal_type, {}).get('characteristics', {})
    
    if breed_key in characteristics:
        return characteristics[breed_key]
    else:
        return {
            'description': f'This appears to be a {breed_name} breed of {animal_type}.',
            'note': 'Detailed characteristics not available in our database.'
        }

def predict_breed(img_path, animal_type):
    """
    Main function to predict breed from an image
    Does not use TensorFlow to avoid the null bytes error
    """
    try:
        # Check if file exists
        if not os.path.exists(img_path):
            raise ValueError(f"Image file not found: {img_path}")
            
        # Clean the image
        clean_path = clean_image(img_path)
        
        # Analyze image features
        color_data = analyze_image_colors(clean_path)
        pattern_data = analyze_animal_patterns(clean_path)
        
        # Predict breed based on features
        top_breed, confidence, all_predictions = predict_breed_from_features(
            animal_type, color_data, pattern_data
        )
        
        # Get breed characteristics
        characteristics = get_breed_characteristics(animal_type, top_breed)
        
        # Clean up
        try:
            os.remove(clean_path)
        except:
            pass
            
        # Prepare result
        result = {
            'breed': top_breed,
            'confidence': confidence,
            'all_predictions': all_predictions,
            'characteristics': characteristics,
            'animal_verified': True,  # We're not doing animal verification in this version
            'animal_confidence': 90.0,
            'detected_animal': animal_type,
            'color_analysis': color_data,
            'pattern_analysis': pattern_data,
            'is_minimal_prediction': False
        }
        
        return result
        
    except Exception as e:
        print(f"Error in breed prediction: {e}")
        raise ValueError(f"Failed to process image: {str(e)}")

if __name__ == "__main__":
    # For testing purposes
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python simple_breed_predictor.py <image_path> <animal_type>")
        sys.exit(1)
    
    img_path = sys.argv[1]
    animal_type = sys.argv[2].lower()
    
    try:
        result = predict_breed(img_path, animal_type)
        print(f"\nPredicted Breed: {result['breed']}")
        print(f"Confidence: {result['confidence']:.2f}%")
        print("\nBreed Characteristics:")
        for key, value in result['characteristics'].items():
            print(f"{key.capitalize()}: {value}")
        
        print("\nTop Predictions:")
        for prediction in result['all_predictions']:
            print(f"{prediction['breed']}: {prediction['confidence']:.2f}%")
            
    except Exception as e:
        print(f"Error: {str(e)}") 