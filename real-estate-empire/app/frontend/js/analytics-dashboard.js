/**
 * Analytics Dashboard JavaScript
 * Handles communication analytics, ROI calculation, and performance visualization
 */

class AnalyticsDashboard {
    constructor() {
        this.dateRange = '30';
        this.customDateRange = {
            start: null,
            end: null
        };
        this.analyticsData = {};
        this.charts = {};
        this.roiCalculator = {
            platformCosts: 500,
            staffTime: 20,
            hourlyRate: 50,
            otherCosts: 0,
            leadsGenerated: 50,
            dealsClosed: 3,
            avgDealValue: 15000
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadAnalyticsData();
        this.initROICalculator();
        this.setupCharts();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e));
        });

        // Header actions
        document.getElementById('refresh-data')?.addEventListener('click', () => this.refreshData());
        document.getElementById('export-report')?.addEventListener('click', () => this.exportReport());

        // Date range selector
        document.getElementById('date-range')?.addEventListener('change', (e) => this.changeDateRange(e));

        // Chart controls
        document.querySelectorAll('.chart-control').forEach(btn => {
            btn.addEventListener('click', (e) => this.updateChartMetric(e));
        });

        // Campaign filters
        document.getElementById('campaign-status-filter')?.addEventListener('change', () => this.filterCampaigns());
        document.getElementById('campaign-type-filter')?.addEventListener('change', () => this.filterCampaigns());

        // Channel comparison
        document.getElementById('comparison-metric')?.addEventListener('change', () => this.updateChannelComparison());

        // ROI Calculator inputs
        this.bindROICalculatorEvents();

        // Modal events
        document.getElementById('close-date-range-modal')?.addEventListener('click', () => this.closeDateRangeModal());
        document.getElementById('cancel-date-range')?.addEventListener('click', () => this.closeDateRangeModal());
        document.getElementById('apply-date-range')?.addEventListener('click', () => this.applyCustomDateRange());

        // Export actions
        document.getElementById('export-campaign-data')?.addEventListener('click', () => this.exportCampaignData());
        document.getElementById('view-all-campaigns')?.addEventListener('click', () => this.viewAllCampaigns());
    }

    bindROICalculatorEvents() {
        const inputs = [
            'platform-costs', 'staff-time', 'hourly-rate', 'other-costs',
            'leads-generated', 'deals-closed', 'avg-deal-value'
        ];

        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                input.addEventListener('input', () => this.updateROICalculation());
            }
        });
    }

    async loadAnalyticsData() {
        try {
            showLoading();
            const response = await fetch(`/api/analytics/communication?period=${this.dateRange}`);
            if (response.ok) {
                this.analyticsData = await response.json();
                this.renderAnalytics();
                this.updateCharts();
            } else {
                throw new Error('Failed to load analytics data');
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
            showNotification('Failed to load analytics data', 'error');
        } finally {
            hideLoading();
        }
    }

    renderAnalytics() {
        this.renderOverviewMetrics();
        this.renderPerformanceTable();
        this.renderChannelMetrics();
        this.renderCampaignTable();
        this.renderConversionFunnel();
        this.updateBenchmarks();
    }

    renderOverviewMetrics() {
        const data = this.analyticsData.overview || {};
        
        // Update metric values
        document.getElementById('total-messages').textContent = formatNumber(data.total_messages || 0);
        document.getElementById('open-rate').textContent = `${data.open_rate || 0}%`;
        document.getElementById('response-rate').textContent = `${data.response_rate || 0}%`;
        document.getElementById('conversion-rate').textContent = `${data.conversion_rate || 0}%`;
        
        // Update metric changes
        this.updateMetricChange('messages-change', data.messages_change || 0);
        this.updateMetricChange('open-rate-change', data.open_rate_change || 0);
        this.updateMetricChange('response-rate-change', data.response_rate_change || 0);
        this.updateMetricChange('conversion-rate-change', data.conversion_rate_change || 0);
    }

    updateMetricChange(elementId, change) {
        const element = document.getElementById(elementId);
        if (!element) return;

        const isPositive = change > 0;
        const isNegative = change < 0;
        
        element.className = `metric-change ${isPositive ? 'positive' : isNegative ? 'negative' : 'neutral'}`;
        element.innerHTML = `
            <i class="fas fa-arrow-${isPositive ? 'up' : isNegative ? 'down' : 'right'}"></i>
            ${isPositive ? '+' : ''}${change}%
        `;
    }

    renderPerformanceTable() {
        const tbody = document.getElementById('performance-table-body');
        if (!tbody || !this.analyticsData.recent_campaigns) return;

        tbody.innerHTML = this.analyticsData.recent_campaigns.map(campaign => `
            <tr>
                <td>${escapeHtml(campaign.name)}</td>
                <td>
                    <span class="channel-badge ${campaign.primary_channel}">
                        ${campaign.primary_channel.toUpperCase()}
                    </span>
                </td>
                <td>${formatNumber(campaign.sent)}</td>
                <td>${formatNumber(campaign.delivered)}</td>
                <td>${campaign.open_rate}%</td>
                <td>${campaign.response_rate}%</td>
                <td>${campaign.conversion_rate}%</td>
                <td class="${campaign.roi >= 0 ? 'positive' : 'negative'}">${campaign.roi}%</td>
            </tr>
        `).join('');
    }

    renderChannelMetrics() {
        const channels = this.analyticsData.channels || {};
        
        // Email metrics
        if (channels.email) {
            document.getElementById('email-sent').textContent = formatNumber(channels.email.sent || 0);
            document.getElementById('email-open-rate').textContent = `${channels.email.open_rate || 0}%`;
            document.getElementById('email-response-rate').textContent = `${channels.email.response_rate || 0}%`;
        }
        
        // SMS metrics
        if (channels.sms) {
            document.getElementById('sms-sent').textContent = formatNumber(channels.sms.sent || 0);
            document.getElementById('sms-delivery-rate').textContent = `${channels.sms.delivery_rate || 0}%`;
            document.getElementById('sms-response-rate').textContent = `${channels.sms.response_rate || 0}%`;
        }
        
        // Voice metrics
        if (channels.voice) {
            document.getElementById('voice-calls').textContent = formatNumber(channels.voice.calls || 0);
            document.getElementById('voice-answer-rate').textContent = `${channels.voice.answer_rate || 0}%`;
            document.getElementById('voice-conversion-rate').textContent = `${channels.voice.conversion_rate || 0}%`;
        }

        // Update insights
        this.updateChannelInsights();
    }

    updateChannelInsights() {
        const insights = this.analyticsData.insights || {};
        
        document.getElementById('best-channel-insight').textContent = 
            insights.best_channel || 'Email shows the highest conversion rate';
        document.getElementById('timing-insight').textContent = 
            insights.optimal_timing || 'Tuesday-Thursday 10-11 AM shows higher response rates';
        document.getElementById('improvement-insight').textContent = 
            insights.improvement_opportunity || 'Consider A/B testing subject lines';
    }

    renderCampaignTable() {
        const tbody = document.getElementById('campaign-table-body');
        if (!tbody || !this.analyticsData.campaigns) return;

        tbody.innerHTML = this.analyticsData.campaigns.map(campaign => `
            <tr>
                <td>${escapeHtml(campaign.name)}</td>
                <td>${campaign.type.replace('_', ' ')}</td>
                <td>
                    <span class="campaign-status ${campaign.status}">${campaign.status}</span>
                </td>
                <td>${formatDate(campaign.start_date)}</td>
                <td>${formatNumber(campaign.messages_sent)}</td>
                <td>${campaign.open_rate}%</td>
                <td>${campaign.response_rate}%</td>
                <td>${campaign.conversions}</td>
                <td class="${campaign.roi >= 0 ? 'positive' : 'negative'}">${campaign.roi}%</td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="analyticsManager.viewCampaignDetails('${campaign.id}')">
                        View
                    </button>
                </td>
            </tr>
        `).join('');
    }

    renderConversionFunnel() {
        const funnel = this.analyticsData.funnel || {};
        
        // Update funnel values
        document.getElementById('funnel-sent').textContent = formatNumber(funnel.sent || 0);
        document.getElementById('funnel-delivered').textContent = formatNumber(funnel.delivered || 0);
        document.getElementById('funnel-opened').textContent = formatNumber(funnel.opened || 0);
        document.getElementById('funnel-responded').textContent = formatNumber(funnel.responded || 0);
        document.getElementById('funnel-converted').textContent = formatNumber(funnel.converted || 0);
        
        // Update percentages and bar widths
        const total = funnel.sent || 1;
        const stages = [
            { key: 'delivered', value: funnel.delivered || 0 },
            { key: 'opened', value: funnel.opened || 0 },
            { key: 'responded', value: funnel.responded || 0 },
            { key: 'converted', value: funnel.converted || 0 }
        ];
        
        stages.forEach(stage => {
            const percentage = Math.round((stage.value / total) * 100);
            const pctElement = document.getElementById(`funnel-${stage.key}-pct`);
            const barElement = document.getElementById(`funnel-${stage.key}-bar`);
            
            if (pctElement) pctElement.textContent = `${percentage}%`;
            if (barElement) barElement.style.width = `${percentage}%`;
        });

        // Update funnel insights
        this.updateFunnelInsights(funnel);
    }

    updateFunnelInsights(funnel) {
        const insights = this.analyticsData.funnel_insights || {};
        
        document.getElementById('biggest-dropoff').textContent = 
            insights.biggest_dropoff || 'From Delivered to Opened (40% drop)';
        document.getElementById('conversion-bottleneck').textContent = 
            insights.conversion_bottleneck || 'Response to Conversion (50% drop)';
        document.getElementById('best-segment').textContent = 
            insights.best_segment || 'High-value properties (25% conversion)';
    }

    setupCharts() {
        this.initVolumeChart();
        this.initChannelDistributionChart();
        this.initChannelTrendCharts();
        this.initCampaignComparisonChart();
        this.initFunnelBreakdownChart();
        this.initROIHistoryChart();
    }

    initVolumeChart() {
        const ctx = document.getElementById('volume-chart');
        if (!ctx) return;

        this.charts.volume = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Messages Sent',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    initChannelDistributionChart() {
        const ctx = document.getElementById('channel-distribution-chart');
        if (!ctx) return;

        this.charts.channelDistribution = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Email', 'SMS', 'Voice'],
                datasets: [{
                    data: [0, 0, 0],
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

    initChannelTrendCharts() {
        const channels = ['email', 'sms', 'voice'];
        
        channels.forEach(channel => {
            const ctx = document.getElementById(`${channel}-trend-chart`);
            if (!ctx) return;

            this.charts[`${channel}Trend`] = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Performance',
                        data: [],
                        borderColor: channel === 'email' ? '#3b82f6' : channel === 'sms' ? '#10b981' : '#f59e0b',
                        backgroundColor: 'transparent',
                        tension: 0.4,
                        pointRadius: 0,
                        borderWidth: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        x: {
                            display: false
                        },
                        y: {
                            display: false,
                            beginAtZero: true
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        });
    }

    initCampaignComparisonChart() {
        const ctx = document.getElementById('campaign-comparison-chart');
        if (!ctx) return;

        this.charts.campaignComparison = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [],
                datasets: [{
                    label: 'Response Rate',
                    data: [],
                    backgroundColor: '#3b82f6',
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    initFunnelBreakdownChart() {
        const ctx = document.getElementById('funnel-breakdown-chart');
        if (!ctx) return;

        this.charts.funnelBreakdown = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['Email', 'SMS', 'Voice'],
                datasets: [
                    {
                        label: 'Sent',
                        data: [0, 0, 0],
                        backgroundColor: '#e5e7eb'
                    },
                    {
                        label: 'Opened',
                        data: [0, 0, 0],
                        backgroundColor: '#3b82f6'
                    },
                    {
                        label: 'Responded',
                        data: [0, 0, 0],
                        backgroundColor: '#10b981'
                    },
                    {
                        label: 'Converted',
                        data: [0, 0, 0],
                        backgroundColor: '#f59e0b'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        stacked: false
                    },
                    y: {
                        stacked: false,
                        beginAtZero: true
                    }
                }
            }
        });
    }

    initROIHistoryChart() {
        const ctx = document.getElementById('roi-history-chart');
        if (!ctx) return;

        this.charts.roiHistory = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'ROI %',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }

    updateCharts() {
        this.updateVolumeChart();
        this.updateChannelDistributionChart();
        this.updateChannelTrendCharts();
        this.updateCampaignComparisonChart();
        this.updateFunnelBreakdownChart();
        this.updateROIHistoryChart();
    }

    updateVolumeChart() {
        if (!this.charts.volume || !this.analyticsData.volume_data) return;

        const data = this.analyticsData.volume_data;
        this.charts.volume.data.labels = data.labels || [];
        this.charts.volume.data.datasets[0].data = data.sent || [];
        this.charts.volume.update();
    }

    updateChannelDistributionChart() {
        if (!this.charts.channelDistribution || !this.analyticsData.channel_distribution) return;

        const data = this.analyticsData.channel_distribution;
        this.charts.channelDistribution.data.datasets[0].data = [
            data.email || 0,
            data.sms || 0,
            data.voice || 0
        ];
        this.charts.channelDistribution.update();
    }

    updateChannelTrendCharts() {
        const channels = ['email', 'sms', 'voice'];
        
        channels.forEach(channel => {
            const chart = this.charts[`${channel}Trend`];
            const data = this.analyticsData.channel_trends?.[channel];
            
            if (chart && data) {
                chart.data.labels = data.labels || [];
                chart.data.datasets[0].data = data.values || [];
                chart.update();
            }
        });
    }

    updateCampaignComparisonChart() {
        if (!this.charts.campaignComparison || !this.analyticsData.campaign_comparison) return;

        const data = this.analyticsData.campaign_comparison;
        this.charts.campaignComparison.data.labels = data.labels || [];
        this.charts.campaignComparison.data.datasets[0].data = data.response_rates || [];
        this.charts.campaignComparison.update();
    }

    updateFunnelBreakdownChart() {
        if (!this.charts.funnelBreakdown || !this.analyticsData.funnel_by_channel) return;

        const data = this.analyticsData.funnel_by_channel;
        const datasets = this.charts.funnelBreakdown.data.datasets;
        
        datasets[0].data = [data.email?.sent || 0, data.sms?.sent || 0, data.voice?.sent || 0];
        datasets[1].data = [data.email?.opened || 0, data.sms?.opened || 0, data.voice?.opened || 0];
        datasets[2].data = [data.email?.responded || 0, data.sms?.responded || 0, data.voice?.responded || 0];
        datasets[3].data = [data.email?.converted || 0, data.sms?.converted || 0, data.voice?.converted || 0];
        
        this.charts.funnelBreakdown.update();
    }

    updateROIHistoryChart() {
        if (!this.charts.roiHistory || !this.analyticsData.roi_history) return;

        const data = this.analyticsData.roi_history;
        this.charts.roiHistory.data.labels = data.labels || [];
        this.charts.roiHistory.data.datasets[0].data = data.values || [];
        this.charts.roiHistory.update();
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
        
        // Load specific data for tabs
        if (tabName === 'channels') {
            this.updateChannelComparison();
        } else if (tabName === 'campaigns') {
            this.filterCampaigns();
        } else if (tabName === 'roi') {
            this.updateROICalculation();
        }
    }

    changeDateRange(event) {
        const value = event.target.value;
        
        if (value === 'custom') {
            this.showDateRangeModal();
        } else {
            this.dateRange = value;
            this.loadAnalyticsData();
        }
    }

    showDateRangeModal() {
        document.getElementById('date-range-modal')?.classList.add('active');
    }

    closeDateRangeModal() {
        document.getElementById('date-range-modal')?.classList.remove('active');
        // Reset select to previous value if custom was cancelled
        if (!this.customDateRange.start) {
            document.getElementById('date-range').value = this.dateRange;
        }
    }

    applyCustomDateRange() {
        const startDate = document.getElementById('start-date').value;
        const endDate = document.getElementById('end-date').value;
        
        if (!startDate || !endDate) {
            showNotification('Please select both start and end dates', 'warning');
            return;
        }
        
        if (new Date(startDate) > new Date(endDate)) {
            showNotification('Start date must be before end date', 'warning');
            return;
        }
        
        this.customDateRange = { start: startDate, end: endDate };
        this.dateRange = 'custom';
        this.closeDateRangeModal();
        this.loadAnalyticsData();
    }

    updateChartMetric(event) {
        const metric = event.currentTarget.dataset.metric;
        const chartContainer = event.currentTarget.closest('.chart-container');
        
        // Update active button
        chartContainer.querySelectorAll('.chart-control').forEach(btn => {
            btn.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Update chart based on metric
        this.updateChartForMetric(chartContainer, metric);
    }

    updateChartForMetric(container, metric) {
        const chartId = container.querySelector('canvas').id;
        
        if (chartId === 'volume-chart') {
            this.updateVolumeChartMetric(metric);
        } else if (chartId === 'campaign-comparison-chart') {
            this.updateCampaignComparisonMetric(metric);
        }
    }

    updateVolumeChartMetric(metric) {
        if (!this.charts.volume || !this.analyticsData.volume_data) return;

        const data = this.analyticsData.volume_data[metric] || [];
        this.charts.volume.data.datasets[0].data = data;
        this.charts.volume.data.datasets[0].label = metric.charAt(0).toUpperCase() + metric.slice(1);
        this.charts.volume.update();
    }

    updateCampaignComparisonMetric(metric) {
        if (!this.charts.campaignComparison || !this.analyticsData.campaign_comparison) return;

        const data = this.analyticsData.campaign_comparison[metric] || [];
        this.charts.campaignComparison.data.datasets[0].data = data;
        this.charts.campaignComparison.data.datasets[0].label = metric.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
        this.charts.campaignComparison.update();
    }

    filterCampaigns() {
        // Implementation for filtering campaigns
        this.renderCampaignTable();
    }

    updateChannelComparison() {
        // Implementation for updating channel comparison
        this.renderChannelMetrics();
    }

    initROICalculator() {
        // Set initial values
        document.getElementById('platform-costs').value = this.roiCalculator.platformCosts;
        document.getElementById('staff-time').value = this.roiCalculator.staffTime;
        document.getElementById('hourly-rate').value = this.roiCalculator.hourlyRate;
        document.getElementById('other-costs').value = this.roiCalculator.otherCosts;
        document.getElementById('leads-generated').value = this.roiCalculator.leadsGenerated;
        document.getElementById('deals-closed').value = this.roiCalculator.dealsClosed;
        document.getElementById('avg-deal-value').value = this.roiCalculator.avgDealValue;
        
        this.updateROICalculation();
    }

    updateROICalculation() {
        // Get input values
        const platformCosts = parseFloat(document.getElementById('platform-costs').value) || 0;
        const staffTime = parseFloat(document.getElementById('staff-time').value) || 0;
        const hourlyRate = parseFloat(document.getElementById('hourly-rate').value) || 0;
        const otherCosts = parseFloat(document.getElementById('other-costs').value) || 0;
        const leadsGenerated = parseInt(document.getElementById('leads-generated').value) || 0;
        const dealsClosed = parseInt(document.getElementById('deals-closed').value) || 0;
        const avgDealValue = parseFloat(document.getElementById('avg-deal-value').value) || 0;
        
        // Calculate totals
        const totalCost = platformCosts + (staffTime * hourlyRate) + otherCosts;
        const totalRevenue = dealsClosed * avgDealValue;
        const netProfit = totalRevenue - totalCost;
        const roi = totalCost > 0 ? ((netProfit / totalCost) * 100) : 0;
        const costPerLead = leadsGenerated > 0 ? (totalCost / leadsGenerated) : 0;
        const costPerAcquisition = dealsClosed > 0 ? (totalCost / dealsClosed) : 0;
        const conversionRate = leadsGenerated > 0 ? ((dealsClosed / leadsGenerated) * 100) : 0;
        
        // Update calculated fields
        document.getElementById('total-cost').value = totalCost.toFixed(2);
        document.getElementById('total-revenue').value = totalRevenue.toFixed(2);
        document.getElementById('net-profit').value = netProfit.toFixed(2);
        document.getElementById('roi-percentage').value = roi.toFixed(2);
        
        // Update result cards
        document.getElementById('result-roi').textContent = `${roi.toFixed(1)}%`;
        document.getElementById('result-cpl').textContent = `$${costPerLead.toFixed(2)}`;
        document.getElementById('result-cpa').textContent = `$${costPerAcquisition.toFixed(2)}`;
        document.getElementById('result-conversion').textContent = `${conversionRate.toFixed(1)}%`;
    }

    updateBenchmarks() {
        const data = this.analyticsData.overview || {};
        
        // Update your metrics
        document.getElementById('your-email-open').textContent = `${data.open_rate || 0}%`;
        document.getElementById('your-response-rate').textContent = `${data.response_rate || 0}%`;
        document.getElementById('your-cpl').textContent = `$${data.cost_per_lead || 0}`;
        
        // Update benchmark status
        this.updateBenchmarkStatus('email-open-status', data.open_rate || 0, 25);
        this.updateBenchmarkStatus('response-rate-status', data.response_rate || 0, 8);
        this.updateBenchmarkStatus('cpl-status', data.cost_per_lead || 0, 45, true); // Lower is better for CPL
    }

    updateBenchmarkStatus(elementId, yourValue, industryValue, lowerIsBetter = false) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        let status, text;
        
        if (lowerIsBetter) {
            if (yourValue <= industryValue * 0.8) {
                status = 'good';
                text = 'Above Average';
            } else if (yourValue <= industryValue * 1.2) {
                status = 'average';
                text = 'Average';
            } else {
                status = 'poor';
                text = 'Below Average';
            }
        } else {
            if (yourValue >= industryValue * 1.2) {
                status = 'good';
                text = 'Above Average';
            } else if (yourValue >= industryValue * 0.8) {
                status = 'average';
                text = 'Average';
            } else {
                status = 'poor';
                text = 'Below Average';
            }
        }
        
        element.className = `benchmark-status ${status}`;
        element.textContent = text;
    }

    async refreshData() {
        await this.loadAnalyticsData();
        showNotification('Analytics data refreshed', 'success');
    }

    exportReport() {
        showNotification('Export functionality coming soon', 'info');
    }

    exportCampaignData() {
        showNotification('Campaign data export coming soon', 'info');
    }

    viewAllCampaigns() {
        // Switch to campaigns tab
        document.querySelector('[data-tab="campaigns"]').click();
    }

    viewCampaignDetails(campaignId) {
        showNotification('Campaign details view coming soon', 'info');
    }
}

// Utility functions
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
let analyticsManager;
document.addEventListener('DOMContentLoaded', () => {
    analyticsManager = new AnalyticsDashboard();
});