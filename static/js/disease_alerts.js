// Disease Alerts Interactive Functions

document.addEventListener('DOMContentLoaded', function() {
    // Set up auto-refresh timer (every 30 minutes)
    setAutoRefreshTimer();
    
    // Disease modal event handler
    const diseaseModal = document.getElementById('diseaseModal');
    if (diseaseModal) {
        diseaseModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const diseaseName = button.getAttribute('data-disease');
            const modal = this;
            
            // Update modal title
            modal.querySelector('.modal-title').textContent = diseaseName;
            
            // Show loading spinner
            modal.querySelector('.disease-info-content').innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3">Loading disease information...</p>
                </div>
            `;
            
            // Fetch disease information
            fetch(`/api/disease-alerts/info?disease=${encodeURIComponent(diseaseName)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Generate content HTML
                    let content = '<div class="row">';
                    
                    // Description
                    content += `
                        <div class="col-12 mb-4">
                            <h5>Description</h5>
                            <p>${data.description}</p>
                        </div>
                    `;
                    
                    // Symptoms section
                    if (data.symptoms && data.symptoms.length > 0) {
                        content += `
                            <div class="col-md-6 mb-4">
                                <h5>Symptoms</h5>
                                <ul class="list-group list-group-flush">
                        `;
                        
                        data.symptoms.forEach(function(symptom) {
                            content += `<li class="list-group-item">${symptom}</li>`;
                        });
                        
                        content += `
                                </ul>
                            </div>
                        `;
                    }
                    
                    // Prevention section
                    if (data.prevention && data.prevention.length > 0) {
                        content += `
                            <div class="col-md-6 mb-4">
                                <h5>Prevention</h5>
                                <ul class="list-group list-group-flush">
                        `;
                        
                        data.prevention.forEach(function(measure) {
                            content += `<li class="list-group-item">${measure}</li>`;
                        });
                        
                        content += `
                                </ul>
                            </div>
                        `;
                    }
                    
                    // Treatment info
                    if (data.treatment) {
                        content += `
                            <div class="col-12 mb-4">
                                <h5>Treatment</h5>
                                <p>${data.treatment}</p>
                            </div>
                        `;
                    }
                    
                    // Weather risk factors
                    if (data.risk_factors) {
                        content += `
                            <div class="col-12 mb-4">
                                <h5>Weather Risk Factors</h5>
                                <div class="table-responsive">
                                    <table class="table table-sm table-bordered">
                                        <thead class="table-light">
                                            <tr>
                                                <th>Factor</th>
                                                <th>Risk Condition</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                        `;
                        
                        for (const [key, value] of Object.entries(data.risk_factors)) {
                            const factor = key.replace(/_/g, ' ')
                                .split(' ')
                                .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                                .join(' ');
                                
                            content += `
                                <tr>
                                    <td>${factor}</td>
                                    <td>${value}</td>
                                </tr>
                            `;
                        }
                        
                        content += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        `;
                    }
                    
                    // Zoonotic warning if applicable
                    if (data.zoonotic) {
                        content += `
                            <div class="col-12">
                                <div class="alert alert-danger">
                                    <i class="fas fa-exclamation-triangle me-2"></i>
                                    <strong>Warning:</strong> This is a zoonotic disease that can be transmitted to humans.
                                </div>
                            </div>
                        `;
                    }
                    
                    content += '</div>';
                    
                    // Update modal content
                    modal.querySelector('.disease-info-content').innerHTML = content;
                })
                .catch(error => {
                    // Show error message
                    modal.querySelector('.disease-info-content').innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Error loading disease information: ${error.message}. Please try again later.
                        </div>
                    `;
                });
        });
    }
    
    // Outbreak modal event handler
    const outbreakModal = document.getElementById('outbreakModal');
    if (outbreakModal) {
        outbreakModal.addEventListener('show.bs.modal', function(event) {
            const button = event.relatedTarget;
            const outbreakId = button.getAttribute('data-outbreak-id');
            const modal = this;
            
            // Show loading spinner
            modal.querySelector('.outbreak-info-content').innerHTML = `
                <div class="text-center py-5">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-3">Loading outbreak information...</p>
                </div>
            `;
            
            // Fetch outbreak information
            fetch(`/api/disease-alerts/outbreak/${outbreakId}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    // Update modal title
                    modal.querySelector('.modal-title').textContent = `${data.disease_name} Outbreak Details`;
                    
                    // Generate content HTML
                    let content = '<div class="row">';
                    
                    // Basic information
                    content += `
                        <div class="col-md-6 mb-4">
                            <h5>Basic Information</h5>
                            <ul class="list-group list-group-flush">
                                <li class="list-group-item d-flex justify-content-between"><span>Disease:</span> <strong>${data.disease_name}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>Severity:</span> <strong>${data.severity}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>Location:</span> <strong>${data.location}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>District:</span> <strong>${data.district}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>State:</span> <strong>${data.state}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>Reported Date:</span> <strong>${data.reported_date}</strong></li>
                                <li class="list-group-item d-flex justify-content-between"><span>Distance from Farm:</span> <strong>${data.distance} km</strong></li>
                            </ul>
                        </div>
                    `;
                    
                    // Outbreak statistics
                    if (data.statistics) {
                        content += `
                            <div class="col-md-6 mb-4">
                                <h5>Outbreak Statistics</h5>
                                <ul class="list-group list-group-flush">
                        `;
                        
                        if (data.statistics.affected_animals) {
                            content += `<li class="list-group-item d-flex justify-content-between"><span>Affected Animals:</span> <strong>${data.statistics.affected_animals}</strong></li>`;
                        }
                        
                        if (data.statistics.deaths) {
                            content += `<li class="list-group-item d-flex justify-content-between"><span>Deaths:</span> <strong>${data.statistics.deaths}</strong></li>`;
                        }
                        
                        if (data.statistics.morbidity_rate) {
                            content += `<li class="list-group-item d-flex justify-content-between"><span>Morbidity Rate:</span> <strong>${data.statistics.morbidity_rate}%</strong></li>`;
                        }
                        
                        if (data.statistics.mortality_rate) {
                            content += `<li class="list-group-item d-flex justify-content-between"><span>Mortality Rate:</span> <strong>${data.statistics.mortality_rate}%</strong></li>`;
                        }
                        
                        content += `
                                </ul>
                            </div>
                        `;
                    }
                    
                    // Preventive measures
                    if (data.preventive_measures && data.preventive_measures.length > 0) {
                        content += `
                            <div class="col-12 mb-4">
                                <h5>Preventive Measures</h5>
                                <ul class="list-group list-group-flush">
                        `;
                        
                        data.preventive_measures.forEach(function(measure) {
                            content += `<li class="list-group-item">${measure}</li>`;
                        });
                        
                        content += `
                                </ul>
                            </div>
                        `;
                    }
                    
                    // Additional details
                    if (data.details) {
                        content += `
                            <div class="col-12 mb-4">
                                <h5>Additional Details</h5>
                                <p>${data.details}</p>
                            </div>
                        `;
                    }
                    
                    content += '</div>';
                    
                    // Update modal content
                    modal.querySelector('.outbreak-info-content').innerHTML = content;
                })
                .catch(error => {
                    // Show error message
                    modal.querySelector('.outbreak-info-content').innerHTML = `
                        <div class="alert alert-danger">
                            <i class="fas fa-exclamation-circle me-2"></i>
                            Error loading outbreak information: ${error.message}. Please try again later.
                        </div>
                    `;
                });
        });
    }
    
    // Download prevention guide button
    const downloadPreventionBtn = document.querySelector('.download-prevention');
    if (downloadPreventionBtn) {
        downloadPreventionBtn.addEventListener('click', function() {
            const diseaseName = document.querySelector('#diseaseModalLabel').textContent;
            
            // Show loading status
            const modalFooter = this.closest('.modal-footer');
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Downloading...';
            this.disabled = true;
            
            fetch(`/api/disease-alerts/prevention-guide?disease=${encodeURIComponent(diseaseName)}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(data => {
                    if (data.success) {
                        // Show success message
                        const alertDiv = document.createElement('div');
                        alertDiv.className = 'alert alert-success mt-2 w-100';
                        alertDiv.innerHTML = `<i class="fas fa-check-circle me-2"></i> ${data.message}`;
                        modalFooter.appendChild(alertDiv);
                        
                        // Remove alert after 5 seconds
                        setTimeout(() => {
                            alertDiv.remove();
                        }, 5000);
                    } else {
                        throw new Error(data.message || 'Unknown error');
                    }
                })
                .catch(error => {
                    // Show error message
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert alert-danger mt-2 w-100';
                    alertDiv.innerHTML = `<i class="fas fa-exclamation-circle me-2"></i> Error: ${error.message}`;
                    modalFooter.appendChild(alertDiv);
                    
                    // Remove alert after 5 seconds
                    setTimeout(() => {
                        alertDiv.remove();
                    }, 5000);
                })
                .finally(() => {
                    // Restore button state
                    this.innerHTML = originalText;
                    this.disabled = false;
                });
        });
    }
    
    // Filter buttons functionality
    const locationFilters = document.querySelectorAll('.location-filter');
    if (locationFilters.length > 0) {
        locationFilters.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all location filters
                locationFilters.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                const location = this.getAttribute('data-location');
                filterAlerts('location', location);
            });
        });
    }
    
    // Animal type filter
    const animalFilter = document.getElementById('animal-filter');
    if (animalFilter) {
        animalFilter.addEventListener('change', function() {
            filterAlerts('animal', this.value);
        });
    }
    
    // Risk level filter
    const riskFilter = document.getElementById('risk-filter');
    if (riskFilter) {
        riskFilter.addEventListener('change', function() {
            filterAlerts('risk', this.value);
        });
    }
    
    // Filter alerts based on selected criteria
    function filterAlerts(filterType, value) {
        const alertItems = document.querySelectorAll('.alert-item');
        
        alertItems.forEach(item => {
            // Get data attributes
            const itemLocation = item.getAttribute('data-location');
            const itemAnimal = item.getAttribute('data-animal');
            const itemRisk = item.getAttribute('data-risk');
            
            // Check if item should be shown
            let shouldShow = true;
            
            // Apply location filter
            if (filterType === 'location' && value !== 'all' && itemLocation !== value) {
                shouldShow = false;
            }
            
            // Apply animal filter
            if (filterType === 'animal' && value !== 'all' && itemAnimal !== value) {
                shouldShow = false;
            }
            
            // Apply risk filter
            if (filterType === 'risk' && value !== 'all' && itemRisk !== value) {
                shouldShow = false;
            }
            
            // Show or hide item
            if (shouldShow) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    // Function to refresh alerts data
    window.refreshAlerts = function() {
        // Show loading indicator
        const refreshButton = document.querySelector('button[onclick="refreshAlerts()"]');
        const originalText = refreshButton.innerHTML;
        refreshButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Refreshing...';
        refreshButton.disabled = true;
        
        fetch('/api/disease-alerts/refresh')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    // Create a toast notification
                    showToast('Success', 'Disease alerts refreshed with real-time data', 'success');
                    // Reload the page to show new data
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    throw new Error('Failed to refresh alert data: ' + data.message);
                }
            })
            .catch(error => {
                // Show error message
                showToast('Error', error.message, 'danger');
                // Reset button
                refreshButton.innerHTML = originalText;
                refreshButton.disabled = false;
            });
    };
    
    // Function to set up automatic refresh timer
    function setAutoRefreshTimer() {
        // Auto-refresh every 30 minutes (1800000 ms)
        const refreshInterval = 30 * 60 * 1000;
        
        setInterval(function() {
            // Silently refresh data without page reload
            fetch('/api/disease-alerts/refresh')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Check if there are new risks or outbreaks
                        Promise.all([
                            fetch('/api/disease-alerts/risks').then(resp => resp.json()),
                            fetch('/api/disease-alerts/nearby').then(resp => resp.json())
                        ])
                        .then(([risksData, outbreaksData]) => {
                            // If we got new data, show a notification
                            showToast('Auto Update', 'Disease risk data updated with latest weather conditions', 'info');
                            
                            // Reload the page to show new data
                            setTimeout(() => {
                                window.location.reload();
                            }, 3000);
                        })
                        .catch(err => console.error('Error checking for updates:', err));
                    }
                })
                .catch(error => console.error('Auto-refresh error:', error));
        }, refreshInterval);
        
        console.log('Auto-refresh timer set for disease alerts - every 30 minutes');
    }
    
    // Function to show toast notifications
    function showToast(title, message, type = 'primary') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        // Create unique ID for this toast
        const toastId = 'toast-' + Date.now();
        
        // Create toast HTML
        const toastHtml = `
            <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header bg-${type} text-white">
                    <strong class="me-auto">${title}</strong>
                    <small>just now</small>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        // Add toast to container
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        // Initialize and show the toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
        toast.show();
        
        // Remove toast from DOM after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            this.remove();
        });
    }
}); 