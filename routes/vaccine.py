from flask import Blueprint, render_template, request, jsonify
from utils.vaccine_data import get_vaccines_for_animal, get_vaccines_for_disease

vaccine_bp = Blueprint('vaccine', __name__)

@vaccine_bp.route('/vaccine')
def vaccine_page():
    """Display vaccine information for different animals"""
    # Get vaccines for each animal type
    cow_vaccines = get_vaccines_for_animal('cow')
    goat_vaccines = get_vaccines_for_animal('goat')
    chicken_vaccines = get_vaccines_for_animal('chicken')
    
    # Get highlighted disease from query parameter (if any)
    highlight_disease = request.args.get('highlight', None)
    
    return render_template('vaccine.html', 
                          cow_vaccines=cow_vaccines,
                          goat_vaccines=goat_vaccines,
                          chicken_vaccines=chicken_vaccines,
                          highlight_disease=highlight_disease)

@vaccine_bp.route('/api/vaccine-info/<disease>')
def vaccine_info(disease):
    """API endpoint to get vaccine information for a specific disease"""
    print(f"Fetching vaccine info for disease: '{disease}'")
    # Convert disease name to lowercase for case-insensitive matching
    vaccine_data = get_vaccines_for_disease(disease.lower())
    print(f"Retrieved vaccine data: {vaccine_data}")
    return jsonify(vaccine_data)

@vaccine_bp.route('/api/test-vaccine/<disease>')
def test_vaccine_info(disease):
    """Test API endpoint for debugging"""
    try:
        print(f"TEST: Fetching vaccine info for disease: '{disease}'")
        vaccine_data = get_vaccines_for_disease(disease)
        print(f"TEST: Retrieved vaccine data: {vaccine_data}")
        
        # Add the disease name to make debugging easier
        response = {
            "status": "success",
            "requested_disease": disease,
            "vaccine_data": vaccine_data
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "requested_disease": disease
        })

# Add other vaccine-related routes here