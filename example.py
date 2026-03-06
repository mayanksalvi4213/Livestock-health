"""
Example script to demonstrate how to use the AgriHealth system for image analysis
This script shows how to:
1. Create minimal models for quick testing
2. Use the disease prediction and breed identification modules
"""

import os
import random
import sys
import glob
from PIL import Image
import matplotlib.pyplot as plt

# Check if models directory exists
if not os.path.exists('models'):
    os.makedirs('models', exist_ok=True)

# Check if minimal models need to be created
models_exist = False
for animal in ['cow', 'goat', 'chicken']:
    for category in ['breed', 'diseases']:
        if os.path.exists(f'models/{animal}_{category}_model.h5'):
            models_exist = True
            break

if not models_exist:
    print("No models found. Creating minimal models for testing...")
    try:
        import create_minimal_model
        create_minimal_model.create_minimal_model('cow', 'diseases')
        print("Created minimal cow disease model for testing.")
    except Exception as e:
        print(f"Error creating minimal model: {str(e)}")
        print("Please run 'python create_minimal_model.py all all' to create all minimal models.")
        sys.exit(1)

def find_sample_image(animal_type='cow', category='diseases'):
    """Find a sample image from the dataset"""
    data_dir = os.path.join('dataset', f"{animal_type} {category}")
    if not os.path.exists(data_dir):
        print(f"Data directory {data_dir} not found.")
        return None
    
    # Get all class directories
    class_dirs = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    if not class_dirs:
        print(f"No class directories found in {data_dir}")
        return None
    
    # Pick a random class directory
    class_dir = random.choice(class_dirs)
    class_path = os.path.join(data_dir, class_dir)
    
    # Get all image files in the directory
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.png']:
        image_files.extend(glob.glob(os.path.join(class_path, ext)))
    
    if not image_files:
        print(f"No image files found in {class_path}")
        return None
    
    # Pick a random image file
    image_file = random.choice(image_files)
    print(f"Using sample image: {image_file} (Class: {class_dir})")
    return image_file

def show_image(image_path):
    """Display the image"""
    if not os.path.exists(image_path):
        print(f"Image file {image_path} not found.")
        return
    
    img = Image.open(image_path)
    plt.figure(figsize=(8, 6))
    plt.imshow(img)
    plt.axis('off')
    plt.title(f"Sample image: {os.path.basename(image_path)}")
    plt.show()

def predict_disease(image_path, animal_type='cow'):
    """Predict disease using disease_predict.py"""
    try:
        import disease_predict
        result = disease_predict.predict_disease(image_path, animal_type)
        
        print("\n" + "="*50)
        print(f"DISEASE PREDICTION RESULTS FOR {animal_type.upper()}")
        print("="*50)
        print(f"Predicted Disease: {result['disease']}")
        print(f"Confidence: {result['confidence'] * 100:.2f}%")
        
        if result['detected_features']:
            print("\nDetected Features:")
            for feature in result['detected_features']:
                print(f"- {feature}")
        
        print("\nRecommendations:")
        for rec in result['recommendations']:
            print(f"- {rec}")
        
        print("\nTop Predictions:")
        for disease, conf in result['top_predictions']:
            print(f"{disease}: {conf * 100:.2f}%")
        
        return result
    
    except Exception as e:
        print(f"Error predicting disease: {str(e)}")
        return None

def identify_breed(image_path, animal_type='cow'):
    """Identify breed using breed_predict.py"""
    try:
        import breed_predict
        result = breed_predict.predict_breed(image_path, animal_type)
        
        print("\n" + "="*50)
        print(f"BREED IDENTIFICATION RESULTS FOR {animal_type.upper()}")
        print("="*50)
        print(f"Predicted Breed: {result['breed']}")
        print(f"Confidence: {result['confidence']:.2f}%")
        
        print("\nBreed Characteristics:")
        for key, value in result['characteristics'].items():
            print(f"{key.capitalize()}: {value}")
        
        print("\nTop Predictions:")
        for breed, conf in result['top_predictions']:
            print(f"{breed}: {conf:.2f}%")
        
        return result
    
    except Exception as e:
        print(f"Error identifying breed: {str(e)}")
        return None

if __name__ == "__main__":
    print("\n" + "="*50)
    print("AGRIHEALTH AI MODEL DEMONSTRATION")
    print("="*50)
    
    # Get animal type from command line or use default
    animal_type = 'cow'
    if len(sys.argv) > 1:
        animal_type = sys.argv[1].lower()
    
    # Find sample images
    disease_image = find_sample_image(animal_type, 'diseases')
    breed_image = find_sample_image(animal_type, 'breed')
    
    if disease_image:
        # Show and analyze disease image
        show_image(disease_image)
        predict_disease(disease_image, animal_type)
    
    if breed_image:
        # Show and analyze breed image
        show_image(breed_image)
        identify_breed(breed_image, animal_type)
    
    print("\n" + "="*50)
    print("DEMONSTRATION COMPLETE")
    print("="*50)
    print("\nTo use this system in your application:")
    print("1. Train models with: python train_model.py --animal <animal> --category <category> --epochs <num_epochs>")
    print("2. Use in your app by importing disease_predict.py and breed_predict.py")
    print("3. Call predict_disease() or predict_breed() with your image path and animal type") 