// Form validation utilities

class FormValidator {
    constructor() {
        this.rules = {};
        this.messages = {};
        this.errors = {};
    }

    /**
     * Add validation rule for a field
     */
    addRule(fieldName, rule, message) {
        if (!this.rules[fieldName]) {
            this.rules[fieldName] = [];
        }
        this.rules[fieldName].push(rule);
        
        if (!this.messages[fieldName]) {
            this.messages[fieldName] = [];
        }
        this.messages[fieldName].push(message);
    }

    /**
     * Validate a single field
     */
    validateField(fieldName, value) {
        const rules = this.rules[fieldName];
        const messages = this.messages[fieldName];
        
        if (!rules) return { valid: true };

        for (let i = 0; i < rules.length; i++) {
            const rule = rules[i];
            const message = messages[i];
            
            if (typeof rule === 'function') {
                if (!rule(value)) {
                    return { valid: false, message };
                }
            } else if (typeof rule === 'object' && rule.test) {
                if (!rule.test(value)) {
                    return { valid: false, message };
                }
            }
        }

        return { valid: true };
    }

    /**
     * Validate all fields in a form
     */
    validateForm(formData) {
        const errors = {};
        let isValid = true;

        for (const fieldName in this.rules) {
            const value = formData[fieldName];
            const result = this.validateField(fieldName, value);
            
            if (!result.valid) {
                errors[fieldName] = result.message;
                isValid = false;
            }
        }

        this.errors = errors;
        return { valid: isValid, errors };
    }

    /**
     * Clear validation errors
     */
    clearErrors() {
        this.errors = {};
    }

    /**
     * Get error for a specific field
     */
    getError(fieldName) {
        return this.errors[fieldName];
    }
}

// Common validation rules
const ValidationRules = {
    required: (value) => {
        if (value === null || value === undefined) return false;
        if (typeof value === 'string') return value.trim() !== '';
        if (Array.isArray(value)) return value.length > 0;
        return true;
    },

    email: (value) => {
        if (!value) return true; // Allow empty for optional fields
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(value);
    },

    phone: (value) => {
        if (!value) return true; // Allow empty for optional fields
        const phoneRegex = /^\(?([0-9]{3})\)?[-. ]?([0-9]{3})[-. ]?([0-9]{4})$/;
        return phoneRegex.test(value);
    },

    zipCode: (value) => {
        if (!value) return true; // Allow empty for optional fields
        const zipRegex = /^\d{5}(-\d{4})?$/;
        return zipRegex.test(value);
    },

    minLength: (min) => (value) => {
        if (!value) return true; // Allow empty for optional fields
        return value.length >= min;
    },

    maxLength: (max) => (value) => {
        if (!value) return true; // Allow empty for optional fields
        return value.length <= max;
    },

    min: (min) => (value) => {
        if (value === '' || value === null || value === undefined) return true;
        return parseFloat(value) >= min;
    },

    max: (max) => (value) => {
        if (value === '' || value === null || value === undefined) return true;
        return parseFloat(value) <= max;
    },

    numeric: (value) => {
        if (!value) return true; // Allow empty for optional fields
        return !isNaN(value) && !isNaN(parseFloat(value));
    },

    integer: (value) => {
        if (!value) return true; // Allow empty for optional fields
        return Number.isInteger(parseFloat(value));
    },

    positive: (value) => {
        if (!value) return true; // Allow empty for optional fields
        return parseFloat(value) > 0;
    },

    range: (min, max) => (value) => {
        if (!value) return true; // Allow empty for optional fields
        const num = parseFloat(value);
        return num >= min && num <= max;
    },

    year: (value) => {
        if (!value) return true; // Allow empty for optional fields
        const year = parseInt(value);
        const currentYear = new Date().getFullYear();
        return year >= 1800 && year <= currentYear + 1;
    },

    url: (value) => {
        if (!value) return true; // Allow empty for optional fields
        try {
            new URL(value);
            return true;
        } catch {
            return false;
        }
    }
};

// Property form validation setup
function setupPropertyFormValidation() {
    const validator = new FormValidator();

    // Address validation
    validator.addRule('address', ValidationRules.required, 'Street address is required');
    validator.addRule('address', ValidationRules.minLength(5), 'Address must be at least 5 characters');

    validator.addRule('city', ValidationRules.required, 'City is required');
    validator.addRule('city', ValidationRules.minLength(2), 'City must be at least 2 characters');

    validator.addRule('state', ValidationRules.required, 'State is required');

    validator.addRule('zip_code', ValidationRules.required, 'ZIP code is required');
    validator.addRule('zip_code', ValidationRules.zipCode, 'Please enter a valid ZIP code');

    // Property details validation
    validator.addRule('property_type', ValidationRules.required, 'Property type is required');

    validator.addRule('bedrooms', ValidationRules.integer, 'Bedrooms must be a whole number');
    validator.addRule('bedrooms', ValidationRules.min(0), 'Bedrooms cannot be negative');
    validator.addRule('bedrooms', ValidationRules.max(50), 'Bedrooms seems too high');

    validator.addRule('bathrooms', ValidationRules.numeric, 'Bathrooms must be a number');
    validator.addRule('bathrooms', ValidationRules.min(0), 'Bathrooms cannot be negative');
    validator.addRule('bathrooms', ValidationRules.max(50), 'Bathrooms seems too high');

    validator.addRule('square_feet', ValidationRules.integer, 'Square feet must be a whole number');
    validator.addRule('square_feet', ValidationRules.positive, 'Square feet must be positive');
    validator.addRule('square_feet', ValidationRules.max(50000), 'Square feet seems too high');

    validator.addRule('lot_size', ValidationRules.numeric, 'Lot size must be a number');
    validator.addRule('lot_size', ValidationRules.positive, 'Lot size must be positive');
    validator.addRule('lot_size', ValidationRules.max(1000), 'Lot size seems too high');

    validator.addRule('year_built', ValidationRules.year, 'Please enter a valid year');

    validator.addRule('stories', ValidationRules.integer, 'Stories must be a whole number');
    validator.addRule('stories', ValidationRules.range(1, 10), 'Stories must be between 1 and 10');

    validator.addRule('garage_spaces', ValidationRules.integer, 'Garage spaces must be a whole number');
    validator.addRule('garage_spaces', ValidationRules.min(0), 'Garage spaces cannot be negative');
    validator.addRule('garage_spaces', ValidationRules.max(20), 'Garage spaces seems too high');

    // Financial validation
    validator.addRule('listing_price', ValidationRules.numeric, 'Listing price must be a number');
    validator.addRule('listing_price', ValidationRules.positive, 'Listing price must be positive');

    validator.addRule('current_value', ValidationRules.numeric, 'Current value must be a number');
    validator.addRule('current_value', ValidationRules.positive, 'Current value must be positive');

    validator.addRule('assessed_value', ValidationRules.numeric, 'Assessed value must be a number');
    validator.addRule('assessed_value', ValidationRules.positive, 'Assessed value must be positive');

    validator.addRule('tax_amount', ValidationRules.numeric, 'Tax amount must be a number');
    validator.addRule('tax_amount', ValidationRules.min(0), 'Tax amount cannot be negative');

    validator.addRule('last_sale_price', ValidationRules.numeric, 'Last sale price must be a number');
    validator.addRule('last_sale_price', ValidationRules.positive, 'Last sale price must be positive');

    // Condition validation
    validator.addRule('condition_score', ValidationRules.range(0, 1), 'Condition score must be between 0 and 1');

    validator.addRule('days_on_market', ValidationRules.integer, 'Days on market must be a whole number');
    validator.addRule('days_on_market', ValidationRules.min(0), 'Days on market cannot be negative');

    return validator;
}

// Visual validation feedback
function showFieldError(fieldName, message) {
    const field = document.getElementById(fieldName);
    const formGroup = field?.closest('.form-group');
    const errorElement = document.getElementById(`${fieldName}-error`);

    if (formGroup) {
        formGroup.classList.add('error');
        formGroup.classList.remove('success');
    }

    if (errorElement) {
        errorElement.textContent = message;
        errorElement.classList.add('show');
    }
}

function showFieldSuccess(fieldName) {
    const field = document.getElementById(fieldName);
    const formGroup = field?.closest('.form-group');
    const errorElement = document.getElementById(`${fieldName}-error`);

    if (formGroup) {
        formGroup.classList.add('success');
        formGroup.classList.remove('error');
    }

    if (errorElement) {
        errorElement.classList.remove('show');
    }
}

function clearFieldValidation(fieldName) {
    const field = document.getElementById(fieldName);
    const formGroup = field?.closest('.form-group');
    const errorElement = document.getElementById(`${fieldName}-error`);

    if (formGroup) {
        formGroup.classList.remove('error', 'success');
    }

    if (errorElement) {
        errorElement.classList.remove('show');
    }
}

function clearAllValidation() {
    const formGroups = document.querySelectorAll('.form-group');
    const errorElements = document.querySelectorAll('.field-error');

    formGroups.forEach(group => {
        group.classList.remove('error', 'success');
    });

    errorElements.forEach(error => {
        error.classList.remove('show');
    });
}

// Real-time validation
function setupRealTimeValidation(validator) {
    const form = document.getElementById('property-form');
    if (!form) return;

    const fields = form.querySelectorAll('input, select, textarea');

    fields.forEach(field => {
        // Validate on blur
        field.addEventListener('blur', () => {
            const value = field.value;
            const result = validator.validateField(field.name, value);

            if (value && !result.valid) {
                showFieldError(field.name, result.message);
            } else if (value) {
                showFieldSuccess(field.name);
            } else {
                clearFieldValidation(field.name);
            }
        });

        // Clear validation on focus
        field.addEventListener('focus', () => {
            clearFieldValidation(field.name);
        });

        // Validate on input for certain fields
        if (field.type === 'email' || field.type === 'tel' || field.name === 'zip_code') {
            field.addEventListener('input', Utils.debounce(() => {
                const value = field.value;
                if (value) {
                    const result = validator.validateField(field.name, value);
                    if (!result.valid) {
                        showFieldError(field.name, result.message);
                    } else {
                        showFieldSuccess(field.name);
                    }
                }
            }, 500));
        }
    });
}

// Export validation utilities
window.FormValidator = FormValidator;
window.ValidationRules = ValidationRules;
window.PropertyFormValidation = {
    setupPropertyFormValidation,
    showFieldError,
    showFieldSuccess,
    clearFieldValidation,
    clearAllValidation,
    setupRealTimeValidation
};