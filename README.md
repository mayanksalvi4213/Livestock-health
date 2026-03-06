# AgriHealth - Livestock Management System

AgriHealth is a comprehensive livestock management system designed to help farmers monitor and manage the health of their animals, including cows, chickens, and goats.

## Model Training

The system includes machine learning models for identifying animal breeds and diseases. Here's how to work with the model training scripts:

### Prerequisites

- Python 3.8+
- Required libraries (install via `pip install -r requirements.txt`)
- Dataset organized in the following structure:
  ```
  dataset/
    ├── cow breed/
    │   ├── dangi/
    │   ├── gir cow/
    │   ├── jersey/
    │   ├── Ongole cow/
    │   └── sahiwal/
    ├── cow diseases/
    │   ├── healthy_cows/
    │   ├── lumpy_cows/
    │   ├── mastitis/
    │   ├── pinkeye/
    │   └── ringworm/
    ├── chicken breed/
    │   ├── asil chicken/
    │   ├── broiler chicken/
    │   └── kadaknath chicken/
    ├── chicken diseases/
    │   ├── Fowl pox/
    │   ├── healthy chicken/
    │   └── Mareks disease/
    ├── goat breed/
    │   ├── barbari goat/
    │   ├── beetal goat/
    │   ├── black bengal goat/
    │   └── sirohi goat/
    └── goat diseases/
        ├── Bloat/
        ├── Caseous Lymphadenitis/
        ├── foot rot/
        ├── healthy goat/
        ├── Mastitis (goats)/
        └── Orf (contagious Ecthyma)/
  ```

## Improving Model Accuracy

### 1. Data Collection Guidelines

To improve model accuracy, follow these guidelines when collecting training data:

#### Image Quality Requirements
- Resolution: Minimum 640x640 pixels
- Format: JPG, PNG, or WebP
- Lighting: Well-lit images with minimal shadows
- Focus: Clear, sharp images without motion blur
- Background: Varied backgrounds to improve model generalization
- Angles: Multiple angles of the same condition/breed

#### Data Distribution
- Minimum 100 images per class
- Balanced class distribution (similar number of images per class)
- 80:20 split between training and validation data
- Include images from different:
  - Times of day
  - Seasons
  - Weather conditions
  - Geographical locations

### 2. Data Preprocessing

Before training, ensure your data is properly preprocessed:

```bash
python preprocess_data.py --input dataset/ --output processed_dataset/
```

This will:
- Resize images to uniform dimensions
- Apply data augmentation:
  - Random rotations (±15°)
  - Random brightness adjustments
  - Random contrast adjustments
  - Random horizontal flips
- Remove corrupt or invalid images
- Balance class distributions

### 3. Model Fine-tuning

To improve model performance:

#### a. Adjust Training Parameters
```bash
python retrain_model.py --animal <animal_type> --category <category> \
    --epochs 20 \
    --batch-size 32 \
    --learning-rate 0.0001 \
    --dropout 0.3
```

#### b. Transfer Learning
```bash
python transfer_learning.py --animal <animal_type> --category <category> \
    --base-model "EfficientNetV2B0" \
    --weights "imagenet"
```

Available base models:
- EfficientNetV2B0 (default)
- ResNet50V2
- DenseNet121
- MobileNetV3Large

### 4. Model Evaluation

#### a. Basic Evaluation
```bash
python evaluate_models.py --model-path models/<animal>_<category>_model.keras
```

This generates:
- Confusion matrix
- Classification report
- ROC curves
- Precision-Recall curves

#### b. Cross-Validation
```bash
python cross_validate.py --animal <animal_type> --category <category> --folds 5
```

### 5. Continuous Improvement

1. Monitor model performance in production:
```bash
python monitor_performance.py --days 30
```

2. Collect misclassified examples:
```bash
python collect_errors.py --output misclassified/
```

3. Retrain with corrected data:
```bash
python retrain_model.py --animal <animal_type> --category <category> \
    --additional-data misclassified/ \
    --fine-tune
```

### 6. Best Practices

1. Data Quality
- Regularly review and clean training data
- Document image sources and conditions
- Maintain consistent labeling standards
- Version control your datasets

2. Model Versioning
- Keep track of model versions
- Document changes and improvements
- Maintain test sets for comparison

3. Performance Metrics
Track multiple metrics:
- Accuracy
- Precision
- Recall
- F1 Score
- Confusion Matrix
- Inference Time

## Web Application

To run the web application:

```bash
python app.py
```

The application will be available at http://localhost:5000/

## Troubleshooting

If you encounter issues with model training:

1. Check that TensorFlow can access your GPU (if available)
2. Ensure your dataset is properly organized
3. Try running with fewer epochs first to verify the pipeline works
4. If you get "eager execution" errors, use the `retrain_model.py` script which has been optimized to avoid these issues

## License

This project is licensed under the MIT License - see the LICENSE file for details. 