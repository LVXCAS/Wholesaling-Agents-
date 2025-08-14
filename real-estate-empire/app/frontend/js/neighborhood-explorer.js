/**
 * Neighborhood Explorer
 * Implements interactive neighborhood map, trend visualization, school/amenity display, and crime heatmap
 */

class NeighborhoodExplorer {
    constructor() {
        this.map = null;
        this.neighborhoods = [];
        this.selectedNeighborhood = null;
        this.layers = {
            neighborhoods: null,
            schools: null,
            amenities: null,
            crime: null,
            properties: null
        };
        this.activeOverlays = new Set(['neighborhoods']);
        this.trendData = {};
        this.schoolData = {};
        this.amenityData = {};
        this.crimeData = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeMap();
        this.loadNeighborhoodData();
    }

    setupEventListeners() {
        // Layer toggle controls
        document.querySelectorAll('.layer-toggle').forEach(toggle => {
            toggle.addEventListener('change', (e) => {
                const layerName = e.target.dataset.layer;
                if (e.target.checked) {
                    this.showLayer(layerName);
                } else {
                    this.hideLayer(layerName);
                }
            });
        });

        // Search functionality
        const searchInput = document.getElementById('neighborhood-search');
        if (searchInput) {
            const debouncedSearch = Utils.debounce((query) => {
                this.searchNeighborhoods(query);
            }, 300);
            
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }

        // Filter controls
        document.getElementById('price-range-filter')?.addEventListener('change', (e) => {
            this.filterByPriceRange(e.target.value);
        });

        document.getElementById('trend-filter')?.addEventListener('change', (e) => {
            this.filterByTrend(e.target.value);
        });

        // View controls
        document.getElementById('reset-view-btn')?.addEventListener('click', () => {
            this.resetMapView();
        });

        document.getElementById('export-data-btn')?.addEventListener('click', () => {
            this.exportNeighborhoodData();
        });

        // Trend period selector
        document.getElementById('trend-period')?.addEventListener('change', (e) => {
            this.updateTrendPeriod(e.target.value);
        });
    }

    initializeMap() {
        const mapContainer = document.getElementById('neighborhood-map');
        if (!mapContainer) return;

        // Initialize Leaflet map
        this.map = L.map('neighborhood-map').setView([39.8283, -98.5795], 4); // Center of US

        // Add base tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.map);

        // Add map event listeners
        this.map.on('zoomend moveend', () => {
            this.updateVisibleNeighborhoods();
        });

        this.map.on('click', (e) => {
            this.handleMapClick(e);
        });
    }

    async loadNeighborhoodData() {
        try {
            Utils.showLoading(true, 'Loading neighborhood data...');
            
            // In a real implementation, this would load from neighborhood analysis API
            // For now, we'll simulate the data
            this.neighborhoods = await this.generateSampleNeighborhoodData();
            
            this.createNeighborhoodLayer();
            this.populateNeighborhoodList();
            this.updateStats();
            
            Utils.showToast('Neighborhood data loaded successfully', 'success');
            
        } catch (error) {
            console.error('Error loading neighborhood data:', error);
            Utils.showToast('Failed to load neighborhood data', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async generateSampleNeighborhoodData() {
        // Generate sample neighborhood data for demonstration
        const sampleNeighborhoods = [
            {
                id: 'downtown-atlanta',
                name: 'Downtown Atlanta',
                city: 'Atlanta',
                state: 'GA',
                bounds: [
                    [33.7490, -84.3880],
                    [33.7590, -84.3780],
                    [33.7590, -84.3680],
                    [33.7490, -84.3580]
                ],
                center: [33.7540, -84.3730],
                stats: {
                    avgPrice: 450000,
                    medianPrice: 425000,
                    pricePerSqFt: 280,
                    daysOnMarket: 25,
                    inventory: 45,
                    priceChange: 8.5,
                    rentYield: 6.2,
                    walkScore: 85,
                    crimeScore: 6,
                    schoolRating: 7
                },
                trends: {
                    '1year': { priceChange: 8.5, volume: 120 },
                    '2year': { priceChange: 15.2, volume: 240 },
                    '5year': { priceChange: 35.8, volume: 580 }
                },
                demographics: {
                    population: 15000,
                    medianAge: 32,
                    medianIncome: 65000,
                    ownerOccupied: 45
                }
            },
            {
                id: 'buckhead-atlanta',
                name: 'Buckhead',
                city: 'Atlanta',
                state: 'GA',
                bounds: [
                    [33.8400, -84.3900],
                    [33.8500, -84.3800],
                    [33.8500, -84.3700],
                    [33.8400, -84.3600]
                ],
                center: [33.8450, -84.3750],
                stats: {
                    avgPrice: 850000,
                    medianPrice: 750000,
                    pricePerSqFt: 420,
                    daysOnMarket: 35,
                    inventory: 28,
                    priceChange: 12.3,
                    rentYield: 4.8,
                    walkScore: 72,
                    crimeScore: 3,
                    schoolRating: 9
                },
                trends: {
                    '1year': { priceChange: 12.3, volume: 85 },
                    '2year': { priceChange: 22.1, volume: 165 },
                    '5year': { priceChange: 45.6, volume: 420 }
                },
                demographics: {
                    population: 25000,
                    medianAge: 38,
                    medianIncome: 95000,
                    ownerOccupied: 65
                }
            },
            {
                id: 'midtown-atlanta',
                name: 'Midtown',
                city: 'Atlanta',
                state: 'GA',
                bounds: [
                    [33.7700, -84.3900],
                    [33.7800, -84.3800],
                    [33.7800, -84.3700],
                    [33.7700, -84.3600]
                ],
                center: [33.7750, -84.3750],
                stats: {
                    avgPrice: 650000,
                    medianPrice: 580000,
                    pricePerSqFt: 350,
                    daysOnMarket: 20,
                    inventory: 32,
                    priceChange: 10.8,
                    rentYield: 5.5,
                    walkScore: 90,
                    crimeScore: 4,
                    schoolRating: 8
                },
                trends: {
                    '1year': { priceChange: 10.8, volume: 95 },
                    '2year': { priceChange: 18.5, volume: 190 },
                    '5year': { priceChange: 42.3, volume: 475 }
                },
                demographics: {
                    population: 18000,
                    medianAge: 29,
                    medianIncome: 72000,
                    ownerOccupied: 35
                }
            }
        ];

        return sampleNeighborhoods;
    }

    createNeighborhoodLayer() {
        if (this.layers.neighborhoods) {
            this.map.removeLayer(this.layers.neighborhoods);
        }

        this.layers.neighborhoods = L.layerGroup();

        this.neighborhoods.forEach(neighborhood => {
            // Create polygon for neighborhood boundary
            const polygon = L.polygon(neighborhood.bounds, {
                color: this.getNeighborhoodColor(neighborhood),
                fillColor: this.getNeighborhoodColor(neighborhood),
                fillOpacity: 0.3,
                weight: 2
            });

            // Add popup with neighborhood info
            polygon.bindPopup(this.createNeighborhoodPopup(neighborhood));

            // Add click event
            polygon.on('click', () => {
                this.selectNeighborhood(neighborhood);
            });

            this.layers.neighborhoods.addLayer(polygon);

            // Add neighborhood label
            const label = L.marker(neighborhood.center, {
                icon: L.divIcon({
                    className: 'neighborhood-label',
                    html: `<div class="label-content">${neighborhood.name}</div>`,
                    iconSize: [100, 20],
                    iconAnchor: [50, 10]
                })
            });

            this.layers.neighborhoods.addLayer(label);
        });

        this.layers.neighborhoods.addTo(this.map);
    }

    getNeighborhoodColor(neighborhood) {
        // Color based on price change trend
        const priceChange = neighborhood.stats.priceChange;
        if (priceChange >= 10) return '#10b981'; // Green for high growth
        if (priceChange >= 5) return '#f59e0b';  // Yellow for moderate growth
        if (priceChange >= 0) return '#6b7280';  // Gray for stable
        return '#ef4444'; // Red for decline
    }

    createNeighborhoodPopup(neighborhood) {
        const stats = neighborhood.stats;
        const priceChangeColor = stats.priceChange >= 0 ? '#10b981' : '#ef4444';
        const priceChangeIcon = stats.priceChange >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';

        return `
            <div class="neighborhood-popup">
                <div class="popup-header">
                    <h4>${neighborhood.name}</h4>
                    <p>${neighborhood.city}, ${neighborhood.state}</p>
                </div>
                <div class="popup-stats">
                    <div class="stat-row">
                        <span class="stat-label">Avg Price:</span>
                        <span class="stat-value">$${stats.avgPrice.toLocaleString()}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Price/Sq Ft:</span>
                        <span class="stat-value">$${stats.pricePerSqFt}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Price Change:</span>
                        <span class="stat-value" style="color: ${priceChangeColor}">
                            <i class="fas ${priceChangeIcon}"></i> ${Math.abs(stats.priceChange)}%
                        </span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Days on Market:</span>
                        <span class="stat-value">${stats.daysOnMarket}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Walk Score:</span>
                        <span class="stat-value">${stats.walkScore}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">School Rating:</span>
                        <span class="stat-value">${stats.schoolRating}/10</span>
                    </div>
                </div>
                <div class="popup-actions">
                    <button class="btn btn-sm btn-primary" onclick="neighborhoodExplorer.selectNeighborhood('${neighborhood.id}')">
                        View Details
                    </button>
                </div>
            </div>
        `;
    }

    async showLayer(layerName) {
        this.activeOverlays.add(layerName);

        switch (layerName) {
            case 'schools':
                await this.loadSchoolLayer();
                break;
            case 'amenities':
                await this.loadAmenityLayer();
                break;
            case 'crime':
                await this.loadCrimeLayer();
                break;
            case 'properties':
                await this.loadPropertyLayer();
                break;
        }
    }

    hideLayer(layerName) {
        this.activeOverlays.delete(layerName);

        if (this.layers[layerName]) {
            this.map.removeLayer(this.layers[layerName]);
            this.layers[layerName] = null;
        }
    }

    async loadSchoolLayer() {
        if (this.layers.schools) return;

        try {
            // Generate sample school data
            const schools = this.generateSampleSchoolData();
            
            this.layers.schools = L.layerGroup();

            schools.forEach(school => {
                const marker = L.marker(school.location, {
                    icon: L.divIcon({
                        className: `school-marker ${school.type}`,
                        html: `<i class="fas fa-graduation-cap"></i>`,
                        iconSize: [30, 30],
                        iconAnchor: [15, 15]
                    })
                });

                marker.bindPopup(this.createSchoolPopup(school));
                this.layers.schools.addLayer(marker);
            });

            this.layers.schools.addTo(this.map);
        } catch (error) {
            console.error('Error loading school layer:', error);
        }
    }

    generateSampleSchoolData() {
        return [
            {
                id: 'atlanta-elementary-1',
                name: 'Downtown Elementary School',
                type: 'elementary',
                location: [33.7520, -84.3720],
                rating: 7,
                enrollment: 450,
                studentTeacherRatio: 18
            },
            {
                id: 'atlanta-middle-1',
                name: 'Midtown Middle School',
                type: 'middle',
                location: [33.7760, -84.3740],
                rating: 8,
                enrollment: 650,
                studentTeacherRatio: 16
            },
            {
                id: 'atlanta-high-1',
                name: 'Buckhead High School',
                type: 'high',
                location: [33.8460, -84.3740],
                rating: 9,
                enrollment: 1200,
                studentTeacherRatio: 15
            }
        ];
    }

    createSchoolPopup(school) {
        return `
            <div class="school-popup">
                <div class="popup-header">
                    <h4>${school.name}</h4>
                    <span class="school-type">${school.type.charAt(0).toUpperCase() + school.type.slice(1)}</span>
                </div>
                <div class="popup-stats">
                    <div class="stat-row">
                        <span class="stat-label">Rating:</span>
                        <span class="stat-value">${school.rating}/10</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Enrollment:</span>
                        <span class="stat-value">${school.enrollment}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Student/Teacher:</span>
                        <span class="stat-value">${school.studentTeacherRatio}:1</span>
                    </div>
                </div>
            </div>
        `;
    }

    async loadAmenityLayer() {
        if (this.layers.amenities) return;

        try {
            const amenities = this.generateSampleAmenityData();
            
            this.layers.amenities = L.layerGroup();

            amenities.forEach(amenity => {
                const marker = L.marker(amenity.location, {
                    icon: L.divIcon({
                        className: `amenity-marker ${amenity.category}`,
                        html: `<i class="fas ${amenity.icon}"></i>`,
                        iconSize: [25, 25],
                        iconAnchor: [12, 12]
                    })
                });

                marker.bindPopup(this.createAmenityPopup(amenity));
                this.layers.amenities.addLayer(marker);
            });

            this.layers.amenities.addTo(this.map);
        } catch (error) {
            console.error('Error loading amenity layer:', error);
        }
    }

    generateSampleAmenityData() {
        return [
            {
                id: 'grocery-1',
                name: 'Whole Foods Market',
                category: 'grocery',
                icon: 'fa-shopping-cart',
                location: [33.7530, -84.3710],
                rating: 4.2,
                distance: 0.3
            },
            {
                id: 'hospital-1',
                name: 'Atlanta Medical Center',
                category: 'healthcare',
                icon: 'fa-hospital',
                location: [33.7580, -84.3680],
                rating: 4.5,
                distance: 0.8
            },
            {
                id: 'park-1',
                name: 'Centennial Olympic Park',
                category: 'recreation',
                icon: 'fa-tree',
                location: [33.7600, -84.3700],
                rating: 4.7,
                distance: 0.5
            },
            {
                id: 'transit-1',
                name: 'MARTA Station',
                category: 'transit',
                icon: 'fa-subway',
                location: [33.7510, -84.3750],
                rating: 3.8,
                distance: 0.2
            }
        ];
    }

    createAmenityPopup(amenity) {
        return `
            <div class="amenity-popup">
                <div class="popup-header">
                    <h4>${amenity.name}</h4>
                    <span class="amenity-category">${amenity.category}</span>
                </div>
                <div class="popup-stats">
                    <div class="stat-row">
                        <span class="stat-label">Rating:</span>
                        <span class="stat-value">${amenity.rating}/5</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Distance:</span>
                        <span class="stat-value">${amenity.distance} mi</span>
                    </div>
                </div>
            </div>
        `;
    }

    async loadCrimeLayer() {
        if (this.layers.crime) return;

        try {
            const crimeData = this.generateSampleCrimeData();
            
            this.layers.crime = L.layerGroup();

            // Create heatmap points
            crimeData.forEach(incident => {
                const circle = L.circle(incident.location, {
                    color: this.getCrimeColor(incident.severity),
                    fillColor: this.getCrimeColor(incident.severity),
                    fillOpacity: 0.6,
                    radius: incident.severity * 50
                });

                circle.bindPopup(this.createCrimePopup(incident));
                this.layers.crime.addLayer(circle);
            });

            this.layers.crime.addTo(this.map);
        } catch (error) {
            console.error('Error loading crime layer:', error);
        }
    }

    generateSampleCrimeData() {
        return [
            {
                id: 'crime-1',
                type: 'Property Crime',
                severity: 3,
                location: [33.7540, -84.3740],
                date: '2024-01-15',
                description: 'Theft from vehicle'
            },
            {
                id: 'crime-2',
                type: 'Violent Crime',
                severity: 8,
                location: [33.7520, -84.3760],
                date: '2024-01-10',
                description: 'Assault'
            },
            {
                id: 'crime-3',
                type: 'Property Crime',
                severity: 4,
                location: [33.7560, -84.3720],
                date: '2024-01-12',
                description: 'Burglary'
            }
        ];
    }

    getCrimeColor(severity) {
        if (severity >= 7) return '#ef4444'; // Red for high severity
        if (severity >= 4) return '#f59e0b'; // Yellow for medium severity
        return '#10b981'; // Green for low severity
    }

    createCrimePopup(incident) {
        return `
            <div class="crime-popup">
                <div class="popup-header">
                    <h4>${incident.type}</h4>
                    <span class="crime-severity severity-${incident.severity}">Severity: ${incident.severity}/10</span>
                </div>
                <div class="popup-content">
                    <p><strong>Date:</strong> ${new Date(incident.date).toLocaleDateString()}</p>
                    <p><strong>Description:</strong> ${incident.description}</p>
                </div>
            </div>
        `;
    }

    async loadPropertyLayer() {
        if (this.layers.properties) return;

        try {
            // Load properties from the existing leads/properties data
            const properties = await this.getPropertiesInView();
            
            this.layers.properties = L.layerGroup();

            properties.forEach(property => {
                if (property.latitude && property.longitude) {
                    const marker = L.marker([property.latitude, property.longitude], {
                        icon: L.divIcon({
                            className: 'property-marker',
                            html: `<i class="fas fa-home"></i>`,
                            iconSize: [20, 20],
                            iconAnchor: [10, 10]
                        })
                    });

                    marker.bindPopup(this.createPropertyPopup(property));
                    this.layers.properties.addLayer(marker);
                }
            });

            this.layers.properties.addTo(this.map);
        } catch (error) {
            console.error('Error loading property layer:', error);
        }
    }

    async getPropertiesInView() {
        // In a real implementation, this would get properties from the API
        // For now, return sample data
        return [
            {
                id: 'prop-1',
                address: '123 Main St',
                latitude: 33.7535,
                longitude: -84.3725,
                price: 425000,
                bedrooms: 3,
                bathrooms: 2,
                squareFeet: 1800
            },
            {
                id: 'prop-2',
                address: '456 Oak Ave',
                latitude: 33.7555,
                longitude: -84.3745,
                price: 380000,
                bedrooms: 2,
                bathrooms: 2,
                squareFeet: 1500
            }
        ];
    }

    createPropertyPopup(property) {
        return `
            <div class="property-popup">
                <div class="popup-header">
                    <h4>${property.address}</h4>
                </div>
                <div class="popup-stats">
                    <div class="stat-row">
                        <span class="stat-label">Price:</span>
                        <span class="stat-value">$${property.price.toLocaleString()}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Beds/Baths:</span>
                        <span class="stat-value">${property.bedrooms}/${property.bathrooms}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">Sq Ft:</span>
                        <span class="stat-value">${property.squareFeet.toLocaleString()}</span>
                    </div>
                </div>
            </div>
        `;
    }

    selectNeighborhood(neighborhoodId) {
        const neighborhood = this.neighborhoods.find(n => n.id === neighborhoodId);
        if (!neighborhood) return;

        this.selectedNeighborhood = neighborhood;
        
        // Zoom to neighborhood
        this.map.fitBounds(neighborhood.bounds, { padding: [20, 20] });
        
        // Update detail panel
        this.updateNeighborhoodDetails(neighborhood);
        
        // Show detail panel
        const detailPanel = document.getElementById('neighborhood-details');
        if (detailPanel) {
            detailPanel.classList.remove('hidden');
        }
    }

    updateNeighborhoodDetails(neighborhood) {
        const container = document.getElementById('neighborhood-details-content');
        if (!container) return;

        const stats = neighborhood.stats;
        const demographics = neighborhood.demographics;
        const trends = neighborhood.trends;

        container.innerHTML = `
            <div class="neighborhood-header">
                <h2>${neighborhood.name}</h2>
                <p>${neighborhood.city}, ${neighborhood.state}</p>
            </div>

            <div class="details-section">
                <h3>Market Statistics</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">$${stats.avgPrice.toLocaleString()}</div>
                        <div class="stat-label">Average Price</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">$${stats.pricePerSqFt}</div>
                        <div class="stat-label">Price per Sq Ft</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.daysOnMarket}</div>
                        <div class="stat-label">Days on Market</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">${stats.inventory}</div>
                        <div class="stat-label">Active Listings</div>
                    </div>
                </div>
            </div>

            <div class="details-section">
                <h3>Price Trends</h3>
                <div class="trend-chart" id="trend-chart-${neighborhood.id}">
                    <!-- Trend chart would be rendered here -->
                </div>
                <div class="trend-summary">
                    <div class="trend-item">
                        <span class="trend-period">1 Year:</span>
                        <span class="trend-value ${trends['1year'].priceChange >= 0 ? 'positive' : 'negative'}">
                            ${trends['1year'].priceChange >= 0 ? '+' : ''}${trends['1year'].priceChange}%
                        </span>
                    </div>
                    <div class="trend-item">
                        <span class="trend-period">2 Years:</span>
                        <span class="trend-value ${trends['2year'].priceChange >= 0 ? 'positive' : 'negative'}">
                            ${trends['2year'].priceChange >= 0 ? '+' : ''}${trends['2year'].priceChange}%
                        </span>
                    </div>
                    <div class="trend-item">
                        <span class="trend-period">5 Years:</span>
                        <span class="trend-value ${trends['5year'].priceChange >= 0 ? 'positive' : 'negative'}">
                            ${trends['5year'].priceChange >= 0 ? '+' : ''}${trends['5year'].priceChange}%
                        </span>
                    </div>
                </div>
            </div>

            <div class="details-section">
                <h3>Quality of Life</h3>
                <div class="quality-metrics">
                    <div class="metric-item">
                        <div class="metric-label">Walk Score</div>
                        <div class="metric-bar">
                            <div class="bar-fill" style="width: ${stats.walkScore}%"></div>
                            <span class="metric-value">${stats.walkScore}</span>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">School Rating</div>
                        <div class="metric-bar">
                            <div class="bar-fill" style="width: ${stats.schoolRating * 10}%"></div>
                            <span class="metric-value">${stats.schoolRating}/10</span>
                        </div>
                    </div>
                    <div class="metric-item">
                        <div class="metric-label">Safety Score</div>
                        <div class="metric-bar">
                            <div class="bar-fill" style="width: ${(10 - stats.crimeScore) * 10}%"></div>
                            <span class="metric-value">${10 - stats.crimeScore}/10</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="details-section">
                <h3>Demographics</h3>
                <div class="demographics-grid">
                    <div class="demo-item">
                        <div class="demo-value">${demographics.population.toLocaleString()}</div>
                        <div class="demo-label">Population</div>
                    </div>
                    <div class="demo-item">
                        <div class="demo-value">${demographics.medianAge}</div>
                        <div class="demo-label">Median Age</div>
                    </div>
                    <div class="demo-item">
                        <div class="demo-value">$${demographics.medianIncome.toLocaleString()}</div>
                        <div class="demo-label">Median Income</div>
                    </div>
                    <div class="demo-item">
                        <div class="demo-value">${demographics.ownerOccupied}%</div>
                        <div class="demo-label">Owner Occupied</div>
                    </div>
                </div>
            </div>

            <div class="details-section">
                <h3>Investment Metrics</h3>
                <div class="investment-metrics">
                    <div class="metric-card">
                        <div class="metric-value">${stats.rentYield}%</div>
                        <div class="metric-label">Rental Yield</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${stats.priceChange >= 0 ? '+' : ''}${stats.priceChange}%</div>
                        <div class="metric-label">Price Appreciation</div>
                    </div>
                </div>
            </div>
        `;
    }

    populateNeighborhoodList() {
        const container = document.getElementById('neighborhood-list');
        if (!container) return;

        const sortedNeighborhoods = [...this.neighborhoods].sort((a, b) => 
            b.stats.priceChange - a.stats.priceChange
        );

        container.innerHTML = sortedNeighborhoods.map(neighborhood => `
            <div class="neighborhood-item" data-id="${neighborhood.id}" onclick="neighborhoodExplorer.selectNeighborhood('${neighborhood.id}')">
                <div class="item-header">
                    <h4>${neighborhood.name}</h4>
                    <span class="price-change ${neighborhood.stats.priceChange >= 0 ? 'positive' : 'negative'}">
                        ${neighborhood.stats.priceChange >= 0 ? '+' : ''}${neighborhood.stats.priceChange}%
                    </span>
                </div>
                <div class="item-details">
                    <span>Avg: $${neighborhood.stats.avgPrice.toLocaleString()}</span>
                    <span>Walk Score: ${neighborhood.stats.walkScore}</span>
                    <span>Schools: ${neighborhood.stats.schoolRating}/10</span>
                </div>
            </div>
        `).join('');
    }

    searchNeighborhoods(query) {
        if (!query) {
            this.populateNeighborhoodList();
            return;
        }

        const filteredNeighborhoods = this.neighborhoods.filter(neighborhood =>
            neighborhood.name.toLowerCase().includes(query.toLowerCase()) ||
            neighborhood.city.toLowerCase().includes(query.toLowerCase()) ||
            neighborhood.state.toLowerCase().includes(query.toLowerCase())
        );

        const container = document.getElementById('neighborhood-list');
        if (!container) return;

        container.innerHTML = filteredNeighborhoods.map(neighborhood => `
            <div class="neighborhood-item" data-id="${neighborhood.id}" onclick="neighborhoodExplorer.selectNeighborhood('${neighborhood.id}')">
                <div class="item-header">
                    <h4>${neighborhood.name}</h4>
                    <span class="price-change ${neighborhood.stats.priceChange >= 0 ? 'positive' : 'negative'}">
                        ${neighborhood.stats.priceChange >= 0 ? '+' : ''}${neighborhood.stats.priceChange}%
                    </span>
                </div>
                <div class="item-details">
                    <span>Avg: $${neighborhood.stats.avgPrice.toLocaleString()}</span>
                    <span>Walk Score: ${neighborhood.stats.walkScore}</span>
                    <span>Schools: ${neighborhood.stats.schoolRating}/10</span>
                </div>
            </div>
        `).join('');
    }

    filterByPriceRange(range) {
        // Implementation for price range filtering
        console.log('Filter by price range:', range);
    }

    filterByTrend(trend) {
        // Implementation for trend filtering
        console.log('Filter by trend:', trend);
    }

    resetMapView() {
        this.map.setView([39.8283, -98.5795], 4);
        
        // Hide detail panel
        const detailPanel = document.getElementById('neighborhood-details');
        if (detailPanel) {
            detailPanel.classList.add('hidden');
        }
        
        this.selectedNeighborhood = null;
    }

    updateVisibleNeighborhoods() {
        // Update visible neighborhoods based on map bounds
        const bounds = this.map.getBounds();
        const visibleNeighborhoods = this.neighborhoods.filter(neighborhood =>
            bounds.contains(neighborhood.center)
        );

        // Update visible count
        const visibleCount = document.getElementById('visible-neighborhoods-count');
        if (visibleCount) {
            visibleCount.textContent = `${visibleNeighborhoods.length} neighborhoods visible`;
        }
    }

    updateStats() {
        const statsContainer = document.getElementById('explorer-stats');
        if (!statsContainer) return;

        const totalNeighborhoods = this.neighborhoods.length;
        const avgPriceChange = this.neighborhoods.reduce((sum, n) => sum + n.stats.priceChange, 0) / totalNeighborhoods;
        const avgWalkScore = this.neighborhoods.reduce((sum, n) => sum + n.stats.walkScore, 0) / totalNeighborhoods;

        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${totalNeighborhoods}</div>
                    <div class="stat-label">Neighborhoods</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${avgPriceChange.toFixed(1)}%</div>
                    <div class="stat-label">Avg Price Change</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${avgWalkScore.toFixed(0)}</div>
                    <div class="stat-label">Avg Walk Score</div>
                </div>
            </div>
        `;
    }

    handleMapClick(e) {
        // Handle map clicks for additional functionality
        console.log('Map clicked at:', e.latlng);
    }

    updateTrendPeriod(period) {
        // Update trend visualization period
        console.log('Update trend period:', period);
    }

    exportNeighborhoodData() {
        try {
            const data = {
                neighborhoods: this.neighborhoods,
                selectedNeighborhood: this.selectedNeighborhood,
                exportDate: new Date().toISOString()
            };

            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `neighborhood-data-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            Utils.showToast('Neighborhood data exported successfully', 'success');
        } catch (error) {
            console.error('Error exporting data:', error);
            Utils.showToast('Failed to export data', 'error');
        }
    }
}

// Initialize neighborhood explorer when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('neighborhood-explorer-container')) {
        window.neighborhoodExplorer = new NeighborhoodExplorer();
    }
});