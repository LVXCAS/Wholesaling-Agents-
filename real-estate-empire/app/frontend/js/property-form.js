// Property form functionality

class PropertyForm {
    constructor() {
        this.form = document.getElementById('property-form');
        this.validator = null;
        this.uploadedPhotos = [];
        this.addressSuggestions = [];
        
        this.init();
    }

    init() {
        if (!this.form) return;

        // Setup validation
        this.validator = PropertyFormValidation.setupPropertyFormValidation();
        PropertyFormValidation.setupRealTimeValidation(this.validator);

        // Setup event listeners
        this.setupEventListeners();
        
        // Setup address lookup
        this.setupAddressLookup();
        
        // Setup photo upload
        this.setupPhotoUpload();
        
        // Setup form auto-save
        this.setupAutoSave();
    }

    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => this.handleSubmit(e));

        // Clear form button
        const clearBtn = document.getElementById('clear-form');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearForm());
        }

        // Condition score slider
        const conditionSlider = document.getElementById('condition_score');
        const conditionValue = document.getElementById('condition-value');
        if (conditionSlider && conditionValue) {
            conditionSlider.addEventListener('input', (e) => {
                conditionValue.textContent = parseFloat(e.target.value).toFixed(1);
            });
        }

        // Property type change
        const propertyType = document.getElementById('property_type');
        if (propertyType) {
            propertyType.addEventListener('change', (e) => {
                this.handlePropertyTypeChange(e.target.value);
            });
        }

        // Numeric field formatting
        this.setupNumericFields();
    }

    setupNumericFields() {
        const numericFields = [
            'listing_price', 'current_value', 'assessed_value', 
            'tax_amount', 'last_sale_price'
        ];

        numericFields.forEach(fieldName => {
            const field = document.getElementById(fieldName);
            if (field) {
                field.addEventListener('blur', (e) => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value)) {
                        e.target.value = value.toLocaleString();
                    }
                });

                field.addEventListener('focus', (e) => {
                    const value = e.target.value.replace(/,/g, '');
                    if (!isNaN(parseFloat(value))) {
                        e.target.value = value;
                    }
                });
            }
        });
    }

    setupAddressLookup() {
        const addressSearch = document.getElementById('address-search');
        const lookupBtn = document.getElementById('address-lookup-btn');
        const suggestionsContainer = document.getElementById('address-suggestions');

        if (!addressSearch || !lookupBtn || !suggestionsContainer) return;

        // Search on input with debounce
        addressSearch.addEventListener('input', Utils.debounce((e) => {
            const query = e.target.value.trim();
            if (query.length >= 3) {
                this.searchAddresses(query);
            } else {
                this.hideSuggestions();
            }
        }, 300));

        // Search on button click
        lookupBtn.addEventListener('click', () => {
            const query = addressSearch.value.trim();
            if (query) {
                this.searchAddresses(query);
            }
        });

        // Hide suggestions when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.address-lookup')) {
                this.hideSuggestions();
            }
        });
    }

    async searchAddresses(query) {
        const suggestionsContainer = document.getElementById('address-suggestions');
        
        try {
            Utils.showLoading(true, 'Searching addresses...');
            const suggestions = await API.lookupAddress(query);
            this.addressSuggestions = suggestions;
            this.displaySuggestions(suggestions);
        } catch (error) {
            console.error('Address lookup failed:', error);
            Utils.showToast('Failed to search addresses', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    displaySuggestions(suggestions) {
        const container = document.getElementById('address-suggestions');
        
        if (suggestions.length === 0) {
            container.innerHTML = '<div class="address-suggestion">No addresses found</div>';
            return;
        }

        container.innerHTML = suggestions.map(suggestion => `
            <div class="address-suggestion" data-suggestion='${JSON.stringify(suggestion)}'>
                <strong>${suggestion.address}</strong><br>
                <small>${suggestion.city}, ${suggestion.state} ${suggestion.zip_code}</small>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.address-suggestion').forEach(item => {
            item.addEventListener('click', (e) => {
                const suggestion = JSON.parse(e.currentTarget.dataset.suggestion);
                this.selectAddress(suggestion);
            });
        });
    }

    selectAddress(suggestion) {
        // Fill in address fields
        document.getElementById('address').value = suggestion.address;
        document.getElementById('city').value = suggestion.city;
        document.getElementById('state').value = suggestion.state;
        document.getElementById('zip_code').value = suggestion.zip_code;

        // Clear search and hide suggestions
        document.getElementById('address-search').value = '';
        this.hideSuggestions();

        // Validate filled fields
        ['address', 'city', 'state', 'zip_code'].forEach(field => {
            const element = document.getElementById(field);
            const result = this.validator.validateField(field, element.value);
            if (result.valid) {
                PropertyFormValidation.showFieldSuccess(field);
            }
        });

        Utils.showToast('Address selected successfully', 'success');
    }

    hideSuggestions() {
        const container = document.getElementById('address-suggestions');
        container.innerHTML = '';
    }

    setupPhotoUpload() {
        const uploadZone = document.getElementById('photo-upload-zone');
        const photoInput = document.getElementById('photo-input');
        const previewContainer = document.getElementById('photo-preview');

        if (!uploadZone || !photoInput || !previewContainer) return;

        // Drag and drop
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');
            
            const files = Array.from(e.dataTransfer.files);
            this.handlePhotoFiles(files);
        });

        // File input change
        photoInput.addEventListener('change', (e) => {
            const files = Array.from(e.target.files);
            this.handlePhotoFiles(files);
        });

        // Click to upload
        uploadZone.addEventListener('click', (e) => {
            if (e.target.tagName !== 'BUTTON') {
                photoInput.click();
            }
        });
    }

    handlePhotoFiles(files) {
        files.forEach(file => {
            const validation = Utils.isValidImageFile(file);
            
            if (!validation.valid) {
                Utils.showToast(validation.error, 'error');
                return;
            }

            this.addPhoto(file);
        });
    }

    addPhoto(file) {
        const photoId = Utils.generateUUID();
        const photoData = {
            id: photoId,
            file: file,
            name: file.name,
            size: file.size,
            url: null
        };

        this.uploadedPhotos.push(photoData);

        // Create preview
        Utils.createImagePreview(file, (dataUrl) => {
            photoData.url = dataUrl;
            this.renderPhotoPreview(photoData);
        });
    }

    renderPhotoPreview(photoData) {
        const previewContainer = document.getElementById('photo-preview');
        
        const photoElement = document.createElement('div');
        photoElement.className = 'photo-item';
        photoElement.dataset.photoId = photoData.id;
        
        photoElement.innerHTML = `
            <img src="${photoData.url}" alt="${photoData.name}">
            <button type="button" class="photo-remove" onclick="propertyForm.removePhoto('${photoData.id}')">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        previewContainer.appendChild(photoElement);
    }

    removePhoto(photoId) {
        // Remove from array
        this.uploadedPhotos = this.uploadedPhotos.filter(photo => photo.id !== photoId);
        
        // Remove from DOM
        const photoElement = document.querySelector(`[data-photo-id="${photoId}"]`);
        if (photoElement) {
            photoElement.remove();
        }
    }

    handlePropertyTypeChange(propertyType) {
        // Show/hide relevant fields based on property type
        const commercialFields = ['square_feet', 'lot_size'];
        const residentialFields = ['bedrooms', 'bathrooms', 'stories', 'garage_spaces'];

        if (propertyType === 'commercial') {
            // Hide residential-specific fields for commercial properties
            residentialFields.forEach(fieldName => {
                const field = document.getElementById(fieldName);
                const formGroup = field?.closest('.form-group');
                if (formGroup) {
                    formGroup.style.display = 'none';
                }
            });
        } else if (propertyType === 'land') {
            // Hide building-specific fields for land
            [...residentialFields, 'square_feet', 'year_built', 'stories'].forEach(fieldName => {
                const field = document.getElementById(fieldName);
                const formGroup = field?.closest('.form-group');
                if (formGroup) {
                    formGroup.style.display = 'none';
                }
            });
        } else {
            // Show all fields for other property types
            [...residentialFields, ...commercialFields, 'year_built'].forEach(fieldName => {
                const field = document.getElementById(fieldName);
                const formGroup = field?.closest('.form-group');
                if (formGroup) {
                    formGroup.style.display = '';
                }
            });
        }
    }

    setupAutoSave() {
        // Auto-save form data to localStorage every 30 seconds
        setInterval(() => {
            this.saveFormData();
        }, 30000);

        // Save on form change
        this.form.addEventListener('change', Utils.debounce(() => {
            this.saveFormData();
        }, 2000));

        // Load saved data on page load
        this.loadFormData();
    }

    saveFormData() {
        const formData = this.getFormData();
        Utils.storage.set('property-form-draft', {
            data: formData,
            timestamp: new Date().toISOString()
        });
    }

    loadFormData() {
        const saved = Utils.storage.get('property-form-draft');
        
        if (saved && saved.data) {
            // Check if saved data is recent (within 24 hours)
            const savedTime = new Date(saved.timestamp);
            const now = new Date();
            const hoursDiff = (now - savedTime) / (1000 * 60 * 60);
            
            if (hoursDiff < 24) {
                this.populateForm(saved.data);
                Utils.showToast('Draft data restored', 'info');
            }
        }
    }

    getFormData() {
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            // Convert numeric fields
            if (['bedrooms', 'bathrooms', 'square_feet', 'lot_size', 'year_built', 
                 'stories', 'garage_spaces', 'listing_price', 'current_value', 
                 'assessed_value', 'tax_amount', 'last_sale_price', 'days_on_market'].includes(key)) {
                data[key] = value ? parseFloat(value.replace(/,/g, '')) : null;
            }
            // Convert boolean fields
            else if (key === 'renovation_needed') {
                data[key] = formData.has(key);
            }
            // Convert date fields
            else if (key === 'last_sale_date') {
                data[key] = value || null;
            }
            // Convert condition score
            else if (key === 'condition_score') {
                data[key] = value ? parseFloat(value) : null;
            }
            // String fields
            else {
                data[key] = value || null;
            }
        }

        return data;
    }

    populateForm(data) {
        Object.keys(data).forEach(key => {
            const field = document.getElementById(key);
            if (field && data[key] !== null) {
                if (field.type === 'checkbox') {
                    field.checked = data[key];
                } else {
                    field.value = data[key];
                }
            }
        });

        // Update condition score display
        const conditionValue = document.getElementById('condition-value');
        if (conditionValue && data.condition_score) {
            conditionValue.textContent = parseFloat(data.condition_score).toFixed(1);
        }
    }

    async handleSubmit(e) {
        e.preventDefault();
        
        const formData = this.getFormData();
        
        // Validate form
        const validation = this.validator.validateForm(formData);
        
        if (!validation.valid) {
            // Show validation errors
            Object.keys(validation.errors).forEach(field => {
                PropertyFormValidation.showFieldError(field, validation.errors[field]);
            });
            
            Utils.showToast('Please fix the errors in the form', 'error');
            
            // Scroll to first error
            const firstErrorField = Object.keys(validation.errors)[0];
            const firstErrorElement = document.getElementById(firstErrorField);
            if (firstErrorElement) {
                Utils.scrollToElement(firstErrorElement, 100);
            }
            
            return;
        }

        try {
            Utils.showLoading(true, 'Saving property...');
            
            // Upload photos first if any
            if (this.uploadedPhotos.length > 0) {
                const photoFiles = this.uploadedPhotos.map(photo => photo.file);
                const uploadResult = await API.uploadPhotos(photoFiles);
                formData.photos = uploadResult.photo_urls;
            }

            // Create property
            const result = await API.createProperty(formData);
            
            Utils.showToast('Property saved successfully!', 'success');
            
            // Clear form and saved data
            this.clearForm();
            Utils.storage.remove('property-form-draft');
            
            // Optionally redirect to property details or analysis
            if (confirm('Property saved! Would you like to analyze this property now?')) {
                this.analyzeProperty(result.id);
            }
            
        } catch (error) {
            console.error('Error saving property:', error);
            Utils.showToast(`Failed to save property: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async analyzeProperty(propertyId) {
        try {
            Utils.showLoading(true, 'Analyzing property...');
            
            const analysis = await API.analyzeProperty(propertyId, 'comprehensive');
            
            Utils.showToast('Property analysis completed!', 'success');
            
            // Switch to financial dashboard tab and show results
            this.showAnalysisResults(analysis);
            
        } catch (error) {
            console.error('Error analyzing property:', error);
            Utils.showToast(`Failed to analyze property: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    showAnalysisResults(analysis) {
        // Switch to financial dashboard tab
        const dashboardTab = document.querySelector('[data-tab="financial-dashboard"]');
        const dashboardContent = document.getElementById('financial-dashboard');
        
        if (dashboardTab && dashboardContent) {
            // Update active tab
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            dashboardTab.classList.add('active');
            dashboardContent.classList.add('active');
            
            // TODO: Populate dashboard with analysis results
            // This will be implemented in subtask 4.2
        }
    }

    clearForm() {
        this.form.reset();
        this.uploadedPhotos = [];
        
        // Clear photo preview
        const previewContainer = document.getElementById('photo-preview');
        if (previewContainer) {
            previewContainer.innerHTML = '';
        }
        
        // Clear validation
        PropertyFormValidation.clearAllValidation();
        
        // Reset condition score display
        const conditionValue = document.getElementById('condition-value');
        if (conditionValue) {
            conditionValue.textContent = '0.7';
        }
        
        // Show all form groups (in case they were hidden by property type)
        this.form.querySelectorAll('.form-group').forEach(group => {
            group.style.display = '';
        });
        
        Utils.showToast('Form cleared', 'info');
    }
}

// Initialize property form when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.propertyForm = new PropertyForm();
});