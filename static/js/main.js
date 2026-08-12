// Global Variables
let socket = null;

// Initialize Socket.IO connection when logged in
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Initialize Socket.IO if user is authenticated
    if (document.querySelector('#socket-init')) {
        initializeSocket();
    }
});

// Socket.IO Initialization
function initializeSocket() {
    if (typeof io !== 'undefined') {
        socket = io();
        
        socket.on('connect', function() {
            console.log('Connected to WebSocket server');
            
            // Join user's personal room
            const userId = document.querySelector('#user-id')?.value;
            if (userId) {
                socket.emit('join_room', { room: `user_${userId}` });
            }
            
            // Join regional rooms based on user's region
            const region = document.querySelector('#user-region')?.value;
            if (region) {
                socket.emit('join_room', { room: `region_${region}` });
            }
        });
        
        socket.on('disconnect', function() {
            console.log('Disconnected from WebSocket server');
        });
        
        socket.on('new_notification', function(notification) {
            showNotification(notification);
            updateNotificationBadge();
        });
        
        socket.on('new_message', function(message) {
            displayNewMessage(message);
        });
    }
}

// Notification Functions
function showNotification(notification) {
    // Show browser notification if permitted
    if (Notification.permission === 'granted') {
        new Notification(notification.title, {
            body: notification.message,
            icon: '/static/img/notification-icon.png'
        });
    }
    
    // Show toast notification
    const toastContainer = document.querySelector('#toast-container') || createToastContainer();
    const toast = createToast(notification.title, notification.message, notification.type);
    toastContainer.appendChild(toast);
    
    // Auto-dismiss toast after 5 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 5000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1050;
    `;
    document.body.appendChild(container);
    return container;
}

function createToast(title, message, type) {
    const toast = document.createElement('div');
    toast.className = `toast show fade-in`;
    toast.style.cssText = `
        min-width: 250px;
        background: white;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
        border-left: 4px solid ${getColorForType(type)};
    `;
    toast.innerHTML = `
        <div class="toast-header">
            <strong class="me-auto">${title}</strong>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
        <div class="toast-body">${message}</div>
    `;
    return toast;
}

function getColorForType(type) {
    const colors = {
        'success': '#22c55e',
        'danger': '#ef4444',
        'warning': '#f59e0b',
        'info': '#3b82f6',
        'default': '#2563eb'
    };
    return colors[type] || colors.default;
}

function updateNotificationBadge() {
    // Update the notification badge count via AJAX
    fetch('/api/notification-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge .badge');
            if (badge) {
                badge.textContent = data.count;
                badge.style.display = data.count > 0 ? 'inline' : 'none';
            }
        });
}

// Utility Functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

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

// Loading spinner
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `;
    }
}

function hideLoading(containerId, content) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = content;
    }
}

// File download helper
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Confirm dialog wrapper
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Request permission for notifications
if ('Notification' in window && Notification.permission !== 'granted' && Notification.permission !== 'denied') {
    Notification.requestPermission();
}

// Auto-refresh dashboard every 30 seconds if on dashboard
if (window.location.pathname === '/dashboard') {
    setInterval(() => {
        location.reload();
    }, 30000);
}
