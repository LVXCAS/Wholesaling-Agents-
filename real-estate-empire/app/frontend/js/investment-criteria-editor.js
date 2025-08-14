/**
 * Investment Criteria Editor
 * Implements criteria form interface, template management, testing tool, and impact visualization
 */

class InvestmentCriteriaEditor {
    constructor() {
        this.currentCriteria = null;
        this.templates = [];
        this.testResults = null;
        this.impactData = null;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadTemplates();
        this.initializeForm();
    }

    setupEventListeners() {
        // Template management
        document.getElementById('load-template-btn')?.addEventListener('click', () => {
            this.showTemplateSelector();
        });

        document.getElementById('save-template-btn')?.addEventListener('click', () => {
            this.saveAsTemplate();
        });

        document.getElementById('new-criteria-btn')?.addEventListener('click', () => {
            this.createNewCriteria();
        });

        // Form submission
        document.getElementById('save-criteria-btn')?.addEventListener('click', () => {
            this.saveCriteria();
        });

        document.getElementById('test-criteria-btn')?.addEventListener('click', () => {
            this.testCriteria();
        });

        // Template selector events
        document.getElementById('template-selector')?.addEventListener('change', (e) => {
            if (e.target.value) {
                this.loadTemplate(e.target.value);
            }
        });

        // Form change events for impact visualization
        const form = document.getElementById('criteria-form');
        if (form) {
            form.addEventListener('input', Utils.debounce(() => {
                this.updateImpactVisualization();
            }, 500));
        }

        // Strategy type change
        document.getElementById('strategy-type')?.addEventListener('change', (e) => {
            this.updateFormForStrategy(e.target.value);
        });

        // Range sliders
        this.setupRangeSliders();
    }

    setupRangeSliders() {
        const sliders = document.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            const valueDisplay = document.getElementById(slider.id + '-value');
            if (valueDisplay) {
                slider.addEventListener('input', (e) => {
                    valueDisplay.textContent = this.formatSliderValue(slider.id, e.target.value);
                });
            }
        });
    }

    formatSliderValue(sliderId, value) {
        switch (sliderId) {
            case 'min-cap-rate':
            case 'min-coc-return':
            case 'min-roi':
                return value + '%';
            case 'max-price':
            case 'min-arv':
                return '$' + parseInt(value).toLocaleString();
            case 'max-repair-cost':
                return '$' + parseInt(value).toLocaleString();
            default:
                return value;
        }
    }

    async loadTemplates() {
        try {
            const response = await API.get('/api/investment-criteria/templates');
            this.templates = response;
            this.populateTemplateSelector();
        } catch (error) {
            console.error('Error loading templates:', error);
            Utils.showToast('Failed to load templates', 'error');
        }
    }

    populateTemplateSelector() {
        const selector = document.getElementById('template-selector');
        if (!selector) return;

        selector.innerHTML = '<option value="">Select a template...</option>';
        
        // Group templates by strategy
        const groupedTemplates = this.templates.reduce((groups, template) => {
            const strategy = template.strategy || 'general';
            if (!groups[strategy]) groups[strategy] = [];
            groups[strategy].push(template);
            return groups;
        }, {});

        Object.keys(groupedTemplates).forEach(strategy => {
            const optgroup = document.createElement('optgroup');
            optgroup.label = this.formatStrategyName(strategy);
            
            groupedTemplates[strategy].forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                optgroup.appendChild(option);
            });
            
            selector.appendChild(optgroup);
        });
    }

    formatStrategyName(strategy) {
        const strategyNames = {
            'flip': 'Fix & Flip',
            'rental': 'Buy & Hold Rental',
            'wholesale': 'Wholesale',
            'brrrr': 'BRRRR',
            'commercial': 'Commercial',
            'general': 'General'
        };
        return strategyNames[strategy] || strategy.charAt(0).toUpperCase() + strategy.slice(1);
    }

    initializeForm() {
        // Set default values
        this.createNewCriteria();
    }

    createNewCriteria() {
        this.currentCriteria = {
            id: null,
            name: '',
            description: '',
            strategy_type: 'rental',
            active: true,
            
            // Location criteria
            target_markets: [],
            exclude_markets: [],
            max_distance_miles: 50,
            
            // Property criteria
            property_types: ['single_family'],
            min_bedrooms: 2,
            max_bedrooms: null,
            min_bathrooms: 1,
            max_bathrooms: null,
            min_square_feet: 800,
            max_square_feet: null,
            min_year_built: 1950,
            max_year_built: null,
            
            // Financial criteria
            max_price: 300000,
            min_arv: 200000,
            max_repair_cost: 50000,
            min_cap_rate: 8.0,
            min_coc_return: 12.0,
            min_roi: 15.0,
            max_ltv: 80.0,
            min_rent_ratio: 1.0,
            
            // Deal criteria
            max_days_on_market: 90,
            min_equity_percentage: 20.0,
            require_seller_financing: false,
            allow_short_sales: true,
            allow_foreclosures: true,
            
            // Risk criteria
            max_crime_score: 7,
            min_school_rating: 5,
            flood_zone_acceptable: false,
            environmental_issues_acceptable: false
        };

        this.populateForm();
        this.updateImpactVisualization();
    }

    async loadTemplate(templateId) {
        try {
            const template = this.templates.find(t => t.id === templateId);
            if (!template) {
                Utils.showToast('Template not found', 'error');
                return;
            }

            this.currentCriteria = { ...template.criteria };
            this.currentCriteria.id = null; // New criteria based on template
            this.currentCriteria.name = `${template.name} - Copy`;

            this.populateForm();
            this.updateImpactVisualization();
            
            Utils.showToast(`Loaded template: ${template.name}`, 'success');
        } catch (error) {
            console.error('Error loading template:', error);
            Utils.showToast('Failed to load template', 'error');
        }
    }

    populateForm() {
        if (!this.currentCriteria) return;

        // Basic information
        this.setFormValue('criteria-name', this.currentCriteria.name);
        this.setFormValue('criteria-description', this.currentCriteria.description);
        this.setFormValue('strategy-type', this.currentCriteria.strategy_type);
        this.setFormValue('criteria-active', this.currentCriteria.active);

        // Location criteria
        this.setFormValue('target-markets', this.currentCriteria.target_markets.join(', '));
        this.setFormValue('exclude-markets', this.currentCriteria.exclude_markets.join(', '));
        this.setFormValue('max-distance', this.currentCriteria.max_distance_miles);

        // Property criteria
        this.setCheckboxGroup('property-types', this.currentCriteria.property_types);
        this.setFormValue('min-bedrooms', this.currentCriteria.min_bedrooms);
        this.setFormValue('max-bedrooms', this.currentCriteria.max_bedrooms);
        this.setFormValue('min-bathrooms', this.currentCriteria.min_bathrooms);
        this.setFormValue('max-bathrooms', this.currentCriteria.max_bathrooms);
        this.setFormValue('min-square-feet', this.currentCriteria.min_square_feet);
        this.setFormValue('max-square-feet', this.currentCriteria.max_square_feet);
        this.setFormValue('min-year-built', this.currentCriteria.min_year_built);
        this.setFormValue('max-year-built', this.currentCriteria.max_year_built);

        // Financial criteria
        this.setFormValue('max-price', this.currentCriteria.max_price);
        this.setFormValue('min-arv', this.currentCriteria.min_arv);
        this.setFormValue('max-repair-cost', this.currentCriteria.max_repair_cost);
        this.setFormValue('min-cap-rate', this.currentCriteria.min_cap_rate);
        this.setFormValue('min-coc-return', this.currentCriteria.min_coc_return);
        this.setFormValue('min-roi', this.currentCriteria.min_roi);
        this.setFormValue('max-ltv', this.currentCriteria.max_ltv);
        this.setFormValue('min-rent-ratio', this.currentCriteria.min_rent_ratio);

        // Deal criteria
        this.setFormValue('max-days-on-market', this.currentCriteria.max_days_on_market);
        this.setFormValue('min-equity-percentage', this.currentCriteria.min_equity_percentage);
        this.setFormValue('require-seller-financing', this.currentCriteria.require_seller_financing);
        this.setFormValue('allow-short-sales', this.currentCriteria.allow_short_sales);
        this.setFormValue('allow-foreclosures', this.currentCriteria.allow_foreclosures);

        // Risk criteria
        this.setFormValue('max-crime-score', this.currentCriteria.max_crime_score);
        this.setFormValue('min-school-rating', this.currentCriteria.min_school_rating);
        this.setFormValue('flood-zone-acceptable', this.currentCriteria.flood_zone_acceptable);
        this.setFormValue('environmental-issues-acceptable', this.currentCriteria.environmental_issues_acceptable);

        // Update strategy-specific fields
        this.updateFormForStrategy(this.currentCriteria.strategy_type);

        // Update range slider displays
        this.updateRangeDisplays();
    }

    setFormValue(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;

        if (element.type === 'checkbox') {
            element.checked = Boolean(value);
        } else {
            element.value = value || '';
        }
    }

    setCheckboxGroup(groupName, values) {
        const checkboxes = document.querySelectorAll(`input[name="${groupName}"]`);
        checkboxes.forEach(checkbox => {
            checkbox.checked = values.includes(checkbox.value);
        });
    }

    updateRangeDisplays() {
        const sliders = document.querySelectorAll('input[type="range"]');
        sliders.forEach(slider => {
            const valueDisplay = document.getElementById(slider.id + '-value');
            if (valueDisplay) {
                valueDisplay.textContent = this.formatSliderValue(slider.id, slider.value);
            }
        });
    }

    updateFormForStrategy(strategy) {
        // Show/hide strategy-specific fields
        const strategyFields = {
            'flip': ['min-arv', 'max-repair-cost', 'min-roi'],
            'rental': ['min-cap-rate', 'min-coc-return', 'min-rent-ratio'],
            'wholesale': ['min-equity-percentage', 'max-days-on-market'],
            'brrrr': ['min-arv', 'max-repair-cost', 'min-cap-rate', 'min-coc-return'],
            'commercial': ['min-cap-rate', 'max-ltv']
        };

        // Hide all strategy-specific fields first
        Object.values(strategyFields).flat().forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.closest('.form-group')?.classList.add('hidden');
            }
        });

        // Show relevant fields for current strategy
        const relevantFields = strategyFields[strategy] || [];
        relevantFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.closest('.form-group')?.classList.remove('hidden');
            }
        });
    }

    collectFormData() {
        const formData = {
            name: this.getFormValue('criteria-name'),
            description: this.getFormValue('criteria-description'),
            strategy_type: this.getFormValue('strategy-type'),
            active: this.getFormValue('criteria-active', 'boolean'),

            // Location criteria
            target_markets: this.getFormValue('target-markets').split(',').map(s => s.trim()).filter(s => s),
            exclude_markets: this.getFormValue('exclude-markets').split(',').map(s => s.trim()).filter(s => s),
            max_distance_miles: this.getFormValue('max-distance', 'number'),

            // Property criteria
            property_types: this.getCheckboxGroupValues('property-types'),
            min_bedrooms: this.getFormValue('min-bedrooms', 'number'),
            max_bedrooms: this.getFormValue('max-bedrooms', 'number'),
            min_bathrooms: this.getFormValue('min-bathrooms', 'number'),
            max_bathrooms: this.getFormValue('max-bathrooms', 'number'),
            min_square_feet: this.getFormValue('min-square-feet', 'number'),
            max_square_feet: this.getFormValue('max-square-feet', 'number'),
            min_year_built: this.getFormValue('min-year-built', 'number'),
            max_year_built: this.getFormValue('max-year-built', 'number'),

            // Financial criteria
            max_price: this.getFormValue('max-price', 'number'),
            min_arv: this.getFormValue('min-arv', 'number'),
            max_repair_cost: this.getFormValue('max-repair-cost', 'number'),
            min_cap_rate: this.getFormValue('min-cap-rate', 'number'),
            min_coc_return: this.getFormValue('min-coc-return', 'number'),
            min_roi: this.getFormValue('min-roi', 'number'),
            max_ltv: this.getFormValue('max-ltv', 'number'),
            min_rent_ratio: this.getFormValue('min-rent-ratio', 'number'),

            // Deal criteria
            max_days_on_market: this.getFormValue('max-days-on-market', 'number'),
            min_equity_percentage: this.getFormValue('min-equity-percentage', 'number'),
            require_seller_financing: this.getFormValue('require-seller-financing', 'boolean'),
            allow_short_sales: this.getFormValue('allow-short-sales', 'boolean'),
            allow_foreclosures: this.getFormValue('allow-foreclosures', 'boolean'),

            // Risk criteria
            max_crime_score: this.getFormValue('max-crime-score', 'number'),
            min_school_rating: this.getFormValue('min-school-rating', 'number'),
            flood_zone_acceptable: this.getFormValue('flood-zone-acceptable', 'boolean'),
            environmental_issues_acceptable: this.getFormValue('environmental-issues-acceptable', 'boolean')
        };

        return formData;
    }

    getFormValue(elementId, type = 'string') {
        const element = document.getElementById(elementId);
        if (!element) return type === 'boolean' ? false : null;

        if (type === 'boolean') {
            return element.type === 'checkbox' ? element.checked : Boolean(element.value);
        } else if (type === 'number') {
            const value = parseFloat(element.value);
            return isNaN(value) ? null : value;
        } else {
            return element.value.trim() || null;
        }
    }

    getCheckboxGroupValues(groupName) {
        const checkboxes = document.querySelectorAll(`input[name="${groupName}"]:checked`);
        return Array.from(checkboxes).map(cb => cb.value);
    }

    async saveCriteria() {
        try {
            const formData = this.collectFormData();
            
            // Validate required fields
            if (!formData.name) {
                Utils.showToast('Please enter a criteria name', 'error');
                return;
            }

            if (!formData.strategy_type) {
                Utils.showToast('Please select a strategy type', 'error');
                return;
            }

            Utils.showLoading(true, 'Saving criteria...');

            let response;
            if (this.currentCriteria?.id) {
                // Update existing criteria
                response = await API.put(`/api/investment-criteria/criteria/${this.currentCriteria.id}`, formData);
            } else {
                // Create new criteria
                response = await API.post('/api/investment-criteria/criteria', formData);
            }

            this.currentCriteria = response;
            Utils.showToast('Criteria saved successfully', 'success');

        } catch (error) {
            console.error('Error saving criteria:', error);
            Utils.showToast('Failed to save criteria', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async saveAsTemplate() {
        try {
            const formData = this.collectFormData();
            
            if (!formData.name) {
                Utils.showToast('Please enter a criteria name', 'error');
                return;
            }

            const templateName = prompt('Enter template name:', `${formData.name} Template`);
            if (!templateName) return;

            const templateData = {
                name: templateName,
                description: `Template based on ${formData.name}`,
                strategy: formData.strategy_type,
                criteria: formData,
                is_public: false
            };

            Utils.showLoading(true, 'Saving template...');

            await API.post('/api/investment-criteria/templates', templateData);
            
            // Reload templates
            await this.loadTemplates();
            
            Utils.showToast('Template saved successfully', 'success');

        } catch (error) {
            console.error('Error saving template:', error);
            Utils.showToast('Failed to save template', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async testCriteria() {
        try {
            const formData = this.collectFormData();
            
            Utils.showLoading(true, 'Testing criteria...');

            // Get sample properties for testing
            const sampleProperties = await API.get('/api/v1/leads', { limit: 100 });
            
            if (sampleProperties.length === 0) {
                Utils.showToast('No properties available for testing', 'warning');
                return;
            }

            // Test criteria against sample properties
            const testResults = await API.post('/api/investment-criteria/validate-criteria', formData);
            
            if (testResults.valid) {
                // Run evaluation on sample properties
                const evaluationResults = await this.evaluatePropertiesAgainstCriteria(sampleProperties, formData);
                this.showTestResults(evaluationResults);
            } else {
                Utils.showToast(`Criteria validation failed: ${testResults.message}`, 'error');
            }

        } catch (error) {
            console.error('Error testing criteria:', error);
            Utils.showToast('Failed to test criteria', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async evaluatePropertiesAgainstCriteria(properties, criteria) {
        // Client-side evaluation for testing purposes
        const results = {
            total_properties: properties.length,
            matching_properties: 0,
            matches: [],
            rejection_reasons: {}
        };

        properties.forEach(property => {
            const evaluation = this.evaluateProperty(property, criteria);
            
            if (evaluation.matches) {
                results.matching_properties++;
                results.matches.push({
                    property: property,
                    score: evaluation.score,
                    reasons: evaluation.reasons
                });
            } else {
                evaluation.rejectionReasons.forEach(reason => {
                    results.rejection_reasons[reason] = (results.rejection_reasons[reason] || 0) + 1;
                });
            }
        });

        return results;
    }

    evaluateProperty(property, criteria) {
        const evaluation = {
            matches: true,
            score: 100,
            reasons: [],
            rejectionReasons: []
        };

        // Price criteria
        if (criteria.max_price && property.listing_price > criteria.max_price) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Price too high');
        }

        // Property type
        if (criteria.property_types.length > 0 && !criteria.property_types.includes(property.property_type)) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Property type not allowed');
        }

        // Bedrooms
        if (criteria.min_bedrooms && property.bedrooms < criteria.min_bedrooms) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Too few bedrooms');
        }

        if (criteria.max_bedrooms && property.bedrooms > criteria.max_bedrooms) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Too many bedrooms');
        }

        // Bathrooms
        if (criteria.min_bathrooms && property.bathrooms < criteria.min_bathrooms) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Too few bathrooms');
        }

        // Square feet
        if (criteria.min_square_feet && property.square_feet < criteria.min_square_feet) {
            evaluation.matches = false;
            evaluation.rejectionReasons.push('Too small');
        }

        // Lead score bonus
        if (property.lead_score) {
            evaluation.score += property.lead_score * 0.2;
        }

        return evaluation;
    }

    showTestResults(results) {
        const modal = document.getElementById('test-results-modal');
        const content = document.getElementById('test-results-content');
        
        if (!modal || !content) return;

        const matchPercentage = (results.matching_properties / results.total_properties * 100).toFixed(1);
        
        content.innerHTML = `
            <div class="test-results">
                <div class="results-summary">
                    <h3>Test Results Summary</h3>
                    <div class="summary-stats">
                        <div class="stat-item">
                            <div class="stat-value">${results.total_properties}</div>
                            <div class="stat-label">Total Properties Tested</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${results.matching_properties}</div>
                            <div class="stat-label">Matching Properties</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${matchPercentage}%</div>
                            <div class="stat-label">Match Rate</div>
                        </div>
                    </div>
                </div>

                <div class="rejection-reasons">
                    <h4>Common Rejection Reasons</h4>
                    <div class="reasons-list">
                        ${Object.entries(results.rejection_reasons)
                            .sort(([,a], [,b]) => b - a)
                            .slice(0, 5)
                            .map(([reason, count]) => `
                                <div class="reason-item">
                                    <span class="reason-text">${reason}</span>
                                    <span class="reason-count">${count} properties</span>
                                </div>
                            `).join('')}
                    </div>
                </div>

                <div class="matching-properties">
                    <h4>Top Matching Properties</h4>
                    <div class="matches-list">
                        ${results.matches
                            .sort((a, b) => b.score - a.score)
                            .slice(0, 5)
                            .map(match => `
                                <div class="match-item">
                                    <div class="match-property">
                                        <strong>${match.property.property_address || 'Address not available'}</strong>
                                        <span class="match-score">Score: ${match.score.toFixed(1)}</span>
                                    </div>
                                    <div class="match-details">
                                        ${match.property.listing_price ? `$${match.property.listing_price.toLocaleString()}` : 'Price N/A'} • 
                                        ${match.property.bedrooms || 'N/A'} bed • 
                                        ${match.property.bathrooms || 'N/A'} bath
                                    </div>
                                </div>
                            `).join('')}
                    </div>
                </div>
            </div>
        `;

        modal.classList.add('active');
    }

    async updateImpactVisualization() {
        try {
            const formData = this.collectFormData();
            
            // Simulate impact calculation (in real implementation, this would call an API)
            const impact = this.calculateCriteriaImpact(formData);
            this.renderImpactVisualization(impact);
            
        } catch (error) {
            console.error('Error updating impact visualization:', error);
        }
    }

    calculateCriteriaImpact(criteria) {
        // Simulate impact calculation based on criteria restrictiveness
        let restrictiveness = 0;
        let estimatedMatches = 1000; // Base number of properties

        // Price impact
        if (criteria.max_price) {
            const priceRestriction = Math.max(0, (500000 - criteria.max_price) / 500000);
            restrictiveness += priceRestriction * 0.3;
            estimatedMatches *= (1 - priceRestriction * 0.5);
        }

        // Property type impact
        const allPropertyTypes = ['single_family', 'multi_family', 'condo', 'townhouse', 'commercial'];
        const typeRestriction = 1 - (criteria.property_types.length / allPropertyTypes.length);
        restrictiveness += typeRestriction * 0.2;
        estimatedMatches *= (1 - typeRestriction * 0.3);

        // Bedroom/bathroom restrictions
        if (criteria.min_bedrooms > 1) {
            restrictiveness += 0.1;
            estimatedMatches *= 0.8;
        }

        // Financial criteria impact
        if (criteria.min_cap_rate > 6) {
            restrictiveness += 0.2;
            estimatedMatches *= 0.6;
        }

        if (criteria.min_coc_return > 10) {
            restrictiveness += 0.15;
            estimatedMatches *= 0.7;
        }

        return {
            restrictiveness: Math.min(restrictiveness, 1),
            estimatedMatches: Math.max(Math.round(estimatedMatches), 10),
            impactFactors: {
                price: criteria.max_price ? 'High' : 'Low',
                propertyType: typeRestriction > 0.5 ? 'High' : 'Low',
                financial: (criteria.min_cap_rate > 6 || criteria.min_coc_return > 10) ? 'High' : 'Low',
                location: criteria.target_markets.length > 0 ? 'Medium' : 'Low'
            }
        };
    }

    renderImpactVisualization(impact) {
        const container = document.getElementById('impact-visualization');
        if (!container) return;

        const restrictivenessPct = (impact.restrictiveness * 100).toFixed(1);
        const restrictivenesColor = impact.restrictiveness > 0.7 ? '#ef4444' : 
                                   impact.restrictiveness > 0.4 ? '#f59e0b' : '#10b981';

        container.innerHTML = `
            <div class="impact-summary">
                <h4>Criteria Impact Analysis</h4>
                
                <div class="impact-metrics">
                    <div class="impact-metric">
                        <div class="metric-label">Estimated Matches</div>
                        <div class="metric-value">${impact.estimatedMatches.toLocaleString()}</div>
                        <div class="metric-subtitle">properties</div>
                    </div>
                    
                    <div class="impact-metric">
                        <div class="metric-label">Restrictiveness</div>
                        <div class="metric-value" style="color: ${restrictivenesColor}">${restrictivenessPct}%</div>
                        <div class="metric-subtitle">
                            ${impact.restrictiveness > 0.7 ? 'Very High' : 
                              impact.restrictiveness > 0.4 ? 'Medium' : 'Low'}
                        </div>
                    </div>
                </div>

                <div class="impact-factors">
                    <h5>Impact Factors</h5>
                    <div class="factors-grid">
                        ${Object.entries(impact.impactFactors).map(([factor, level]) => `
                            <div class="factor-item">
                                <span class="factor-name">${factor.charAt(0).toUpperCase() + factor.slice(1)}</span>
                                <span class="factor-level ${level.toLowerCase()}">${level}</span>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <div class="restrictiveness-bar">
                    <div class="bar-background">
                        <div class="bar-fill" style="width: ${restrictivenessPct}%; background-color: ${restrictivenesColor}"></div>
                    </div>
                    <div class="bar-labels">
                        <span>Less Restrictive</span>
                        <span>More Restrictive</span>
                    </div>
                </div>
            </div>
        `;
    }

    showTemplateSelector() {
        const modal = document.getElementById('template-selector-modal');
        if (modal) {
            modal.classList.add('active');
        }
    }
}

// Initialize investment criteria editor when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('criteria-editor-container')) {
        window.criteriaEditor = new InvestmentCriteriaEditor();
    }
});