/**
 * Deal Finder Interface
 * Implements map view, list view, filtering, and property cards for deal sourcing
 */

class DealFinder {
    constructor() {
        this.properties = [];
        this.filteredProperties = [];
        this.currentView = 'list'; // 'list' or 'map'
        this.map = null;
        this.markers = [];
        this.filters = {
            minPrice: null,
            maxPrice: null,
            propertyType: '',
            minBedrooms: null,
            maxBedrooms: null,
            minBathrooms: null,
            maxBathrooms: null,
            minSquareFeet: null,
            maxSquareFeet: null,
            status: '',
            source: '',
            minLeadScore: null,
            maxLeadScore: null,
            location: ''
        };
        this.sortBy = 'created_at';
        this.sortOrder = 'desc';
        this.currentPage = 1;
        this.itemsPerPage = 20;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeMap();
        this.loadProperties();
    }

    setupEventListeners() {
        // View toggle buttons
        document.getElementById('list-view-btn')?.addEventListener('click', () => {
            this.switchView('list');
        });

        document.getElementById('map-view-btn')?.addEventListener('click', () => {
            this.switchView('map');
        });

        // Filter controls
        document.getElementById('apply-filters-btn')?.addEventListener('click', () => {
            this.applyFilters();
        });

        document.getElementById('clear-filters-btn')?.addEventListener('click', () => {
            this.clearFilters();
        });

        // Sort controls
        document.getElementById('sort-by')?.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.sortProperties();
        });

        document.getElementById('sort-order')?.addEventListener('change', (e) => {
            this.sortOrder = e.target.value;
            this.sortProperties();
        });

        // Search
        const searchInput = document.getElementById('property-search');
        if (searchInput) {
            const debouncedSearch = Utils.debounce((query) => {
                this.searchProperties(query);
            }, 300);
            
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }

        // Refresh button
        document.getElementById('refresh-properties-btn')?.addEventListener('click', () => {
            this.loadProperties();
        });
    }

    initializeMap() {
        const mapContainer = document.getElementById('properties-map');
        if (!mapContainer) return;

        // Initialize Leaflet map
        this.map = L.map('properties-map').setView([39.8283, -98.5795], 4); // Center of US

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add map event listeners
        this.map.on('zoomend moveend', () => {
            this.updateVisibleProperties();
        });
    }

    async loadProperties() {
        try {
            Utils.showLoading(true, 'Loading properties...');
            
            // Load properties from lead management API
            const response = await API.get('/api/v1/leads', {
                limit: 1000, // Load all for client-side filtering
                sort_by: this.sortBy,
                sort_order: this.sortOrder
            });

            this.properties = response.map(lead => this.transformLeadToProperty(lead));
            this.filteredProperties = [...this.properties];
            
            this.renderProperties();
            this.updateMapMarkers();
            this.updateStats();
            
            Utils.showToast('Properties loaded successfully', 'success');
            
        } catch (error) {
            console.error('Error loading properties:', error);
            Utils.showToast('Failed to load properties', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    transformLeadToProperty(lead) {
        // Transform lead data to property format for display
        return {
            id: lead.id,
            address: lead.property_address || 'Address not available',
            city: lead.property_city || '',
            state: lead.property_state || '',
            zipCode: lead.property_zip || '',
            propertyType: lead.property_type || 'unknown',
            bedrooms: lead.bedrooms,
            bathrooms: lead.bathrooms,
            squareFeet: lead.square_feet,
            listingPrice: lead.listing_price,
            estimatedValue: lead.estimated_value,
            leadScore: lead.lead_score,
            status: lead.status,
            source: lead.source,
            ownerName: lead.owner_name,
            ownerEmail: lead.owner_email,
            ownerPhone: lead.owner_phone,
            createdAt: lead.created_at,
            updatedAt: lead.updated_at,
            latitude: lead.latitude,
            longitude: lead.longitude,
            photos: lead.photos || [],
            description: lead.notes || '',
            daysOnMarket: lead.days_on_market,
            lastContactDate: lead.last_contact_date,
            contactAttempts: lead.contact_attempts
        };
    }

    switchView(view) {
        this.currentView = view;
        
        // Update button states
        document.querySelectorAll('.view-toggle .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.getElementById(`${view}-view-btn`)?.classList.add('active');
        
        // Show/hide appropriate containers
        const listContainer = document.getElementById('properties-list-container');
        const mapContainer = document.getElementById('properties-map-container');
        
        if (view === 'list') {
            listContainer?.classList.remove('hidden');
            mapContainer?.classList.add('hidden');
        } else {
            listContainer?.classList.add('hidden');
            mapContainer?.classList.remove('hidden');
            
            // Refresh map after showing
            setTimeout(() => {
                this.map?.invalidateSize();
                this.updateMapMarkers();
            }, 100);
        }
    }

    applyFilters() {
        // Collect filter values
        this.filters = {
            minPrice: this.getFilterValue('min-price', 'number'),
            maxPrice: this.getFilterValue('max-price', 'number'),
            propertyType: this.getFilterValue('property-type'),
            minBedrooms: this.getFilterValue('min-bedrooms', 'number'),
            maxBedrooms: this.getFilterValue('max-bedrooms', 'number'),
            minBathrooms: this.getFilterValue('min-bathrooms', 'number'),
            maxBathrooms: this.getFilterValue('max-bathrooms', 'number'),
            minSquareFeet: this.getFilterValue('min-square-feet', 'number'),
            maxSquareFeet: this.getFilterValue('max-square-feet', 'number'),
            status: this.getFilterValue('status-filter'),
            source: this.getFilterValue('source-filter'),
            minLeadScore: this.getFilterValue('min-lead-score', 'number'),
            maxLeadScore: this.getFilterValue('max-lead-score', 'number'),
            location: this.getFilterValue('location-filter')
        };

        this.filterProperties();
    }

    getFilterValue(elementId, type = 'string') {
        const element = document.getElementById(elementId);
        if (!element || !element.value) return null;
        
        if (type === 'number') {
            const value = parseFloat(element.value);
            return isNaN(value) ? null : value;
        }
        
        return element.value.trim();
    }

    clearFilters() {
        // Reset filter form
        document.querySelectorAll('.filter-form input, .filter-form select').forEach(input => {
            input.value = '';
        });

        // Reset filter object
        Object.keys(this.filters).forEach(key => {
            this.filters[key] = key === 'propertyType' || key === 'status' || key === 'source' || key === 'location' ? '' : null;
        });

        this.filterProperties();
    }

    filterProperties() {
        this.filteredProperties = this.properties.filter(property => {
            // Price filters
            if (this.filters.minPrice && property.listingPrice < this.filters.minPrice) return false;
            if (this.filters.maxPrice && property.listingPrice > this.filters.maxPrice) return false;

            // Property type filter
            if (this.filters.propertyType && property.propertyType !== this.filters.propertyType) return false;

            // Bedroom filters
            if (this.filters.minBedrooms && property.bedrooms < this.filters.minBedrooms) return false;
            if (this.filters.maxBedrooms && property.bedrooms > this.filters.maxBedrooms) return false;

            // Bathroom filters
            if (this.filters.minBathrooms && property.bathrooms < this.filters.minBathrooms) return false;
            if (this.filters.maxBathrooms && property.bathrooms > this.filters.maxBathrooms) return false;

            // Square feet filters
            if (this.filters.minSquareFeet && property.squareFeet < this.filters.minSquareFeet) return false;
            if (this.filters.maxSquareFeet && property.squareFeet > this.filters.maxSquareFeet) return false;

            // Status filter
            if (this.filters.status && property.status !== this.filters.status) return false;

            // Source filter
            if (this.filters.source && property.source !== this.filters.source) return false;

            // Lead score filters
            if (this.filters.minLeadScore && property.leadScore < this.filters.minLeadScore) return false;
            if (this.filters.maxLeadScore && property.leadScore > this.filters.maxLeadScore) return false;

            // Location filter (search in address, city, state)
            if (this.filters.location) {
                const locationSearch = this.filters.location.toLowerCase();
                const searchText = `${property.address} ${property.city} ${property.state}`.toLowerCase();
                if (!searchText.includes(locationSearch)) return false;
            }

            return true;
        });

        this.currentPage = 1; // Reset to first page
        this.renderProperties();
        this.updateMapMarkers();
        this.updateStats();
    }

    searchProperties(query) {
        if (!query) {
            this.filteredProperties = [...this.properties];
        } else {
            const searchTerm = query.toLowerCase();
            this.filteredProperties = this.properties.filter(property => {
                return (
                    property.address.toLowerCase().includes(searchTerm) ||
                    property.city.toLowerCase().includes(searchTerm) ||
                    property.state.toLowerCase().includes(searchTerm) ||
                    property.ownerName?.toLowerCase().includes(searchTerm) ||
                    property.description.toLowerCase().includes(searchTerm)
                );
            });
        }

        this.currentPage = 1;
        this.renderProperties();
        this.updateMapMarkers();
        this.updateStats();
    }

    sortProperties() {
        this.filteredProperties.sort((a, b) => {
            let aValue = a[this.sortBy];
            let bValue = b[this.sortBy];

            // Handle null/undefined values
            if (aValue == null) aValue = this.sortOrder === 'asc' ? -Infinity : Infinity;
            if (bValue == null) bValue = this.sortOrder === 'asc' ? -Infinity : Infinity;

            // Handle different data types
            if (typeof aValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }

            if (this.sortOrder === 'asc') {
                return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
            } else {
                return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
            }
        });

        this.renderProperties();
    }

    renderProperties() {
        if (this.currentView === 'list') {
            this.renderListView();
        }
        this.renderPagination();
    }

    renderListView() {
        const container = document.getElementById('properties-list');
        if (!container) return;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageProperties = this.filteredProperties.slice(startIndex, endIndex);

        if (pageProperties.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search fa-3x"></i>
                    <h3>No properties found</h3>
                    <p>Try adjusting your filters or search criteria</p>
                </div>
            `;
            return;
        }

        container.innerHTML = pageProperties.map(property => this.createPropertyCard(property)).join('');
    }

    createPropertyCard(property) {
        const priceDisplay = property.listingPrice ? 
            `$${property.listingPrice.toLocaleString()}` : 
            'Price not available';

        const scoreColor = this.getScoreColor(property.leadScore);
        const statusBadge = this.getStatusBadge(property.status);
        
        return `
            <div class="property-card" data-property-id="${property.id}">
                <div class="property-card-header">
                    <div class="property-image">
                        ${property.photos && property.photos.length > 0 ? 
                            `<img src="${property.photos[0]}" alt="Property photo" loading="lazy">` :
                            `<div class="no-image"><i class="fas fa-home"></i></div>`
                        }
                        <div class="property-badges">
                            ${statusBadge}
                            <span class="lead-score-badge" style="background-color: ${scoreColor}">
                                Score: ${property.leadScore || 'N/A'}
                            </span>
                        </div>
                    </div>
                </div>
                
                <div class="property-card-content">
                    <div class="property-address">
                        <h3>${property.address}</h3>
                        <p>${property.city}, ${property.state} ${property.zipCode}</p>
                    </div>
                    
                    <div class="property-details">
                        <div class="property-specs">
                            ${property.bedrooms ? `<span><i class="fas fa-bed"></i> ${property.bedrooms} bed</span>` : ''}
                            ${property.bathrooms ? `<span><i class="fas fa-bath"></i> ${property.bathrooms} bath</span>` : ''}
                            ${property.squareFeet ? `<span><i class="fas fa-ruler-combined"></i> ${property.squareFeet.toLocaleString()} sq ft</span>` : ''}
                        </div>
                        
                        <div class="property-price">
                            <span class="price">${priceDisplay}</span>
                            ${property.estimatedValue ? 
                                `<span class="estimated-value">Est: $${property.estimatedValue.toLocaleString()}</span>` : 
                                ''
                            }
                        </div>
                    </div>
                    
                    <div class="property-meta">
                        <div class="property-source">
                            <i class="fas fa-tag"></i>
                            <span>Source: ${property.source || 'Unknown'}</span>
                        </div>
                        
                        <div class="property-contact">
                            ${property.ownerName ? 
                                `<span><i class="fas fa-user"></i> ${property.ownerName}</span>` : 
                                ''
                            }
                            ${property.lastContactDate ? 
                                `<span><i class="fas fa-clock"></i> Last contact: ${new Date(property.lastContactDate).toLocaleDateString()}</span>` :
                                `<span><i class="fas fa-clock"></i> Never contacted</span>`
                            }
                        </div>
                    </div>
                    
                    ${property.description ? 
                        `<div class="property-description">
                            <p>${property.description.substring(0, 150)}${property.description.length > 150 ? '...' : ''}</p>
                        </div>` : 
                        ''
                    }
                </div>
                
                <div class="property-card-actions">
                    <button class="btn btn-primary btn-sm" onclick="dealFinder.viewPropertyDetails('${property.id}')">
                        <i class="fas fa-eye"></i> View Details
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="dealFinder.quickAnalysis('${property.id}')">
                        <i class="fas fa-calculator"></i> Quick Analysis
                    </button>
                    <button class="btn btn-secondary btn-sm" onclick="dealFinder.contactOwner('${property.id}')">
                        <i class="fas fa-phone"></i> Contact
                    </button>
                </div>
            </div>
        `;
    }

    getScoreColor(score) {
        if (!score) return '#6b7280';
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        if (score >= 40) return '#ef4444';
        return '#6b7280';
    }

    getStatusBadge(status) {
        const statusConfig = {
            'new': { color: '#3b82f6', text: 'New' },
            'contacted': { color: '#f59e0b', text: 'Contacted' },
            'interested': { color: '#10b981', text: 'Interested' },
            'qualified': { color: '#8b5cf6', text: 'Qualified' },
            'under_contract': { color: '#06b6d4', text: 'Under Contract' },
            'closed': { color: '#10b981', text: 'Closed' },
            'not_interested': { color: '#6b7280', text: 'Not Interested' },
            'do_not_contact': { color: '#ef4444', text: 'Do Not Contact' }
        };

        const config = statusConfig[status] || { color: '#6b7280', text: status || 'Unknown' };
        
        return `<span class="status-badge" style="background-color: ${config.color}">${config.text}</span>`;
    }

    updateMapMarkers() {
        if (!this.map) return;

        // Clear existing markers
        this.markers.forEach(marker => this.map.removeLayer(marker));
        this.markers = [];

        // Add markers for filtered properties
        this.filteredProperties.forEach(property => {
            if (property.latitude && property.longitude) {
                const marker = L.marker([property.latitude, property.longitude])
                    .bindPopup(this.createMapPopup(property))
                    .addTo(this.map);
                
                this.markers.push(marker);
            }
        });

        // Fit map to markers if there are any
        if (this.markers.length > 0) {
            const group = new L.featureGroup(this.markers);
            this.map.fitBounds(group.getBounds().pad(0.1));
        }
    }

    createMapPopup(property) {
        const priceDisplay = property.listingPrice ? 
            `$${property.listingPrice.toLocaleString()}` : 
            'Price not available';

        return `
            <div class="map-popup">
                <div class="popup-header">
                    <h4>${property.address}</h4>
                    <p>${property.city}, ${property.state}</p>
                </div>
                <div class="popup-content">
                    <div class="popup-price">${priceDisplay}</div>
                    <div class="popup-specs">
                        ${property.bedrooms ? `${property.bedrooms} bed` : ''} 
                        ${property.bathrooms ? `${property.bathrooms} bath` : ''}
                        ${property.squareFeet ? `${property.squareFeet.toLocaleString()} sq ft` : ''}
                    </div>
                    <div class="popup-score">Lead Score: ${property.leadScore || 'N/A'}</div>
                </div>
                <div class="popup-actions">
                    <button class="btn btn-primary btn-sm" onclick="dealFinder.viewPropertyDetails('${property.id}')">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    renderPagination() {
        const container = document.getElementById('properties-pagination');
        if (!container) return;

        const totalPages = Math.ceil(this.filteredProperties.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let paginationHTML = '<div class="pagination">';
        
        // Previous button
        paginationHTML += `
            <button class="pagination-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
                    ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="dealFinder.goToPage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Page numbers
        const startPage = Math.max(1, this.currentPage - 2);
        const endPage = Math.min(totalPages, this.currentPage + 2);

        if (startPage > 1) {
            paginationHTML += `<button class="pagination-btn" onclick="dealFinder.goToPage(1)">1</button>`;
            if (startPage > 2) {
                paginationHTML += `<span class="pagination-ellipsis">...</span>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="dealFinder.goToPage(${i})">${i}</button>
            `;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                paginationHTML += `<span class="pagination-ellipsis">...</span>`;
            }
            paginationHTML += `<button class="pagination-btn" onclick="dealFinder.goToPage(${totalPages})">${totalPages}</button>`;
        }

        // Next button
        paginationHTML += `
            <button class="pagination-btn ${this.currentPage === totalPages ? 'disabled' : ''}" 
                    ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="dealFinder.goToPage(${this.currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        paginationHTML += '</div>';
        
        // Add results info
        const startResult = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endResult = Math.min(this.currentPage * this.itemsPerPage, this.filteredProperties.length);
        
        paginationHTML += `
            <div class="pagination-info">
                Showing ${startResult}-${endResult} of ${this.filteredProperties.length} properties
            </div>
        `;

        container.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredProperties.length / this.itemsPerPage);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.renderProperties();
    }

    updateStats() {
        const statsContainer = document.getElementById('properties-stats');
        if (!statsContainer) return;

        const total = this.filteredProperties.length;
        const avgScore = total > 0 ? 
            this.filteredProperties.reduce((sum, p) => sum + (p.leadScore || 0), 0) / total : 0;
        
        const avgPrice = total > 0 ? 
            this.filteredProperties
                .filter(p => p.listingPrice)
                .reduce((sum, p) => sum + p.listingPrice, 0) / 
            this.filteredProperties.filter(p => p.listingPrice).length : 0;

        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${total}</div>
                    <div class="stat-label">Total Properties</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${avgScore.toFixed(1)}</div>
                    <div class="stat-label">Avg Lead Score</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${avgPrice > 0 ? '$' + avgPrice.toLocaleString() : 'N/A'}</div>
                    <div class="stat-label">Avg Price</div>
                </div>
            </div>
        `;
    }

    updateVisibleProperties() {
        // Update properties visible in current map bounds
        if (!this.map || this.currentView !== 'map') return;

        const bounds = this.map.getBounds();
        const visibleProperties = this.filteredProperties.filter(property => {
            if (!property.latitude || !property.longitude) return false;
            return bounds.contains([property.latitude, property.longitude]);
        });

        // Update visible count
        const visibleCount = document.getElementById('visible-properties-count');
        if (visibleCount) {
            visibleCount.textContent = `${visibleProperties.length} properties visible`;
        }
    }

    // Action methods
    async viewPropertyDetails(propertyId) {
        try {
            const property = this.properties.find(p => p.id === propertyId);
            if (!property) {
                Utils.showToast('Property not found', 'error');
                return;
            }

            // Show property details modal or navigate to details page
            this.showPropertyDetailsModal(property);
            
        } catch (error) {
            console.error('Error viewing property details:', error);
            Utils.showToast('Failed to load property details', 'error');
        }
    }

    async quickAnalysis(propertyId) {
        try {
            const property = this.properties.find(p => p.id === propertyId);
            if (!property) {
                Utils.showToast('Property not found', 'error');
                return;
            }

            Utils.showLoading(true, 'Running quick analysis...');

            // Call property analysis API
            const analysis = await API.post('/api/v1/properties/analyze', {
                property_id: propertyId,
                analysis_type: 'quick'
            });

            this.showQuickAnalysisModal(property, analysis);
            
        } catch (error) {
            console.error('Error running quick analysis:', error);
            Utils.showToast('Failed to run analysis', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async contactOwner(propertyId) {
        try {
            const property = this.properties.find(p => p.id === propertyId);
            if (!property) {
                Utils.showToast('Property not found', 'error');
                return;
            }

            // Show contact modal or initiate contact workflow
            this.showContactModal(property);
            
        } catch (error) {
            console.error('Error initiating contact:', error);
            Utils.showToast('Failed to initiate contact', 'error');
        }
    }

    showPropertyDetailsModal(property) {
        // Implementation for property details modal
        console.log('Show property details for:', property);
        // This would open a detailed view modal
    }

    showQuickAnalysisModal(property, analysis) {
        // Implementation for quick analysis modal
        console.log('Show quick analysis for:', property, analysis);
        // This would show analysis results in a modal
    }

    showContactModal(property) {
        // Implementation for contact modal
        console.log('Show contact modal for:', property);
        // This would show contact options and forms
    }
}

// Initialize deal finder when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('deal-finder-container')) {
        window.dealFinder = new DealFinder();
    }
});