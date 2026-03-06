// Breed Identification Interactive Functions

document.addEventListener('DOMContentLoaded', function() {
    const predictionForm = document.getElementById('breed-prediction-form');
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
            fetch('/breed/predict', {
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
        
        // Handle source code string error specific to this application
        if (message.includes('source code string') || message.includes('null byte')) {
            errorTitle = 'Image Processing Error';
            errorIcon = 'exclamation-triangle';
            additionalContent = `
                <hr>
                <p class="mb-0">The system encountered an error processing this image.</p>
                <ul class="mt-2 mb-0">
                    <li>Try uploading a different image</li>
                    <li>Ensure the image is not corrupted</li>
                    <li>Images should be in common formats like JPG or PNG</li>
                </ul>
            `;
        }
        
        // Use SweetAlert2 for a better user experience
        if (typeof Swal !== 'undefined') {
            Swal.fire({
                title: errorTitle,
                html: `<p>${message}</p>${additionalContent}`,
                icon: 'error',
                confirmButtonText: 'Try Again',
                confirmButtonColor: '#157347'
            });
        } else {
            // Fallback to regular HTML if SweetAlert is not available
            errorContainer.innerHTML = `
                <div class="alert ${alertClass}">
                    <h4 class="alert-heading"><i class="fas fa-${errorIcon} me-2"></i>${errorTitle}</h4>
                    <p>${message}</p>
                    ${additionalContent}
                </div>
            `;
        }
        
        errorContainer.classList.remove('d-none');
    }
    
    // Function to display prediction result
    function displayResult(data) {
        // Generate HTML for result
        let resultHTML = `
            <div class="card mb-4">
                <div class="card-header bg-primary text-white">
                    <h5 class="mb-0"><i class="fas fa-dna me-2"></i>Breed Identification Result</h5>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-4 text-center">
                            <div class="mb-3">
                                <img src="${data.image_url}" class="img-fluid rounded" alt="Uploaded image" style="max-height: 200px;">
                            </div>
                            <div class="breed-result">
                                <h4>${data.breed}</h4>
                                <div class="confidence-badge ${getConfidenceBadgeClass(data.confidence_value)}">
                                    ${data.confidence} Confidence
                                </div>
                            </div>
                        </div>
                        <div class="col-md-8">
                            <h5>Other Possible Breeds:</h5>
                            <div class="list-group mb-3">
        `;
        
        // Add top predictions
        if (data.all_predictions && data.all_predictions.length > 0) {
            data.all_predictions.forEach(prediction => {
                resultHTML += `
                    <div class="list-group-item d-flex justify-content-between align-items-center">
                        ${prediction.breed}
                        <span class="badge ${getConfidenceBadgeClass(parseFloat(prediction.confidence))} rounded-pill">${prediction.confidence.toFixed(1)}%</span>
                    </div>
                `;
            });
        } else {
            resultHTML += `<div class="list-group-item text-muted">No other breeds identified</div>`;
        }
        
        resultHTML += `
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add breed characteristics if available
        if (data.characteristics && Object.keys(data.characteristics).length > 0) {
            resultHTML += `
                <div class="card mb-4">
                    <div class="card-header bg-success text-white">
                        <h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Breed Characteristics</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
            `;
            
            // Description if available
            if (data.characteristics.description) {
                resultHTML += `
                    <div class="col-12 mb-3">
                        <h6>Description</h6>
                        <p>${data.characteristics.description}</p>
                    </div>
                `;
            }
            
            // Create a table for other characteristics
            resultHTML += `
                <div class="col-12">
                    <table class="table table-bordered">
                        <tbody>
            `;
            
            // Add each characteristic except description (already shown above)
            for (const [key, value] of Object.entries(data.characteristics)) {
                if (key !== 'description') {
                    const formattedKey = key.replace(/_/g, ' ')
                        .split(' ')
                        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                        .join(' ');
                    
                    resultHTML += `
                        <tr>
                            <th scope="row" style="width: 30%;">${formattedKey}</th>
                            <td>${value}</td>
                        </tr>
                    `;
                }
            }
            
            resultHTML += `
                        </tbody>
                    </table>
                </div>
            `;
            
            resultHTML += `
                        </div>
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