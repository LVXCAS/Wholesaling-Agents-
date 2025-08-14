/**
 * Campaign Management JavaScript
 * Handles campaign creation, monitoring, and analytics
 */

class CampaignManager {
    constructor() {
        this.campaigns = [];
        this.currentStep = 1;
        this.campaignData = {
            name: '',
            description: '',
            type: '',
            priority: 'normal',
            channels: [],
            audience: {
                type: 'all-leads',
                filters: {},
                count: 0
            },
            messages: {},
            schedule: {
                type: 'immediate',
                details: {}
            }
        };
        this.analytics = {};
        this.abTests = [];
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadCampaigns();
        this.loadAnalytics();
        this.loadABTests();
        this.initCharts();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e));
        });

        // Campaign creation
        document.getElementById('create-campaign')?.addEventListener('click', () => this.showCampaignBuilder());

        // Campaign filters
        document.getElementById('status-filter')?.addEventListener('change', () => this.filterCampaigns());
        document.getElementById('channel-filter')?.addEventListener('change', () => this.filterCampaigns());
        document.getElementById('campaign-search')?.addEventListener('input', () => this.filterCampaigns());

        // Campaign builder navigation
        document.getElementById('next-step')?.addEventListener('click', () => this.nextStep());
        document.getElementById('prev-step')?.addEventListener('click', () => this.prevStep());
        document.getElementById('save-draft')?.addEventListener('click', () => this.saveDraft());
        document.getElementById('launch-campaign')?.addEventListener('click', () => this.launchCampaign());

        // Form inputs
        document.getElementById('campaign-name')?.addEventListener('input', (e) => {
            this.campaignData.name = e.target.value;
            this.updateSummary();
        });

        document.getElementById('campaign-description')?.addEventListener('input', (e) => {
            this.campaignData.description = e.target.value;
        });

        document.getElementById('campaign-type')?.addEventListener('change', (e) => {
            this.campaignData.type = e.target.value;
        });

        document.getElementById('campaign-priority')?.addEventListener('change', (e) => {
            this.campaignData.priority = e.target.value;
        });

        // Channel selection
        document.querySelectorAll('input[type="checkbox"][id^="channel-"]').forEach(checkbox => {
            checkbox.addEventListener('change', () => this.updateChannels());
        });

        // Audience selection
        document.querySelectorAll('.audience-option').forEach(option => {
            option.addEventListener('click', (e) => this.selectAudience(e));
        });

        // Audience filters
        document.querySelectorAll('#audience-filters select, #audience-filters input').forEach(input => {
            input.addEventListener('change', () => this.updateAudienceFilters());
        });

        // Schedule type
        document.querySelectorAll('input[name="schedule-type"]').forEach(radio => {
            radio.addEventListener('change', (e) => this.updateScheduleType(e));
        });

        // Analytics controls
        document.getElementById('analytics-period')?.addEventListener('change', () => this.updateAnalytics());
        document.querySelectorAll('.chart-control').forEach(btn => {
            btn.addEventListener('click', (e) => this.updateChart(e));
        });

        // A/B Testing
        document.getElementById('create-ab-test')?.addEventListener('click', () => this.createABTest());

        // Modal controls
        document.getElementById('close-campaign-modal')?.addEventListener('click', () => this.closeCampaignModal());
    }

    async loadCampaigns() {
        try {
            showLoading();
            const response = await fetch('/api/campaigns');
            if (response.ok) {
                this.campaigns = await response.json();
                this.renderCampaigns();
            } else {
                throw new Error('Failed to load campaigns');
            }
        } catch (error) {
            console.error('Error loading campaigns:', error);
            showNotification('Failed to load campaigns', 'error');
        } finally {
            hideLoading();
        }
    }

    renderCampaigns() {
        const container = document.getElementById('campaigns-grid');
        if (!container) return;

        if (this.campaigns.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-bullhorn"></i>
                    <h3>No campaigns yet</h3>
                    <p>Create your first campaign to start reaching out to leads</p>
                    <button class="btn btn-primary" onclick="campaignManager.showCampaignBuilder()">
                        <i class="fas fa-plus"></i> Create Campaign
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = this.campaigns.map(campaign => `
            <div class="campaign-card" data-campaign-id="${campaign.id}">
                <div class="campaign-card-header">
                    <div>
                        <div class="campaign-title">${escapeHtml(campaign.name)}</div>
                        <div class="campaign-type">${campaign.type.replace('_', ' ')}</div>
                    </div>
                    <div class="campaign-status ${campaign.status}">${campaign.status}</div>
                </div>
                <div class="campaign-description">${escapeHtml(campaign.description || '')}</div>
                <div class="campaign-channels">
                    ${campaign.channels.map(channel => `
                        <div class="channel-badge">
                            <i class="fas fa-${this.getChannelIcon(channel)}"></i>
                            ${channel.toUpperCase()}
                        </div>
                    `).join('')}
                </div>
                <div class="campaign-metrics">
                    <div class="metric">
                        <div class="metric-value">${campaign.metrics.sent || 0}</div>
                        <div class="metric-label">Sent</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${campaign.metrics.open_rate || 0}%</div>
                        <div class="metric-label">Open Rate</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">${campaign.metrics.response_rate || 0}%</div>
                        <div class="metric-label">Response Rate</div>
                    </div>
                </div>
                <div class="campaign-actions">
                    <div class="campaign-date">
                        Created ${formatDate(campaign.created_at)}
                    </div>
                    <div class="campaign-controls">
                        <button class="control-btn" onclick="campaignManager.viewCampaign('${campaign.id}')">
                            <i class="fas fa-eye"></i> View
                        </button>
                        <button class="control-btn" onclick="campaignManager.editCampaign('${campaign.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="control-btn" onclick="campaignManager.toggleCampaign('${campaign.id}')">
                            <i class="fas fa-${campaign.status === 'active' ? 'pause' : 'play'}"></i>
                            ${campaign.status === 'active' ? 'Pause' : 'Resume'}
                        </button>
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.campaign-card').forEach(card => {
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.campaign-controls')) {
                    const campaignId = card.dataset.campaignId;
                    this.viewCampaign(campaignId);
                }
            });
        });
    }

    filterCampaigns() {
        const statusFilter = document.getElementById('status-filter')?.value || 'all';
        const channelFilter = document.getElementById('channel-filter')?.value || 'all';
        const searchTerm = document.getElementById('campaign-search')?.value.toLowerCase() || '';

        let filteredCampaigns = this.campaigns.filter(campaign => {
            if (statusFilter !== 'all' && campaign.status !== statusFilter) {
                return false;
            }
            if (channelFilter !== 'all') {
                if (channelFilter === 'multi' && campaign.channels.length <= 1) {
                    return false;
                }
                if (channelFilter !== 'multi' && !campaign.channels.includes(channelFilter)) {
                    return false;
                }
            }
            if (searchTerm && !campaign.name.toLowerCase().includes(searchTerm) && 
                !campaign.description.toLowerCase().includes(searchTerm)) {
                return false;
            }
            return true;
        });

        // Temporarily store filtered campaigns and re-render
        const originalCampaigns = this.campaigns;
        this.campaigns = filteredCampaigns;
        this.renderCampaigns();
        this.campaigns = originalCampaigns;
    }

    switchTab(event) {
        const tabName = event.currentTarget.dataset.tab;
        
        // Update tab buttons
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`)?.classList.add('active');
        
        // Load data for specific tabs
        if (tabName === 'analytics') {
            this.loadAnalytics();
        } else if (tabName === 'ab-testing') {
            this.loadABTests();
        }
    }

    showCampaignBuilder() {
        // Switch to builder tab
        document.querySelector('[data-tab="builder"]').click();
        
        // Reset campaign data
        this.resetCampaignData();
        this.currentStep = 1;
        this.updateBuilderStep();
    }

    resetCampaignData() {
        this.campaignData = {
            name: '',
            description: '',
            type: '',
            priority: 'normal',
            channels: [],
            audience: {
                type: 'all-leads',
                filters: {},
                count: 0
            },
            messages: {},
            schedule: {
                type: 'immediate',
                details: {}
            }
        };
        
        // Clear form inputs
        document.getElementById('campaign-name').value = '';
        document.getElementById('campaign-description').value = '';
        document.getElementById('campaign-type').value = '';
        document.getElementById('campaign-priority').value = 'normal';
        
        // Clear channel checkboxes
        document.querySelectorAll('input[type="checkbox"][id^="channel-"]').forEach(checkbox => {
            checkbox.checked = false;
        });
        
        this.updateSummary();
    }

    nextStep() {
        if (this.validateCurrentStep()) {
            this.currentStep++;
            this.updateBuilderStep();
        }
    }

    prevStep() {
        this.currentStep--;
        this.updateBuilderStep();
    }

    updateBuilderStep() {
        // Update step indicators
        document.querySelectorAll('.step').forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNumber === this.currentStep) {
                step.classList.add('active');
            } else if (stepNumber < this.currentStep) {
                step.classList.add('completed');
            }
        });
        
        // Update step content
        document.querySelectorAll('.step-content').forEach((content, index) => {
            const stepNumber = index + 1;
            content.classList.remove('active');
            
            if (stepNumber === this.currentStep) {
                content.classList.add('active');
            }
        });
        
        // Update navigation buttons
        const prevBtn = document.getElementById('prev-step');
        const nextBtn = document.getElementById('next-step');
        const launchBtn = document.getElementById('launch-campaign');
        
        if (prevBtn) prevBtn.style.display = this.currentStep > 1 ? 'block' : 'none';
        if (nextBtn) nextBtn.style.display = this.currentStep < 4 ? 'block' : 'none';
        if (launchBtn) launchBtn.style.display = this.currentStep === 4 ? 'block' : 'none';
        
        // Load step-specific data
        if (this.currentStep === 2) {
            this.loadAudienceData();
        } else if (this.currentStep === 3) {
            this.setupMessageEditor();
        } else if (this.currentStep === 4) {
            this.updateSummary();
        }
    }

    validateCurrentStep() {
        switch (this.currentStep) {
            case 1:
                if (!this.campaignData.name || !this.campaignData.type || this.campaignData.channels.length === 0) {
                    showNotification('Please fill in all required fields', 'warning');
                    return false;
                }
                break;
            case 2:
                if (this.campaignData.audience.count === 0) {
                    showNotification('Please select an audience', 'warning');
                    return false;
                }
                break;
            case 3:
                if (Object.keys(this.campaignData.messages).length === 0) {
                    showNotification('Please create messages for at least one channel', 'warning');
                    return false;
                }
                break;
        }
        return true;
    }

    updateChannels() {
        this.campaignData.channels = [];
        document.querySelectorAll('input[type="checkbox"][id^="channel-"]:checked').forEach(checkbox => {
            this.campaignData.channels.push(checkbox.value);
        });
        this.updateSummary();
    }

    selectAudience(event) {
        const option = event.currentTarget.dataset.option;
        
        // Update UI
        document.querySelectorAll('.audience-option').forEach(opt => {
            opt.classList.remove('selected');
        });
        event.currentTarget.classList.add('selected');
        
        // Update data
        this.campaignData.audience.type = option;
        
        // Show/hide filters
        const filtersContainer = document.getElementById('audience-filters');
        if (option === 'filtered-leads') {
            filtersContainer.style.display = 'block';
            this.updateAudienceFilters();
        } else {
            filtersContainer.style.display = 'none';
            this.loadAudienceCount();
        }
    }

    async loadAudienceCount() {
        try {
            const response = await fetch('/api/leads/count', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    type: this.campaignData.audience.type,
                    filters: this.campaignData.audience.filters
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.campaignData.audience.count = data.count;
                
                // Update UI
                document.querySelectorAll('.lead-count').forEach(el => {
                    el.textContent = `${data.count} leads`;
                });
                document.getElementById('filtered-count').textContent = data.count;
            }
        } catch (error) {
            console.error('Error loading audience count:', error);
        }
    }

    updateAudienceFilters() {
        this.campaignData.audience.filters = {
            property_type: document.getElementById('filter-property-type')?.value || '',
            location: document.getElementById('filter-location')?.value || '',
            source: document.getElementById('filter-source')?.value || '',
            score: document.getElementById('filter-score')?.value || ''
        };
        
        this.loadAudienceCount();
    }

    setupMessageEditor() {
        const tabsContainer = document.getElementById('message-channel-tabs');
        const editorContainer = document.getElementById('message-editor');
        
        if (!tabsContainer || !editorContainer) return;
        
        // Create tabs for selected channels
        tabsContainer.innerHTML = this.campaignData.channels.map((channel, index) => `
            <button class="channel-tab ${index === 0 ? 'active' : ''}" data-channel="${channel}">
                <i class="fas fa-${this.getChannelIcon(channel)}"></i>
                ${channel.toUpperCase()}
            </button>
        `).join('');
        
        // Create editors for each channel
        editorContainer.innerHTML = this.campaignData.channels.map((channel, index) => `
            <div class="channel-editor ${index === 0 ? 'active' : ''}" data-channel="${channel}">
                ${this.getChannelEditor(channel)}
            </div>
        `).join('');
        
        // Bind tab events
        tabsContainer.querySelectorAll('.channel-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchMessageChannel(e));
        });
    }

    getChannelEditor(channel) {
        switch (channel) {
            case 'email':
                return `
                    <div class="form-group">
                        <label for="email-subject-builder">Subject Line</label>
                        <input type="text" id="email-subject-builder" class="form-control" placeholder="Enter email subject">
                    </div>
                    <div class="form-group">
                        <label for="email-content-builder">Email Content</label>
                        <textarea id="email-content-builder" class="form-control" rows="8" placeholder="Enter email content"></textarea>
                    </div>
                `;
            case 'sms':
                return `
                    <div class="form-group">
                        <label for="sms-content-builder">SMS Message</label>
                        <textarea id="sms-content-builder" class="form-control" rows="4" maxlength="160" placeholder="Enter SMS message"></textarea>
                        <div class="character-count">
                            <span id="sms-char-count-builder">0</span>/160
                        </div>
                    </div>
                `;
            case 'voice':
                return `
                    <div class="form-group">
                        <label for="voice-script-builder">Voice Script</label>
                        <textarea id="voice-script-builder" class="form-control" rows="6" placeholder="Enter voice call script"></textarea>
                    </div>
                    <div class="form-group">
                        <label>
                            <input type="checkbox" id="voice-voicemail-builder"> Leave voicemail if no answer
                        </label>
                    </div>
                `;
            default:
                return '<p>Channel editor not available</p>';
        }
    }

    switchMessageChannel(event) {
        const channel = event.currentTarget.dataset.channel;
        
        // Update tabs
        document.querySelectorAll('.channel-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Update editors
        document.querySelectorAll('.channel-editor').forEach(editor => {
            editor.classList.remove('active');
        });
        document.querySelector(`[data-channel="${channel}"]`).classList.add('active');
    }

    updateScheduleType(event) {
        const scheduleType = event.target.value;
        this.campaignData.schedule.type = scheduleType;
        
        const detailsContainer = document.getElementById('schedule-details');
        if (!detailsContainer) return;
        
        switch (scheduleType) {
            case 'scheduled':
                detailsContainer.innerHTML = `
                    <div class="form-group">
                        <label for="schedule-date">Schedule Date & Time</label>
                        <input type="datetime-local" id="schedule-date" class="form-control">
                    </div>
                `;
                break;
            case 'sequence':
                detailsContainer.innerHTML = `
                    <div class="sequence-builder">
                        <h4>Message Sequence</h4>
                        <p>Define when each message should be sent</p>
                        <div id="sequence-steps">
                            <!-- Sequence steps will be added here -->
                        </div>
                        <button class="btn btn-secondary" id="add-sequence-step">
                            <i class="fas fa-plus"></i> Add Step
                        </button>
                    </div>
                `;
                break;
            default:
                detailsContainer.innerHTML = '';
        }
        
        this.updateSummary();
    }

    updateSummary() {
        document.getElementById('summary-name').textContent = this.campaignData.name || '-';
        document.getElementById('summary-audience').textContent = 
            `${this.campaignData.audience.count} leads (${this.campaignData.audience.type.replace('-', ' ')})`;
        document.getElementById('summary-channels').textContent = 
            this.campaignData.channels.join(', ').toUpperCase() || '-';
        document.getElementById('summary-schedule').textContent = 
            this.campaignData.schedule.type.replace('-', ' ') || '-';
    }

    async saveDraft() {
        try {
            showLoading();
            const response = await fetch('/api/campaigns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...this.campaignData,
                    status: 'draft'
                })
            });
            
            if (response.ok) {
                showNotification('Campaign saved as draft', 'success');
                this.loadCampaigns();
            } else {
                throw new Error('Failed to save campaign');
            }
        } catch (error) {
            console.error('Error saving campaign:', error);
            showNotification('Failed to save campaign', 'error');
        } finally {
            hideLoading();
        }
    }

    async launchCampaign() {
        if (!this.validateCurrentStep()) return;
        
        try {
            showLoading();
            const response = await fetch('/api/campaigns', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...this.campaignData,
                    status: 'active'
                })
            });
            
            if (response.ok) {
                showNotification('Campaign launched successfully!', 'success');
                this.loadCampaigns();
                // Switch back to campaigns tab
                document.querySelector('[data-tab="campaigns"]').click();
            } else {
                throw new Error('Failed to launch campaign');
            }
        } catch (error) {
            console.error('Error launching campaign:', error);
            showNotification('Failed to launch campaign', 'error');
        } finally {
            hideLoading();
        }
    }

    async loadAnalytics() {
        try {
            const period = document.getElementById('analytics-period')?.value || '30';
            const response = await fetch(`/api/campaigns/analytics?period=${period}`);
            
            if (response.ok) {
                this.analytics = await response.json();
                this.renderAnalytics();
                this.updateCharts();
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        }
    }

    renderAnalytics() {
        if (!this.analytics) return;
        
        // Update metric cards
        document.getElementById('total-sent').textContent = this.analytics.total_sent || 0;
        document.getElementById('open-rate').textContent = `${this.analytics.open_rate || 0}%`;
        document.getElementById('response-rate').textContent = `${this.analytics.response_rate || 0}%`;
        document.getElementById('roi').textContent = `${this.analytics.roi || 0}%`;
        
        // Update performance table
        this.renderPerformanceTable();
    }

    renderPerformanceTable() {
        const tbody = document.getElementById('performance-table-body');
        if (!tbody || !this.analytics.campaigns) return;
        
        tbody.innerHTML = this.analytics.campaigns.map(campaign => `
            <tr>
                <td>${escapeHtml(campaign.name)}</td>
                <td>${campaign.channels.join(', ').toUpperCase()}</td>
                <td>${campaign.sent}</td>
                <td>${campaign.delivered}</td>
                <td>${campaign.opened}</td>
                <td>${campaign.replied}</td>
                <td>${campaign.roi}%</td>
                <td><span class="campaign-status ${campaign.status}">${campaign.status}</span></td>
            </tr>
        `).join('');
    }

    initCharts() {
        // Initialize Chart.js charts
        this.performanceChart = null;
        this.channelChart = null;
    }

    updateCharts() {
        this.updatePerformanceChart();
        this.updateChannelChart();
    }

    updatePerformanceChart() {
        const ctx = document.getElementById('performance-chart');
        if (!ctx || !this.analytics.performance_data) return;
        
        if (this.performanceChart) {
            this.performanceChart.destroy();
        }
        
        this.performanceChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.analytics.performance_data.labels,
                datasets: [{
                    label: 'Messages Sent',
                    data: this.analytics.performance_data.sent,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Messages Opened',
                    data: this.analytics.performance_data.opened,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Replies Received',
                    data: this.analytics.performance_data.replied,
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    updateChannelChart() {
        const ctx = document.getElementById('channel-chart');
        if (!ctx || !this.analytics.channel_data) return;
        
        if (this.channelChart) {
            this.channelChart.destroy();
        }
        
        this.channelChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: this.analytics.channel_data.labels,
                datasets: [{
                    data: this.analytics.channel_data.values,
                    backgroundColor: ['#3b82f6', '#10b981', '#f59e0b'],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    updateChart(event) {
        const metric = event.currentTarget.dataset.metric;
        
        // Update active button
        document.querySelectorAll('.chart-control').forEach(btn => {
            btn.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Update chart data based on selected metric
        // Implementation would depend on your specific chart library and data structure
        console.log('Updating chart for metric:', metric);
    }

    async loadABTests() {
        try {
            const response = await fetch('/api/campaigns/ab-tests');
            if (response.ok) {
                this.abTests = await response.json();
                this.renderABTests();
            }
        } catch (error) {
            console.error('Error loading A/B tests:', error);
        }
    }

    renderABTests() {
        const container = document.getElementById('ab-tests-list');
        if (!container) return;
        
        if (this.abTests.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-flask"></i>
                    <h3>No A/B tests yet</h3>
                    <p>Create your first A/B test to optimize campaign performance</p>
                </div>
            `;
            return;
        }
        
        // Render A/B tests
        container.innerHTML = this.abTests.map(test => `
            <div class="ab-test-card">
                <h3>${escapeHtml(test.name)}</h3>
                <p>${escapeHtml(test.description)}</p>
                <!-- A/B test details would go here -->
            </div>
        `).join('');
    }

    createABTest() {
        showNotification('A/B test creation coming soon', 'info');
    }

    async viewCampaign(campaignId) {
        try {
            const response = await fetch(`/api/campaigns/${campaignId}`);
            if (response.ok) {
                const campaign = await response.json();
                this.showCampaignModal(campaign);
            }
        } catch (error) {
            console.error('Error loading campaign details:', error);
            showNotification('Failed to load campaign details', 'error');
        }
    }

    showCampaignModal(campaign) {
        const modal = document.getElementById('campaign-modal');
        const title = document.getElementById('campaign-modal-title');
        const body = document.getElementById('campaign-modal-body');
        
        if (!modal || !title || !body) return;
        
        title.textContent = campaign.name;
        body.innerHTML = `
            <div class="campaign-details">
                <div class="detail-section">
                    <h3>Campaign Information</h3>
                    <div class="detail-grid">
                        <div class="detail-item">
                            <label>Type:</label>
                            <span>${campaign.type.replace('_', ' ')}</span>
                        </div>
                        <div class="detail-item">
                            <label>Status:</label>
                            <span class="campaign-status ${campaign.status}">${campaign.status}</span>
                        </div>
                        <div class="detail-item">
                            <label>Priority:</label>
                            <span>${campaign.priority}</span>
                        </div>
                        <div class="detail-item">
                            <label>Created:</label>
                            <span>${formatDateTime(campaign.created_at)}</span>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Performance Metrics</h3>
                    <div class="metrics-grid">
                        <div class="metric-card">
                            <div class="metric-value">${campaign.metrics.sent || 0}</div>
                            <div class="metric-label">Messages Sent</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${campaign.metrics.delivered || 0}</div>
                            <div class="metric-label">Delivered</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${campaign.metrics.opened || 0}</div>
                            <div class="metric-label">Opened</div>
                        </div>
                        <div class="metric-card">
                            <div class="metric-value">${campaign.metrics.replied || 0}</div>
                            <div class="metric-label">Replied</div>
                        </div>
                    </div>
                </div>
                
                <div class="detail-section">
                    <h3>Campaign Actions</h3>
                    <div class="action-buttons">
                        <button class="btn btn-primary" onclick="campaignManager.editCampaign('${campaign.id}')">
                            <i class="fas fa-edit"></i> Edit Campaign
                        </button>
                        <button class="btn btn-secondary" onclick="campaignManager.duplicateCampaign('${campaign.id}')">
                            <i class="fas fa-copy"></i> Duplicate
                        </button>
                        <button class="btn btn-secondary" onclick="campaignManager.exportCampaign('${campaign.id}')">
                            <i class="fas fa-download"></i> Export Data
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        modal.classList.add('active');
    }

    closeCampaignModal() {
        document.getElementById('campaign-modal')?.classList.remove('active');
    }

    editCampaign(campaignId) {
        showNotification('Campaign editing coming soon', 'info');
    }

    duplicateCampaign(campaignId) {
        showNotification('Campaign duplication coming soon', 'info');
    }

    exportCampaign(campaignId) {
        showNotification('Campaign export coming soon', 'info');
    }

    async toggleCampaign(campaignId) {
        try {
            const response = await fetch(`/api/campaigns/${campaignId}/toggle`, {
                method: 'POST'
            });
            
            if (response.ok) {
                showNotification('Campaign status updated', 'success');
                this.loadCampaigns();
            } else {
                throw new Error('Failed to update campaign status');
            }
        } catch (error) {
            console.error('Error toggling campaign:', error);
            showNotification('Failed to update campaign status', 'error');
        }
    }

    getChannelIcon(channel) {
        const icons = {
            email: 'envelope',
            sms: 'sms',
            voice: 'phone'
        };
        return icons[channel] || 'comment';
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showLoading() {
    console.log('Loading...');
}

function hideLoading() {
    console.log('Loading complete');
}

function showNotification(message, type = 'info') {
    console.log(`${type.toUpperCase()}: ${message}`);
}

// Initialize when DOM is loaded
let campaignManager;
document.addEventListener('DOMContentLoaded', () => {
    campaignManager = new CampaignManager();
});