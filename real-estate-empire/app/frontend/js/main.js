// Main application JavaScript

class RealEstateApp {
    constructor() {
        this.currentTab = 'property-input';
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupGlobalEventListeners();
        this.checkAPIConnection();
        
        // Initialize based on URL parameters
        const params = Utils.getQueryParams();
        if (params.tab) {
            this.switchTab(params.tab);
        }
    }

    setupNavigation() {
        const navItems = document.querySelectorAll('.nav-item[data-tab]');
        
        navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = item.dataset.tab;
                this.switchTab(tabName);
            });
        });
    }

    switchTab(tabName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeNavItem = document.querySelector(`[data-tab="${tabName}"]`);
        if (activeNavItem) {
            activeNavItem.classList.add('active');
        }

        // Update content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        
        const activeContent = document.getElementById(tabName);
        if (activeContent) {
            activeContent.classList.add('active');
        }

        // Update URL
        Utils.setQueryParam('tab', tabName);
        this.currentTab = tabName;

        // Load tab-specific content
        this.loadTabContent(tabName);
    }

    async loadTabContent(tabName) {
        switch (tabName) {
            case 'property-input':
                // Property input form is already loaded
                break;
                
            case 'financial-dashboard':
                await this.loadFinancialDashboard();
                break;
                
            case 'comparables-viewer':
                await this.loadComparablesViewer();
                break;
                
            case 'strategy-comparison':
                await this.loadStrategyComparison();
                break;
        }
    }

    async loadFinancialDashboard() {
        const dashboardContent = document.getElementById('financial-dashboard');
        const placeholder = dashboardContent.querySelector('.dashboard-placeholder');
        
        if (placeholder) {
            // Replace placeholder with actual dashboard content
            // This will be implemented in subtask 4.2
            console.log('Loading financial dashboard...');
        }
    }

    async loadComparablesViewer() {
        const viewerContent = document.getElementById('comparables-viewer');
        const placeholder = viewerContent.querySelector('.dashboard-placeholder');
        
        if (placeholder) {
            // Replace placeholder with actual comparables viewer
            // This will be implemented in subtask 4.3
            console.log('Loading comparables viewer...');
        }
    }

    async loadStrategyComparison() {
        const comparisonContent = document.getElementById('strategy-comparison');
        const placeholder = comparisonContent.querySelector('.dashboard-placeholder');
        
        if (placeholder) {
            // Replace placeholder with actual strategy comparison
            // This will be implemented in subtask 4.4
            console.log('Loading strategy comparison...');
        }
    }

    setupGlobalEventListeners() {
        // Handle escape key to close modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // Handle browser back/forward
        window.addEventListener('popstate', () => {
            const params = Utils.getQueryParams();
            if (params.tab && params.tab !== this.currentTab) {
                this.switchTab(params.tab);
            }
        });

        // Handle online/offline status
        window.addEventListener('online', () => {
            Utils.showToast('Connection restored', 'success');
            this.checkAPIConnection();
        });

        window.addEventListener('offline', () => {
            Utils.showToast('Connection lost - working offline', 'warning');
        });

        // Handle unload to save form data
        window.addEventListener('beforeunload', (e) => {
            if (window.propertyForm) {
                window.propertyForm.saveFormData();
            }
        });
    }

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-overlay.active');
        modals.forEach(modal => {
            modal.classList.remove('active');
        });
    }

    async checkAPIConnection() {
        try {
            await API.healthCheck();
            this.updateConnectionStatus(true);
        } catch (error) {
            console.error('API connection failed:', error);
            this.updateConnectionStatus(false);
        }
    }

    updateConnectionStatus(connected) {
        // Add connection indicator to navbar
        let indicator = document.querySelector('.connection-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'connection-indicator';
            document.querySelector('.navbar').appendChild(indicator);
        }

        if (connected) {
            indicator.innerHTML = '<i class="fas fa-circle" style="color: #10b981;"></i>';
            indicator.title = 'Connected to server';
        } else {
            indicator.innerHTML = '<i class="fas fa-circle" style="color: #ef4444;"></i>';
            indicator.title = 'Disconnected from server';
        }
    }

    // Utility methods for other components to use

    showModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.add('active');
        }
    }

    hideModal(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('active');
        }
    }

    async exportData(format, data) {
        try {
            Utils.showLoading(true, `Exporting to ${format.toUpperCase()}...`);
            
            let result;
            switch (format) {
                case 'pdf':
                    result = await API.exportToPDF(data.propertyId, data.analysisId);
                    break;
                case 'csv':
                    result = await API.exportToCSV(data.propertyIds);
                    break;
                case 'json':
                    result = await API.exportToJSON(data.propertyId, data.analysisId);
                    break;
                default:
                    throw new Error('Unsupported export format');
            }
            
            // Handle file download
            this.downloadFile(result, format);
            Utils.showToast(`Data exported to ${format.toUpperCase()} successfully`, 'success');
            
        } catch (error) {
            console.error('Export failed:', error);
            Utils.showToast(`Failed to export data: ${error.message}`, 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    downloadFile(data, format) {
        const blob = new Blob([data], { 
            type: this.getMimeType(format) 
        });
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `property-analysis-${new Date().toISOString().split('T')[0]}.${format}`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    getMimeType(format) {
        const mimeTypes = {
            pdf: 'application/pdf',
            csv: 'text/csv',
            json: 'application/json'
        };
        return mimeTypes[format] || 'application/octet-stream';
    }

    // Search functionality
    setupSearch(searchInputId, searchCallback) {
        const searchInput = document.getElementById(searchInputId);
        if (!searchInput) return;

        const debouncedSearch = Utils.debounce(searchCallback, 300);
        
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            debouncedSearch(query);
        });
    }

    // Pagination functionality
    setupPagination(containerId, data, itemsPerPage, renderCallback) {
        const container = document.getElementById(containerId);
        if (!container) return;

        const totalPages = Math.ceil(data.length / itemsPerPage);
        let currentPage = 1;

        const renderPage = (page) => {
            const startIndex = (page - 1) * itemsPerPage;
            const endIndex = startIndex + itemsPerPage;
            const pageData = data.slice(startIndex, endIndex);
            
            renderCallback(pageData);
            this.renderPaginationControls(container, page, totalPages, renderPage);
        };

        renderPage(currentPage);
    }

    renderPaginationControls(container, currentPage, totalPages, onPageChange) {
        let paginationContainer = container.querySelector('.pagination');
        
        if (!paginationContainer) {
            paginationContainer = document.createElement('div');
            paginationContainer.className = 'pagination';
            container.appendChild(paginationContainer);
        }

        const pages = [];
        
        // Previous button
        pages.push(`
            <button class="pagination-item ${currentPage === 1 ? 'disabled' : ''}" 
                    ${currentPage === 1 ? 'disabled' : ''} 
                    onclick="this.onclick = null; arguments[0](${currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `);

        // Page numbers
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        if (startPage > 1) {
            pages.push(`<button class="pagination-item" onclick="this.onclick = null; arguments[0](1)">1</button>`);
            if (startPage > 2) {
                pages.push(`<span class="pagination-item disabled">...</span>`);
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            pages.push(`
                <button class="pagination-item ${i === currentPage ? 'active' : ''}" 
                        onclick="this.onclick = null; arguments[0](${i})">${i}</button>
            `);
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                pages.push(`<span class="pagination-item disabled">...</span>`);
            }
            pages.push(`<button class="pagination-item" onclick="this.onclick = null; arguments[0](${totalPages})">${totalPages}</button>`);
        }

        // Next button
        pages.push(`
            <button class="pagination-item ${currentPage === totalPages ? 'disabled' : ''}" 
                    ${currentPage === totalPages ? 'disabled' : ''} 
                    onclick="this.onclick = null; arguments[0](${currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `);

        paginationContainer.innerHTML = pages.join('');
        
        // Add event listeners
        paginationContainer.querySelectorAll('button:not(.disabled)').forEach(button => {
            button.onclick = (e) => {
                const page = parseInt(e.target.textContent) || (e.target.querySelector('i.fa-chevron-left') ? currentPage - 1 : currentPage + 1);
                onPageChange(page);
            };
        });
    }
}

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new RealEstateApp();
    
    // Add some global utility functions
    window.showModal = (modalId) => window.app.showModal(modalId);
    window.hideModal = (modalId) => window.app.hideModal(modalId);
    window.exportData = (format, data) => window.app.exportData(format, data);
});

// Handle service worker for offline functionality (if needed)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}