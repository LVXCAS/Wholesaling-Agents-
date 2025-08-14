// Market Analysis JavaScript

async function getMarketStats() {
    const city = document.getElementById('city').value.trim();
    const state = document.getElementById('state').value.trim();
    
    if (!city || !state) {
        alert('Please enter both city and state');
        return;
    }
    
    const resultsDiv = document.getElementById('market-stats-results');
    resultsDiv.innerHTML = '<div class="loading">Loading market statistics...</div>';
    
    try {
        const response = await fetch(`/api/v1/market-data/stats/${encodeURIComponent(city)}/${encodeURIComponent(state)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const stats = await response.json();
        displayMarketStats(stats, resultsDiv);
        
    } catch (error) {
        console.error('Error fetching market stats:', error);
        resultsDiv.innerHTML = `<div class="error">Error loading market statistics: ${error.message}</div>`;
    }
}

function displayMarketStats(stats, container) {
    const html = `
        <div class="market-stats-card">
            <h3>${stats.city}, ${stats.state}</h3>
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-label">Average Price</div>
                    <div class="stat-value">$${formatNumber(stats.avg_price)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Median Price</div>
                    <div class="stat-value">$${formatNumber(stats.median_price)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Price per Sq Ft</div>
                    <div class="stat-value">$${stats.avg_price_per_sqft.toFixed(2)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Total Listings</div>
                    <div class="stat-value">${formatNumber(stats.total_listings)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Avg Bedrooms</div>
                    <div class="stat-value">${stats.avg_bedrooms.toFixed(1)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Avg Bathrooms</div>
                    <div class="stat-value">${stats.avg_bathrooms.toFixed(1)}</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Avg House Size</div>
                    <div class="stat-value">${formatNumber(stats.avg_house_size)} sq ft</div>
                </div>
            </div>
        </div>
    `;
    container.innerHTML = html;
}

async function analyzeInvestment() {
    const propertyData = {
        city: document.getElementById('val-city').value.trim(),
        state: document.getElementById('val-state').value.trim(),
        bedrooms: parseInt(document.getElementById('bedrooms').value) || 0,
        bathrooms: parseFloat(document.getElementById('bathrooms').value) || 0,
        house_size: parseInt(document.getElementById('house-size').value) || 0,
        asking_price: parseInt(document.getElementById('asking-price').value) || 0,
        estimated_rent: parseInt(document.getElementById('estimated-rent').value) || 0,
        acre_lot: parseFloat(document.getElementById('acre-lot').value) || 0
    };
    
    if (!propertyData.city || !propertyData.state) {
        alert('Please enter city and state');
        return;
    }
    
    const resultsDiv = document.getElementById('valuation-results');
    resultsDiv.innerHTML = '<div class="loading">Analyzing investment opportunity...</div>';
    
    try {
        const response = await fetch('/api/v1/investment-analysis/analyze-deal', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(propertyData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const analysis = await response.json();
        displayInvestmentAnalysis(analysis, resultsDiv);
        
    } catch (error) {
        console.error('Error analyzing investment:', error);
        resultsDiv.innerHTML = `<div class="error">Error analyzing investment: ${error.message}</div>`;
    }
}

function displayInvestmentAnalysis(analysis, container) {
    const recommendation = analysis.recommendation.toLowerCase();
    let analysisClass = 'investment-analysis';
    let recommendationClass = 'recommendation';
    
    if (recommendation.includes('strong buy')) {
        recommendationClass += ' strong-buy';
    } else if (recommendation.includes('buy')) {
        recommendationClass += ' buy';
    } else if (recommendation.includes('consider')) {
        recommendationClass += ' consider';
        analysisClass += ' warning';
    } else if (recommendation.includes('caution')) {
        recommendationClass += ' caution';
        analysisClass += ' warning';
    } else if (recommendation.includes('avoid')) {
        recommendationClass += ' avoid';
        analysisClass += ' danger';
    }
    
    const html = `
        <div class="${analysisClass}">
            <div class="${recommendationClass}">${analysis.recommendation}</div>
            <div>Confidence Score: ${analysis.confidence_score.toFixed(1)}%</div>
            
            <div class="metrics-grid">
                <div class="metric-item">
                    <div class="metric-label">Estimated Value</div>
                    <div class="metric-value">$${formatNumber(analysis.property.estimated_value)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Asking Price</div>
                    <div class="metric-value">$${formatNumber(analysis.property.asking_price)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Equity Potential</div>
                    <div class="metric-value">$${formatNumber(analysis.property.equity_potential)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Investment Score</div>
                    <div class="metric-value">${analysis.investment_metrics.investment_score.toFixed(1)}/100</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Cap Rate</div>
                    <div class="metric-value">${analysis.investment_metrics.cap_rate ? analysis.investment_metrics.cap_rate.toFixed(2) + '%' : 'N/A'}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Cash on Cash</div>
                    <div class="metric-value">${analysis.investment_metrics.cash_on_cash_return ? analysis.investment_metrics.cash_on_cash_return.toFixed(2) + '%' : 'N/A'}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Monthly Cash Flow</div>
                    <div class="metric-value">$${analysis.investment_metrics.monthly_cash_flow ? formatNumber(analysis.investment_metrics.monthly_cash_flow) : 'N/A'}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Risk Level</div>
                    <div class="metric-value">${analysis.investment_metrics.risk_level}</div>
                </div>
            </div>
            
            ${analysis.market_comparison && analysis.market_comparison.market_avg_price ? `
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                    <strong>Market Comparison:</strong><br>
                    Market Avg: $${formatNumber(analysis.market_comparison.market_avg_price)} | 
                    Market Median: $${formatNumber(analysis.market_comparison.market_median_price)} | 
                    vs Avg: ${analysis.market_comparison.price_vs_market_avg ? analysis.market_comparison.price_vs_market_avg.toFixed(1) + '%' : 'N/A'}
                </div>
            ` : ''}
        </div>
    `;
    container.innerHTML = html;
}

async function getComparables() {
    const propertyData = {
        city: document.getElementById('val-city').value.trim(),
        state: document.getElementById('val-state').value.trim(),
        bedrooms: parseInt(document.getElementById('bedrooms').value) || 0,
        bathrooms: parseFloat(document.getElementById('bathrooms').value) || 0,
        house_size: parseInt(document.getElementById('house-size').value) || 0
    };
    
    if (!propertyData.city || !propertyData.state) {
        alert('Please enter city and state');
        return;
    }
    
    const resultsDiv = document.getElementById('valuation-results');
    resultsDiv.innerHTML = '<div class="loading">Finding comparable properties...</div>';
    
    try {
        const response = await fetch('/api/v1/market-data/comparables', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(propertyData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayComparables(data.comparables, resultsDiv);
        
    } catch (error) {
        console.error('Error finding comparables:', error);
        resultsDiv.innerHTML = `<div class="error">Error finding comparables: ${error.message}</div>`;
    }
}

function displayComparables(comparables, container) {
    if (!comparables || comparables.length === 0) {
        container.innerHTML = '<div class="error">No comparable properties found</div>';
        return;
    }
    
    const html = `
        <div class="comparables-list">
            <h4>Found ${comparables.length} Comparable Properties</h4>
            ${comparables.map(comp => `
                <div class="comparable-item">
                    <div class="comparable-header">
                        <div class="comparable-price">$${formatNumber(comp.property.price)}</div>
                        <div class="similarity-score">${comp.similarity_score.toFixed(1)}% match</div>
                    </div>
                    <div class="comparable-details">
                        ${comp.property.bedrooms || 0} bed, ${comp.property.bathrooms || 0} bath | 
                        ${formatNumber(comp.property.house_size)} sq ft | 
                        ${comp.property.city}, ${comp.property.state} ${comp.property.zip_code || ''} |
                        ${comp.property.price_per_sqft ? '$' + comp.property.price_per_sqft.toFixed(2) + '/sq ft' : ''}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    container.innerHTML = html;
}

async function getTopMarkets() {
    const resultsDiv = document.getElementById('top-markets-results');
    resultsDiv.innerHTML = '<div class="loading">Loading top markets...</div>';
    
    try {
        const response = await fetch('/api/v1/market-data/top-markets?limit=20');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        displayTopMarkets(data.markets, resultsDiv);
        
    } catch (error) {
        console.error('Error fetching top markets:', error);
        resultsDiv.innerHTML = `<div class="error">Error loading top markets: ${error.message}</div>`;
    }
}

function displayTopMarkets(markets, container) {
    const html = `
        <div class="markets-grid">
            ${markets.map(market => `
                <div class="market-card">
                    <div class="market-header">${market.city}, ${market.state}</div>
                    <div class="market-stats-mini">
                        <div>Avg Price: $${formatNumber(market.avg_price)}</div>
                        <div>Listings: ${formatNumber(market.total_listings)}</div>
                        <div>$/sq ft: $${market.avg_price_per_sqft.toFixed(2)}</div>
                        <div>Avg Size: ${formatNumber(market.avg_house_size)} sq ft</div>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
    container.innerHTML = html;
}

async function trainModel() {
    const resultsDiv = document.getElementById('model-results');
    resultsDiv.innerHTML = '<div class="loading">Training valuation model... This may take a few minutes.</div>';
    
    try {
        const response = await fetch('/api/v1/investment-analysis/train-valuation-model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ retrain: true })
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        displayModelTrainingResult(result, resultsDiv);
        
    } catch (error) {
        console.error('Error training model:', error);
        resultsDiv.innerHTML = `<div class="error">Error training model: ${error.message}</div>`;
    }
}

function displayModelTrainingResult(result, container) {
    if (result.error) {
        container.innerHTML = `<div class="error">${result.error}</div>`;
        return;
    }
    
    const html = `
        <div class="model-info">
            <h4>Model Training Complete</h4>
            <p><strong>Status:</strong> ${result.status}</p>
            <p><strong>Training Samples:</strong> ${formatNumber(result.training_samples || 0)}</p>
            <p><strong>Test Samples:</strong> ${formatNumber(result.test_samples || 0)}</p>
            <p><strong>Mean Absolute Error:</strong> $${formatNumber(result.mean_absolute_error || 0)}</p>
            <p><strong>R² Score:</strong> ${(result.r2_score || 0).toFixed(3)}</p>
            
            ${result.feature_importance ? `
                <div class="feature-importance">
                    <h5>Feature Importance:</h5>
                    ${Object.entries(result.feature_importance).map(([feature, importance]) => `
                        <div class="feature-bar">
                            <div class="feature-name">${feature}</div>
                            <div class="feature-bar-bg">
                                <div class="feature-bar-fill" style="width: ${importance * 100}%"></div>
                            </div>
                            <div class="feature-value">${(importance * 100).toFixed(1)}%</div>
                        </div>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    container.innerHTML = html;
}

async function getModelInfo() {
    const resultsDiv = document.getElementById('model-results');
    resultsDiv.innerHTML = '<div class="loading">Loading model information...</div>';
    
    try {
        const response = await fetch('/api/v1/investment-analysis/model-info');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const info = await response.json();
        displayModelInfo(info, resultsDiv);
        
    } catch (error) {
        console.error('Error fetching model info:', error);
        resultsDiv.innerHTML = `<div class="error">Error loading model info: ${error.message}</div>`;
    }
}

function displayModelInfo(info, container) {
    const html = `
        <div class="model-info">
            <h4>Model Information</h4>
            <p><strong>Model Type:</strong> ${info.model_type}</p>
            <p><strong>Model Trained:</strong> ${info.model_trained ? 'Yes' : 'No'}</p>
            
            ${info.feature_importance ? `
                <div class="feature-importance">
                    <h5>Feature Importance:</h5>
                    ${Object.entries(info.feature_importance).map(([feature, importance]) => `
                        <div class="feature-bar">
                            <div class="feature-name">${feature}</div>
                            <div class="feature-bar-bg">
                                <div class="feature-bar-fill" style="width: ${importance * 100}%"></div>
                            </div>
                            <div class="feature-value">${(importance * 100).toFixed(1)}%</div>
                        </div>
                    `).join('')}
                </div>
            ` : '<p>No feature importance data available. Train the model first.</p>'}
        </div>
    `;
    container.innerHTML = html;
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return Math.round(num).toLocaleString();
}