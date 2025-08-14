/**
 * Communication Center JavaScript
 * Handles unified inbox, conversation view, and message composition
 */

class CommunicationCenter {
    constructor() {
        this.currentConversation = null;
        this.currentChannel = 'email';
        this.conversations = [];
        this.templates = {
            email: [],
            sms: [],
            voice: []
        };
        this.filters = {
            status: 'all',
            channel: null,
            search: ''
        };
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadConversations();
        this.loadTemplates();
        this.updateCounts();
        this.setupChannelSwitching();
    }

    bindEvents() {
        // Navigation events
        document.querySelectorAll('.nav-item[data-filter]').forEach(item => {
            item.addEventListener('click', (e) => this.handleFilterChange(e));
        });

        document.querySelectorAll('.nav-item[data-channel]').forEach(item => {
            item.addEventListener('click', (e) => this.handleChannelFilter(e));
        });

        // Header actions
        document.getElementById('refresh-inbox')?.addEventListener('click', () => this.refreshInbox());
        document.getElementById('compose-message')?.addEventListener('click', () => this.composeNewMessage());

        // Search and filters
        document.getElementById('conversation-search')?.addEventListener('input', (e) => this.handleSearch(e));
        document.getElementById('sort-filter')?.addEventListener('change', (e) => this.handleSort(e));

        // Conversation actions
        document.getElementById('mark-important')?.addEventListener('click', () => this.toggleImportant());
        document.getElementById('schedule-followup')?.addEventListener('click', () => this.scheduleFollowup());
        document.getElementById('conversation-settings')?.addEventListener('click', () => this.showConversationSettings());

        // Message composer
        document.querySelectorAll('.channel-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.switchChannel(e));
        });

        document.getElementById('use-template')?.addEventListener('click', () => this.showTemplateSelector());
        document.getElementById('schedule-send')?.addEventListener('click', () => this.scheduleSend());
        document.getElementById('send-message')?.addEventListener('click', () => this.sendMessage());
        document.getElementById('save-draft')?.addEventListener('click', () => this.saveDraft());

        // Template management
        document.getElementById('manage-templates')?.addEventListener('click', () => this.showTemplateManager());
        document.getElementById('close-template-modal')?.addEventListener('click', () => this.closeTemplateManager());

        // Character count for SMS
        document.getElementById('sms-message')?.addEventListener('input', (e) => this.updateCharacterCount(e));

        // AI assist
        document.getElementById('ai-assist')?.addEventListener('click', () => this.showAIAssist());
    }

    async loadConversations() {
        try {
            showLoading();
            const response = await fetch('/api/communication/conversations');
            if (response.ok) {
                this.conversations = await response.json();
                this.renderConversations();
                this.updateCounts();
            } else {
                throw new Error('Failed to load conversations');
            }
        } catch (error) {
            console.error('Error loading conversations:', error);
            showNotification('Failed to load conversations', 'error');
        } finally {
            hideLoading();
        }
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/communication/templates');
            if (response.ok) {
                const templates = await response.json();
                this.templates = {
                    email: templates.filter(t => t.type === 'email'),
                    sms: templates.filter(t => t.type === 'sms'),
                    voice: templates.filter(t => t.type === 'voice')
                };
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }

    renderConversations() {
        const container = document.getElementById('conversation-items');
        if (!container) return;

        // Apply filters
        let filteredConversations = this.conversations.filter(conv => {
            if (this.filters.status !== 'all' && conv.status !== this.filters.status) {
                return false;
            }
            if (this.filters.channel && !conv.channels.includes(this.filters.channel)) {
                return false;
            }
            if (this.filters.search) {
                const searchTerm = this.filters.search.toLowerCase();
                return conv.contact_name.toLowerCase().includes(searchTerm) ||
                       conv.last_message.toLowerCase().includes(searchTerm);
            }
            return true;
        });

        // Sort conversations
        const sortBy = document.getElementById('sort-filter')?.value || 'recent';
        filteredConversations.sort((a, b) => {
            switch (sortBy) {
                case 'unread':
                    if (a.unread_count !== b.unread_count) {
                        return b.unread_count - a.unread_count;
                    }
                    return new Date(b.last_message_time) - new Date(a.last_message_time);
                case 'priority':
                    if (a.priority !== b.priority) {
                        return b.priority - a.priority;
                    }
                    return new Date(b.last_message_time) - new Date(a.last_message_time);
                default:
                    return new Date(b.last_message_time) - new Date(a.last_message_time);
            }
        });

        if (filteredConversations.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <h3>No conversations found</h3>
                    <p>Try adjusting your filters or start a new conversation</p>
                </div>
            `;
            return;
        }

        container.innerHTML = filteredConversations.map(conv => `
            <div class="conversation-item ${conv.unread_count > 0 ? 'unread' : ''} ${this.currentConversation?.id === conv.id ? 'active' : ''}" 
                 data-conversation-id="${conv.id}">
                <div class="conversation-header-info">
                    <div class="conversation-name">${escapeHtml(conv.contact_name)}</div>
                    <div class="conversation-time">${formatRelativeTime(conv.last_message_time)}</div>
                </div>
                <div class="conversation-preview">${escapeHtml(conv.last_message)}</div>
                <div class="conversation-meta">
                    <div class="conversation-channels">
                        ${conv.channels.map(channel => `
                            <div class="channel-indicator ${channel}">
                                <i class="fas fa-${this.getChannelIcon(channel)}"></i>
                            </div>
                        `).join('')}
                    </div>
                    <div class="conversation-status">
                        ${conv.priority > 1 ? '<span class="status-badge high-priority">High Priority</span>' : ''}
                        ${conv.last_reply_time ? '<span class="status-badge replied">Replied</span>' : ''}
                    </div>
                </div>
            </div>
        `).join('');

        // Add click handlers
        container.querySelectorAll('.conversation-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const conversationId = e.currentTarget.dataset.conversationId;
                this.selectConversation(conversationId);
            });
        });
    }

    async selectConversation(conversationId) {
        try {
            showLoading();
            const response = await fetch(`/api/communication/conversations/${conversationId}`);
            if (response.ok) {
                this.currentConversation = await response.json();
                this.renderConversationView();
                this.markAsRead(conversationId);
                
                // Update active state
                document.querySelectorAll('.conversation-item').forEach(item => {
                    item.classList.remove('active');
                });
                document.querySelector(`[data-conversation-id="${conversationId}"]`)?.classList.add('active');
            }
        } catch (error) {
            console.error('Error loading conversation:', error);
            showNotification('Failed to load conversation', 'error');
        } finally {
            hideLoading();
        }
    }

    renderConversationView() {
        if (!this.currentConversation) return;

        const conversationView = document.getElementById('conversation-view');
        if (!conversationView) return;

        conversationView.style.display = 'flex';

        // Update contact info
        document.getElementById('contact-name').textContent = this.currentConversation.contact_name;
        document.getElementById('contact-info').textContent = 
            `${this.currentConversation.contact_email || ''} • ${this.currentConversation.contact_phone || ''}`;

        // Update contact tags
        const tagsContainer = document.getElementById('contact-tags');
        tagsContainer.innerHTML = this.currentConversation.tags.map(tag => 
            `<span class="contact-tag">${escapeHtml(tag)}</span>`
        ).join('');

        // Render messages
        this.renderMessages();
    }

    renderMessages() {
        const container = document.getElementById('messages-container');
        if (!container || !this.currentConversation) return;

        container.innerHTML = this.currentConversation.messages.map(message => `
            <div class="message ${message.direction}">
                <div class="message-avatar">
                    <i class="fas fa-${message.direction === 'outbound' ? 'user-tie' : 'user'}"></i>
                </div>
                <div class="message-content">
                    <div class="message-bubble">
                        <div class="message-header">
                            <div class="message-channel">
                                <i class="fas fa-${this.getChannelIcon(message.channel)}"></i>
                                <span>${message.channel.toUpperCase()}</span>
                            </div>
                            <div class="message-time">${formatDateTime(message.timestamp)}</div>
                        </div>
                        ${message.subject ? `<div class="message-subject">${escapeHtml(message.subject)}</div>` : ''}
                        <div class="message-body">${escapeHtml(message.content)}</div>
                        ${message.direction === 'outbound' ? `
                            <div class="message-status">
                                <i class="fas fa-${this.getStatusIcon(message.status)}"></i>
                                <span>${message.status}</span>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `).join('');

        // Scroll to bottom
        container.scrollTop = container.scrollHeight;
    }

    setupChannelSwitching() {
        const channelBtns = document.querySelectorAll('.channel-btn');
        const composers = {
            email: document.getElementById('email-composer'),
            sms: document.getElementById('sms-composer'),
            voice: document.getElementById('voice-composer')
        };

        channelBtns.forEach(btn => {
            btn.addEventListener('click', () => {
                const channel = btn.dataset.channel;
                
                // Update active button
                channelBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                // Show appropriate composer
                Object.values(composers).forEach(composer => {
                    if (composer) composer.style.display = 'none';
                });
                if (composers[channel]) {
                    composers[channel].style.display = 'block';
                }
                
                this.currentChannel = channel;
            });
        });
    }

    switchChannel(event) {
        const channel = event.currentTarget.dataset.channel;
        this.currentChannel = channel;
        
        // Update UI to show appropriate composer
        document.querySelectorAll('.channel-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        // Show/hide composers
        document.getElementById('email-composer').style.display = channel === 'email' ? 'block' : 'none';
        document.getElementById('sms-composer').style.display = channel === 'sms' ? 'block' : 'none';
        document.getElementById('voice-composer').style.display = channel === 'voice' ? 'block' : 'none';
    }

    async sendMessage() {
        if (!this.currentConversation) {
            showNotification('Please select a conversation first', 'warning');
            return;
        }

        const messageData = this.getMessageData();
        if (!messageData) return;

        try {
            showLoading();
            const response = await fetch('/api/communication/send', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    conversation_id: this.currentConversation.id,
                    channel: this.currentChannel,
                    ...messageData
                })
            });

            if (response.ok) {
                const result = await response.json();
                showNotification('Message sent successfully', 'success');
                this.clearComposer();
                this.refreshConversation();
            } else {
                throw new Error('Failed to send message');
            }
        } catch (error) {
            console.error('Error sending message:', error);
            showNotification('Failed to send message', 'error');
        } finally {
            hideLoading();
        }
    }

    getMessageData() {
        switch (this.currentChannel) {
            case 'email':
                const subject = document.getElementById('email-subject')?.value;
                const emailMessage = document.getElementById('email-message')?.value;
                if (!subject || !emailMessage) {
                    showNotification('Please fill in subject and message', 'warning');
                    return null;
                }
                return { subject, content: emailMessage };
                
            case 'sms':
                const smsMessage = document.getElementById('sms-message')?.value;
                if (!smsMessage) {
                    showNotification('Please enter SMS message', 'warning');
                    return null;
                }
                return { content: smsMessage };
                
            case 'voice':
                const voiceScript = document.getElementById('voice-script')?.value;
                const leaveVoicemail = document.getElementById('leave-voicemail')?.checked;
                if (!voiceScript) {
                    showNotification('Please enter voice script', 'warning');
                    return null;
                }
                return { content: voiceScript, leave_voicemail: leaveVoicemail };
                
            default:
                return null;
        }
    }

    clearComposer() {
        document.getElementById('email-subject').value = '';
        document.getElementById('email-message').value = '';
        document.getElementById('sms-message').value = '';
        document.getElementById('voice-script').value = '';
        document.getElementById('leave-voicemail').checked = false;
        this.updateCharacterCount({ target: document.getElementById('sms-message') });
    }

    async refreshConversation() {
        if (this.currentConversation) {
            await this.selectConversation(this.currentConversation.id);
        }
    }

    async refreshInbox() {
        await this.loadConversations();
        showNotification('Inbox refreshed', 'success');
    }

    composeNewMessage() {
        // Show new message modal or redirect to compose view
        showNotification('New message composer coming soon', 'info');
    }

    handleFilterChange(event) {
        const filter = event.currentTarget.dataset.filter;
        this.filters.status = filter;
        
        // Update active state
        document.querySelectorAll('.nav-item[data-filter]').forEach(item => {
            item.classList.remove('active');
        });
        event.currentTarget.classList.add('active');
        
        this.renderConversations();
    }

    handleChannelFilter(event) {
        const channel = event.currentTarget.dataset.channel;
        this.filters.channel = this.filters.channel === channel ? null : channel;
        
        // Update active state
        event.currentTarget.classList.toggle('active');
        
        this.renderConversations();
    }

    handleSearch(event) {
        this.filters.search = event.target.value;
        this.renderConversations();
    }

    handleSort(event) {
        this.renderConversations();
    }

    updateCharacterCount(event) {
        const input = event.target;
        const count = input.value.length;
        const counter = document.getElementById('sms-char-count');
        if (counter) {
            counter.textContent = count;
            counter.style.color = count > 160 ? 'var(--error-color)' : 'var(--text-secondary)';
        }
    }

    updateCounts() {
        const counts = {
            all: this.conversations.length,
            unread: this.conversations.filter(c => c.unread_count > 0).length,
            replied: this.conversations.filter(c => c.last_reply_time).length,
            scheduled: this.conversations.filter(c => c.scheduled_messages > 0).length,
            email: this.conversations.filter(c => c.channels.includes('email')).length,
            sms: this.conversations.filter(c => c.channels.includes('sms')).length,
            voice: this.conversations.filter(c => c.channels.includes('voice')).length
        };

        Object.entries(counts).forEach(([key, count]) => {
            const element = document.getElementById(`${key}-count`);
            if (element) {
                element.textContent = count;
            }
        });

        // Update response rate and avg response time
        const responseRate = this.calculateResponseRate();
        const avgResponseTime = this.calculateAvgResponseTime();
        
        document.getElementById('response-rate').textContent = `${responseRate}%`;
        document.getElementById('avg-response-time').textContent = avgResponseTime;
    }

    calculateResponseRate() {
        const totalSent = this.conversations.reduce((sum, c) => sum + c.messages_sent, 0);
        const totalReplied = this.conversations.filter(c => c.last_reply_time).length;
        return totalSent > 0 ? Math.round((totalReplied / totalSent) * 100) : 0;
    }

    calculateAvgResponseTime() {
        const responseTimes = this.conversations
            .filter(c => c.avg_response_time)
            .map(c => c.avg_response_time);
        
        if (responseTimes.length === 0) return '0h';
        
        const avgMinutes = responseTimes.reduce((sum, time) => sum + time, 0) / responseTimes.length;
        const hours = Math.round(avgMinutes / 60);
        return `${hours}h`;
    }

    async markAsRead(conversationId) {
        try {
            await fetch(`/api/communication/conversations/${conversationId}/read`, {
                method: 'POST'
            });
            
            // Update local state
            const conversation = this.conversations.find(c => c.id === conversationId);
            if (conversation) {
                conversation.unread_count = 0;
                this.updateCounts();
            }
        } catch (error) {
            console.error('Error marking as read:', error);
        }
    }

    showTemplateManager() {
        document.getElementById('template-modal').classList.add('active');
        this.renderTemplates();
    }

    closeTemplateManager() {
        document.getElementById('template-modal').classList.remove('active');
    }

    renderTemplates() {
        // Template management implementation
        showNotification('Template management coming soon', 'info');
    }

    getChannelIcon(channel) {
        const icons = {
            email: 'envelope',
            sms: 'sms',
            voice: 'phone'
        };
        return icons[channel] || 'comment';
    }

    getStatusIcon(status) {
        const icons = {
            sent: 'paper-plane',
            delivered: 'check',
            opened: 'envelope-open',
            replied: 'reply',
            failed: 'exclamation-triangle'
        };
        return icons[status] || 'clock';
    }

    toggleImportant() {
        if (!this.currentConversation) return;
        
        // Toggle important status
        this.currentConversation.important = !this.currentConversation.important;
        
        // Update UI
        const btn = document.getElementById('mark-important');
        if (btn) {
            btn.classList.toggle('active', this.currentConversation.important);
            btn.innerHTML = this.currentConversation.important ? 
                '<i class="fas fa-star"></i>' : '<i class="far fa-star"></i>';
        }
        
        showNotification(
            this.currentConversation.important ? 'Marked as important' : 'Removed from important',
            'success'
        );
    }

    scheduleFollowup() {
        showNotification('Follow-up scheduling coming soon', 'info');
    }

    showConversationSettings() {
        showNotification('Conversation settings coming soon', 'info');
    }

    showTemplateSelector() {
        showNotification('Template selector coming soon', 'info');
    }

    scheduleSend() {
        showNotification('Message scheduling coming soon', 'info');
    }

    saveDraft() {
        showNotification('Draft saved', 'success');
    }

    showAIAssist() {
        showNotification('AI assistance coming soon', 'info');
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function showLoading() {
    // Implementation depends on your loading indicator
    console.log('Loading...');
}

function hideLoading() {
    // Implementation depends on your loading indicator
    console.log('Loading complete');
}

function showNotification(message, type = 'info') {
    // Implementation depends on your notification system
    console.log(`${type.toUpperCase()}: ${message}`);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new CommunicationCenter();
});