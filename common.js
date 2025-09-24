/**
 * Common Utilities for Legal Case Management System
 * Shared functions used across all pages
 */

// Logging system - centralized console logging
const Logger = {
    debug: (message, ...args) => {
        if (window.DEBUG_MODE !== false) {
            console.log(`🔍 ${message}`, ...args);
        }
    },
    info: (message, ...args) => {
        console.log(`ℹ️ ${message}`, ...args);
    },
    success: (message, ...args) => {
        console.log(`✅ ${message}`, ...args);
    },
    warning: (message, ...args) => {
        console.warn(`⚠️ ${message}`, ...args);
    },
    error: (message, ...args) => {
        console.error(`❌ ${message}`, ...args);
    },
    api: (message, ...args) => {
        console.log(`🔗 ${message}`, ...args);
    },
    auth: (message, ...args) => {
        console.log(`🔐 ${message}`, ...args);
    },
    cache: (message, ...args) => {
        console.log(`💾 ${message}`, ...args);
    },
    delete: (message, ...args) => {
        console.log(`🗑️ ${message}`, ...args);
    },
    edit: (message, ...args) => {
        console.log(`✏️ ${message}`, ...args);
    }
};

// Notification system
let notificationStack = [];

function showNotification(message, type = 'info', duration = 5000) {
    // Remove emojis from message for cleaner display
    const cleanMessage = message.replace(/[^\x00-\x7F]/g, '').trim();
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = 'notification';
    notification.textContent = cleanMessage;
    
    // Position notification
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
        z-index: 1000;
        max-width: 300px;
        word-wrap: break-word;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
    `;
    
    // Set background color based on type
    switch(type) {
        case 'success':
            notification.style.backgroundColor = '#28a745';
            break;
        case 'error':
            notification.style.backgroundColor = '#dc3545';
            break;
        case 'warning':
            notification.style.backgroundColor = '#ffc107';
            notification.style.color = '#212529';
            break;
        case 'info':
        default:
            notification.style.backgroundColor = '#17a2b8';
    }
    
    // Handle stacking
    if (notificationStack.length > 0) {
        const lastNotification = notificationStack[notificationStack.length - 1];
        const lastBottom = lastNotification.offsetTop + lastNotification.offsetHeight;
        notification.style.top = `${lastBottom + 10}px`;
    }
    
    // Add to page and stack
    document.body.appendChild(notification);
    notificationStack.push(notification);
    
    // Remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
                
                // Remove from stack and reposition remaining notifications
                const index = notificationStack.indexOf(notification);
                if (index > -1) {
                    notificationStack.splice(index, 1);
                }
                
                // Reposition remaining notifications
                notificationStack.forEach((notif, idx) => {
                    notif.style.top = `${20 + (idx * 70)}px`;
                });
            }, 300);
        }
    }, duration);
}

// Authentication utilities
function checkAuth() {
    const token = localStorage.getItem('userToken');
    const userData = localStorage.getItem('userData');
    
    if (!token || !userData) {
        window.location.href = 'login.html';
        return false;
    }
    return true;
}

function logout() {
    localStorage.removeItem('userToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('userRole');
    window.location.href = 'login.html';
}

// API utilities
function getAuthHeaders() {
    const token = localStorage.getItem('userToken');
    return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
    };
}

// Cache utilities
function clearCache() {
    localStorage.removeItem('userDashboardData');
    localStorage.setItem('cacheUpdated', Date.now().toString());
}

function getCachedData(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('Error parsing cached data:', error);
        return null;
    }
}

function setCachedData(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
    } catch (error) {
        console.error('Error caching data:', error);
    }
}

// Date utilities
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    } catch (error) {
        return 'Invalid Date';
    }
}

function formatDateTime(dateString) {
    if (!dateString) return 'N/A';
    try {
        const date = new Date(dateString);
        return date.toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    } catch (error) {
        return 'Invalid Date';
    }
}

// Validation utilities
function validateCNR(cnr) {
    if (!cnr || cnr.trim().length === 0) {
        return { valid: false, message: 'CNR Number is required' };
    }
    
    if (cnr.trim().length < 10) {
        return { valid: false, message: 'CNR Number must be at least 10 characters' };
    }
    
    return { valid: true, message: 'Valid CNR' };
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// DOM utilities
function createElement(tag, className, textContent) {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (textContent) element.textContent = textContent;
    return element;
}

function hideElement(element) {
    if (element) element.style.display = 'none';
}

function showElement(element) {
    if (element) element.style.display = 'block';
}

// Error handling utilities
function handleApiError(error, context = 'API call') {
    console.error(`Error in ${context}:`, error);
    
    if (error.status === 401) {
        showNotification('Session expired. Please login again.', 'error');
        // Configurable logout delay (default: 2 seconds)
        const LOGOUT_DELAY = window.LOGOUT_DELAY || 2000;
        setTimeout(() => logout(), LOGOUT_DELAY);
    } else if (error.status === 403) {
        showNotification('Access denied. You do not have permission for this action.', 'error');
    } else if (error.status >= 500) {
        showNotification('Server error. Please try again later.', 'error');
    } else {
        showNotification(`Error: ${error.message || 'Unknown error occurred'}`, 'error');
    }
}

// Common API call patterns
async function makeApiCall(url, options = {}) {
    const token = localStorage.getItem('userToken');
    const defaultOptions = {
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    };
    
    Logger.api('Making API call to:', url);
    
    try {
        const response = await fetch(url, defaultOptions);
        Logger.api('API response status:', response.status);
        
        if (response.status === 401) {
            Logger.auth('Token expired, redirecting to login');
            logout();
            return { success: false, error: 'Session expired' };
        }
        
        const data = await response.json();
        return { success: response.ok, data, status: response.status };
    } catch (error) {
        Logger.error('API call failed:', error);
        return { success: false, error: error.message };
    }
}

// Common form validation
function validateForm(formData, rules) {
    const errors = {};
    
    for (const [field, rule] of Object.entries(rules)) {
        const value = formData.get(field);
        
        if (rule.required && (!value || value.trim() === '')) {
            errors[field] = `${rule.label || field} is required`;
        } else if (rule.minLength && value && value.length < rule.minLength) {
            errors[field] = `${rule.label || field} must be at least ${rule.minLength} characters`;
        } else if (rule.maxLength && value && value.length > rule.maxLength) {
            errors[field] = `${rule.label || field} must be no more than ${rule.maxLength} characters`;
        } else if (rule.pattern && value && !rule.pattern.test(value)) {
            errors[field] = rule.message || `${rule.label || field} format is invalid`;
        }
    }
    
    return {
        isValid: Object.keys(errors).length === 0,
        errors
    };
}

// Common form error display
function displayFormErrors(errors) {
    // Clear previous errors
    document.querySelectorAll('.error-message').forEach(el => el.remove());
    
    // Display new errors
    for (const [field, message] of Object.entries(errors)) {
        const fieldElement = document.getElementById(field);
        if (fieldElement) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.textContent = message;
            errorDiv.style.color = '#dc3545';
            errorDiv.style.fontSize = '12px';
            errorDiv.style.marginTop = '4px';
            
            fieldElement.parentNode.insertBefore(errorDiv, fieldElement.nextSibling);
        }
    }
}

// Common loading state management
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.disabled = true;
        element.style.opacity = '0.6';
        if (element.tagName === 'BUTTON') {
            element.dataset.originalText = element.textContent;
            element.textContent = 'Loading...';
        }
    } else {
        element.disabled = false;
        element.style.opacity = '1';
        if (element.tagName === 'BUTTON' && element.dataset.originalText) {
            element.textContent = element.dataset.originalText;
            delete element.dataset.originalText;
        }
    }
}

// Common confirmation dialog
function confirmAction(message, onConfirm, onCancel = null) {
    if (confirm(message)) {
        onConfirm();
    } else if (onCancel) {
        onCancel();
    }
}

// Enhanced alert system - centralized alert management
const Alert = {
    // Standard alert with consistent styling
    show: (message, type = 'info', options = {}) => {
        const {
            title = 'System Message',
            showCancel = false,
            onConfirm = null,
            onCancel = null,
            confirmText = 'OK',
            cancelText = 'Cancel'
        } = options;

        // Create custom modal instead of browser alert
        const modal = document.createElement('div');
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 10000;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
        `;

        const content = document.createElement('div');
        content.style.cssText = `
            background: white;
            border-radius: 12px;
            padding: 24px;
            max-width: 400px;
            width: 90%;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            text-align: center;
        `;

        // Title
        const titleEl = document.createElement('h3');
        titleEl.textContent = title;
        titleEl.style.cssText = `
            margin: 0 0 16px 0;
            font-size: 18px;
            font-weight: 600;
            color: #111827;
        `;

        // Message
        const messageEl = document.createElement('div');
        messageEl.textContent = message;
        messageEl.style.cssText = `
            margin: 0 0 24px 0;
            font-size: 14px;
            line-height: 1.5;
            color: #374151;
            white-space: pre-line;
        `;

        // Buttons container
        const buttonsEl = document.createElement('div');
        buttonsEl.style.cssText = `
            display: flex;
            gap: 12px;
            justify-content: center;
        `;

        // Confirm button
        const confirmBtn = document.createElement('button');
        confirmBtn.textContent = confirmText;
        confirmBtn.style.cssText = `
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        `;

        // Cancel button
        let cancelBtn = null;
        if (showCancel) {
            cancelBtn = document.createElement('button');
            cancelBtn.textContent = cancelText;
            cancelBtn.style.cssText = `
                padding: 8px 16px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                background: white;
                color: #374151;
                transition: all 0.2s;
            `;
        }

        // Set colors based on type
        switch (type) {
            case 'success':
                confirmBtn.style.backgroundColor = '#10b981';
                confirmBtn.style.color = 'white';
                break;
            case 'error':
                confirmBtn.style.backgroundColor = '#ef4444';
                confirmBtn.style.color = 'white';
                break;
            case 'warning':
                confirmBtn.style.backgroundColor = '#f59e0b';
                confirmBtn.style.color = 'white';
                break;
            case 'info':
            default:
                confirmBtn.style.backgroundColor = '#3b82f6';
                confirmBtn.style.color = 'white';
                break;
        }

        // Event handlers
        confirmBtn.addEventListener('click', () => {
            document.body.removeChild(modal);
            if (onConfirm) onConfirm();
        });

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                document.body.removeChild(modal);
                if (onCancel) onCancel();
            });
        }

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
                if (onCancel) onCancel();
            }
        });

        // Assemble modal
        content.appendChild(titleEl);
        content.appendChild(messageEl);
        buttonsEl.appendChild(confirmBtn);
        if (cancelBtn) buttonsEl.appendChild(cancelBtn);
        content.appendChild(buttonsEl);
        modal.appendChild(content);
        document.body.appendChild(modal);

        // Focus confirm button
        confirmBtn.focus();
    },

    // Convenience methods
    success: (message, options = {}) => Alert.show(message, 'success', { title: 'Success', ...options }),
    error: (message, options = {}) => Alert.show(message, 'error', { title: 'Error', ...options }),
    warning: (message, options = {}) => Alert.show(message, 'warning', { title: 'Warning', ...options }),
    info: (message, options = {}) => Alert.show(message, 'info', { title: 'Information', ...options }),

    // Confirmation dialog
    confirm: (message, onConfirm, onCancel = null) => {
        Alert.show(message, 'warning', {
            title: 'Confirm Action',
            showCancel: true,
            confirmText: 'Yes',
            cancelText: 'No',
            onConfirm,
            onCancel
        });
    },

    // Legacy browser alert fallback
    legacy: (message) => {
        alert(message);
    }
};

// Common confirmation dialog
function confirmAction(message, onConfirm, onCancel = null) {
    Alert.confirm(message, onConfirm, onCancel);
}

// Common data formatting
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR'
    }).format(amount);
}

function formatNumber(number) {
    return new Intl.NumberFormat('en-IN').format(number);
}

// Common URL utilities
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

// Common DOM utilities
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

function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other scripts
window.CommonUtils = {
    // Logging
    Logger,
    
    // Notifications
    showNotification,
    
    // Alerts
    Alert,
    
    // Authentication
    checkAuth,
    logout,
    getAuthHeaders,
    
    // Cache management
    clearCache,
    getCachedData,
    setCachedData,
    
    // Date utilities
    formatDate,
    formatDateTime,
    
    // Validation
    validateCNR,
    validateEmail,
    validateForm,
    displayFormErrors,
    
    // DOM utilities
    createElement,
    hideElement,
    showElement,
    setLoadingState,
    
    // API utilities
    makeApiCall,
    handleApiError,
    
    // UI utilities
    confirmAction,
    formatCurrency,
    formatNumber,
    
    // URL utilities
    getUrlParameter,
    setUrlParameter,
    
    // Performance utilities
    debounce,
    throttle
};
