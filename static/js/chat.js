// Congo Connect - Chat System JavaScript

class ChatSystem {
    constructor() {
        this.currentUserId = null;
        this.lastMessageId = 0;
        this.refreshInterval = null;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        if (this.isInitialized) return;
        
        this.bindEvents();
        this.initializeChatIfNeeded();
        this.isInitialized = true;
    }
    
    bindEvents() {
        // Send message form
        const sendForm = document.getElementById('send-message-form');
        if (sendForm) {
            sendForm.addEventListener('submit', (e) => this.handleSendMessage(e));
        }
        
        // Message input auto-resize
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.addEventListener('input', this.autoResizeTextarea);
            messageInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.handleSendMessage(e);
                }
            });
        }
        
        // Chat list item clicks
        document.querySelectorAll('.chat-list-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const userId = item.dataset.userId;
                if (userId) {
                    window.location.href = `/chat/${userId}`;
                }
            });
        });
    }
    
    initializeChatIfNeeded() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            this.currentUserId = chatContainer.dataset.userId;
            this.scrollToBottom();
            this.startMessageRefresh();
            this.markMessagesAsRead();
        }
    }
    
    handleSendMessage(e) {
        e.preventDefault();
        
        const form = e.target.closest('form') || document.getElementById('send-message-form');
        const messageInput = document.getElementById('message-input');
        const message = messageInput.value.trim();
        
        if (!message) {
            this.showError('Le message ne peut pas être vide.');
            return;
        }
        
        if (!this.currentUserId) {
            this.showError('Erreur: destinataire non défini.');
            return;
        }
        
        // Disable form temporarily
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.innerHTML;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Envoi...';
        
        // Send message
        const formData = new FormData();
        formData.append('message', message);
        
        fetch(`/chat/${this.currentUserId}/send`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                this.addMessageToChat(data.message, true);
                messageInput.value = '';
                this.autoResizeTextarea.call(messageInput);
                this.scrollToBottom();
            } else {
                this.showError(data.error || 'Erreur lors de l\'envoi du message.');
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            this.showError('Erreur de connexion. Veuillez réessayer.');
        })
        .finally(() => {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalText;
        });
    }
    
    addMessageToChat(message, isOwn = false) {
        const chatContainer = document.getElementById('chat-messages');
        if (!chatContainer) return;
        
        const messageElement = this.createMessageElement(message, isOwn);
        chatContainer.appendChild(messageElement);
        
        // Update last message ID
        if (message.id > this.lastMessageId) {
            this.lastMessageId = message.id;
        }
        
        // Animate message appearance
        requestAnimationFrame(() => {
            messageElement.classList.add('fade-in');
        });
    }
    
    createMessageElement(message, isOwn = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${isOwn ? 'own' : ''} mb-3`;
        
        messageDiv.innerHTML = `
            <div class="message-content">
                ${this.escapeHtml(message.message)}
            </div>
            <div class="message-time text-muted">
                ${message.created_at}
                ${isOwn ? '' : `- ${this.escapeHtml(message.sender_name)}`}
            </div>
        `;
        
        return messageDiv;
    }
    
    startMessageRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Get initial last message ID
        const lastMessage = document.querySelector('#chat-messages .message:last-child');
        if (lastMessage && lastMessage.dataset.messageId) {
            this.lastMessageId = parseInt(lastMessage.dataset.messageId);
        }
        
        // Refresh every 3 seconds
        this.refreshInterval = setInterval(() => {
            this.fetchNewMessages();
        }, 3000);
    }
    
    fetchNewMessages() {
        if (!this.currentUserId) return;
        
        const url = `/api/chat/messages/${this.currentUserId}?since=${this.lastMessageId}`;
        
        fetch(url)
        .then(response => response.json())
        .then(messages => {
            if (messages.length > 0) {
                messages.forEach(message => {
                    this.addMessageToChat(message, message.is_own);
                });
                this.scrollToBottom();
                
                // Update last message ID
                const lastMessage = messages[messages.length - 1];
                this.lastMessageId = lastMessage.id;
            }
        })
        .catch(error => {
            console.error('Error fetching new messages:', error);
        });
    }
    
    markMessagesAsRead() {
        // Messages are automatically marked as read by the server
        // when fetching new messages
    }
    
    scrollToBottom() {
        const chatContainer = document.getElementById('chat-messages');
        if (chatContainer) {
            requestAnimationFrame(() => {
                chatContainer.scrollTop = chatContainer.scrollHeight;
            });
        }
    }
    
    autoResizeTextarea() {
        this.style.height = 'auto';
        this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    }
    
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        errorDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        errorDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        this.isInitialized = false;
    }
}

// Initialize chat system when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.chatSystem = new ChatSystem();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', function() {
    if (window.chatSystem) {
        window.chatSystem.destroy();
    }
});

// Chat list search functionality
document.addEventListener('DOMContentLoaded', function() {
    const chatSearch = document.getElementById('chat-search');
    if (chatSearch) {
        chatSearch.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const chatItems = document.querySelectorAll('.chat-list-item');
            
            chatItems.forEach(item => {
                const name = item.querySelector('.chat-user-name').textContent.toLowerCase();
                const lastMessage = item.querySelector('.chat-last-message');
                const messageText = lastMessage ? lastMessage.textContent.toLowerCase() : '';
                
                if (name.includes(searchTerm) || messageText.includes(searchTerm)) {
                    item.style.display = 'block';
                } else {
                    item.style.display = 'none';
                }
            });
        });
    }
});

// Online status simulation (could be enhanced with WebSockets)
function updateOnlineStatus() {
    const onlineIndicators = document.querySelectorAll('.online-indicator');
    onlineIndicators.forEach(indicator => {
        // Simple random online status for demo
        // In production, this would come from a real-time system
        const isOnline = Math.random() > 0.5;
        indicator.classList.toggle('online', isOnline);
        indicator.classList.toggle('offline', !isOnline);
    });
}

// Update online status every 30 seconds
setInterval(updateOnlineStatus, 30000);
updateOnlineStatus(); // Initial call
