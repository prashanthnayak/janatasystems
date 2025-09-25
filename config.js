/**
 * Dynamic Configuration for Legal Management System
 * Automatically detects the current server IP and configures API endpoints
 */

class Config {
    constructor() {
        this.API_HOST = null;
        this.API_PORT = window.API_PORT || '5002';
        this.WEB_PORT = window.WEB_PORT || '8000';
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
        console.log(`🔍 DEBUG: API_HOST = "${this.API_HOST}"`);
        console.log(`🔍 DEBUG: API_PORT = "${this.API_PORT}"`);
    }

    async getServerIP() {
        try {
            // Build the correct URL for the API server
            const apiHost = window.location.hostname;
            const apiUrl = `http://${apiHost}:${this.API_PORT}/api/server-info`;
            
            console.log(`🔍 Trying to get server info from: ${apiUrl}`);
            
            const response = await fetch(apiUrl, {
                method: 'GET'
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ Got server info:', data);
                return data.public_ip || data.hostname || apiHost;
            } else {
                console.log('❌ Server info request failed:', response.status);
            }
        } catch (error) {
            console.log('❌ Server info endpoint not available:', error.message);
        }

        // Fallback: use current hostname
        console.log('🔄 Using fallback hostname:', window.location.hostname);
        return window.location.hostname;
    }

    getApiUrl(endpoint = '') {
        if (!this.initialized) {
            throw new Error('Config not initialized. Call await config.init() first.');
        }
        
        const baseUrl = `http://${this.API_HOST}:${this.API_PORT}/api`;
        const result = endpoint ? `${baseUrl}${endpoint.startsWith('/') ? '' : '/'}${endpoint}` : baseUrl;
        console.log(`🔍 DEBUG: getApiUrl('${endpoint}') = "${result}"`);
        return result;
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
        
        const origins = [
            `http://${this.API_HOST}:${this.WEB_PORT}`
        ];
        
        // Add localhost variants
        origins.push(`http://localhost:${this.WEB_PORT}`);
        origins.push(`http://127.0.0.1:${this.WEB_PORT}`);
        
        // Add any additional origins from environment or config
        const additionalOrigins = window.ADDITIONAL_CORS_ORIGINS || '';
        if (additionalOrigins) {
            origins.push(...additionalOrigins.split(','));
        }
        
        return origins;
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
