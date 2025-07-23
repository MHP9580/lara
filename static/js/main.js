// Congo Connect - Main JavaScript

// Global variables
let userLat = null;
let userLon = null;

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    initializeFileUploads();
    updateUnreadMessageCount();
    
    // Auto-refresh unread message count every 60 seconds (reduced frequency)
    setInterval(updateUnreadMessageCount, 60000);
});

// Initialize main application features
function initializeApp() {
    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner me-2"></span>Chargement...';
            }
        });
    });

    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Simplified geolocation - no automatic prompts
function initializeGeolocation() {
    // Remove automatic geolocation requests that slow down the site
}

// Initialize file upload features
function initializeFileUploads() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            handleFileUpload(this);
        });
        
        // Add drag and drop functionality
        const container = input.closest('.upload-zone');
        if (container) {
            setupDragAndDrop(container, input);
        }
    });
}

// Handle file upload preview
function handleFileUpload(input) {
    const files = input.files;
    const previewContainer = document.getElementById('preview-container');
    
    if (files && previewContainer) {
        previewContainer.innerHTML = '';
        
        Array.from(files).forEach(file => {
            if (file.type.startsWith('image/')) {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    const preview = document.createElement('div');
                    preview.className = 'col-md-3 mb-3';
                    preview.innerHTML = `
                        <div class="position-relative">
                            <img src="${e.target.result}" class="img-fluid rounded shadow-sm" alt="Preview">
                            <button type="button" class="btn btn-danger btn-sm position-absolute top-0 end-0 m-1 rounded-circle" 
                                    onclick="removePreview(this)">
                                <i class="fas fa-times"></i>
                            </button>
                        </div>
                    `;
                    previewContainer.appendChild(preview);
                };
                
                reader.readAsDataURL(file);
            }
        });
    }
}

// Setup drag and drop for file uploads
function setupDragAndDrop(container, input) {
    container.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('dragover');
    });
    
    container.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
    });
    
    container.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('dragover');
        
        const files = e.dataTransfer.files;
        input.files = files;
        handleFileUpload(input);
    });
    
    container.addEventListener('click', function() {
        input.click();
    });
}

// Remove image preview
function removePreview(button) {
    button.closest('.col-md-3').remove();
}

// Simplified search features - removed for performance
function initializeSearchFeatures() {
    // Search features removed for better performance
}

// Update unread message count
function updateUnreadMessageCount() {
    if (!document.querySelector('#chat-badge')) return;
    
    fetch('/api/chat/unread-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.getElementById('chat-badge');
            if (data.unread_count > 0) {
                badge.textContent = data.unread_count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        })
        .catch(error => console.log('Error updating unread count:', error));
}

// Initialize scroll animations
function initializeScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, observerOptions);
    
    document.querySelectorAll('.slide-up').forEach(el => {
        observer.observe(el);
    });
}

// Toggle listing sold status
function toggleSoldStatus(listingId, button) {
    fetch(`/listings/${listingId}/toggle_sold`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            button.textContent = data.is_sold ? 'Marquer disponible' : 'Marquer vendu';
            button.className = data.is_sold ? 'btn btn-warning btn-sm' : 'btn btn-success btn-sm';
            
            // Update card appearance
            const card = button.closest('.card');
            if (data.is_sold) {
                card.classList.add('sold-listing');
            } else {
                card.classList.remove('sold-listing');
            }
            
            showNotification(`Annonce marquée comme ${data.status}`, 'success');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Erreur lors de la mise à jour', 'error');
    });
}

// Show notification
function showNotification(message, type = 'info') {
    const alertClass = type === 'error' ? 'alert-danger' : 
                      type === 'success' ? 'alert-success' : 
                      type === 'warning' ? 'alert-warning' : 'alert-info';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function formatPrice(price) {
    return new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency: 'XAF',
        minimumFractionDigits: 0
    }).format(price).replace('XAF', 'FCFA');
}

function formatTimeAgo(date) {
    const now = new Date();
    const diff = now - new Date(date);
    const seconds = Math.floor(diff / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);
    
    if (days > 0) {
        return `il y a ${days} jour${days > 1 ? 's' : ''}`;
    } else if (hours > 0) {
        return `il y a ${hours} heure${hours > 1 ? 's' : ''}`;
    } else if (minutes > 0) {
        return `il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
    } else {
        return "à l'instant";
    }
}

// Phone number validation for Congolese format
function validateCongoPhone(phone) {
    const pattern = /^242\d{9}$/;
    return pattern.test(phone);
}

// Form validation enhancement
document.addEventListener('DOMContentLoaded', function() {
    const phoneInputs = document.querySelectorAll('input[name="phone_number"], input[name="payment_phone"]');
    
    phoneInputs.forEach(input => {
        input.addEventListener('input', function() {
            const value = this.value;
            const isValid = validateCongoPhone(value);
            
            if (value.length > 0) {
                if (isValid) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                } else {
                    this.classList.remove('is-valid');
                    this.classList.add('is-invalid');
                }
            } else {
                this.classList.remove('is-valid', 'is-invalid');
            }
        });
    });
});

// Initialize lazy loading for images
if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    document.querySelectorAll('img[data-src]').forEach(img => {
        imageObserver.observe(img);
    });
}

// Export functions for global use
window.toggleSoldStatus = toggleSoldStatus;
window.showNotification = showNotification;
window.removePreview = removePreview;
window.formatPrice = formatPrice;
window.formatTimeAgo = formatTimeAgo;
