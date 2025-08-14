// API client for Real Estate Empire backend

class APIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
        this.defaultHeaders = {
            'Content-Type': 'application/json',
        };
    }

    /**
     * Make HTTP request
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            headers: { ...this.defaultHeaders, ...options.headers },
            ...options
        };

        try {
            const response = await fetch(url, config);
            
            // Handle different response types
            const contentType = response.headers.get('content-type');
            let data;
            
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            } else {
                data = await response.text();
            }

            if (!response.ok) {
                throw new Error(data.error || data.detail || `HTTP error! status: ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    /**
     * GET request
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        
        return this.request(url, {
            method: 'GET'
        });
    }

    /**
     * POST request
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * PUT request
     */
    async put(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    /**
     * DELETE request
     */
    async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE'
        });
    }

    // Property API methods

    /**
     * Create a new property
     */
    async createProperty(propertyData) {
        return this.post('/api/v1/properties/', propertyData);
    }

    /**
     * Get property by ID
     */
    async getProperty(propertyId) {
        return this.get(`/api/v1/properties/${propertyId}`);
    }

    /**
     * Update property
     */
    async updateProperty(propertyId, propertyData) {
        return this.put(`/api/v1/properties/${propertyId}`, propertyData);
    }

    /**
     * Delete property
     */
    async deleteProperty(propertyId) {
        return this.delete(`/api/v1/properties/${propertyId}`);
    }

    /**
     * List properties with filters
     */
    async listProperties(filters = {}) {
        return this.get('/api/v1/properties/', filters);
    }

    /**
     * Analyze property
     */
    async analyzeProperty(propertyId, analysisType = 'comprehensive') {
        return this.post(`/api/v1/properties/${propertyId}/analyze`, {}, {
            headers: {
                ...this.defaultHeaders,
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: new URLSearchParams({ analysis_type: analysisType })
        });
    }

    /**
     * Get comparable properties
     */
    async getComparableProperties(propertyId, options = {}) {
        const params = {
            max_distance: options.maxDistance || 2.0,
            max_age_days: options.maxAgeDays || 180,
            min_comps: options.minComps || 3
        };
        return this.get(`/api/v1/properties/${propertyId}/comparables`, params);
    }

    /**
     * Estimate repair costs
     */
    async estimateRepairCosts(propertyId, options = {}) {
        return this.post(`/api/v1/properties/${propertyId}/repair-estimate`, {
            photos: options.photos || null,
            description: options.description || null,
            condition_override: options.conditionOverride || null
        });
    }

    /**
     * Get property analyses
     */
    async getPropertyAnalyses(propertyId, options = {}) {
        const params = {
            analysis_type: options.analysisType || null,
            limit: options.limit || 10
        };
        return this.get(`/api/v1/properties/${propertyId}/analyses`, params);
    }

    // Strategy Analysis API methods

    /**
     * Analyze flip strategy
     */
    async analyzeFlipStrategy(propertyId, options = {}) {
        return this.post('/api/v1/strategies/flip', {
            property_id: propertyId,
            purchase_price: options.purchasePrice,
            repair_budget: options.repairBudget,
            holding_period: options.holdingPeriod || 6
        });
    }

    /**
     * Analyze rental strategy
     */
    async analyzeRentalStrategy(propertyId, options = {}) {
        return this.post('/api/v1/strategies/rental', {
            property_id: propertyId,
            purchase_price: options.purchasePrice,
            down_payment: options.downPayment,
            interest_rate: options.interestRate,
            loan_term: options.loanTerm || 30
        });
    }

    /**
     * Analyze wholesale strategy
     */
    async analyzeWholesaleStrategy(propertyId, options = {}) {
        return this.post('/api/v1/strategies/wholesale', {
            property_id: propertyId,
            contract_price: options.contractPrice,
            assignment_fee: options.assignmentFee
        });
    }

    /**
     * Analyze BRRRR strategy
     */
    async analyzeBRRRRStrategy(propertyId, options = {}) {
        return this.post('/api/v1/strategies/brrrr', {
            property_id: propertyId,
            purchase_price: options.purchasePrice,
            repair_budget: options.repairBudget,
            refinance_ltv: options.refinanceLTV || 0.75
        });
    }

    /**
     * Compare strategies
     */
    async compareStrategies(propertyId, strategies = []) {
        return this.post('/api/v1/strategies/compare', {
            property_id: propertyId,
            strategies: strategies
        });
    }

    // Data Export API methods

    /**
     * Export property analysis to PDF
     */
    async exportToPDF(propertyId, analysisId) {
        return this.get(`/api/v1/export/pdf/${propertyId}/${analysisId}`);
    }

    /**
     * Export property data to CSV
     */
    async exportToCSV(propertyIds = []) {
        return this.post('/api/v1/export/csv', {
            property_ids: propertyIds
        });
    }

    /**
     * Export analysis data to JSON
     */
    async exportToJSON(propertyId, analysisId) {
        return this.get(`/api/v1/export/json/${propertyId}/${analysisId}`);
    }

    // Address lookup and validation

    /**
     * Lookup address suggestions
     */
    async lookupAddress(query) {
        // This would typically use a geocoding service like Google Maps API
        // For now, we'll return a mock response
        return new Promise((resolve) => {
            setTimeout(() => {
                const mockSuggestions = [
                    {
                        address: `${query} Main St`,
                        city: 'Anytown',
                        state: 'CA',
                        zip_code: '90210',
                        latitude: 34.0522,
                        longitude: -118.2437
                    },
                    {
                        address: `${query} Oak Ave`,
                        city: 'Somewhere',
                        state: 'CA',
                        zip_code: '90211',
                        latitude: 34.0622,
                        longitude: -118.2537
                    }
                ];
                resolve(mockSuggestions);
            }, 300);
        });
    }

    /**
     * Validate address
     */
    async validateAddress(address) {
        // Mock address validation
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve({
                    valid: true,
                    formatted_address: address.address,
                    latitude: 34.0522,
                    longitude: -118.2437,
                    components: {
                        street_number: '123',
                        route: 'Main St',
                        locality: address.city,
                        administrative_area_level_1: address.state,
                        postal_code: address.zip_code,
                        country: 'US'
                    }
                });
            }, 500);
        });
    }

    // File upload methods

    /**
     * Upload property photos
     */
    async uploadPhotos(files) {
        const formData = new FormData();
        files.forEach((file, index) => {
            formData.append(`photo_${index}`, file);
        });

        return this.request('/api/v1/properties/upload-photos', {
            method: 'POST',
            headers: {}, // Remove Content-Type to let browser set it for FormData
            body: formData
        });
    }

    /**
     * Health check
     */
    async healthCheck() {
        return this.get('/health');
    }
}

// Create global API client instance
window.API = new APIClient();

// Export for use in modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}