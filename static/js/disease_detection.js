// Disease Detection Interactive Functions

document.addEventListener('DOMContentLoaded', function() {
    const predictionForm = document.getElementById('disease-prediction-form');
    const resultContainer = document.getElementById('result-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const errorContainer = document.getElementById('error-container');
    
    if (predictionForm) {
        predictionForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading spinner
            loadingSpinner.classList.remove('d-none');
            resultContainer.classList.add('d-none');
            errorContainer.classList.add('d-none');
            
            // Create form data
            const formData = new FormData(predictionForm);
            
            // Make AJAX request
            fetch('/disease/predict', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                // Hide loading spinner
                loadingSpinner.classList.add('d-none');
                
                // Check for animal mismatch error
                if (data.animal_mismatch) {
                    showAnimalMismatchError(data);
                    return;
                }
                
                // Check for other errors
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                // Show result
                displayResult(data);
            })
            .catch(error => {
                // Hide loading spinner and show error
                loadingSpinner.classList.add('d-none');
                showError('An unexpected error occurred. Please try again.');
                console.error('Error:', error);
            });
        });
    }
    
    // Function to display animal mismatch error
    function showAnimalMismatchError(data) {
        errorContainer.innerHTML = `
            <div class="alert alert-warning">
                <h4 class="alert-heading"><i class="fas fa-exclamation-triangle me-2"></i>Animal Type Mismatch</h4>
                <p>${data.error}</p>
                <hr>
                <p class="mb-0">Please select the correct animal type or upload a different image.</p>
            </div>
            ${data.image_url ? `<div class="text-center mt-3">
                <img src="${data.image_url}" class="img-fluid rounded" style="max-height: 300px;">
            </div>` : ''}
        `;
        errorContainer.classList.remove('d-none');
    }
    
    // Function to display general error
    function showError(message) {
        // Check for specific error types and enhance the message
        let errorTitle = 'Error';
        let errorIcon = 'exclamation-circle';
        let alertClass = 'alert-danger';
        let additionalContent = '';
        
        // Check for image corruption
        if (message.includes('null bytes') || 
            message.includes('corrupted') || 
            message.includes('Unable to read')) {
            errorTitle = 'Image Error Detected';
            errorIcon = 'file-image';
            additionalContent = `
                <hr>
                <p class="mb-0">The image appears to be corrupted or invalid. Please try uploading a different image file.</p>
                <ul class="mt-2 mb-0">
                    <li>Ensure the file is a valid image (JPG, PNG, etc.)</li>
                    <li>Try a different image</li>
                    <li>Make sure the file isn't corrupted</li>
                </ul>
            `;
        }
        
        errorContainer.innerHTML = `
            <div class="alert ${alertClass}">
                <h4 class="alert-heading"><i class="fas fa-${errorIcon} me-2"></i>${errorTitle}</h4>
                <p>${message}</p>
                ${additionalContent}
            </div>
        `;
        errorContainer.classList.remove('d-none');
    }
    
    // Function to display prediction result
    function displayResult(data) {
        // Generate HTML for result
        let resultHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-microscope me-2"></i>Disease Detection Result</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <div class="mb-3">
                                <img src="${data.image_url}" class="img-fluid rounded" alt="Uploaded image" style="max-height: 200px;">
                            </div>
                            <div class="disease-result">
                                <h4>${data.disease}</h4>
                                <div class="confidence-badge ${getConfidenceBadgeClass(data.confidence_value)}">
                                    ${data.confidence} Confidence
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h5>Other Possible Diseases:</h5>
                            <div class="list-group mb-3">
        `;
        
        // Add top predictions
        data.top_predictions.forEach(prediction => {
            resultHTML += `
                <div class="list-group-item d-flex justify-content-between align-items-center">
                    ${prediction.disease}
                    <span class="badge ${getConfidenceBadgeClass(parseFloat(prediction.confidence))} rounded-pill">${prediction.confidence}</span>
                </div>
            `;
        });
        
        resultHTML += `
                            </div>
                            
                            <h5>Detected Features:</h5>
                            <ul class="list-group mb-3">
        `;
        
        // Add detected features
        if (data.features && data.features.length > 0) {
            data.features.forEach(feature => {
                resultHTML += `<li class="list-group-item"><i class="fas fa-check-circle text-success me-2"></i>${feature}</li>`;
            });
        } else {
            resultHTML += `<li class="list-group-item text-muted">No specific features detected</li>`;
        }
        
        resultHTML += `
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add recommendations section if available
        if (data.recommendations && data.recommendations.length > 0) {
            resultHTML += `
                <div class="card mb-4">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0"><i class="fas fa-clipboard-list me-2"></i>Treatment & Recommendations</h5>
                    </div>
                    <div class="card-body">
                        <ul class="list-group">
            `;
            
            data.recommendations.forEach(rec => {
                // Check if it's a medicine or diet recommendation
                if (rec.toLowerCase().includes('medicine:')) {
                    resultHTML += `<li class="list-group-item"><i class="fas fa-pills text-danger me-2"></i>${rec}</li>`;
                } else if (rec.toLowerCase().includes('diet:')) {
                    resultHTML += `<li class="list-group-item"><i class="fas fa-utensils text-success me-2"></i>${rec}</li>`;
                } else {
                    resultHTML += `<li class="list-group-item"><i class="fas fa-check text-primary me-2"></i>${rec}</li>`;
                }
            });
            
            resultHTML += `
                        </ul>
                    </div>
                </div>
            `;
        }
        
        // Update result container and show it
        resultContainer.innerHTML = resultHTML;
        resultContainer.classList.remove('d-none');
        
        // Scroll to result
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Helper function to get appropriate badge class based on confidence value
    function getConfidenceBadgeClass(confidence) {
        if (confidence >= 70) return 'bg-success';
        if (confidence >= 40) return 'bg-warning text-dark';
        return 'bg-danger';
    }
}); 