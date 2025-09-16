/**
 * Dynamic Configuration for Legal Management System
 * Automatically detects the current server IP and configures API endpoints
 */

class Config {
    constructor() {
        this.API_HOST = null;
        this.API_PORT = '5002';
        this.WEB_PORT = '8000';
        this.initialized = false;
    }

    async init() {
        if (this.initialized) return;
        
        try {
            // Method 1: Try to get IP from a config endpoint
            this.API_HOST = await this.getServerIP();
        } catch (error) {
            console.log('Could not get server IP, falling back to current host');
            // Method 2: Use current browser host as fallback
            this.API_HOST = window.location.hostname;
        }
        
        this.initialized = true;
        console.log(`🌐 API Host configured: ${this.API_HOST}`);
    }

    async getServerIP() {
        try {
            // Try to get IP from our API server
            const response = await fetch('/api/server-info', {
                method: 'GET',
                timeout: 5000
            });
            
            if (response.ok) {
                const data = await response.json();
                return data.public_ip || data.host;
            }
        } catch (error) {
            console.log('Server info endpoint not available');
        }

        // Fallback: use current hostname
        return window.location.hostname;
    }

    getApiUrl(endpoint = '') {
        if (!this.initialized) {
            throw new Error('Config not initialized. Call await config.init() first.');
        }
        
        const baseUrl = `http://${this.API_HOST}:${this.API_PORT}/api`;
        return endpoint ? `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}` : baseUrl;
    }

    getWebUrl(path = '') {
        if (!this.initialized) {
            throw new Error('Config not initialized. Call await config.init() first.');
        }
        
        const baseUrl = `http://${this.API_HOST}:${this.WEB_PORT}`;
        return path ? `${baseUrl}${path.startsWith('/') ? '' : '/'}${path}` : baseUrl;
    }

    getCorsOrigins() {
        if (!this.initialized) return [];
        
        return [
            `http://${this.API_HOST}:${this.WEB_PORT}`,
            'http://localhost:8000',
            'http://127.0.0.1:8000'
        ];
    }
}

// Create global config instance
const config = new Config();

// Auto-initialize when DOM is loaded
if (typeof document !== 'undefined') {
    document.addEventListener('DOMContentLoaded', async () => {
        try {
            await config.init();
            console.log('✅ Config initialized successfully');
            
            // Dispatch custom event to notify other scripts
            window.dispatchEvent(new CustomEvent('configReady', { detail: config }));
        } catch (error) {
            console.error('❌ Config initialization failed:', error);
        }
    });
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Config;
} else {
    window.Config = Config;
    window.config = config;
}
