// Financial Analysis Dashboard functionality

class FinancialDashboard {
    constructor() {
        this.currentProperty = null;
        this.currentAnalysis = null;
        this.charts = {};
        this.calculatorInputs = {};
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupCalculator();
        this.loadProperties();
    }

    setupEventListeners() {
        // Property selection
        const propertySelect = document.getElementById('property-select');
        if (propertySelect) {
            propertySelect.addEventListener('change', (e) => {
                this.selectProperty(e.target.value);
            });
        }

        // Analysis button
        const analyzeBtn = document.getElementById('analyze-btn');
        if (analyzeBtn) {
            analyzeBtn.addEventListener('click', () => {
                this.analyzeCurrentProperty();
            });
        }

        // Sensitivity analysis
        const runSensitivityBtn = document.getElementById('run-sensitivity');
        if (runSensitivityBtn) {
            runSensitivityBtn.addEventListener('click', () => {
                this.runSensitivityAnalysis();
            });
        }

        // Scenario inputs
        this.setupScenarioListeners();
    }

    setupScenarioListeners() {
        const scenarios = ['conventional', 'fha', 'cash'];
        
        scenarios.forEach(scenarioType => {
            const scenarioCard = document.getElementById(`scenario-${scenarioType}`);
            if (scenarioCard) {
                const inputs = scenarioCard.querySelectorAll('input');
                inputs.forEach(input => {
                    input.addEventListener('input', Utils.debounce(() => {
                        this.updateScenario(scenarioType);
                    }, 500));
                });
            }
        });
    }

    setupCalculator() {
        const calculatorInputs = [
            'calc-purchase-price', 'calc-down-payment', 'calc-interest-rate',
            'calc-loan-term', 'calc-monthly-rent', 'calc-monthly-expenses',
            'calc-vacancy-rate', 'calc-maintenance-rate'
        ];

        calculatorInputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                this.calculatorInputs[inputId] = input;
                input.addEventListener('input', Utils.debounce(() => {
                    this.updateCalculator();
                }, 300));
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
        const select = document.getElementById('property-select');
        if (!select) return;

        // Clear existing options except the first one
        select.innerHTML = '<option value="">Choose a property to analyze...</option>';

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
            
            // Load existing analyses
            const analyses = await API.getPropertyAnalyses(propertyId, { limit: 1 });
            if (analyses.length > 0) {
                this.currentAnalysis = analyses[0];
                this.displayAnalysis(this.currentAnalysis);
            } else {
                this.showNoAnalysisState();
            }
            
            // Update calculator with property data
            this.populateCalculatorFromProperty(property);
            
        } catch (error) {
            console.error('Failed to load property:', error);
            Utils.showToast('Failed to load property', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    async analyzeCurrentProperty() {
        if (!this.currentProperty) {
            Utils.showToast('Please select a property first', 'warning');
            return;
        }

        const analysisType = document.getElementById('analysis-type').value;

        try {
            Utils.showLoading(true, 'Analyzing property...');
            
            const analysis = await API.analyzeProperty(this.currentProperty.id, analysisType);
            this.currentAnalysis = analysis;
            
            this.displayAnalysis(analysis);
            Utils.showToast('Property analysis completed!', 'success');
            
        } catch (error) {
            console.error('Analysis failed:', error);
            Utils.showToast(`Analysis failed: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    displayAnalysis(analysis) {
        this.hideEmptyState();
        this.showAnalysisResults();
        
        // Update key metrics
        this.updateKeyMetrics(analysis);
        
        // Create charts
        this.createCharts(analysis);
        
        // Update scenarios with analysis data
        this.updateScenariosFromAnalysis(analysis);
    }

    updateKeyMetrics(analysis) {
        const analysisData = analysis.analysis || {};
        const valuation = analysisData.valuation || {};
        const repairEstimate = analysisData.repair_estimate || {};
        const financialMetrics = analysisData.financial_metrics || {};

        // ARV
        const arvValue = valuation.arv || 0;
        const arvConfidence = valuation.confidence_score || 0;
        document.getElementById('arv-value').textContent = Utils.formatCurrency(arvValue);
        this.updateConfidenceIndicator('arv-confidence', 'arv-confidence-label', arvConfidence);

        // Repair Cost
        const repairCost = repairEstimate.total_cost || 0;
        const repairConfidence = repairEstimate.confidence_score || 0;
        document.getElementById('repair-cost-value').textContent = Utils.formatCurrency(repairCost);
        this.updateConfidenceIndicator('repair-confidence', 'repair-confidence-label', repairConfidence);

        // Potential Profit
        const potentialProfit = financialMetrics.flip_profit || 0;
        const roi = financialMetrics.roi || 0;
        document.getElementById('potential-profit-value').textContent = Utils.formatCurrency(potentialProfit);
        
        const profitChange = document.getElementById('profit-change');
        profitChange.className = `metric-change ${potentialProfit >= 0 ? 'positive' : 'negative'}`;
        profitChange.innerHTML = `
            <i class="fas fa-arrow-${potentialProfit >= 0 ? 'up' : 'down'}"></i>
            <span>ROI: ${Utils.formatPercentage(roi)}</span>
        `;

        // Cash Flow
        const cashFlow = financialMetrics.monthly_cash_flow || 0;
        const capRate = financialMetrics.cap_rate || 0;
        document.getElementById('cash-flow-value').textContent = Utils.formatCurrency(cashFlow);
        
        const cashflowChange = document.getElementById('cashflow-change');
        cashflowChange.className = `metric-change ${cashFlow >= 0 ? 'positive' : 'negative'}`;
        cashflowChange.innerHTML = `
            <i class="fas fa-arrow-${cashFlow >= 0 ? 'up' : 'down'}"></i>
            <span>Cap Rate: ${Utils.formatPercentage(capRate)}</span>
        `;
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

    createCharts(analysis) {
        this.createInvestmentBreakdownChart(analysis);
        this.createCashFlowChart(analysis);
        this.createScenariosChart();
    }

    createInvestmentBreakdownChart(analysis) {
        const ctx = document.getElementById('investment-breakdown-chart');
        if (!ctx) return;

        const analysisData = analysis.analysis || {};
        const purchasePrice = this.currentProperty?.listing_price || 200000;
        const repairCost = analysisData.repair_estimate?.total_cost || 0;
        const closingCosts = purchasePrice * 0.03; // Estimate 3%
        const holdingCosts = 5000; // Estimate

        if (this.charts.investmentBreakdown) {
            this.charts.investmentBreakdown.destroy();
        }

        this.charts.investmentBreakdown = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Purchase Price', 'Repair Costs', 'Closing Costs', 'Holding Costs'],
                datasets: [{
                    data: [purchasePrice, repairCost, closingCosts, holdingCosts],
                    backgroundColor: [
                        '#2563eb',
                        '#dc2626',
                        '#f59e0b',
                        '#10b981'
                    ],
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
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.parsed;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(1);
                                return `${context.label}: ${Utils.formatCurrency(value)} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    createCashFlowChart(analysis) {
        const ctx = document.getElementById('cash-flow-chart');
        if (!ctx) return;

        const analysisData = analysis.analysis || {};
        const monthlyCashFlow = analysisData.financial_metrics?.monthly_cash_flow || 0;
        
        // Generate 12 months of projected cash flow
        const months = [];
        const cashFlowData = [];
        const cumulativeData = [];
        let cumulative = 0;

        for (let i = 1; i <= 12; i++) {
            months.push(`Month ${i}`);
            // Add some variation to make it more realistic
            const variation = (Math.random() - 0.5) * 0.2; // ±10% variation
            const monthlyFlow = monthlyCashFlow * (1 + variation);
            cashFlowData.push(monthlyFlow);
            cumulative += monthlyFlow;
            cumulativeData.push(cumulative);
        }

        if (this.charts.cashFlow) {
            this.charts.cashFlow.destroy();
        }

        this.charts.cashFlow = new Chart(ctx, {
            type: 'line',
            data: {
                labels: months,
                datasets: [{
                    label: 'Monthly Cash Flow',
                    data: cashFlowData,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4
                }, {
                    label: 'Cumulative Cash Flow',
                    data: cumulativeData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    fill: false,
                    tension: 0.4,
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Monthly Cash Flow ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Cumulative Cash Flow ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
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

    updateCalculator() {
        const purchasePrice = parseFloat(this.calculatorInputs['calc-purchase-price'].value) || 0;
        const downPaymentPercent = parseFloat(this.calculatorInputs['calc-down-payment'].value) || 20;
        const interestRate = parseFloat(this.calculatorInputs['calc-interest-rate'].value) || 7.5;
        const loanTerm = parseFloat(this.calculatorInputs['calc-loan-term'].value) || 30;
        const monthlyRent = parseFloat(this.calculatorInputs['calc-monthly-rent'].value) || 0;
        const monthlyExpenses = parseFloat(this.calculatorInputs['calc-monthly-expenses'].value) || 0;
        const vacancyRate = parseFloat(this.calculatorInputs['calc-vacancy-rate'].value) || 5;
        const maintenanceRate = parseFloat(this.calculatorInputs['calc-maintenance-rate'].value) || 10;

        if (purchasePrice === 0) return;

        // Calculate loan details
        const downPayment = purchasePrice * (downPaymentPercent / 100);
        const loanAmount = purchasePrice - downPayment;
        const monthlyRate = (interestRate / 100) / 12;
        const numPayments = loanTerm * 12;
        
        let monthlyPayment = 0;
        if (loanAmount > 0 && monthlyRate > 0) {
            monthlyPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                           (Math.pow(1 + monthlyRate, numPayments) - 1);
        }

        // Calculate cash flow
        const effectiveRent = monthlyRent * (1 - vacancyRate / 100);
        const maintenanceCost = monthlyRent * (maintenanceRate / 100);
        const totalExpenses = monthlyExpenses + maintenanceCost;
        const netCashFlow = effectiveRent - monthlyPayment - totalExpenses;

        // Calculate returns
        const annualRent = monthlyRent * 12;
        const annualExpenses = (monthlyExpenses + maintenanceCost) * 12;
        const noi = annualRent - annualExpenses; // Net Operating Income
        const capRate = purchasePrice > 0 ? (noi / purchasePrice) * 100 : 0;
        const annualCashFlow = netCashFlow * 12;
        const cocReturn = downPayment > 0 ? (annualCashFlow / downPayment) * 100 : 0;
        const totalRoi = purchasePrice > 0 ? ((annualCashFlow + (purchasePrice * 0.03)) / purchasePrice) * 100 : 0; // Assuming 3% appreciation
        const breakEvenRent = (monthlyPayment + monthlyExpenses) / (1 - vacancyRate / 100 - maintenanceRate / 100);

        // Update display
        document.getElementById('calc-monthly-payment').textContent = Utils.formatCurrency(monthlyPayment);
        document.getElementById('calc-net-cash-flow').textContent = Utils.formatCurrency(netCashFlow);
        document.getElementById('calc-cap-rate').textContent = Utils.formatPercentage(capRate / 100);
        document.getElementById('calc-coc-return').textContent = Utils.formatPercentage(cocReturn / 100);
        document.getElementById('calc-total-roi').textContent = Utils.formatPercentage(totalRoi / 100);
        document.getElementById('calc-break-even').textContent = Utils.formatCurrency(breakEvenRent);
    }

    populateCalculatorFromProperty(property) {
        if (property.listing_price) {
            this.calculatorInputs['calc-purchase-price'].value = property.listing_price;
        }
        
        // Estimate monthly rent based on property value (rough estimate)
        if (property.listing_price && !this.calculatorInputs['calc-monthly-rent'].value) {
            const estimatedRent = property.listing_price * 0.01; // 1% rule
            this.calculatorInputs['calc-monthly-rent'].value = Math.round(estimatedRent);
        }
        
        // Estimate monthly expenses
        if (property.tax_amount && !this.calculatorInputs['calc-monthly-expenses'].value) {
            const monthlyTax = property.tax_amount / 12;
            const estimatedInsurance = property.listing_price * 0.005 / 12; // 0.5% annually
            this.calculatorInputs['calc-monthly-expenses'].value = Math.round(monthlyTax + estimatedInsurance);
        }
        
        this.updateCalculator();
    }

    runSensitivityAnalysis() {
        const variable = document.getElementById('sensitivity-variable').value;
        const range = parseFloat(document.getElementById('sensitivity-range').value) || 20;
        
        if (!this.currentProperty) {
            Utils.showToast('Please select a property first', 'warning');
            return;
        }

        this.createSensitivityChart(variable, range);
    }

    createSensitivityChart(variable, range) {
        const ctx = document.getElementById('sensitivity-chart');
        if (!ctx) return;

        const baseValue = this.getBaseValue(variable);
        const steps = 11; // -50% to +50% in 10% increments
        const stepSize = (range * 2) / (steps - 1);
        
        const labels = [];
        const cashFlowData = [];
        const roiData = [];

        for (let i = 0; i < steps; i++) {
            const changePercent = -range + (i * stepSize);
            const newValue = baseValue * (1 + changePercent / 100);
            
            labels.push(`${changePercent >= 0 ? '+' : ''}${changePercent.toFixed(0)}%`);
            
            // Calculate impact on cash flow and ROI
            const impact = this.calculateSensitivityImpact(variable, newValue);
            cashFlowData.push(impact.cashFlow);
            roiData.push(impact.roi);
        }

        if (this.charts.sensitivity) {
            this.charts.sensitivity.destroy();
        }

        this.charts.sensitivity = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Monthly Cash Flow',
                    data: cashFlowData,
                    borderColor: '#2563eb',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    yAxisID: 'y'
                }, {
                    label: 'ROI (%)',
                    data: roiData,
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    yAxisID: 'y1'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Monthly Cash Flow ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'ROI (%)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: `Sensitivity Analysis: ${Utils.snakeToTitle(variable)}`
                    }
                }
            }
        });
    }

    getBaseValue(variable) {
        const purchasePrice = parseFloat(this.calculatorInputs['calc-purchase-price'].value) || 0;
        const monthlyRent = parseFloat(this.calculatorInputs['calc-monthly-rent'].value) || 0;
        const interestRate = parseFloat(this.calculatorInputs['calc-interest-rate'].value) || 7.5;
        const vacancyRate = parseFloat(this.calculatorInputs['calc-vacancy-rate'].value) || 5;
        const repairCost = this.currentAnalysis?.analysis?.repair_estimate?.total_cost || 0;

        switch (variable) {
            case 'purchase_price': return purchasePrice;
            case 'rent': return monthlyRent;
            case 'interest_rate': return interestRate;
            case 'vacancy_rate': return vacancyRate;
            case 'repair_cost': return repairCost;
            default: return 0;
        }
    }

    calculateSensitivityImpact(variable, newValue) {
        // This is a simplified calculation - in a real app you'd want more sophisticated modeling
        const baseCalculation = this.getCurrentCalculation();
        
        let modifiedCalculation = { ...baseCalculation };
        
        switch (variable) {
            case 'purchase_price':
                modifiedCalculation.purchasePrice = newValue;
                break;
            case 'rent':
                modifiedCalculation.monthlyRent = newValue;
                break;
            case 'interest_rate':
                modifiedCalculation.interestRate = newValue;
                break;
            case 'vacancy_rate':
                modifiedCalculation.vacancyRate = newValue;
                break;
            case 'repair_cost':
                modifiedCalculation.repairCost = newValue;
                break;
        }
        
        return this.calculateFinancials(modifiedCalculation);
    }

    getCurrentCalculation() {
        return {
            purchasePrice: parseFloat(this.calculatorInputs['calc-purchase-price'].value) || 0,
            downPaymentPercent: parseFloat(this.calculatorInputs['calc-down-payment'].value) || 20,
            interestRate: parseFloat(this.calculatorInputs['calc-interest-rate'].value) || 7.5,
            loanTerm: parseFloat(this.calculatorInputs['calc-loan-term'].value) || 30,
            monthlyRent: parseFloat(this.calculatorInputs['calc-monthly-rent'].value) || 0,
            monthlyExpenses: parseFloat(this.calculatorInputs['calc-monthly-expenses'].value) || 0,
            vacancyRate: parseFloat(this.calculatorInputs['calc-vacancy-rate'].value) || 5,
            maintenanceRate: parseFloat(this.calculatorInputs['calc-maintenance-rate'].value) || 10,
            repairCost: this.currentAnalysis?.analysis?.repair_estimate?.total_cost || 0
        };
    }

    calculateFinancials(params) {
        const {
            purchasePrice, downPaymentPercent, interestRate, loanTerm,
            monthlyRent, monthlyExpenses, vacancyRate, maintenanceRate
        } = params;

        const downPayment = purchasePrice * (downPaymentPercent / 100);
        const loanAmount = purchasePrice - downPayment;
        const monthlyRate = (interestRate / 100) / 12;
        const numPayments = loanTerm * 12;
        
        let monthlyPayment = 0;
        if (loanAmount > 0 && monthlyRate > 0) {
            monthlyPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                           (Math.pow(1 + monthlyRate, numPayments) - 1);
        }

        const effectiveRent = monthlyRent * (1 - vacancyRate / 100);
        const maintenanceCost = monthlyRent * (maintenanceRate / 100);
        const totalExpenses = monthlyExpenses + maintenanceCost;
        const netCashFlow = effectiveRent - monthlyPayment - totalExpenses;
        
        const annualCashFlow = netCashFlow * 12;
        const roi = downPayment > 0 ? (annualCashFlow / downPayment) * 100 : 0;

        return {
            cashFlow: netCashFlow,
            roi: roi
        };
    }

    updateScenario(scenarioType) {
        const scenarioCard = document.getElementById(`scenario-${scenarioType}`);
        if (!scenarioCard) return;

        const inputs = scenarioCard.querySelectorAll('input');
        const downPayment = parseFloat(inputs[0].value) || 0;
        const interestRate = parseFloat(inputs[1].value) || 0;
        const term = parseFloat(inputs[2].value) || 0;

        const purchasePrice = parseFloat(this.calculatorInputs['calc-purchase-price'].value) || 0;
        const monthlyRent = parseFloat(this.calculatorInputs['calc-monthly-rent'].value) || 0;
        const monthlyExpenses = parseFloat(this.calculatorInputs['calc-monthly-expenses'].value) || 0;

        if (purchasePrice === 0) return;

        const downPaymentAmount = purchasePrice * (downPayment / 100);
        const loanAmount = purchasePrice - downPaymentAmount;
        
        let monthlyPayment = 0;
        if (loanAmount > 0 && interestRate > 0 && term > 0) {
            const monthlyRate = (interestRate / 100) / 12;
            const numPayments = term * 12;
            monthlyPayment = loanAmount * (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) / 
                           (Math.pow(1 + monthlyRate, numPayments) - 1);
        }

        const cashFlow = monthlyRent - monthlyPayment - monthlyExpenses;

        // Update scenario results
        const results = scenarioCard.querySelector('.scenario-results');
        const metrics = results.querySelectorAll('.metric-value');
        
        metrics[0].textContent = Utils.formatCurrency(monthlyPayment); // Monthly Payment
        metrics[1].textContent = Utils.formatCurrency(downPaymentAmount); // Cash Required
        metrics[2].textContent = Utils.formatCurrency(cashFlow); // Cash Flow

        // Update scenarios comparison chart
        this.updateScenariosChart();
    }

    updateScenariosFromAnalysis(analysis) {
        const purchasePrice = this.currentProperty?.listing_price || 0;
        if (purchasePrice > 0) {
            this.calculatorInputs['calc-purchase-price'].value = purchasePrice;
            this.updateCalculator();
            
            // Update all scenarios
            ['conventional', 'fha', 'cash'].forEach(scenario => {
                this.updateScenario(scenario);
            });
        }
    }

    createScenariosChart() {
        const ctx = document.getElementById('scenarios-chart');
        if (!ctx) return;

        // Get data from scenario cards
        const scenarios = ['conventional', 'fha', 'cash'];
        const labels = ['Conventional', 'FHA', 'Cash'];
        const monthlyPayments = [];
        const cashRequired = [];
        const cashFlows = [];

        scenarios.forEach(scenarioType => {
            const scenarioCard = document.getElementById(`scenario-${scenarioType}`);
            if (scenarioCard) {
                const metrics = scenarioCard.querySelectorAll('.metric-value');
                monthlyPayments.push(this.parseMoneyValue(metrics[0].textContent));
                cashRequired.push(this.parseMoneyValue(metrics[1].textContent));
                cashFlows.push(this.parseMoneyValue(metrics[2].textContent));
            }
        });

        if (this.charts.scenarios) {
            this.charts.scenarios.destroy();
        }

        this.charts.scenarios = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Monthly Payment',
                    data: monthlyPayments,
                    backgroundColor: 'rgba(37, 99, 235, 0.8)',
                    yAxisID: 'y'
                }, {
                    label: 'Cash Required',
                    data: cashRequired,
                    backgroundColor: 'rgba(239, 68, 68, 0.8)',
                    yAxisID: 'y1'
                }, {
                    label: 'Monthly Cash Flow',
                    data: cashFlows,
                    backgroundColor: 'rgba(16, 185, 129, 0.8)',
                    yAxisID: 'y'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Monthly Amount ($)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Cash Required ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
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

    updateScenariosChart() {
        // Debounce chart updates
        if (this.scenarioUpdateTimeout) {
            clearTimeout(this.scenarioUpdateTimeout);
        }
        
        this.scenarioUpdateTimeout = setTimeout(() => {
            this.createScenariosChart();
        }, 500);
    }

    parseMoneyValue(text) {
        return parseFloat(text.replace(/[$,]/g, '')) || 0;
    }

    showEmptyState() {
        document.getElementById('analysis-results').style.display = 'none';
        document.getElementById('dashboard-empty-state').style.display = 'block';
    }

    hideEmptyState() {
        document.getElementById('dashboard-empty-state').style.display = 'none';
    }

    showAnalysisResults() {
        document.getElementById('analysis-results').style.display = 'block';
        this.hideEmptyState();
    }

    showNoAnalysisState() {
        this.hideEmptyState();
        document.getElementById('analysis-results').style.display = 'none';
        
        // Show a message encouraging analysis
        Utils.showToast('Click "Analyze Property" to generate financial analysis', 'info');
    }
}

// Refresh chart function for dashboard card actions
window.refreshChart = function(chartType) {
    if (window.financialDashboard) {
        switch (chartType) {
            case 'investment-breakdown':
                if (window.financialDashboard.currentAnalysis) {
                    window.financialDashboard.createInvestmentBreakdownChart(window.financialDashboard.currentAnalysis);
                }
                break;
            case 'cash-flow':
                if (window.financialDashboard.currentAnalysis) {
                    window.financialDashboard.createCashFlowChart(window.financialDashboard.currentAnalysis);
                }
                break;
        }
        Utils.showToast('Chart refreshed', 'success');
    }
};

// Initialize financial dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.financialDashboard = new FinancialDashboard();
});