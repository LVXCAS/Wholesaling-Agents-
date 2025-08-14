/**
 * Scheduling Interface JavaScript
 * Handles calendar view, appointments, follow-ups, and reminders
 */

class SchedulingManager {
    constructor() {
        this.calendar = null;
        this.appointments = [];
        this.followUps = [];
        this.reminderRules = [];
        this.reminderHistory = [];
        this.currentView = 'dayGridMonth';
        this.filters = {
            appointments: true,
            'follow-ups': true,
            reminders: true,
            campaigns: true
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.initCalendar();
        this.loadAppointments();
        this.loadFollowUps();
        this.loadReminderRules();
        this.loadReminderHistory();
    }

    bindEvents() {
        // Tab switching
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e));
        });

        // Header actions
        document.getElementById('sync-calendar')?.addEventListener('click', () => this.syncCalendar());
        document.getElementById('schedule-appointment')?.addEventListener('click', () => this.showAppointmentModal());

        // Calendar controls
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.changeCalendarView(e));
        });
        document.getElementById('today-btn')?.addEventListener('click', () => this.goToToday());

        // Calendar filters
        document.querySelectorAll('input[data-filter]').forEach(checkbox => {
            checkbox.addEventListener('change', (e) => this.updateCalendarFilters(e));
        });

        // Appointment filters
        document.getElementById('appointment-status-filter')?.addEventListener('change', () => this.filterAppointments());
        document.getElementById('appointment-type-filter')?.addEventListener('change', () => this.filterAppointments());
        document.getElementById('appointment-search')?.addEventListener('input', () => this.filterAppointments());

        // Follow-up controls
        document.getElementById('create-follow-up')?.addEventListener('click', () => this.showFollowUpModal());
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.filterFollowUps(e));
        });
        document.getElementById('follow-up-sort')?.addEventListener('change', () => this.sortFollowUps());

        // Reminder controls
        document.getElementById('create-reminder-rule')?.addEventListener('click', () => this.showReminderRuleModal());

        // Modal controls
        this.bindModalEvents();
    }

    bindModalEvents() {
        // Appointment modal
        document.getElementById('close-appointment-modal')?.addEventListener('click', () => this.closeAppointmentModal());
        document.getElementById('cancel-appointment')?.addEventListener('click', () => this.closeAppointmentModal());
        document.getElementById('save-appointment')?.addEventListener('click', () => this.saveAppointment());

        // Follow-up modal
        document.getElementById('close-follow-up-modal')?.addEventListener('click', () => this.closeFollowUpModal());
        document.getElementById('cancel-follow-up')?.addEventListener('click', () => this.closeFollowUpModal());
        document.getElementById('save-follow-up')?.addEventListener('click', () => this.saveFollowUp());

        // Auto follow-up toggle
        document.getElementById('auto-follow-up-enabled')?.addEventListener('change', (e) => {
            const details = document.getElementById('auto-follow-up-details');
            if (details) {
                details.style.display = e.target.checked ? 'block' : 'none';
            }
        });

        // Reminder rule modal
        document.getElementById('close-reminder-rule-modal')?.addEventListener('click', () => this.closeReminderRuleModal());
        document.getElementById('cancel-reminder-rule')?.addEventListener('click', () => this.closeReminderRuleModal());
        document.getElementById('save-reminder-rule')?.addEventListener('click', () => this.saveReminderRule());
    }

    initCalendar() {
        const calendarEl = document.getElementById('calendar');
        if (!calendarEl) return;

        this.calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: this.currentView,
            headerToolbar: {
                left: 'prev,next',
                center: 'title',
                right: ''
            },
            height: 'auto',
            events: [],
            eventClick: (info) => this.handleEventClick(info),
            dateClick: (info) => this.handleDateClick(info),
            eventDidMount: (info) => this.styleEvent(info),
            dayMaxEvents: 3,
            moreLinkClick: 'popover'
        });

        this.calendar.render();
    }

    async loadAppointments() {
        try {
            showLoading();
            const response = await fetch('/api/appointments');
            if (response.ok) {
                this.appointments = await response.json();
                this.renderAppointments();
                this.updateCalendarEvents();
                this.updateUpcomingEvents();
            } else {
                throw new Error('Failed to load appointments');
            }
        } catch (error) {
            console.error('Error loading appointments:', error);
            showNotification('Failed to load appointments', 'error');
        } finally {
            hideLoading();
        }
    }

    async loadFollowUps() {
        try {
            const response = await fetch('/api/follow-ups');
            if (response.ok) {
                this.followUps = await response.json();
                this.renderFollowUps();
                this.updateFollowUpStats();
                this.updateCalendarEvents();
            } else {
                throw new Error('Failed to load follow-ups');
            }
        } catch (error) {
            console.error('Error loading follow-ups:', error);
            showNotification('Failed to load follow-ups', 'error');
        }
    }

    async loadReminderRules() {
        try {
            const response = await fetch('/api/reminder-rules');
            if (response.ok) {
                this.reminderRules = await response.json();
                this.renderReminderRules();
            }
        } catch (error) {
            console.error('Error loading reminder rules:', error);
        }
    }

    async loadReminderHistory() {
        try {
            const response = await fetch('/api/reminder-history');
            if (response.ok) {
                this.reminderHistory = await response.json();
                this.renderReminderHistory();
            }
        } catch (error) {
            console.error('Error loading reminder history:', error);
        }
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
        if (tabName === 'appointments') {
            this.loadAppointments();
        } else if (tabName === 'follow-ups') {
            this.loadFollowUps();
        } else if (tabName === 'reminders') {
            this.loadReminderRules();
            this.loadReminderHistory();
        }
    }

    changeCalendarView(event) {
        const view = event.currentTarget.dataset.view;
        this.currentView = view;
        
        // Update active button
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Change calendar view
        if (this.calendar) {
            this.calendar.changeView(view);
        }
    }

    goToToday() {
        if (this.calendar) {
            this.calendar.today();
        }
    }

    updateCalendarFilters(event) {
        const filter = event.target.dataset.filter;
        this.filters[filter] = event.target.checked;
        this.updateCalendarEvents();
    }

    updateCalendarEvents() {
        if (!this.calendar) return;

        const events = [];

        // Add appointments
        if (this.filters.appointments) {
            this.appointments.forEach(appointment => {
                events.push({
                    id: `appointment-${appointment.id}`,
                    title: appointment.title,
                    start: appointment.datetime,
                    end: appointment.end_datetime,
                    className: 'appointments',
                    extendedProps: {
                        type: 'appointment',
                        data: appointment
                    }
                });
            });
        }

        // Add follow-ups
        if (this.filters['follow-ups']) {
            this.followUps.forEach(followUp => {
                events.push({
                    id: `follow-up-${followUp.id}`,
                    title: followUp.title,
                    start: followUp.due_datetime,
                    allDay: !followUp.due_time,
                    className: 'follow-ups',
                    extendedProps: {
                        type: 'follow-up',
                        data: followUp
                    }
                });
            });
        }

        // Update calendar
        this.calendar.removeAllEvents();
        this.calendar.addEventSource(events);
    }

    updateUpcomingEvents() {
        const container = document.getElementById('upcoming-events-list');
        if (!container) return;

        const now = new Date();
        const nextWeek = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);

        const upcomingEvents = [
            ...this.appointments.filter(apt => {
                const date = new Date(apt.datetime);
                return date >= now && date <= nextWeek;
            }).map(apt => ({
                ...apt,
                type: 'appointment',
                datetime: apt.datetime
            })),
            ...this.followUps.filter(fu => {
                const date = new Date(fu.due_datetime);
                return date >= now && date <= nextWeek;
            }).map(fu => ({
                ...fu,
                type: 'follow-up',
                datetime: fu.due_datetime
            }))
        ].sort((a, b) => new Date(a.datetime) - new Date(b.datetime));

        if (upcomingEvents.length === 0) {
            container.innerHTML = '<p class="text-secondary">No upcoming events</p>';
            return;
        }

        container.innerHTML = upcomingEvents.slice(0, 5).map(event => `
            <div class="event-item" data-event-id="${event.id}" data-event-type="${event.type}">
                <div class="event-title">${escapeHtml(event.title)}</div>
                <div class="event-time">${formatDateTime(event.datetime)}</div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.event-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const eventId = e.currentTarget.dataset.eventId;
                const eventType = e.currentTarget.dataset.eventType;
                this.viewEvent(eventId, eventType);
            });
        });
    }

    renderAppointments() {
        const container = document.getElementById('appointments-list');
        if (!container) return;

        if (this.appointments.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-handshake"></i>
                    <h3>No appointments scheduled</h3>
                    <p>Schedule your first appointment to see it here</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.appointments.map(appointment => `
            <div class="appointment-card" data-appointment-id="${appointment.id}">
                <div class="appointment-header">
                    <div>
                        <div class="appointment-title">${escapeHtml(appointment.title)}</div>
                        <div class="appointment-type">${appointment.type.replace('_', ' ')}</div>
                    </div>
                    <div class="appointment-status ${appointment.status}">${appointment.status}</div>
                </div>
                <div class="appointment-details">
                    <div class="appointment-detail">
                        <i class="fas fa-calendar"></i>
                        <span>${formatDateTime(appointment.datetime)}</span>
                    </div>
                    <div class="appointment-detail">
                        <i class="fas fa-clock"></i>
                        <span>${appointment.duration} minutes</span>
                    </div>
                    ${appointment.contact_name ? `
                        <div class="appointment-detail">
                            <i class="fas fa-user"></i>
                            <span>${escapeHtml(appointment.contact_name)}</span>
                        </div>
                    ` : ''}
                    ${appointment.location ? `
                        <div class="appointment-detail">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${escapeHtml(appointment.location)}</span>
                        </div>
                    ` : ''}
                </div>
                <div class="appointment-actions">
                    <div class="appointment-meta">
                        Created ${formatDate(appointment.created_at)}
                    </div>
                    <div class="appointment-controls">
                        <button class="control-btn" onclick="schedulingManager.editAppointment('${appointment.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="control-btn" onclick="schedulingManager.rescheduleAppointment('${appointment.id}')">
                            <i class="fas fa-calendar-alt"></i> Reschedule
                        </button>
                        <button class="control-btn" onclick="schedulingManager.cancelAppointment('${appointment.id}')">
                            <i class="fas fa-times"></i> Cancel
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    renderFollowUps() {
        const container = document.getElementById('follow-ups-list');
        if (!container) return;

        if (this.followUps.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-tasks"></i>
                    <h3>No follow-ups scheduled</h3>
                    <p>Create your first follow-up to see it here</p>
                </div>
            `;
            return;
        }

        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());

        container.innerHTML = this.followUps.map(followUp => {
            const dueDate = new Date(followUp.due_datetime);
            const isOverdue = dueDate < now;
            const isDueToday = dueDate >= today && dueDate < new Date(today.getTime() + 24 * 60 * 60 * 1000);
            
            let cardClass = 'follow-up-card';
            if (isOverdue) cardClass += ' overdue';
            else if (isDueToday) cardClass += ' due-today';

            return `
                <div class="${cardClass}" data-follow-up-id="${followUp.id}">
                    <div class="follow-up-header">
                        <div>
                            <div class="follow-up-title">${escapeHtml(followUp.title)}</div>
                            <div class="follow-up-contact">${escapeHtml(followUp.contact_name || 'No contact')}</div>
                        </div>
                        <div class="follow-up-priority ${followUp.priority}">${followUp.priority}</div>
                    </div>
                    <div class="follow-up-details">
                        ${followUp.description ? `
                            <div class="follow-up-description">${escapeHtml(followUp.description)}</div>
                        ` : ''}
                        <div class="follow-up-meta">
                            <span><i class="fas fa-${this.getFollowUpTypeIcon(followUp.type)}"></i> ${followUp.type}</span>
                            <span><i class="fas fa-calendar"></i> Created ${formatDate(followUp.created_at)}</span>
                        </div>
                    </div>
                    <div class="follow-up-actions">
                        <div class="follow-up-due ${isOverdue ? 'overdue' : isDueToday ? 'due-today' : ''}">
                            Due: ${formatDateTime(followUp.due_datetime)}
                            ${isOverdue ? ' (Overdue)' : isDueToday ? ' (Today)' : ''}
                        </div>
                        <div class="follow-up-controls">
                            <button class="control-btn" onclick="schedulingManager.completeFollowUp('${followUp.id}')">
                                <i class="fas fa-check"></i> Complete
                            </button>
                            <button class="control-btn" onclick="schedulingManager.editFollowUp('${followUp.id}')">
                                <i class="fas fa-edit"></i> Edit
                            </button>
                            <button class="control-btn" onclick="schedulingManager.snoozeFollowUp('${followUp.id}')">
                                <i class="fas fa-clock"></i> Snooze
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    updateFollowUpStats() {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const weekFromNow = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);

        const stats = {
            overdue: this.followUps.filter(fu => new Date(fu.due_datetime) < now && fu.status !== 'completed').length,
            today: this.followUps.filter(fu => {
                const due = new Date(fu.due_datetime);
                return due >= today && due < new Date(today.getTime() + 24 * 60 * 60 * 1000) && fu.status !== 'completed';
            }).length,
            week: this.followUps.filter(fu => {
                const due = new Date(fu.due_datetime);
                return due >= today && due <= weekFromNow && fu.status !== 'completed';
            }).length,
            completed: this.followUps.filter(fu => fu.status === 'completed').length
        };

        document.getElementById('overdue-count').textContent = stats.overdue;
        document.getElementById('today-count').textContent = stats.today;
        document.getElementById('week-count').textContent = stats.week;
        document.getElementById('completed-count').textContent = stats.completed;
    }

    renderReminderRules() {
        const appointmentRules = document.getElementById('appointment-reminder-rules');
        const followUpRules = document.getElementById('follow-up-reminder-rules');
        const campaignRules = document.getElementById('campaign-reminder-rules');

        if (!appointmentRules || !followUpRules || !campaignRules) return;

        const rulesByType = {
            appointment: this.reminderRules.filter(rule => rule.trigger.includes('appointment')),
            followUp: this.reminderRules.filter(rule => rule.trigger.includes('follow-up')),
            campaign: this.reminderRules.filter(rule => rule.trigger.includes('campaign'))
        };

        [appointmentRules, followUpRules, campaignRules].forEach((container, index) => {
            const type = ['appointment', 'followUp', 'campaign'][index];
            const rules = rulesByType[type];

            if (rules.length === 0) {
                container.innerHTML = '<p class="text-secondary">No reminder rules configured</p>';
                return;
            }

            container.innerHTML = rules.map(rule => `
                <div class="rule-card">
                    <div class="rule-header">
                        <div>
                            <div class="rule-name">${escapeHtml(rule.name)}</div>
                            <div class="rule-trigger">${rule.trigger.replace('_', ' ')}</div>
                        </div>
                        <div class="rule-status ${rule.active ? 'active' : 'inactive'}">
                            ${rule.active ? 'Active' : 'Inactive'}
                        </div>
                    </div>
                    <div class="rule-details">
                        <div class="rule-timing">
                            <i class="fas fa-clock"></i>
                            <span>${rule.timing.replace('_', ' ')}</span>
                        </div>
                        <div class="rule-channels">
                            <i class="fas fa-paper-plane"></i>
                            <span>${rule.channels.join(', ').toUpperCase()}</span>
                        </div>
                    </div>
                    <div class="rule-actions">
                        <button class="control-btn" onclick="schedulingManager.editReminderRule('${rule.id}')">
                            <i class="fas fa-edit"></i> Edit
                        </button>
                        <button class="control-btn" onclick="schedulingManager.toggleReminderRule('${rule.id}')">
                            <i class="fas fa-${rule.active ? 'pause' : 'play'}"></i>
                            ${rule.active ? 'Disable' : 'Enable'}
                        </button>
                        <button class="control-btn" onclick="schedulingManager.deleteReminderRule('${rule.id}')">
                            <i class="fas fa-trash"></i> Delete
                        </button>
                    </div>
                </div>
            `).join('');
        });
    }

    renderReminderHistory() {
        const container = document.getElementById('reminder-history-list');
        if (!container) return;

        if (this.reminderHistory.length === 0) {
            container.innerHTML = '<p class="text-secondary">No recent reminders</p>';
            return;
        }

        container.innerHTML = this.reminderHistory.slice(0, 10).map(reminder => `
            <div class="history-item">
                <div class="history-content">
                    <div class="history-title">${escapeHtml(reminder.title)}</div>
                    <div class="history-details">
                        ${reminder.channel.toUpperCase()} • ${escapeHtml(reminder.recipient)}
                    </div>
                </div>
                <div class="history-time">${formatRelativeTime(reminder.sent_at)}</div>
            </div>
        `).join('');
    }

    // Modal functions
    showAppointmentModal(appointment = null) {
        const modal = document.getElementById('appointment-modal');
        const title = document.getElementById('appointment-modal-title');
        
        if (!modal || !title) return;

        title.textContent = appointment ? 'Edit Appointment' : 'Schedule Appointment';
        
        if (appointment) {
            // Populate form with appointment data
            document.getElementById('appointment-title').value = appointment.title || '';
            document.getElementById('appointment-type').value = appointment.type || '';
            document.getElementById('appointment-contact').value = appointment.contact_id || '';
            document.getElementById('appointment-property').value = appointment.property_id || '';
            document.getElementById('appointment-date').value = appointment.date || '';
            document.getElementById('appointment-time').value = appointment.time || '';
            document.getElementById('appointment-duration').value = appointment.duration || '60';
            document.getElementById('appointment-location').value = appointment.location || '';
            document.getElementById('appointment-description').value = appointment.description || '';
            document.getElementById('appointment-priority').value = appointment.priority || 'normal';
        } else {
            // Clear form
            document.getElementById('appointment-form').reset();
        }

        modal.classList.add('active');
    }

    closeAppointmentModal() {
        document.getElementById('appointment-modal')?.classList.remove('active');
    }

    async saveAppointment() {
        const formData = {
            title: document.getElementById('appointment-title').value,
            type: document.getElementById('appointment-type').value,
            contact_id: document.getElementById('appointment-contact').value,
            property_id: document.getElementById('appointment-property').value,
            date: document.getElementById('appointment-date').value,
            time: document.getElementById('appointment-time').value,
            duration: parseInt(document.getElementById('appointment-duration').value),
            location: document.getElementById('appointment-location').value,
            description: document.getElementById('appointment-description').value,
            priority: document.getElementById('appointment-priority').value,
            reminders: []
        };

        // Get selected reminders
        document.querySelectorAll('input[id^="reminder-"]:checked').forEach(checkbox => {
            formData.reminders.push(checkbox.value);
        });

        // Validate required fields
        if (!formData.title || !formData.type || !formData.date || !formData.time) {
            showNotification('Please fill in all required fields', 'warning');
            return;
        }

        try {
            showLoading();
            const response = await fetch('/api/appointments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                showNotification('Appointment scheduled successfully', 'success');
                this.closeAppointmentModal();
                this.loadAppointments();
            } else {
                throw new Error('Failed to save appointment');
            }
        } catch (error) {
            console.error('Error saving appointment:', error);
            showNotification('Failed to save appointment', 'error');
        } finally {
            hideLoading();
        }
    }

    showFollowUpModal(followUp = null) {
        const modal = document.getElementById('follow-up-modal');
        const title = document.getElementById('follow-up-modal-title');
        
        if (!modal || !title) return;

        title.textContent = followUp ? 'Edit Follow-up' : 'Create Follow-up';
        
        if (followUp) {
            // Populate form with follow-up data
            document.getElementById('follow-up-title').value = followUp.title || '';
            document.getElementById('follow-up-contact').value = followUp.contact_id || '';
            document.getElementById('follow-up-type').value = followUp.type || 'call';
            document.getElementById('follow-up-due-date').value = followUp.due_date || '';
            document.getElementById('follow-up-due-time').value = followUp.due_time || '';
            document.getElementById('follow-up-priority').value = followUp.priority || 'normal';
            document.getElementById('follow-up-description').value = followUp.description || '';
        } else {
            // Clear form
            document.getElementById('follow-up-form').reset();
        }

        modal.classList.add('active');
    }

    closeFollowUpModal() {
        document.getElementById('follow-up-modal')?.classList.remove('active');
    }

    async saveFollowUp() {
        const formData = {
            title: document.getElementById('follow-up-title').value,
            contact_id: document.getElementById('follow-up-contact').value,
            type: document.getElementById('follow-up-type').value,
            due_date: document.getElementById('follow-up-due-date').value,
            due_time: document.getElementById('follow-up-due-time').value,
            priority: document.getElementById('follow-up-priority').value,
            description: document.getElementById('follow-up-description').value,
            auto_follow_up: {
                enabled: document.getElementById('auto-follow-up-enabled').checked,
                days: document.getElementById('auto-follow-up-days').value,
                type: document.getElementById('auto-follow-up-type').value
            }
        };

        // Validate required fields
        if (!formData.title || !formData.contact_id || !formData.due_date) {
            showNotification('Please fill in all required fields', 'warning');
            return;
        }

        try {
            showLoading();
            const response = await fetch('/api/follow-ups', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                showNotification('Follow-up created successfully', 'success');
                this.closeFollowUpModal();
                this.loadFollowUps();
            } else {
                throw new Error('Failed to save follow-up');
            }
        } catch (error) {
            console.error('Error saving follow-up:', error);
            showNotification('Failed to save follow-up', 'error');
        } finally {
            hideLoading();
        }
    }

    showReminderRuleModal(rule = null) {
        const modal = document.getElementById('reminder-rule-modal');
        if (!modal) return;

        if (rule) {
            // Populate form with rule data
            document.getElementById('rule-name').value = rule.name || '';
            document.getElementById('rule-trigger').value = rule.trigger || '';
            document.getElementById('rule-timing').value = rule.timing || '';
            document.getElementById('rule-message').value = rule.message || '';
            document.getElementById('rule-active').checked = rule.active !== false;
            
            // Set channels
            rule.channels?.forEach(channel => {
                const checkbox = document.getElementById(`rule-${channel}`);
                if (checkbox) checkbox.checked = true;
            });
        } else {
            // Clear form
            document.getElementById('reminder-rule-form').reset();
        }

        modal.classList.add('active');
    }

    closeReminderRuleModal() {
        document.getElementById('reminder-rule-modal')?.classList.remove('active');
    }

    async saveReminderRule() {
        const formData = {
            name: document.getElementById('rule-name').value,
            trigger: document.getElementById('rule-trigger').value,
            timing: document.getElementById('rule-timing').value,
            message: document.getElementById('rule-message').value,
            active: document.getElementById('rule-active').checked,
            channels: []
        };

        // Get selected channels
        document.querySelectorAll('input[id^="rule-"]:checked').forEach(checkbox => {
            if (checkbox.value) {
                formData.channels.push(checkbox.value);
            }
        });

        // Validate required fields
        if (!formData.name || !formData.trigger) {
            showNotification('Please fill in all required fields', 'warning');
            return;
        }

        try {
            showLoading();
            const response = await fetch('/api/reminder-rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                showNotification('Reminder rule created successfully', 'success');
                this.closeReminderRuleModal();
                this.loadReminderRules();
            } else {
                throw new Error('Failed to save reminder rule');
            }
        } catch (error) {
            console.error('Error saving reminder rule:', error);
            showNotification('Failed to save reminder rule', 'error');
        } finally {
            hideLoading();
        }
    }

    // Event handlers
    handleEventClick(info) {
        const eventType = info.event.extendedProps.type;
        const eventData = info.event.extendedProps.data;
        
        if (eventType === 'appointment') {
            this.showAppointmentModal(eventData);
        } else if (eventType === 'follow-up') {
            this.showFollowUpModal(eventData);
        }
    }

    handleDateClick(info) {
        // Pre-fill appointment form with clicked date
        document.getElementById('appointment-date').value = info.dateStr;
        this.showAppointmentModal();
    }

    styleEvent(info) {
        // Additional event styling can be added here
    }

    // Utility functions
    getFollowUpTypeIcon(type) {
        const icons = {
            call: 'phone',
            email: 'envelope',
            sms: 'sms',
            meeting: 'handshake',
            task: 'tasks'
        };
        return icons[type] || 'tasks';
    }

    filterAppointments() {
        // Implementation for filtering appointments
        this.renderAppointments();
    }

    filterFollowUps(event) {
        const filter = event.currentTarget.dataset.filter;
        
        // Update active tab
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Filter and render follow-ups
        this.renderFollowUps();
    }

    sortFollowUps() {
        // Implementation for sorting follow-ups
        this.renderFollowUps();
    }

    async syncCalendar() {
        try {
            showLoading();
            const response = await fetch('/api/calendar/sync', { method: 'POST' });
            if (response.ok) {
                showNotification('Calendar synced successfully', 'success');
                this.loadAppointments();
            } else {
                throw new Error('Failed to sync calendar');
            }
        } catch (error) {
            console.error('Error syncing calendar:', error);
            showNotification('Failed to sync calendar', 'error');
        } finally {
            hideLoading();
        }
    }

    // Action functions (placeholders)
    editAppointment(appointmentId) {
        const appointment = this.appointments.find(a => a.id === appointmentId);
        if (appointment) {
            this.showAppointmentModal(appointment);
        }
    }

    rescheduleAppointment(appointmentId) {
        showNotification('Reschedule functionality coming soon', 'info');
    }

    cancelAppointment(appointmentId) {
        showNotification('Cancel appointment functionality coming soon', 'info');
    }

    completeFollowUp(followUpId) {
        showNotification('Complete follow-up functionality coming soon', 'info');
    }

    editFollowUp(followUpId) {
        const followUp = this.followUps.find(f => f.id === followUpId);
        if (followUp) {
            this.showFollowUpModal(followUp);
        }
    }

    snoozeFollowUp(followUpId) {
        showNotification('Snooze follow-up functionality coming soon', 'info');
    }

    editReminderRule(ruleId) {
        const rule = this.reminderRules.find(r => r.id === ruleId);
        if (rule) {
            this.showReminderRuleModal(rule);
        }
    }

    toggleReminderRule(ruleId) {
        showNotification('Toggle reminder rule functionality coming soon', 'info');
    }

    deleteReminderRule(ruleId) {
        showNotification('Delete reminder rule functionality coming soon', 'info');
    }

    viewEvent(eventId, eventType) {
        if (eventType === 'appointment') {
            this.editAppointment(eventId);
        } else if (eventType === 'follow-up') {
            this.editFollowUp(eventId);
        }
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

function formatRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
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
let schedulingManager;
document.addEventListener('DOMContentLoaded', () => {
    schedulingManager = new SchedulingManager();
});