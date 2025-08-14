// Comparable Properties Viewer functionality

class ComparablesViewer {
    constructor() {
        this.currentProperty = null;
        this.comparableProperties = [];
        this.selectedComparable = null;
        this.map = null;
        this.markers = [];
        this.sortColumn = 'similarity';
        this.sortDirection = 'desc';
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProperties();
        this.initializeMap();
    }

    setupEventListeners() {
        // Property selection
        const propertySelect = document.getElementById('comp-property-select');
        if (propertySelect) {
            propertySelect.addEventListener('change', (e) => {
                this.selectProperty(e.target.value);
            });
        }

        // Find comparables button
        const findBtn = document.getElementById('find-comparables-btn');
        if (findBtn) {
            findBtn.addEventListener('click', () => {
                this.findComparables();
            });
        }

        // Search parameter changes
        ['comp-max-distance', 'comp-max-age', 'comp-min-count'].forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('change', () => {
                    if (this.currentProperty) {
                        this.findComparables();
                    }
                });
            }
        });
    }

    async loadProperties() {
        try {
            const properties = await API.listProperties();
            this.populatePropertySelect(properties);
        } catch (error) {
            console.error('Failed to load properties:', error);
            Utils.showToast('Failed to load properties', 'error');
        }
    }

    populatePropertySelect(properties) {
        const select = document.getElementById('comp-property-select');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">Select property to find comparables...</option>';

        properties.forEach(property => {
            const option = document.createElement('option');
            option.value = property.id;
            option.textContent = `${property.address}, ${property.city}, ${property.state}`;
            select.appendChild(option);
        });

        if (properties.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No properties found - Add a property first';
            option.disabled = true;
            select.appendChild(option);
        }
    }

    async selectProperty(propertyId) {
        if (!propertyId) {
            this.showEmptyState();
            return;
        }

        try {
            Utils.showLoading(true, 'Loading property...');
            
            const property = await API.getProperty(propertyId);
            this.currentProperty = property;
            
            this.displaySubjectProperty(property);
            this.hideEmptyState();
            
            // Auto-find comparables if property has location data
            if (property.latitude && property.longitude) {
                await this.findComparables();
            }
            
        } catch (error) {
            console.error('Failed to load property:', error);
            Utils.showToast('Failed to load property', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    displaySubjectProperty(property) {
        const summaryContainer = document.getElementById('subject-property-summary');
        if (!summaryContainer) return;

        summaryContainer.innerHTML = `
            <div class="property-details-grid">
                <div class="property-detail">
                    <label>Address:</label>
                    <span>${property.address}, ${property.city}, ${property.state} ${property.zip_code}</span>
                </div>
                <div class="property-detail">
                    <label>Property Type:</label>
                    <span>${Utils.snakeToTitle(property.property_type)}</span>
                </div>
                <div class="property-detail">
                    <label>Bedrooms:</label>
                    <span>${property.bedrooms || 'N/A'}</span>
                </div>
                <div class="property-detail">
                    <label>Bathrooms:</label>
                    <span>${property.bathrooms || 'N/A'}</span>
                </div>
                <div class="property-detail">
                    <label>Square Feet:</label>
                    <span>${property.square_feet ? Utils.formatNumber(property.square_feet) : 'N/A'}</span>
                </div>
                <div class="property-detail">
                    <label>Year Built:</label>
                    <span>${property.year_built || 'N/A'}</span>
                </div>
                <div class="property-detail">
                    <label>Listing Price:</label>
                    <span>${property.listing_price ? Utils.formatCurrency(property.listing_price) : 'N/A'}</span>
                </div>
                <div class="property-detail">
                    <label>Current Value:</label>
                    <span>${property.current_value ? Utils.formatCurrency(property.current_value) : 'N/A'}</span>
                </div>
            </div>
        `;
    }

    async findComparables() {
        if (!this.currentProperty) {
            Utils.showToast('Please select a property first', 'warning');
            return;
        }

        const maxDistance = parseFloat(document.getElementById('comp-max-distance').value) || 2.0;
        const maxAge = parseInt(document.getElementById('comp-max-age').value) || 180;
        const minCount = parseInt(document.getElementById('comp-min-count').value) || 3;

        try {
            Utils.showLoading(true, 'Finding comparable properties...');
            
            const result = await API.getComparableProperties(this.currentProperty.id, {
                maxDistance,
                maxAgeDays: maxAge,
                minComps: minCount
            });
            
            this.comparableProperties = result.comparable_properties || [];
            this.displayComparables(result);
            this.updateMap();
            
            Utils.showToast(`Found ${this.comparableProperties.length} comparable properties`, 'success');
            
        } catch (error) {
            console.error('Failed to find comparables:', error);
            Utils.showToast(`Failed to find comparables: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    displayComparables(result) {
        this.showComparablesResults();
        
        // Update summary metrics
        this.updateSummaryMetrics(result);
        
        // Populate comparables table
        this.populateComparablesTable();
        
        // Update confidence analysis
        this.updateConfidenceAnalysis(result);
    }

    updateSummaryMetrics(result) {
        const valuation = result.valuation_estimate || {};
        const comparables = this.comparableProperties;

        // Estimated value
        const estimatedValue = valuation.estimated_value || 0;
        const confidence = valuation.confidence_score || 0;
        document.getElementById('comp-estimated-value').textContent = Utils.formatCurrency(estimatedValue);
        this.updateConfidenceIndicator('comp-value-confidence', 'comp-value-confidence-label', confidence);

        // Comparable count and price range
        document.getElementById('comp-count').textContent = comparables.length;
        if (comparables.length > 0) {
            const prices = comparables.map(comp => comp.sale_price || comp.listing_price || 0);
            const minPrice = Math.min(...prices);
            const maxPrice = Math.max(...prices);
            document.getElementById('comp-range').innerHTML = `<span>Range: ${Utils.formatCurrency(minPrice)} - ${Utils.formatCurrency(maxPrice)}</span>`;
        }

        // Average price per square foot
        const validComps = comparables.filter(comp => comp.square_feet && (comp.sale_price || comp.listing_price));
        if (validComps.length > 0) {
            const sqftPrices = validComps.map(comp => (comp.sale_price || comp.listing_price) / comp.square_feet);
            const avgSqftPrice = sqftPrices.reduce((a, b) => a + b, 0) / sqftPrices.length;
            const minSqftPrice = Math.min(...sqftPrices);
            const maxSqftPrice = Math.max(...sqftPrices);
            
            document.getElementById('comp-avg-sqft-price').textContent = Utils.formatCurrency(avgSqftPrice);
            document.getElementById('comp-sqft-range').innerHTML = `<span>Range: ${Utils.formatCurrency(minSqftPrice)} - ${Utils.formatCurrency(maxSqftPrice)}</span>`;
        }

        // Average days on market
        const daysOnMarket = comparables.filter(comp => comp.days_on_market).map(comp => comp.days_on_market);
        if (daysOnMarket.length > 0) {
            const avgDays = Math.round(daysOnMarket.reduce((a, b) => a + b, 0) / daysOnMarket.length);
            document.getElementById('comp-avg-days-market').textContent = avgDays;
            
            // Determine market trend
            const marketTrend = avgDays < 30 ? 'Hot' : avgDays < 60 ? 'Balanced' : 'Slow';
            const trendIcon = avgDays < 30 ? 'fa-fire' : avgDays < 60 ? 'fa-balance-scale' : 'fa-snowflake';
            const trendColor = avgDays < 30 ? 'var(--error-color)' : avgDays < 60 ? 'var(--warning-color)' : 'var(--primary-color)';
            
            document.getElementById('comp-market-trend').innerHTML = `
                <i class="fas ${trendIcon}" style="color: ${trendColor}"></i>
                <span>${marketTrend} Market</span>
            `;
        }
    }

    populateComparablesTable() {
        const tableBody = document.getElementById('comparables-table-body');
        if (!tableBody) return;

        // Sort comparables
        const sortedComparables = this.sortComparablesData([...this.comparableProperties]);

        tableBody.innerHTML = sortedComparables.map((comp, index) => {
            const price = comp.sale_price || comp.listing_price || 0;
            const pricePerSqft = comp.square_feet ? price / comp.square_feet : 0;
            const similarity = comp.similarity_score || 0;
            const distance = comp.distance_miles || 0;
            const daysAgo = comp.days_since_sale || comp.days_on_market || 0;

            return `
                <tr class="comparable-row" data-comp-index="${index}" onclick="comparablesViewer.selectComparable(${index})">
                    <td class="address-cell">
                        <div class="comp-address">${comp.address || 'N/A'}</div>
                        <div class="comp-city">${comp.city || ''}, ${comp.state || ''}</div>
                    </td>
                    <td class="price-cell">${Utils.formatCurrency(price)}</td>
                    <td class="sqft-cell">${comp.square_feet ? Utils.formatNumber(comp.square_feet) : 'N/A'}</td>
                    <td class="price-sqft-cell">${pricePerSqft ? Utils.formatCurrency(pricePerSqft) : 'N/A'}</td>
                    <td class="bed-bath-cell">${comp.bedrooms || 0}/${comp.bathrooms || 0}</td>
                    <td class="distance-cell">${distance.toFixed(1)} mi</td>
                    <td class="days-cell">${daysAgo} days</td>
                    <td class="similarity-cell">
                        <div class="similarity-bar">
                            <div class="similarity-fill" style="width: ${similarity * 100}%"></div>
                            <span class="similarity-text">${Math.round(similarity * 100)}%</span>
                        </div>
                    </td>
                    <td class="actions-cell">
                        <button class="btn-icon" onclick="event.stopPropagation(); comparablesViewer.viewComparableDetails(${index})" title="View Details">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn-icon" onclick="event.stopPropagation(); comparablesViewer.excludeComparable(${index})" title="Exclude">
                            <i class="fas fa-times"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    sortComparablesData(comparables) {
        return comparables.sort((a, b) => {
            let aValue, bValue;
            
            switch (this.sortColumn) {
                case 'price':
                    aValue = a.sale_price || a.listing_price || 0;
                    bValue = b.sale_price || b.listing_price || 0;
                    break;
                case 'sqft':
                    aValue = a.square_feet || 0;
                    bValue = b.square_feet || 0;
                    break;
                case 'distance':
                    aValue = a.distance_miles || 0;
                    bValue = b.distance_miles || 0;
                    break;
                case 'similarity':
                    aValue = a.similarity_score || 0;
                    bValue = b.similarity_score || 0;
                    break;
                default:
                    return 0;
            }
            
            if (this.sortDirection === 'asc') {
                return aValue - bValue;
            } else {
                return bValue - aValue;
            }
        });
    }

    selectComparable(index) {
        // Remove previous selection
        document.querySelectorAll('.comparable-row').forEach(row => {
            row.classList.remove('selected');
        });

        // Add selection to clicked row
        const row = document.querySelector(`[data-comp-index="${index}"]`);
        if (row) {
            row.classList.add('selected');
        }

        this.selectedComparable = this.comparableProperties[index];
        this.displayAdjustments(this.selectedComparable);
        this.highlightMarkerOnMap(index);
    }

    displayAdjustments(comparable) {
        const adjustmentsContainer = document.getElementById('adjustments-details');
        const explanationContainer = document.querySelector('.adjustments-explanation');
        
        if (!adjustmentsContainer || !explanationContainer) return;

        explanationContainer.style.display = 'none';
        adjustmentsContainer.style.display = 'block';

        // Calculate adjustments
        const adjustments = this.calculateAdjustments(comparable);
        
        // Display property adjustments
        this.displayAdjustmentCategory('property-adjustments', adjustments.property);
        
        // Display location adjustments
        this.displayAdjustmentCategory('location-adjustments', adjustments.location);
        
        // Display market adjustments
        this.displayAdjustmentCategory('market-adjustments', adjustments.market);
        
        // Update adjustment summary
        const originalPrice = comparable.sale_price || comparable.listing_price || 0;
        const totalAdjustments = adjustments.total;
        const adjustedValue = originalPrice + totalAdjustments;
        
        document.getElementById('original-price').textContent = Utils.formatCurrency(originalPrice);
        document.getElementById('total-adjustments').textContent = Utils.formatCurrency(totalAdjustments);
        document.getElementById('adjusted-value').textContent = Utils.formatCurrency(adjustedValue);
    }

    calculateAdjustments(comparable) {
        const subject = this.currentProperty;
        const adjustments = {
            property: [],
            location: [],
            market: [],
            total: 0
        };

        // Property characteristic adjustments
        if (subject.square_feet && comparable.square_feet) {
            const sqftDiff = subject.square_feet - comparable.square_feet;
            const sqftAdjustment = sqftDiff * 100; // $100 per sq ft difference
            adjustments.property.push({
                factor: 'Square Footage',
                difference: `${sqftDiff > 0 ? '+' : ''}${sqftDiff} sq ft`,
                adjustment: sqftAdjustment
            });
            adjustments.total += sqftAdjustment;
        }

        if (subject.bedrooms && comparable.bedrooms) {
            const bedroomDiff = subject.bedrooms - comparable.bedrooms;
            const bedroomAdjustment = bedroomDiff * 5000; // $5,000 per bedroom
            adjustments.property.push({
                factor: 'Bedrooms',
                difference: `${bedroomDiff > 0 ? '+' : ''}${bedroomDiff}`,
                adjustment: bedroomAdjustment
            });
            adjustments.total += bedroomAdjustment;
        }

        if (subject.bathrooms && comparable.bathrooms) {
            const bathroomDiff = subject.bathrooms - comparable.bathrooms;
            const bathroomAdjustment = bathroomDiff * 3000; // $3,000 per bathroom
            adjustments.property.push({
                factor: 'Bathrooms',
                difference: `${bathroomDiff > 0 ? '+' : ''}${bathroomDiff}`,
                adjustment: bathroomAdjustment
            });
            adjustments.total += bathroomAdjustment;
        }

        if (subject.garage_spaces && comparable.garage_spaces) {
            const garageDiff = subject.garage_spaces - comparable.garage_spaces;
            const garageAdjustment = garageDiff * 2000; // $2,000 per garage space
            adjustments.property.push({
                factor: 'Garage Spaces',
                difference: `${garageDiff > 0 ? '+' : ''}${garageDiff}`,
                adjustment: garageAdjustment
            });
            adjustments.total += garageAdjustment;
        }

        // Location adjustments
        const distance = comparable.distance_miles || 0;
        if (distance > 1) {
            const locationAdjustment = -(distance - 1) * 1000; // -$1,000 per mile beyond 1 mile
            adjustments.location.push({
                factor: 'Distance',
                difference: `${distance.toFixed(1)} miles`,
                adjustment: locationAdjustment
            });
            adjustments.total += locationAdjustment;
        }

        // Market condition adjustments
        const daysAgo = comparable.days_since_sale || 0;
        if (daysAgo > 90) {
            const marketAdjustment = Math.floor(daysAgo / 30) * 500; // +$500 per month for appreciation
            adjustments.market.push({
                factor: 'Market Appreciation',
                difference: `${Math.floor(daysAgo / 30)} months ago`,
                adjustment: marketAdjustment
            });
            adjustments.total += marketAdjustment;
        }

        return adjustments;
    }

    displayAdjustmentCategory(containerId, adjustments) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (adjustments.length === 0) {
            container.innerHTML = '<div class="no-adjustments">No adjustments needed</div>';
            return;
        }

        container.innerHTML = adjustments.map(adj => `
            <div class="adjustment-item">
                <div class="adjustment-factor">${adj.factor}</div>
                <div class="adjustment-difference">${adj.difference}</div>
                <div class="adjustment-amount ${adj.adjustment >= 0 ? 'positive' : 'negative'}">
                    ${adj.adjustment >= 0 ? '+' : ''}${Utils.formatCurrency(adj.adjustment)}
                </div>
            </div>
        `).join('');
    }

    updateConfidenceAnalysis(result) {
        const comparables = this.comparableProperties;
        const valuation = result.valuation_estimate || {};

        // Number of comparables score
        const compCountScore = Math.min(comparables.length / 10, 1); // Max score at 10 comparables
        this.updateProgressBar('comp-count-score', compCountScore);
        document.getElementById('comp-count-score-text').textContent = `${comparables.length}/10`;

        // Similarity score
        const avgSimilarity = comparables.length > 0 ? 
            comparables.reduce((sum, comp) => sum + (comp.similarity_score || 0), 0) / comparables.length : 0;
        this.updateProgressBar('similarity-score', avgSimilarity);
        document.getElementById('similarity-score-text').textContent = `${Math.round(avgSimilarity * 100)}%`;

        // Market activity score (based on days on market)
        const avgDaysOnMarket = comparables.length > 0 ?
            comparables.reduce((sum, comp) => sum + (comp.days_on_market || 90), 0) / comparables.length : 90;
        const marketActivityScore = Math.max(0, (90 - avgDaysOnMarket) / 90); // Higher score for faster sales
        this.updateProgressBar('market-activity-score', marketActivityScore);
        const activityLevel = marketActivityScore > 0.7 ? 'High' : marketActivityScore > 0.4 ? 'Medium' : 'Low';
        document.getElementById('market-activity-score-text').textContent = activityLevel;

        // Price consistency score
        const prices = comparables.map(comp => comp.sale_price || comp.listing_price || 0).filter(p => p > 0);
        let priceConsistencyScore = 0;
        if (prices.length > 1) {
            const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;
            const variance = prices.reduce((sum, price) => sum + Math.pow(price - avgPrice, 2), 0) / prices.length;
            const stdDev = Math.sqrt(variance);
            const coefficientOfVariation = stdDev / avgPrice;
            priceConsistencyScore = Math.max(0, 1 - coefficientOfVariation); // Lower CV = higher consistency
        }
        this.updateProgressBar('price-consistency-score', priceConsistencyScore);
        document.getElementById('price-consistency-score-text').textContent = `${Math.round(priceConsistencyScore * 100)}%`;

        // Overall confidence
        const overallConfidence = (compCountScore + avgSimilarity + marketActivityScore + priceConsistencyScore) / 4;
        document.getElementById('overall-confidence-percentage').textContent = `${Math.round(overallConfidence * 100)}%`;
        
        // Update confidence circle color
        const confidenceCircle = document.querySelector('.confidence-circle');
        if (confidenceCircle) {
            const confidenceLevel = overallConfidence >= 0.8 ? 'high' : overallConfidence >= 0.6 ? 'medium' : 'low';
            confidenceCircle.className = `confidence-circle ${confidenceLevel}`;
        }
    }

    updateProgressBar(barId, score) {
        const progressBar = document.getElementById(barId);
        if (progressBar) {
            const percentage = Math.round(score * 100);
            progressBar.style.width = `${percentage}%`;
            
            // Update color based on score
            if (score >= 0.8) {
                progressBar.className = 'progress-fill success';
            } else if (score >= 0.6) {
                progressBar.className = 'progress-fill warning';
            } else {
                progressBar.className = 'progress-fill error';
            }
        }
    }

    updateConfidenceIndicator(dotsId, labelId, confidence) {
        const dotsContainer = document.getElementById(dotsId);
        const label = document.getElementById(labelId);
        
        if (!dotsContainer || !label) return;

        const confidenceLevel = confidence >= 0.8 ? 'high' : confidence >= 0.6 ? 'medium' : 'low';
        const confidenceText = confidence >= 0.8 ? 'High' : confidence >= 0.6 ? 'Medium' : 'Low';
        
        dotsContainer.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            const dot = document.createElement('div');
            dot.className = `confidence-dot ${i < confidence * 5 ? 'active ' + confidenceLevel : ''}`;
            dotsContainer.appendChild(dot);
        }
        
        label.textContent = `${confidenceText} Confidence`;
    }

    initializeMap() {
        const mapContainer = document.getElementById('comparables-map');
        if (!mapContainer) return;

        // Initialize Leaflet map
        this.map = L.map('comparables-map').setView([39.8283, -98.5795], 4); // Center of US

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Set initial size
        setTimeout(() => {
            this.map.invalidateSize();
        }, 100);
    }

    updateMap() {
        if (!this.map || !this.currentProperty) return;

        // Clear existing markers
        this.markers.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.markers = [];

        // Add subject property marker
        if (this.currentProperty.latitude && this.currentProperty.longitude) {
            const subjectMarker = L.marker([this.currentProperty.latitude, this.currentProperty.longitude], {
                icon: this.createCustomIcon('subject')
            }).addTo(this.map);

            subjectMarker.bindPopup(`
                <div class="map-popup">
                    <h4>Subject Property</h4>
                    <p><strong>${this.currentProperty.address}</strong></p>
                    <p>${this.currentProperty.city}, ${this.currentProperty.state}</p>
                    <p>Listing: ${this.currentProperty.listing_price ? Utils.formatCurrency(this.currentProperty.listing_price) : 'N/A'}</p>
                </div>
            `);

            this.markers.push(subjectMarker);
        }

        // Add comparable property markers
        this.comparableProperties.forEach((comp, index) => {
            if (comp.latitude && comp.longitude) {
                const compMarker = L.marker([comp.latitude, comp.longitude], {
                    icon: this.createCustomIcon('comparable')
                }).addTo(this.map);

                const price = comp.sale_price || comp.listing_price || 0;
                compMarker.bindPopup(`
                    <div class="map-popup">
                        <h4>Comparable #${index + 1}</h4>
                        <p><strong>${comp.address || 'N/A'}</strong></p>
                        <p>${comp.city || ''}, ${comp.state || ''}</p>
                        <p>Price: ${Utils.formatCurrency(price)}</p>
                        <p>Similarity: ${Math.round((comp.similarity_score || 0) * 100)}%</p>
                        <button onclick="comparablesViewer.selectComparable(${index})" class="btn btn-primary btn-sm">
                            View Details
                        </button>
                    </div>
                `);

                // Store index for highlighting
                compMarker.compIndex = index;
                this.markers.push(compMarker);
            }
        });

        // Fit map to show all markers
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    createCustomIcon(type) {
        const colors = {
            subject: '#2563eb',
            comparable: '#10b981',
            selected: '#f59e0b'
        };

        return L.divIcon({
            className: 'custom-marker',
            html: `<div style="background-color: ${colors[type]}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);"></div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
    }

    highlightMarkerOnMap(index) {
        // Reset all markers to comparable style
        this.markers.forEach(marker => {
            if (marker.compIndex !== undefined) {
                marker.setIcon(this.createCustomIcon('comparable'));
            }
        });

        // Highlight selected marker
        const selectedMarker = this.markers.find(marker => marker.compIndex === index);
        if (selectedMarker) {
            selectedMarker.setIcon(this.createCustomIcon('selected'));
            this.map.setView(selectedMarker.getLatLng(), Math.max(this.map.getZoom(), 15));
        }
    }

    // Public methods for UI interactions

    centerMap() {
        if (this.map && this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    toggleMapType() {
        // This would toggle between different map tile layers
        Utils.showToast('Map type toggle not implemented yet', 'info');
    }

    sortComparables(column) {
        if (this.sortColumn === column) {
            this.sortDirection = this.sortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            this.sortColumn = column;
            this.sortDirection = 'desc';
        }
        
        this.populateComparablesTable();
        Utils.showToast(`Sorted by ${Utils.snakeToTitle(column)} (${this.sortDirection})`, 'info');
    }

    async exportComparables() {
        if (this.comparableProperties.length === 0) {
            Utils.showToast('No comparables to export', 'warning');
            return;
        }

        try {
            // Create CSV data
            const headers = ['Address', 'City', 'State', 'Price', 'Square Feet', 'Price/Sq Ft', 'Bedrooms', 'Bathrooms', 'Distance (mi)', 'Days Ago', 'Similarity'];
            const rows = this.comparableProperties.map(comp => [
                comp.address || '',
                comp.city || '',
                comp.state || '',
                comp.sale_price || comp.listing_price || 0,
                comp.square_feet || '',
                comp.square_feet ? (comp.sale_price || comp.listing_price || 0) / comp.square_feet : '',
                comp.bedrooms || '',
                comp.bathrooms || '',
                (comp.distance_miles || 0).toFixed(1),
                comp.days_since_sale || comp.days_on_market || '',
                Math.round((comp.similarity_score || 0) * 100)
            ]);

            const csvContent = [headers, ...rows].map(row => row.join(',')).join('\n');
            
            // Download CSV
            const blob = new Blob([csvContent], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `comparables-${this.currentProperty.address.replace(/[^a-zA-Z0-9]/g, '_')}-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            Utils.showToast('Comparables exported successfully', 'success');
            
        } catch (error) {
            console.error('Export failed:', error);
            Utils.showToast('Failed to export comparables', 'error');
        }
    }

    viewComparableDetails(index) {
        const comparable = this.comparableProperties[index];
        if (!comparable) return;

        // This would open a modal with detailed comparable information
        Utils.showToast('Detailed view not implemented yet', 'info');
    }

    excludeComparable(index) {
        if (confirm('Are you sure you want to exclude this comparable from the analysis?')) {
            this.comparableProperties.splice(index, 1);
            this.populateComparablesTable();
            this.updateMap();
            Utils.showToast('Comparable excluded from analysis', 'success');
        }
    }

    showEmptyState() {
        document.getElementById('comparables-results').style.display = 'none';
        document.getElementById('comparables-empty-state').style.display = 'block';
    }

    hideEmptyState() {
        document.getElementById('comparables-empty-state').style.display = 'none';
    }

    showComparablesResults() {
        document.getElementById('comparables-results').style.display = 'block';
        this.hideEmptyState();
    }
}

// Initialize comparables viewer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.comparablesViewer = new ComparablesViewer();
});