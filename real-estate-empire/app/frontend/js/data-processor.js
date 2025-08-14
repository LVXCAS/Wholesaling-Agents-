/**
 * Data Processor Frontend JavaScript
 * Handles file uploads, AI processing, and results display
 */

class DataProcessor {
    constructor() {
        this.selectedFile = null;
        this.processedData = null;
        this.currentTab = 'summary';
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // Processing mode radio buttons
        document.querySelectorAll('input[name="processingMode"]').forEach(radio => {
            radio.addEventListener('change', this.handleModeChange.bind(this));
        });

        // File input change
        document.getElementById('zipFile').addEventListener('change', this.handleFileSelect.bind(this));
    }

    setupDragAndDrop() {
        const fileInput = document.getElementById('zipFile');
        const dropZone = fileInput.parentElement;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => fileInput.classList.add('dragover'), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => fileInput.classList.remove('dragover'), false);
        });

        dropZone.addEventListener('drop', this.handleDrop.bind(this), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;

        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.zip')) {
                document.getElementById('zipFile').files = files;
                this.handleFileSelect({ target: { files: files } });
            } else {
                this.showMessage('Please select a ZIP file', 'error');
            }
        }
    }

    handleModeChange(event) {
        const schemaInput = document.getElementById('schemaInput');
        if (event.target.value === 'schema') {
            schemaInput.style.display = 'block';
        } else {
            schemaInput.style.display = 'none';
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        if (!file.name.endsWith('.zip')) {
            this.showMessage('Please select a ZIP file', 'error');
            return;
        }

        this.selectedFile = file;
        this.showFilePreview(file);
        document.getElementById('processBtn').disabled = false;
    }

    showFilePreview(file) {
        const preview = document.getElementById('filePreview');
        const fileInfo = document.getElementById('fileInfo');

        const sizeInMB = (file.size / (1024 * 1024)).toFixed(2);
        
        fileInfo.innerHTML = `
            <div class="file-info-item">
                <span><i class="fas fa-file-archive me-2"></i><strong>${file.name}</strong></span>
                <span class="file-size">${sizeInMB} MB</span>
            </div>
            <div class="file-info-item">
                <span>Last Modified</span>
                <span>${new Date(file.lastModified).toLocaleString()}</span>
            </div>
            <div class="file-info-item">
                <span>Type</span>
                <span class="file-type csv">ZIP Archive</span>
            </div>
        `;

        preview.style.display = 'block';
    }

    async processFile() {
        if (!this.selectedFile) {
            this.showMessage('Please select a file first', 'error');
            return;
        }

        const processBtn = document.getElementById('processBtn');
        const progressContainer = document.getElementById('progressContainer');
        
        // Disable button and show progress
        processBtn.disabled = true;
        processBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
        progressContainer.style.display = 'block';

        try {
            // Simulate progress updates
            this.updateProgress(20, 'Uploading file...');
            
            const formData = new FormData();
            formData.append('file', this.selectedFile);

            const mode = document.querySelector('input[name="processingMode"]:checked').value;
            let endpoint = '/api/data-processor/auto-format';

            if (mode === 'schema') {
                const schemaText = document.getElementById('targetSchema').value;
                if (schemaText.trim()) {
                    try {
                        JSON.parse(schemaText); // Validate JSON
                        formData.append('target_schema', schemaText);
                        endpoint = '/api/data-processor/upload-zip';
                    } catch (e) {
                        throw new Error('Invalid JSON in target schema');
                    }
                }
            }

            this.updateProgress(40, 'Extracting files...');

            // Try different API base URLs
            const apiBaseUrls = [
                'http://localhost:8000',
                'http://127.0.0.1:8000',
                '' // Relative URL
            ];
            
            let response = null;
            let lastError = null;
            
            for (const baseUrl of apiBaseUrls) {
                try {
                    const fullUrl = baseUrl + endpoint;
                    console.log(`Trying API endpoint: ${fullUrl}`);
                    
                    response = await fetch(fullUrl, {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (response.ok) {
                        break; // Success, exit loop
                    } else {
                        lastError = `HTTP ${response.status}: ${response.statusText}`;
                    }
                } catch (error) {
                    lastError = error.message;
                    console.warn(`Failed to connect to ${baseUrl}: ${error.message}`);
                    continue;
                }
            }
            
            if (!response || !response.ok) {
                throw new Error(lastError || 'All API endpoints failed');
            }

            this.updateProgress(70, 'AI processing...');

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Processing failed');
            }

            const result = await response.json();
            this.updateProgress(100, 'Complete!');

            // Store processed data
            this.processedData = result;

            // Show results
            setTimeout(() => {
                this.displayResults(result);
                this.hideProgress();
            }, 1000);

        } catch (error) {
            console.error('Processing error:', error);
            this.showMessage(`Processing failed: ${error.message}`, 'error');
            this.hideProgress();
        } finally {
            // Reset button
            processBtn.disabled = false;
            processBtn.innerHTML = '<i class="fas fa-cogs me-2"></i>Process with AI';
        }
    }

    updateProgress(percent, text) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        progressBar.style.width = `${percent}%`;
        progressText.textContent = text;
    }

    hideProgress() {
        document.getElementById('progressContainer').style.display = 'none';
    }

    displayResults(result) {
        const resultsContainer = document.getElementById('resultsContainer');
        const exportContainer = document.getElementById('exportContainer');

        // Show results container
        resultsContainer.style.display = 'block';
        exportContainer.style.display = 'block';

        // Display summary
        this.displaySummary(result);
        
        // Display data preview
        this.displayDataPreview(result);
        
        // Display AI analysis
        this.displayAIAnalysis(result);

        // Scroll to results
        resultsContainer.scrollIntoView({ behavior: 'smooth' });
    }

    displaySummary(result) {
        const summaryDiv = document.getElementById('processingReport');
        const report = result.result?.report || {};
        const summary = report.summary || {};

        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-md-6">
                    <div class="ai-insight">
                        <h6><i class="fas fa-chart-bar me-2"></i>Processing Summary</h6>
                        <p><strong>Files Processed:</strong> ${summary.total_files_processed || 0}</p>
                        <p><strong>Successful Extractions:</strong> ${summary.successful_extractions || 0}</p>
                        <p><strong>Total Records:</strong> ${summary.total_records || 0}</p>
                        <p><strong>Processing Time:</strong> ${new Date(summary.processing_time || Date.now()).toLocaleString()}</p>
                    </div>
                </div>
                <div class="col-md-6">
                    <div class="ai-insight">
                        <h6><i class="fas fa-file-alt me-2"></i>File Breakdown</h6>
                        ${this.renderFileBreakdown(report.file_breakdown)}
                    </div>
                </div>
            </div>
            <div class="ai-insight">
                <h6><i class="fas fa-lightbulb me-2"></i>Recommendations</h6>
                ${this.renderRecommendations(report.recommendations || [])}
            </div>
        `;
    }

    renderFileBreakdown(breakdown) {
        if (!breakdown) return '<p>No file breakdown available</p>';

        const fileTypes = breakdown.file_types || {};
        let html = '<ul class="list-unstyled">';
        
        for (const [type, count] of Object.entries(fileTypes)) {
            html += `<li><span class="file-type ${type.replace('.', '')}">${type}</span> × ${count}</li>`;
        }
        
        html += '</ul>';
        return html;
    }

    renderRecommendations(recommendations) {
        if (!recommendations.length) return '<p>No specific recommendations available</p>';

        let html = '';
        recommendations.forEach(rec => {
            html += `<div class="recommendation-item">
                <i class="fas fa-check-circle text-success me-2"></i>${rec}
            </div>`;
        });
        
        return html;
    }

    displayDataPreview(result) {
        const dataDiv = document.getElementById('dataPreview');
        const processedData = result.result?.processed_data || {};

        let html = '<div class="accordion" id="dataAccordion">';
        let index = 0;

        for (const [fileName, fileData] of Object.entries(processedData)) {
            if (fileData.type === 'dataframe') {
                html += `
                    <div class="accordion-item">
                        <h2 class="accordion-header" id="heading${index}">
                            <button class="accordion-button ${index > 0 ? 'collapsed' : ''}" type="button" 
                                    data-bs-toggle="collapse" data-bs-target="#collapse${index}">
                                <i class="fas fa-table me-2"></i>${fileName}
                                <span class="badge bg-primary ms-2">${fileData.shape[0]} rows × ${fileData.shape[1]} cols</span>
                            </button>
                        </h2>
                        <div id="collapse${index}" class="accordion-collapse collapse ${index === 0 ? 'show' : ''}" 
                             data-bs-parent="#dataAccordion">
                            <div class="accordion-body">
                                ${this.renderDataTable(fileData)}
                            </div>
                        </div>
                    </div>
                `;
                index++;
            }
        }

        html += '</div>';
        dataDiv.innerHTML = html;
    }

    renderDataTable(fileData) {
        if (!fileData.sample_data || !fileData.sample_data.length) {
            return '<p>No data preview available</p>';
        }

        const columns = fileData.columns || Object.keys(fileData.sample_data[0]);
        
        let html = `
            <div class="data-table">
                <table class="table table-sm table-striped">
                    <thead>
                        <tr>
                            ${columns.map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
        `;

        fileData.sample_data.slice(0, 10).forEach(row => {
            html += '<tr>';
            columns.forEach(col => {
                const value = row[col];
                const displayValue = value !== null && value !== undefined ? 
                    (typeof value === 'string' && value.length > 50 ? value.substring(0, 50) + '...' : value) : 
                    '<em>null</em>';
                html += `<td>${displayValue}</td>`;
            });
            html += '</tr>';
        });

        html += `
                    </tbody>
                </table>
            </div>
            <small class="text-muted">Showing first 10 rows of ${fileData.shape[0]} total rows</small>
        `;

        return html;
    }

    displayAIAnalysis(result) {
        const aiDiv = document.getElementById('aiAnalysis');
        const reformattedData = result.result?.reformatted_data || {};
        const geminiAnalysis = reformattedData.gemini_analysis || {};

        let html = `
            <div class="ai-insight">
                <h6><i class="fas fa-robot me-2"></i>Gemini AI Analysis</h6>
                ${this.renderGeminiInsights(geminiAnalysis)}
            </div>
        `;

        if (reformattedData.auto_format) {
            html += `
                <div class="ai-insight">
                    <h6><i class="fas fa-magic me-2"></i>Auto-Format Recommendations</h6>
                    <p>AI has analyzed your data and provided automatic formatting suggestions.</p>
                </div>
            `;
        }

        aiDiv.innerHTML = html;
    }

    renderGeminiInsights(analysis) {
        if (!analysis || Object.keys(analysis).length === 0) {
            return '<p>AI analysis is being processed...</p>';
        }

        let html = '';

        if (analysis.mapping_strategy) {
            html += `<p><strong>Mapping Strategy:</strong> ${analysis.mapping_strategy}</p>`;
        }

        if (analysis.cleaning_steps) {
            html += '<p><strong>Cleaning Steps:</strong></p><ul>';
            const steps = Array.isArray(analysis.cleaning_steps) ? analysis.cleaning_steps : [analysis.cleaning_steps];
            steps.forEach(step => {
                html += `<li>${step}</li>`;
            });
            html += '</ul>';
        }

        if (analysis.feature_engineering) {
            html += '<p><strong>Feature Engineering:</strong></p><ul>';
            const features = Array.isArray(analysis.feature_engineering) ? analysis.feature_engineering : [analysis.feature_engineering];
            features.forEach(feature => {
                html += `<li>${feature}</li>`;
            });
            html += '</ul>';
        }

        if (analysis.recommendations) {
            const recs = typeof analysis.recommendations === 'string' ? 
                [analysis.recommendations] : analysis.recommendations;
            html += '<p><strong>AI Recommendations:</strong></p>';
            if (Array.isArray(recs)) {
                recs.forEach(rec => {
                    html += `<div class="recommendation-item">${rec}</div>`;
                });
            } else {
                html += `<div class="recommendation-item">${recs}</div>`;
            }
        }

        return html || '<p>Analysis completed successfully.</p>';
    }

    showTab(tabName) {
        // Hide all tabs
        document.querySelectorAll('.result-tab').forEach(tab => {
            tab.style.display = 'none';
        });

        // Remove active class from all buttons
        document.querySelectorAll('.btn-group .btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Show selected tab
        document.getElementById(`${tabName}Tab`).style.display = 'block';
        
        // Add active class to clicked button
        event.target.classList.add('active');
        
        this.currentTab = tabName;
    }

    async exportData(format) {
        if (!this.processedData) {
            this.showMessage('No processed data to export', 'error');
            return;
        }

        try {
            const response = await fetch(`/api/data-processor/export/${format}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.processedData.result)
            });

            if (!response.ok) {
                throw new Error('Export failed');
            }

            // Download file
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `processed_data.${format}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showMessage(`Data exported as ${format.toUpperCase()}`, 'success');

        } catch (error) {
            console.error('Export error:', error);
            this.showMessage(`Export failed: ${error.message}`, 'error');
        }
    }

    loadSampleSchema() {
        const sampleSchema = {
            "fields": {
                "price": {"type": "float", "required": true, "description": "Property price"},
                "bedrooms": {"type": "int", "min": 0, "max": 10},
                "bathrooms": {"type": "float", "min": 0, "max": 10},
                "square_feet": {"type": "int", "min": 100},
                "lot_size": {"type": "float", "min": 0},
                "year_built": {"type": "int", "min": 1800, "max": 2024},
                "location": {"type": "string", "required": true},
                "property_type": {"type": "string", "enum": ["house", "condo", "townhouse"]}
            },
            "target_variable": "price",
            "ml_task": "regression",
            "preprocessing": {
                "handle_missing": "median",
                "scale_features": true,
                "encode_categorical": "onehot"
            }
        };

        document.getElementById('targetSchema').value = JSON.stringify(sampleSchema, null, 2);
        this.showMessage('Sample schema loaded', 'success');
    }

    async validateSchema() {
        const schemaText = document.getElementById('targetSchema').value;
        
        if (!schemaText.trim()) {
            this.showMessage('Please enter a schema to validate', 'warning');
            return;
        }

        try {
            const schema = JSON.parse(schemaText);
            
            const response = await fetch('/api/data-processor/validate-schema', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(schema)
            });

            const result = await response.json();
            
            if (result.valid) {
                this.showMessage('Schema is valid!', 'success');
            } else {
                this.showMessage(`Schema validation failed: ${result.errors.join(', ')}`, 'error');
            }

        } catch (error) {
            this.showMessage(`Invalid JSON: ${error.message}`, 'error');
        }
    }

    showMessage(message, type = 'info') {
        const container = document.getElementById('statusMessages');
        const toast = document.createElement('div');
        
        const bgClass = {
            'success': 'bg-success',
            'error': 'bg-danger',
            'warning': 'bg-warning',
            'info': 'bg-info'
        }[type] || 'bg-info';

        const icon = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        }[type] || 'info-circle';

        toast.className = `toast show toast-${type}`;
        toast.innerHTML = `
            <div class="toast-header ${bgClass} text-white">
                <i class="fas fa-${icon} me-2"></i>
                <strong class="me-auto">Data Processor</strong>
                <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.parentElement.remove()"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;

        container.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (toast.parentElement) {
                toast.remove();
            }
        }, 5000);
    }
}

// Global functions for HTML onclick handlers
function handleFileSelect(event) {
    dataProcessor.handleFileSelect(event);
}

function processFile() {
    dataProcessor.processFile();
}

function showTab(tabName) {
    dataProcessor.showTab(tabName);
}

function exportData(format) {
    dataProcessor.exportData(format);
}

function loadSampleSchema() {
    dataProcessor.loadSampleSchema();
}

function validateSchema() {
    dataProcessor.validateSchema();
}

function showHelp() {
    const helpModal = new bootstrap.Modal(document.getElementById('helpModal'));
    helpModal.show();
}

// Initialize the data processor when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.dataProcessor = new DataProcessor();
});