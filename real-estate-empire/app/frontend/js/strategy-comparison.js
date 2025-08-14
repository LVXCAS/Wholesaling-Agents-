// Strategy Comparison functionality

class StrategyComparison {
    constructor() {
        this.currentProperty = null;
        this.strategyAnalyses = {};
        this.charts = {};
        this.timeframe = 5; // Default 5 years
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadProperties();
    }

    setupEventListeners() {
        // Property selection
        const propertySelect = document.getElementById('strategy-property-select');
        if (propertySelect) {
            propertySelect.addEventListener('change', (e) => {
                this.selectProperty(e.target.value);
            });
        }

        // Timeframe selection
        const timeframeSelect = document.getElementById('strategy-timeframe');
        if (timeframeSelect) {
            timeframeSelect.addEventListener('change', (e) => {
                this.timeframe = parseInt(e.target.value);
                if (this.currentProperty) {
                    this.analyzeStrategies();
                }
            });
        }

        // Analyze strategies button
        const analyzeBtn = document.getElementById('analyze-strategies-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.analyzeStrategies();
            });
        }
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
        const select = document.getElementById('strategy-property-select');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">Choose a property to analyze strategies...</option>';

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
            
            this.hideEmptyState();
            
            // Auto-analyze strategies if property has required data
            if (property.listing_price) {
                await this.analyzeStrategies();
            }
            
        } catch (error) {
            console.error('Failed to load property:', error);
            Utils.showToast('Failed to load property', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async analyzeStrategies() {
        if (!this.currentProperty) {
            Utils.showToast('Please select a property first', 'warning');
            return;
        }

        try {
            Utils.showLoading(true, 'Analyzing investment strategies...');
            
            // Analyze each strategy
            await Promise.all([
                this.analyzeFlipStrategy(),
                this.analyzeRentalStrategy(),
                this.analyzeWholesaleStrategy(),
                this.analyzeBRRRRStrategy()
            ]);
            
            // Display results
            this.displayStrategyResults();
            this.createCharts();
            this.generateRecommendation();
            
            Utils.showToast('Strategy analysis completed!', 'success');
            
        } catch (error) {
            console.error('Strategy analysis failed:', error);
            Utils.showToast(`Strategy analysis failed: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async analyzeFlipStrategy() {
        const purchasePrice = this.currentProperty.listing_price || 0;
        const repairBudget = this.estimateRepairCost();
        const holdingPeriod = 6; // months

        try {
            const result = await API.analyzeFlipStrategy(this.currentProperty.id, {
                purchasePrice,
                repairBudget,
                holdingPeriod
            });
            
            this.strategyAnalyses.flip = result;
        } catch (error) {
            // Fallback to manual calculation if API fails
            this.strategyAnalyses.flip = this.calculateFlipStrategy(purchasePrice, repairBudget, holdingPeriod);
        }
    }

    async analyzeRentalStrategy() {
        const purchasePrice = this.currentProperty.listing_price || 0;
        const downPayment = purchasePrice * 0.25; // 25% down
        const interestRate = 0.075; // 7.5%
        const loanTerm = 30;

        try {
            const result = await API.analyzeRentalStrategy(this.currentProperty.id, {
                purchasePrice,
                downPayment,
                interestRate,
                loanTerm
            });
            
            this.strategyAnalyses.rental = result;
        } catch (error) {
            // Fallback to manual calculation
            this.strategyAnalyses.rental = this.calculateRentalStrategy(purchasePrice, downPayment, interestRate, loanTerm);
        }
    }

    async analyzeWholesaleStrategy() {
        const contractPrice = this.currentProperty.listing_price || 0;
        const assignmentFee = Math.min(contractPrice * 0.05, 15000); // 5% or $15k max

        try {
            const result = await API.analyzeWholesaleStrategy(this.currentProperty.id, {
                contractPrice,
                assignmentFee
            });
            
            this.strategyAnalyses.wholesale = result;
        } catch (error) {
            // Fallback to manual calculation
            this.strategyAnalyses.wholesale = this.calculateWholesaleStrategy(contractPrice, assignmentFee);
        }
    }

    async analyzeBRRRRStrategy() {
        const purchasePrice = this.currentProperty.listing_price || 0;
        const repairBudget = this.estimateRepairCost();
        const refinanceLTV = 0.75; // 75% LTV

        try {
            const result = await API.analyzeBRRRRStrategy(this.currentProperty.id, {
                purchasePrice,
                repairBudget,
                refinanceLTV
            });
            
            this.strategyAnalyses.brrrr = result;
        } catch (error) {
            // Fallback to manual calculation
            this.strategyAnalyses.brrrr = this.calculateBRRRRStrategy(purchasePrice, repairBudget, refinanceLTV);
        }
    }

    // Fallback calculation methods

    calculateFlipStrategy(purchasePrice, repairBudget, holdingPeriod) {
        const arv = purchasePrice * 1.3; // Estimate 30% increase after repairs
        const sellingCosts = arv * 0.08; // 8% selling costs
        const holdingCosts = (purchasePrice + repairBudget) * 0.01 * (holdingPeriod / 12); // 1% per year
        const totalCosts = purchasePrice + repairBudget + sellingCosts + holdingCosts;
        const profit = arv - totalCosts;
        const roi = (profit / (purchasePrice + repairBudget)) * 100;

        return {
            strategy: 'flip',
            profit: profit,
            roi: roi,
            timeline: holdingPeriod,
            risk_level: 'medium',
            arv: arv,
            total_investment: purchasePrice + repairBudget,
            selling_costs: sellingCosts,
            holding_costs: holdingCosts
        };
    }

    calculateRentalStrategy(purchasePrice, downPayment, interestRate, loanTerm) {
        const loanAmount = purchasePrice - downPayment;
        const monthlyRate = interestRate / 12;
        const numPayments = loanTerm * 12;
        
        const monthlyPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                              (Math.pow(1 + monthlyRate, numPayments) - 1);
        
        const estimatedRent = purchasePrice * 0.01; // 1% rule
        const monthlyExpenses = estimatedRent * 0.4; // 40% expense ratio
        const monthlyCashFlow = estimatedRent - monthlyPayment - monthlyExpenses;
        const annualCashFlow = monthlyCashFlow * 12;
        const capRate = (annualCashFlow + monthlyPayment * 12) / purchasePrice * 100;
        const cocReturn = (annualCashFlow / downPayment) * 100;

        return {
            strategy: 'rental',
            monthly_cash_flow: monthlyCashFlow,
            annual_cash_flow: annualCashFlow,
            cap_rate: capRate,
            cash_on_cash_return: cocReturn,
            estimated_rent: estimatedRent,
            monthly_payment: monthlyPayment,
            risk_level: 'low'
        };
    }

    calculateWholesaleStrategy(contractPrice, assignmentFee) {
        const marketingCosts = 1000; // Estimated marketing costs
        const netProfit = assignmentFee - marketingCosts;
        const roi = (netProfit / marketingCosts) * 100;

        return {
            strategy: 'wholesale',
            assignment_fee: assignmentFee,
            marketing_costs: marketingCosts,
            net_profit: netProfit,
            roi: roi,
            timeline: 30, // days
            risk_level: 'low'
        };
    }

    calculateBRRRRStrategy(purchasePrice, repairBudget, refinanceLTV) {
        const totalInvestment = purchasePrice + repairBudget;
        const arv = purchasePrice * 1.25; // 25% increase after repairs
        const refinanceAmount = arv * refinanceLTV;
        const cashRecovered = Math.min(refinanceAmount, totalInvestment);
        const cashLeft = totalInvestment - cashRecovered;
        
        const estimatedRent = arv * 0.01; // 1% rule on ARV
        const monthlyPayment = refinanceAmount * 0.006; // Estimate 7.2% annual rate
        const monthlyExpenses = estimatedRent * 0.4;
        const monthlyCashFlow = estimatedRent - monthlyPayment - monthlyExpenses;

        return {
            strategy: 'brrrr',
            total_investment: totalInvestment,
            arv: arv,
            refinance_amount: refinanceAmount,
            cash_recovered: cashRecovered,
            cash_left_in_deal: cashLeft,
            monthly_cash_flow: monthlyCashFlow,
            timeline: 12, // months
            risk_level: 'high'
        };
    }

    estimateRepairCost() {
        // Estimate repair cost based on property characteristics
        const squareFeet = this.currentProperty.square_feet || 1500;
        const condition = this.currentProperty.condition_score || 0.7;
        const baseRepairCost = squareFeet * 20; // $20 per sq ft base
        const conditionMultiplier = 1.5 - condition; // Lower condition = higher cost
        return Math.round(baseRepairCost * conditionMultiplier);
    }

    displayStrategyResults() {
        this.showStrategyResults();
        
        // Update strategy cards
        this.updateStrategyCard('flip', this.strategyAnalyses.flip);
        this.updateStrategyCard('rental', this.strategyAnalyses.rental);
        this.updateStrategyCard('wholesale', this.strategyAnalyses.wholesale);
        this.updateStrategyCard('brrrr', this.strategyAnalyses.brrrr);
        
        // Update comparison table
        this.updateComparisonTable();
    }

    updateStrategyCard(strategyType, analysis) {
        if (!analysis) return;

        const scoreValue = this.calculateStrategyScore(strategyType, analysis);
        const scoreElement = document.getElementById(`${strategyType}-score`).querySelector('.score-value');
        if (scoreElement) {
            scoreElement.textContent = scoreValue;
        }

        // Update score circle color
        const scoreCircle = document.getElementById(`${strategyType}-score`).querySelector('.score-circle');
        if (scoreCircle) {
            const scoreClass = scoreValue >= 80 ? 'high' : scoreValue >= 60 ? 'medium' : 'low';
            scoreCircle.className = `score-circle ${scoreClass}`;
        }

        // Update metrics based on strategy type
        switch (strategyType) {
            case 'flip':
                this.updateElement(`${strategyType}-profit`, Utils.formatCurrency(analysis.profit || 0));
                this.updateElement(`${strategyType}-roi`, Utils.formatPercentage((analysis.roi || 0) / 100));
                this.updateElement(`${strategyType}-timeline`, `${analysis.timeline || 6} months`);
                break;
                
            case 'rental':
                this.updateElement(`${strategyType}-cashflow`, Utils.formatCurrency(analysis.monthly_cash_flow || 0));
                this.updateElement(`${strategyType}-caprate`, Utils.formatPercentage((analysis.cap_rate || 0) / 100));
                this.updateElement(`${strategyType}-coc`, Utils.formatPercentage((analysis.cash_on_cash_return || 0) / 100));
                break;
                
            case 'wholesale':
                this.updateElement(`${strategyType}-fee`, Utils.formatCurrency(analysis.assignment_fee || 0));
                this.updateElement(`${strategyType}-roi`, Utils.formatPercentage((analysis.roi || 0) / 100));
                this.updateElement(`${strategyType}-timeline`, `${analysis.timeline || 30} days`);
                break;
                
            case 'brrrr':
                this.updateElement(`${strategyType}-recovery`, Utils.formatCurrency(analysis.cash_recovered || 0));
                this.updateElement(`${strategyType}-cashflow`, Utils.formatCurrency(analysis.monthly_cash_flow || 0));
                this.updateElement(`${strategyType}-timeline`, `${analysis.timeline || 12} months`);
                break;
        }

        // Update risk level
        const riskElement = document.getElementById(`${strategyType}-risk`);
        if (riskElement) {
            const riskLevel = analysis.risk_level || 'medium';
            riskElement.textContent = Utils.titleCase(riskLevel);
            riskElement.className = `metric-value risk-${riskLevel}`;
        }
    }

    calculateStrategyScore(strategyType, analysis) {
        // Calculate a score from 0-100 based on strategy performance
        let score = 50; // Base score

        switch (strategyType) {
            case 'flip':
                const roi = analysis.roi || 0;
                score = Math.min(100, Math.max(0, roi * 2)); // ROI * 2 for score
                break;
                
            case 'rental':
                const cashFlow = analysis.monthly_cash_flow || 0;
                const capRate = analysis.cap_rate || 0;
                score = Math.min(100, Math.max(0, (cashFlow / 10) + (capRate * 5)));
                break;
                
            case 'wholesale':
                const profit = analysis.net_profit || 0;
                score = Math.min(100, Math.max(0, profit / 100)); // $100 profit = 1 point
                break;
                
            case 'brrrr':
                const recovery = analysis.cash_recovered || 0;
                const investment = analysis.total_investment || 1;
                const recoveryRate = (recovery / investment) * 100;
                score = Math.min(100, Math.max(0, recoveryRate));
                break;
        }

        return Math.round(score);
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateComparisonTable() {
        const tableBody = document.getElementById('comparison-table-body');
        if (!tableBody) return;

        const metrics = [
            {
                label: 'Initial Investment',
                flip: Utils.formatCurrency((this.strategyAnalyses.flip?.total_investment || 0)),
                rental: Utils.formatCurrency((this.currentProperty?.listing_price || 0) * 0.25),
                wholesale: Utils.formatCurrency(this.strategyAnalyses.wholesale?.marketing_costs || 0),
                brrrr: Utils.formatCurrency(this.strategyAnalyses.brrrr?.total_investment || 0)
            },
            {
                label: 'Potential Profit (Year 1)',
                flip: Utils.formatCurrency(this.strategyAnalyses.flip?.profit || 0),
                rental: Utils.formatCurrency((this.strategyAnalyses.rental?.monthly_cash_flow || 0) * 12),
                wholesale: Utils.formatCurrency(this.strategyAnalyses.wholesale?.net_profit || 0),
                brrrr: Utils.formatCurrency((this.strategyAnalyses.brrrr?.monthly_cash_flow || 0) * 12)
            },
            {
                label: 'ROI',
                flip: Utils.formatPercentage((this.strategyAnalyses.flip?.roi || 0) / 100),
                rental: Utils.formatPercentage((this.strategyAnalyses.rental?.cash_on_cash_return || 0) / 100),
                wholesale: Utils.formatPercentage((this.strategyAnalyses.wholesale?.roi || 0) / 100),
                brrrr: 'Infinite*'
            },
            {
                label: 'Timeline',
                flip: `${this.strategyAnalyses.flip?.timeline || 6} months`,
                rental: 'Ongoing',
                wholesale: `${this.strategyAnalyses.wholesale?.timeline || 30} days`,
                brrrr: `${this.strategyAnalyses.brrrr?.timeline || 12} months`
            },
            {
                label: 'Risk Level',
                flip: Utils.titleCase(this.strategyAnalyses.flip?.risk_level || 'medium'),
                rental: Utils.titleCase(this.strategyAnalyses.rental?.risk_level || 'low'),
                wholesale: Utils.titleCase(this.strategyAnalyses.wholesale?.risk_level || 'low'),
                brrrr: Utils.titleCase(this.strategyAnalyses.brrrr?.risk_level || 'high')
            },
            {
                label: 'Liquidity',
                flip: 'High',
                rental: 'Low',
                wholesale: 'High',
                brrrr: 'Low'
            }
        ];

        tableBody.innerHTML = metrics.map(metric => `
            <tr>
                <td class="metric-label-cell">${metric.label}</td>
                <td class="strategy-cell flip">${metric.flip}</td>
                <td class="strategy-cell rental">${metric.rental}</td>
                <td class="strategy-cell wholesale">${metric.wholesale}</td>
                <td class="strategy-cell brrrr">${metric.brrrr}</td>
            </tr>
        `).join('');
    }

    createCharts() {
        this.createRiskRewardChart();
        this.createCashFlowChart();
        this.createROIChart();
    }

    createRiskRewardChart() {
        const ctx = document.getElementById('risk-reward-chart');
        if (!ctx) return;

        const strategies = [
            {
                name: 'Fix & Flip',
                risk: this.getRiskScore('flip'),
                reward: this.getRewardScore('flip'),
                color: '#dc2626'
            },
            {
                name: 'Buy & Hold',
                risk: this.getRiskScore('rental'),
                reward: this.getRewardScore('rental'),
                color: '#10b981'
            },
            {
                name: 'Wholesale',
                risk: this.getRiskScore('wholesale'),
                reward: this.getRewardScore('wholesale'),
                color: '#f59e0b'
            },
            {
                name: 'BRRRR',
                risk: this.getRiskScore('brrrr'),
                reward: this.getRewardScore('brrrr'),
                color: '#8b5cf6'
            }
        ];

        if (this.charts.riskReward) {
            this.charts.riskReward.destroy();
        }

        this.charts.riskReward = new Chart(ctx, {
            type: 'scatter',
            data: {
                datasets: strategies.map(strategy => ({
                    label: strategy.name,
                    data: [{ x: strategy.risk, y: strategy.reward }],
                    backgroundColor: strategy.color,
                    borderColor: strategy.color,
                    pointRadius: 10,
                    pointHoverRadius: 12
                }))
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Risk Level (0-100)'
                        },
                        min: 0,
                        max: 100
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Potential Reward (0-100)'
                        },
                        min: 0,
                        max: 100
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: Risk ${context.parsed.x}, Reward ${context.parsed.y}`;
                            }
                        }
                    },
                    legend: {
                        display: false // We have our own legend
                    }
                }
            }
        });
    }

    createCashFlowChart() {
        const ctx = document.getElementById('strategy-cashflow-chart');
        if (!ctx) return;

        const months = Array.from({ length: this.timeframe * 12 }, (_, i) => `Month ${i + 1}`);
        
        const datasets = [
            {
                label: 'Buy & Hold Rental',
                data: this.generateCashFlowData('rental', this.timeframe * 12),
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: false
            },
            {
                label: 'BRRRR',
                data: this.generateCashFlowData('brrrr', this.timeframe * 12),
                borderColor: '#8b5cf6',
                backgroundColor: 'rgba(139, 92, 246, 0.1)',
                fill: false
            }
        ];

        if (this.charts.cashFlow) {
            this.charts.cashFlow.destroy();
        }

        this.charts.cashFlow = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: 'Monthly Cash Flow ($)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `${context.dataset.label}: ${Utils.formatCurrency(context.parsed.y)}`;
                            }
                        }
                    }
                }
            }
        });
    }

    createROIChart() {
        const ctx = document.getElementById('strategy-roi-chart');
        if (!ctx) return;

        const strategies = ['Fix & Flip', 'Buy & Hold', 'Wholesale', 'BRRRR'];
        const roiData = [
            this.strategyAnalyses.flip?.roi || 0,
            this.strategyAnalyses.rental?.cash_on_cash_return || 0,
            this.strategyAnalyses.wholesale?.roi || 0,
            Math.min(200, (this.strategyAnalyses.brrrr?.cash_recovered || 0) / (this.strategyAnalyses.brrrr?.total_investment || 1) * 100)
        ];

        if (this.charts.roi) {
            this.charts.roi.destroy();
        }

        this.charts.roi = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: strategies,
                datasets: [{
                    label: 'ROI (%)',
                    data: roiData,
                    backgroundColor: [
                        '#dc2626',
                        '#10b981',
                        '#f59e0b',
                        '#8b5cf6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'ROI (%)'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return `ROI: ${context.parsed.y.toFixed(1)}%`;
                            }
                        }
                    },
                    legend: {
                        display: false
                    }
                }
            }
        });
    }

    getRiskScore(strategyType) {
        const riskLevels = {
            low: 25,
            medium: 50,
            high: 75
        };
        
        const analysis = this.strategyAnalyses[strategyType];
        const riskLevel = analysis?.risk_level || 'medium';
        return riskLevels[riskLevel] || 50;
    }

    getRewardScore(strategyType) {
        // Convert various reward metrics to a 0-100 scale
        const analysis = this.strategyAnalyses[strategyType];
        if (!analysis) return 0;

        switch (strategyType) {
            case 'flip':
                return Math.min(100, Math.max(0, (analysis.roi || 0) * 2));
            case 'rental':
                return Math.min(100, Math.max(0, (analysis.cash_on_cash_return || 0) * 2));
            case 'wholesale':
                return Math.min(100, Math.max(0, (analysis.roi || 0) / 10));
            case 'brrrr':
                const recovery = analysis.cash_recovered || 0;
                const investment = analysis.total_investment || 1;
                return Math.min(100, (recovery / investment) * 100);
            default:
                return 0;
        }
    }

    generateCashFlowData(strategyType, months) {
        const analysis = this.strategyAnalyses[strategyType];
        if (!analysis) return Array(months).fill(0);

        const monthlyCashFlow = analysis.monthly_cash_flow || 0;
        
        if (strategyType === 'brrrr') {
            // BRRRR has negative cash flow during rehab period, then positive
            const rehabMonths = 6;
            return Array.from({ length: months }, (_, i) => {
                if (i < rehabMonths) {
                    return -2000; // Negative during rehab
                } else {
                    return monthlyCashFlow;
                }
            });
        } else {
            // Rental has consistent cash flow
            return Array(months).fill(monthlyCashFlow);
        }
    }

    generateRecommendation() {
        const container = document.getElementById('strategy-recommendation');
        if (!container) return;

        // Calculate best strategy based on scores
        const scores = {
            flip: this.calculateStrategyScore('flip', this.strategyAnalyses.flip),
            rental: this.calculateStrategyScore('rental', this.strategyAnalyses.rental),
            wholesale: this.calculateStrategyScore('wholesale', this.strategyAnalyses.wholesale),
            brrrr: this.calculateStrategyScore('brrrr', this.strategyAnalyses.brrrr)
        };

        const bestStrategy = Object.keys(scores).reduce((a, b) => scores[a] > scores[b] ? a : b);
        const bestScore = scores[bestStrategy];

        const strategyNames = {
            flip: 'Fix & Flip',
            rental: 'Buy & Hold Rental',
            wholesale: 'Wholesale',
            brrrr: 'BRRRR'
        };

        const recommendations = {
            flip: 'This property shows strong potential for a fix and flip strategy. The estimated profit margin and timeline make it attractive for active investors.',
            rental: 'This property would work well as a rental investment. The cash flow and cap rate indicate good long-term passive income potential.',
            wholesale: 'This property could be a good wholesale opportunity. The quick turnaround and low risk make it suitable for new investors.',
            brrrr: 'This property is ideal for the BRRRR strategy. The potential to recover most of your initial investment while maintaining cash flow is excellent.'
        };

        container.innerHTML = `
            <div class="recommendation-content">
                <div class="recommendation-header">
                    <div class="recommendation-icon">
                        <i class="fas fa-trophy"></i>
                    </div>
                    <div class="recommendation-title">
                        <h3>Recommended Strategy: ${strategyNames[bestStrategy]}</h3>
                        <div class="recommendation-score">Score: ${bestScore}/100</div>
                    </div>
                </div>
                <div class="recommendation-description">
                    <p>${recommendations[bestStrategy]}</p>
                </div>
                <div class="recommendation-factors">
                    <h4>Key Factors:</h4>
                    <ul>
                        ${this.getRecommendationFactors(bestStrategy).map(factor => `<li>${factor}</li>`).join('')}
                    </ul>
                </div>
                <div class="recommendation-actions">
                    <button class="btn btn-primary" onclick="strategyComparison.viewStrategyDetails('${bestStrategy}')">
                        <i class="fas fa-eye"></i> View Detailed Analysis
                    </button>
                </div>
            </div>
        `;
    }

    getRecommendationFactors(strategyType) {
        const analysis = this.strategyAnalyses[strategyType];
        if (!analysis) return [];

        switch (strategyType) {
            case 'flip':
                return [
                    `Estimated profit: ${Utils.formatCurrency(analysis.profit || 0)}`,
                    `ROI: ${Utils.formatPercentage((analysis.roi || 0) / 100)}`,
                    `Timeline: ${analysis.timeline || 6} months`,
                    'Good for active investors with renovation experience'
                ];
            case 'rental':
                return [
                    `Monthly cash flow: ${Utils.formatCurrency(analysis.monthly_cash_flow || 0)}`,
                    `Cap rate: ${Utils.formatPercentage((analysis.cap_rate || 0) / 100)}`,
                    `Cash-on-cash return: ${Utils.formatPercentage((analysis.cash_on_cash_return || 0) / 100)}`,
                    'Provides passive income and long-term appreciation'
                ];
            case 'wholesale':
                return [
                    `Assignment fee: ${Utils.formatCurrency(analysis.assignment_fee || 0)}`,
                    `Quick turnaround: ${analysis.timeline || 30} days`,
                    'Low risk and minimal capital required',
                    'Good for building investor network'
                ];
            case 'brrrr':
                return [
                    `Cash recovered: ${Utils.formatCurrency(analysis.cash_recovered || 0)}`,
                    `Monthly cash flow: ${Utils.formatCurrency(analysis.monthly_cash_flow || 0)}`,
                    'Potential for infinite ROI',
                    'Allows for rapid portfolio scaling'
                ];
            default:
                return [];
        }
    }

    // Public methods for UI interactions

    viewStrategyDetails(strategyType) {
        const analysis = this.strategyAnalyses[strategyType];
        if (!analysis) {
            Utils.showToast('No analysis data available for this strategy', 'warning');
            return;
        }

        // This would open a modal with detailed strategy information
        Utils.showToast(`Detailed ${strategyType} analysis not implemented yet`, 'info');
    }

    async exportComparison() {
        if (!this.currentProperty || Object.keys(this.strategyAnalyses).length === 0) {
            Utils.showToast('No strategy analysis to export', 'warning');
            return;
        }

        try {
            // Create comparison data
            const comparisonData = {
                property: {
                    address: this.currentProperty.address,
                    city: this.currentProperty.city,
                    state: this.currentProperty.state,
                    listing_price: this.currentProperty.listing_price
                },
                strategies: this.strategyAnalyses,
                analysis_date: new Date().toISOString()
            };

            // Convert to JSON and download
            const jsonString = JSON.stringify(comparisonData, null, 2);
            const blob = new Blob([jsonString], { type: 'application/json' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `strategy-comparison-${this.currentProperty.address.replace(/[^a-zA-Z0-9]/g, '_')}-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            Utils.showToast('Strategy comparison exported successfully', 'success');

        } catch (error) {
            console.error('Export failed:', error);
            Utils.showToast('Failed to export strategy comparison', 'error');
        }
    }

    showEmptyState() {
        document.getElementById('strategy-results').style.display = 'none';
        document.getElementById('strategy-empty-state').style.display = 'block';
    }

    hideEmptyState() {
        document.getElementById('strategy-empty-state').style.display = 'none';
    }

    showStrategyResults() {
        document.getElementById('strategy-results').style.display = 'block';
        this.hideEmptyState();
    }
}

// Initialize strategy comparison when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.strategyComparison = new StrategyComparison();
});