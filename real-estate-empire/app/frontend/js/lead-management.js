/**
 * Lead Management Interface
 * Implements lead inbox with filtering, lead detail view, status management, and assignment interface
 */

class LeadManagement {
    constructor() {
        this.leads = [];
        this.filteredLeads = [];
        this.selectedLeads = [];
        this.currentLead = null;
        this.filters = {
            status: '',
            source: '',
            assignedTo: '',
            minScore: null,
            maxScore: null,
            search: ''
        };
        this.sortBy = 'created_at';
        this.sortOrder = 'desc';
        this.currentPage = 1;
        this.itemsPerPage = 25;
        this.users = []; // Available users for assignment
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadUsers();
        this.loadLeads();
        this.setupKeyboardShortcuts();
    }

    setupEventListeners() {
        // Filter controls
        document.getElementById('status-filter')?.addEventListener('change', (e) => {
            this.filters.status = e.target.value;
            this.applyFilters();
        });

        document.getElementById('source-filter')?.addEventListener('change', (e) => {
            this.filters.source = e.target.value;
            this.applyFilters();
        });

        document.getElementById('assigned-filter')?.addEventListener('change', (e) => {
            this.filters.assignedTo = e.target.value;
            this.applyFilters();
        });

        // Search
        const searchInput = document.getElementById('lead-search');
        if (searchInput) {
            const debouncedSearch = Utils.debounce((query) => {
                this.filters.search = query;
                this.applyFilters();
            }, 300);
            
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }

        // Sort controls
        document.getElementById('sort-by')?.addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.sortLeads();
        });

        document.getElementById('sort-order')?.addEventListener('change', (e) => {
            this.sortOrder = e.target.value;
            this.sortLeads();
        });

        // Bulk actions
        document.getElementById('select-all-leads')?.addEventListener('change', (e) => {
            this.selectAllLeads(e.target.checked);
        });

        document.getElementById('bulk-assign-btn')?.addEventListener('click', () => {
            this.showBulkAssignModal();
        });

        document.getElementById('bulk-status-btn')?.addEventListener('click', () => {
            this.showBulkStatusModal();
        });

        document.getElementById('bulk-delete-btn')?.addEventListener('click', () => {
            this.bulkDeleteLeads();
        });

        // Refresh button
        document.getElementById('refresh-leads-btn')?.addEventListener('click', () => {
            this.loadLeads();
        });

        // View toggle
        document.getElementById('list-view-btn')?.addEventListener('click', () => {
            this.switchView('list');
        });

        document.getElementById('kanban-view-btn')?.addEventListener('click', () => {
            this.switchView('kanban');
        });

        // Lead detail modal events
        document.getElementById('save-lead-btn')?.addEventListener('click', () => {
            this.saveLeadDetails();
        });

        document.getElementById('delete-lead-btn')?.addEventListener('click', () => {
            this.deleteLead(this.currentLead?.id);
        });

        // Communication events
        document.getElementById('send-email-btn')?.addEventListener('click', () => {
            this.showEmailModal();
        });

        document.getElementById('send-sms-btn')?.addEventListener('click', () => {
            this.showSMSModal();
        });

        document.getElementById('make-call-btn')?.addEventListener('click', () => {
            this.initiateCall();
        });

        // Quick actions
        document.getElementById('quick-contact-btn')?.addEventListener('click', () => {
            this.quickContact();
        });

        document.getElementById('schedule-followup-btn')?.addEventListener('click', () => {
            this.scheduleFollowup();
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Only handle shortcuts when not in input fields
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;

            switch (e.key) {
                case 'r':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.loadLeads();
                    }
                    break;
                case 'n':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        this.createNewLead();
                    }
                    break;
                case 'f':
                    if (e.ctrlKey || e.metaKey) {
                        e.preventDefault();
                        document.getElementById('lead-search')?.focus();
                    }
                    break;
                case 'Escape':
                    this.closeAllModals();
                    break;
            }
        });
    }

    async loadUsers() {
        try {
            // In a real implementation, this would load from a users API
            this.users = [
                { id: 'user1', name: 'John Smith', email: 'john@example.com' },
                { id: 'user2', name: 'Sarah Johnson', email: 'sarah@example.com' },
                { id: 'user3', name: 'Mike Davis', email: 'mike@example.com' },
                { id: 'unassigned', name: 'Unassigned', email: null }
            ];
            
            this.populateUserSelectors();
        } catch (error) {
            console.error('Error loading users:', error);
        }
    }

    populateUserSelectors() {
        const selectors = document.querySelectorAll('.user-selector');
        selectors.forEach(selector => {
            selector.innerHTML = '<option value="">All Users</option>';
            this.users.forEach(user => {
                const option = document.createElement('option');
                option.value = user.id;
                option.textContent = user.name;
                selector.appendChild(option);
            });
        });
    }

    async loadLeads() {
        try {
            Utils.showLoading(true, 'Loading leads...');
            
            const response = await API.get('/api/v1/leads', {
                limit: 1000, // Load all for client-side filtering
                sort_by: this.sortBy,
                sort_order: this.sortOrder
            });

            this.leads = response;
            this.filteredLeads = [...this.leads];
            
            this.renderLeads();
            this.updateStats();
            
            Utils.showToast('Leads loaded successfully', 'success');
            
        } catch (error) {
            console.error('Error loading leads:', error);
            Utils.showToast('Failed to load leads', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    applyFilters() {
        this.filteredLeads = this.leads.filter(lead => {
            // Status filter
            if (this.filters.status && lead.status !== this.filters.status) return false;

            // Source filter
            if (this.filters.source && lead.source !== this.filters.source) return false;

            // Assigned to filter
            if (this.filters.assignedTo) {
                if (this.filters.assignedTo === 'unassigned' && lead.assigned_to) return false;
                if (this.filters.assignedTo !== 'unassigned' && lead.assigned_to !== this.filters.assignedTo) return false;
            }

            // Score filters
            if (this.filters.minScore && lead.lead_score < this.filters.minScore) return false;
            if (this.filters.maxScore && lead.lead_score > this.filters.maxScore) return false;

            // Search filter
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                const searchText = `${lead.owner_name || ''} ${lead.owner_email || ''} ${lead.owner_phone || ''} ${lead.property_address || ''} ${lead.notes || ''}`.toLowerCase();
                if (!searchText.includes(searchTerm)) return false;
            }

            return true;
        });

        this.currentPage = 1;
        this.renderLeads();
        this.updateStats();
    }

    sortLeads() {
        this.filteredLeads.sort((a, b) => {
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

        this.renderLeads();
    }

    renderLeads() {
        const currentView = document.querySelector('.view-toggle .btn.active')?.id === 'kanban-view-btn' ? 'kanban' : 'list';
        
        if (currentView === 'kanban') {
            this.renderKanbanView();
        } else {
            this.renderListView();
        }
        
        this.renderPagination();
    }

    renderListView() {
        const container = document.getElementById('leads-list');
        if (!container) return;

        const startIndex = (this.currentPage - 1) * this.itemsPerPage;
        const endIndex = startIndex + this.itemsPerPage;
        const pageLeads = this.filteredLeads.slice(startIndex, endIndex);

        if (pageLeads.length === 0) {
            container.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-inbox fa-3x"></i>
                    <h3>No leads found</h3>
                    <p>Try adjusting your filters or search criteria</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="leads-table">
                <div class="table-header">
                    <div class="header-cell checkbox-cell">
                        <input type="checkbox" id="select-all-leads">
                    </div>
                    <div class="header-cell">Lead</div>
                    <div class="header-cell">Property</div>
                    <div class="header-cell">Status</div>
                    <div class="header-cell">Score</div>
                    <div class="header-cell">Assigned</div>
                    <div class="header-cell">Last Contact</div>
                    <div class="header-cell">Actions</div>
                </div>
                <div class="table-body">
                    ${pageLeads.map(lead => this.createLeadRow(lead)).join('')}
                </div>
            </div>
        `;

        // Re-attach event listeners for the new content
        this.attachLeadRowEventListeners();
    }

    createLeadRow(lead) {
        const statusBadge = this.getStatusBadge(lead.status);
        const scoreColor = this.getScoreColor(lead.lead_score);
        const assignedUser = this.users.find(u => u.id === lead.assigned_to);
        const lastContact = lead.last_contact_date ? 
            new Date(lead.last_contact_date).toLocaleDateString() : 
            'Never';

        return `
            <div class="table-row" data-lead-id="${lead.id}">
                <div class="table-cell checkbox-cell">
                    <input type="checkbox" class="lead-checkbox" value="${lead.id}">
                </div>
                <div class="table-cell lead-info">
                    <div class="lead-name">${lead.owner_name || 'Unknown'}</div>
                    <div class="lead-contact">
                        ${lead.owner_email ? `<span><i class="fas fa-envelope"></i> ${lead.owner_email}</span>` : ''}
                        ${lead.owner_phone ? `<span><i class="fas fa-phone"></i> ${lead.owner_phone}</span>` : ''}
                    </div>
                </div>
                <div class="table-cell property-info">
                    <div class="property-address">${lead.property_address || 'Address not available'}</div>
                    <div class="property-details">
                        ${lead.property_city ? `${lead.property_city}, ${lead.property_state}` : ''}
                        ${lead.listing_price ? ` • $${lead.listing_price.toLocaleString()}` : ''}
                    </div>
                </div>
                <div class="table-cell status-cell">
                    ${statusBadge}
                </div>
                <div class="table-cell score-cell">
                    <span class="score-badge" style="background-color: ${scoreColor}">
                        ${lead.lead_score || 'N/A'}
                    </span>
                </div>
                <div class="table-cell assigned-cell">
                    <div class="assigned-user">
                        ${assignedUser ? assignedUser.name : 'Unassigned'}
                    </div>
                </div>
                <div class="table-cell contact-cell">
                    <div class="last-contact">${lastContact}</div>
                    <div class="contact-attempts">${lead.contact_attempts || 0} attempts</div>
                </div>
                <div class="table-cell actions-cell">
                    <div class="action-buttons">
                        <button class="btn btn-sm btn-primary" onclick="leadManagement.viewLeadDetails('${lead.id}')">
                            <i class="fas fa-eye"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="leadManagement.quickContact('${lead.id}')">
                            <i class="fas fa-phone"></i>
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="leadManagement.editLead('${lead.id}')">
                            <i class="fas fa-edit"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    renderKanbanView() {
        const container = document.getElementById('leads-kanban');
        if (!container) return;

        const statusColumns = [
            { key: 'new', label: 'New', color: '#3b82f6' },
            { key: 'contacted', label: 'Contacted', color: '#f59e0b' },
            { key: 'interested', label: 'Interested', color: '#10b981' },
            { key: 'qualified', label: 'Qualified', color: '#8b5cf6' },
            { key: 'under_contract', label: 'Under Contract', color: '#06b6d4' },
            { key: 'closed', label: 'Closed', color: '#10b981' }
        ];

        const kanbanHTML = statusColumns.map(column => {
            const columnLeads = this.filteredLeads.filter(lead => lead.status === column.key);
            
            return `
                <div class="kanban-column" data-status="${column.key}">
                    <div class="column-header" style="border-top: 3px solid ${column.color}">
                        <h3>${column.label}</h3>
                        <span class="lead-count">${columnLeads.length}</span>
                    </div>
                    <div class="column-body">
                        ${columnLeads.map(lead => this.createKanbanCard(lead)).join('')}
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = `<div class="kanban-board">${kanbanHTML}</div>`;
        
        // Setup drag and drop
        this.setupKanbanDragDrop();
    }

    createKanbanCard(lead) {
        const scoreColor = this.getScoreColor(lead.lead_score);
        const assignedUser = this.users.find(u => u.id === lead.assigned_to);

        return `
            <div class="kanban-card" data-lead-id="${lead.id}" draggable="true">
                <div class="card-header">
                    <div class="lead-name">${lead.owner_name || 'Unknown'}</div>
                    <span class="score-badge" style="background-color: ${scoreColor}">
                        ${lead.lead_score || 'N/A'}
                    </span>
                </div>
                <div class="card-content">
                    <div class="property-address">${lead.property_address || 'Address not available'}</div>
                    ${lead.listing_price ? `<div class="property-price">$${lead.listing_price.toLocaleString()}</div>` : ''}
                    <div class="card-meta">
                        ${assignedUser ? `<span><i class="fas fa-user"></i> ${assignedUser.name}</span>` : ''}
                        ${lead.last_contact_date ? 
                            `<span><i class="fas fa-clock"></i> ${new Date(lead.last_contact_date).toLocaleDateString()}</span>` :
                            '<span><i class="fas fa-clock"></i> Never contacted</span>'
                        }
                    </div>
                </div>
                <div class="card-actions">
                    <button class="btn btn-sm btn-primary" onclick="leadManagement.viewLeadDetails('${lead.id}')">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-secondary" onclick="leadManagement.quickContact('${lead.id}')">
                        <i class="fas fa-phone"></i>
                    </button>
                </div>
            </div>
        `;
    }

    setupKanbanDragDrop() {
        const cards = document.querySelectorAll('.kanban-card');
        const columns = document.querySelectorAll('.kanban-column');

        cards.forEach(card => {
            card.addEventListener('dragstart', (e) => {
                e.dataTransfer.setData('text/plain', card.dataset.leadId);
                card.classList.add('dragging');
            });

            card.addEventListener('dragend', () => {
                card.classList.remove('dragging');
            });
        });

        columns.forEach(column => {
            column.addEventListener('dragover', (e) => {
                e.preventDefault();
                column.classList.add('drag-over');
            });

            column.addEventListener('dragleave', () => {
                column.classList.remove('drag-over');
            });

            column.addEventListener('drop', (e) => {
                e.preventDefault();
                column.classList.remove('drag-over');
                
                const leadId = e.dataTransfer.getData('text/plain');
                const newStatus = column.dataset.status;
                
                this.updateLeadStatus(leadId, newStatus);
            });
        });
    }

    attachLeadRowEventListeners() {
        // Checkbox selection
        document.querySelectorAll('.lead-checkbox').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => {
                const leadId = e.target.value;
                if (e.target.checked) {
                    this.selectedLeads.push(leadId);
                } else {
                    this.selectedLeads = this.selectedLeads.filter(id => id !== leadId);
                }
                this.updateBulkActionButtons();
            });
        });

        // Row click to view details
        document.querySelectorAll('.table-row').forEach(row => {
            row.addEventListener('click', (e) => {
                // Don't trigger on button clicks
                if (e.target.closest('button') || e.target.closest('input')) return;
                
                const leadId = row.dataset.leadId;
                this.viewLeadDetails(leadId);
            });
        });
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

    getScoreColor(score) {
        if (!score) return '#6b7280';
        if (score >= 80) return '#10b981';
        if (score >= 60) return '#f59e0b';
        if (score >= 40) return '#ef4444';
        return '#6b7280';
    }

    switchView(view) {
        // Update button states
        document.querySelectorAll('.view-toggle .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        document.getElementById(`${view}-view-btn`)?.classList.add('active');
        
        // Show/hide appropriate containers
        const listContainer = document.getElementById('leads-list-container');
        const kanbanContainer = document.getElementById('leads-kanban-container');
        
        if (view === 'kanban') {
            listContainer?.classList.add('hidden');
            kanbanContainer?.classList.remove('hidden');
        } else {
            listContainer?.classList.remove('hidden');
            kanbanContainer?.classList.add('hidden');
        }
        
        this.renderLeads();
    }

    renderPagination() {
        const container = document.getElementById('leads-pagination');
        if (!container) return;

        const totalPages = Math.ceil(this.filteredLeads.length / this.itemsPerPage);
        
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        // Similar pagination logic as in deal-finder.js
        let paginationHTML = '<div class="pagination">';
        
        // Previous button
        paginationHTML += `
            <button class="pagination-btn ${this.currentPage === 1 ? 'disabled' : ''}" 
                    ${this.currentPage === 1 ? 'disabled' : ''} 
                    onclick="leadManagement.goToPage(${this.currentPage - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
        `;

        // Page numbers (simplified for brevity)
        for (let i = 1; i <= Math.min(totalPages, 5); i++) {
            paginationHTML += `
                <button class="pagination-btn ${i === this.currentPage ? 'active' : ''}" 
                        onclick="leadManagement.goToPage(${i})">${i}</button>
            `;
        }

        // Next button
        paginationHTML += `
            <button class="pagination-btn ${this.currentPage === totalPages ? 'disabled' : ''}" 
                    ${this.currentPage === totalPages ? 'disabled' : ''} 
                    onclick="leadManagement.goToPage(${this.currentPage + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;

        paginationHTML += '</div>';
        
        // Add results info
        const startResult = (this.currentPage - 1) * this.itemsPerPage + 1;
        const endResult = Math.min(this.currentPage * this.itemsPerPage, this.filteredLeads.length);
        
        paginationHTML += `
            <div class="pagination-info">
                Showing ${startResult}-${endResult} of ${this.filteredLeads.length} leads
            </div>
        `;

        container.innerHTML = paginationHTML;
    }

    goToPage(page) {
        const totalPages = Math.ceil(this.filteredLeads.length / this.itemsPerPage);
        if (page < 1 || page > totalPages) return;
        
        this.currentPage = page;
        this.renderLeads();
    }

    updateStats() {
        const statsContainer = document.getElementById('leads-stats');
        if (!statsContainer) return;

        const total = this.filteredLeads.length;
        const newLeads = this.filteredLeads.filter(l => l.status === 'new').length;
        const contacted = this.filteredLeads.filter(l => ['contacted', 'interested', 'qualified'].includes(l.status)).length;
        const avgScore = total > 0 ? 
            this.filteredLeads.reduce((sum, l) => sum + (l.lead_score || 0), 0) / total : 0;

        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-item">
                    <div class="stat-value">${total}</div>
                    <div class="stat-label">Total Leads</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${newLeads}</div>
                    <div class="stat-label">New Leads</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${contacted}</div>
                    <div class="stat-label">In Progress</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${avgScore.toFixed(1)}</div>
                    <div class="stat-label">Avg Score</div>
                </div>
            </div>
        `;
    }

    updateBulkActionButtons() {
        const bulkActions = document.getElementById('bulk-actions');
        if (!bulkActions) return;

        if (this.selectedLeads.length > 0) {
            bulkActions.classList.remove('hidden');
            document.getElementById('selected-count').textContent = this.selectedLeads.length;
        } else {
            bulkActions.classList.add('hidden');
        }
    }

    selectAllLeads(checked) {
        const checkboxes = document.querySelectorAll('.lead-checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = checked;
        });

        if (checked) {
            this.selectedLeads = this.filteredLeads.map(lead => lead.id);
        } else {
            this.selectedLeads = [];
        }

        this.updateBulkActionButtons();
    }

    // Action methods
    async viewLeadDetails(leadId) {
        try {
            const lead = this.leads.find(l => l.id === leadId);
            if (!lead) {
                Utils.showToast('Lead not found', 'error');
                return;
            }

            this.currentLead = lead;
            this.populateLeadDetailsModal(lead);
            this.showModal('lead-details-modal');
            
        } catch (error) {
            console.error('Error viewing lead details:', error);
            Utils.showToast('Failed to load lead details', 'error');
        }
    }

    populateLeadDetailsModal(lead) {
        // Populate the lead details modal with lead information
        document.getElementById('lead-owner-name').value = lead.owner_name || '';
        document.getElementById('lead-owner-email').value = lead.owner_email || '';
        document.getElementById('lead-owner-phone').value = lead.owner_phone || '';
        document.getElementById('lead-property-address').value = lead.property_address || '';
        document.getElementById('lead-status').value = lead.status || '';
        document.getElementById('lead-assigned-to').value = lead.assigned_to || '';
        document.getElementById('lead-score').value = lead.lead_score || '';
        document.getElementById('lead-notes').value = lead.notes || '';
        
        // Load communication history
        this.loadCommunicationHistory(lead.id);
    }

    async loadCommunicationHistory(leadId) {
        try {
            const communications = await API.get(`/api/v1/leads/${leadId}/communications`);
            this.renderCommunicationHistory(communications);
        } catch (error) {
            console.error('Error loading communication history:', error);
        }
    }

    renderCommunicationHistory(communications) {
        const container = document.getElementById('communication-history');
        if (!container) return;

        if (communications.length === 0) {
            container.innerHTML = '<p class="no-communications">No communications yet</p>';
            return;
        }

        container.innerHTML = communications.map(comm => `
            <div class="communication-item">
                <div class="comm-header">
                    <span class="comm-channel">${comm.channel}</span>
                    <span class="comm-direction">${comm.direction}</span>
                    <span class="comm-date">${new Date(comm.created_at).toLocaleString()}</span>
                </div>
                <div class="comm-content">${comm.content}</div>
            </div>
        `).join('');
    }

    async updateLeadStatus(leadId, newStatus) {
        try {
            await API.patch(`/api/v1/leads/${leadId}/status`, { status: newStatus });
            
            // Update local data
            const lead = this.leads.find(l => l.id === leadId);
            if (lead) {
                lead.status = newStatus;
            }
            
            this.renderLeads();
            Utils.showToast('Lead status updated', 'success');
            
        } catch (error) {
            console.error('Error updating lead status:', error);
            Utils.showToast('Failed to update lead status', 'error');
        }
    }

    async quickContact(leadId) {
        // Implementation for quick contact functionality
        console.log('Quick contact for lead:', leadId);
        Utils.showToast('Quick contact feature coming soon', 'info');
    }

    async editLead(leadId) {
        this.viewLeadDetails(leadId);
    }

    async saveLeadDetails() {
        if (!this.currentLead) return;

        try {
            const formData = {
                owner_name: document.getElementById('lead-owner-name').value,
                owner_email: document.getElementById('lead-owner-email').value,
                owner_phone: document.getElementById('lead-owner-phone').value,
                property_address: document.getElementById('lead-property-address').value,
                status: document.getElementById('lead-status').value,
                assigned_to: document.getElementById('lead-assigned-to').value,
                lead_score: parseFloat(document.getElementById('lead-score').value) || null,
                notes: document.getElementById('lead-notes').value
            };

            await API.put(`/api/v1/leads/${this.currentLead.id}`, formData);
            
            // Update local data
            Object.assign(this.currentLead, formData);
            
            this.renderLeads();
            this.hideModal('lead-details-modal');
            Utils.showToast('Lead updated successfully', 'success');
            
        } catch (error) {
            console.error('Error saving lead:', error);
            Utils.showToast('Failed to save lead', 'error');
        }
    }

    async deleteLead(leadId) {
        if (!confirm('Are you sure you want to delete this lead?')) return;

        try {
            await API.delete(`/api/v1/leads/${leadId}`);
            
            // Remove from local data
            this.leads = this.leads.filter(l => l.id !== leadId);
            this.filteredLeads = this.filteredLeads.filter(l => l.id !== leadId);
            
            this.renderLeads();
            this.hideModal('lead-details-modal');
            Utils.showToast('Lead deleted successfully', 'success');
            
        } catch (error) {
            console.error('Error deleting lead:', error);
            Utils.showToast('Failed to delete lead', 'error');
        }
    }

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

    closeAllModals() {
        const modals = document.querySelectorAll('.modal-overlay.active');
        modals.forEach(modal => {
            modal.classList.remove('active');
        });
    }

    // Additional methods for bulk actions, communication, etc. would go here
    showBulkAssignModal() {
        this.showModal('bulk-assign-modal');
    }

    showBulkStatusModal() {
        this.showModal('bulk-status-modal');
    }

    async bulkDeleteLeads() {
        if (!confirm(`Are you sure you want to delete ${this.selectedLeads.length} leads?`)) return;

        try {
            Utils.showLoading(true, 'Deleting leads...');
            
            await Promise.all(this.selectedLeads.map(id => API.delete(`/api/v1/leads/${id}`)));
            
            // Remove from local data
            this.leads = this.leads.filter(l => !this.selectedLeads.includes(l.id));
            this.filteredLeads = this.filteredLeads.filter(l => !this.selectedLeads.includes(l.id));
            this.selectedLeads = [];
            
            this.renderLeads();
            this.updateBulkActionButtons();
            Utils.showToast('Leads deleted successfully', 'success');
            
        } catch (error) {
            console.error('Error deleting leads:', error);
            Utils.showToast('Failed to delete leads', 'error');
        } finally {
            Utils.showLoading(false);
        }
    }

    createNewLead() {
        // Implementation for creating new lead
        console.log('Create new lead');
        Utils.showToast('Create new lead feature coming soon', 'info');
    }

    showEmailModal() {
        this.showModal('email-modal');
    }

    showSMSModal() {
        this.showModal('sms-modal');
    }

    initiateCall() {
        Utils.showToast('Call feature coming soon', 'info');
    }

    scheduleFollowup() {
        Utils.showToast('Schedule followup feature coming soon', 'info');
    }
}

// Initialize lead management when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('lead-management-container')) {
        window.leadManagement = new LeadManagement();
    }
});