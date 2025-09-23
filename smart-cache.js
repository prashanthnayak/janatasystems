/**
 * Smart Cache System for Legal Management System
 * Provides intelligent caching with ETag support, compression, and optimistic updates
 */

class LegalCache {
    constructor() {
        this.cache = new Map();
        this.maxAge = 5 * 60 * 1000; // 5 minutes
        this.compressionEnabled = true;
        
        // Cache keys
        this.CACHE_KEYS = {
            DASHBOARD_DATA: 'legal_dashboard_data',
            CASES: 'legal_cases',
            CLIENTS: 'legal_clients',
            CALENDAR_EVENTS: 'legal_calendar_events',
            CACHE_VERSION: 'legal_cache_version',
            LAST_UPDATED: 'legal_last_updated'
        };
    }

    /**
     * Set cache entry with version and metadata
     */
    set(key, data, version = null, compressed = false) {
        const entry = {
            data,
            version: version || Date.now().toString(),
            timestamp: Date.now(),
            compressed,
            etag: null // Will be set by API response
        };
        
        this.cache.set(key, entry);
        
        // Also store in localStorage for cross-page access
        try {
            const storageKey = this.CACHE_KEYS[key.toUpperCase()] || key;
            localStorage.setItem(storageKey, JSON.stringify(entry));
            localStorage.setItem(this.CACHE_KEYS.CACHE_VERSION, entry.version);
        } catch (e) {
            console.warn('Failed to store in localStorage:', e);
        }
        
        console.log(`💾 Cached ${key} with version ${entry.version}`);
    }

    /**
     * Get cache entry with validation
     */
    get(key, requiredVersion = null) {
        // First check in-memory cache
        let entry = this.cache.get(key);
        
        // If not in memory, try localStorage
        if (!entry) {
            try {
                const storageKey = this.CACHE_KEYS[key.toUpperCase()] || key;
                const stored = localStorage.getItem(storageKey);
                if (stored) {
                    entry = JSON.parse(stored);
                    this.cache.set(key, entry);
                }
            } catch (e) {
                console.warn('Failed to load from localStorage:', e);
                return null;
            }
        }
        
        if (!entry) {
            console.log(`❌ Cache miss for ${key}`);
            return null;
        }
        
        // Check expiration
        if (Date.now() - entry.timestamp > this.maxAge) {
            console.log(`⏰ Cache expired for ${key}`);
            this.delete(key);
            return null;
        }
        
        // Check version if required
        if (requiredVersion && entry.version !== requiredVersion) {
            console.log(`🔄 Version mismatch for ${key}: cached=${entry.version}, required=${requiredVersion}`);
            return null;
        }
        
        console.log(`✅ Cache hit for ${key} (version: ${entry.version})`);
        return entry.data;
    }

    /**
     * Delete cache entry
     */
    delete(key) {
        this.cache.delete(key);
        
        try {
            const storageKey = this.CACHE_KEYS[key.toUpperCase()] || key;
            localStorage.removeItem(storageKey);
        } catch (e) {
            console.warn('Failed to remove from localStorage:', e);
        }
        
        console.log(`🗑️ Deleted cache for ${key}`);
    }

    /**
     * Clear all cache
     */
    clear() {
        this.cache.clear();
        
        try {
            Object.values(this.CACHE_KEYS).forEach(key => {
                localStorage.removeItem(key);
            });
        } catch (e) {
            console.warn('Failed to clear localStorage:', e);
        }
        
        console.log('🧹 Cleared all cache');
    }

    /**
     * Decompress data if needed
     */
    decompress(data, compressed = false) {
        if (!compressed || !this.compressionEnabled) {
            return data;
        }
        
        try {
            // Handle base64 encoded gzip data
            const binaryString = atob(data);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            // Decompress using pako library (would need to be included)
            if (typeof pako !== 'undefined') {
                const decompressed = pako.inflate(bytes, { to: 'string' });
                return JSON.parse(decompressed);
            } else {
                console.warn('pako library not available for decompression');
                return data;
            }
        } catch (e) {
            console.warn('Failed to decompress data:', e);
            return data;
        }
    }

    /**
     * Make API call with ETag support
     */
    async apiCall(url, options = {}) {
        const cacheKey = this.getCacheKeyFromUrl(url);
        const cachedEntry = this.cache.get(cacheKey);
        
        // Add ETag header if we have cached data
        if (cachedEntry && cachedEntry.etag) {
            options.headers = {
                ...options.headers,
                'If-None-Match': cachedEntry.etag
            };
        }
        
        // Add compression support
        options.headers = {
            ...options.headers,
            'Accept-Encoding': 'gzip, deflate'
        };
        
        try {
            const response = await fetch(url, options);
            
            // Handle 304 Not Modified
            if (response.status === 304) {
                console.log(`📦 304 Not Modified for ${url}`);
                return {
                    success: true,
                    data: cachedEntry.data,
                    cached: true
                };
            }
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Extract ETag from response
            const etag = response.headers.get('ETag');
            const compressed = result.compressed || false;
            
            // Decompress if needed
            let data = result;
            if (compressed && result.dashboard_data) {
                data = {
                    ...result,
                    dashboard_data: this.decompress(result.dashboard_data, compressed)
                };
            }
            
            // Cache the result
            this.set(cacheKey, data, result.cache_version, compressed);
            
            // Store ETag for future requests
            if (etag && cachedEntry) {
                cachedEntry.etag = etag;
            }
            
            return {
                success: true,
                data,
                cached: false,
                etag
            };
            
        } catch (error) {
            console.error(`API call failed for ${url}:`, error);
            
            // Return cached data if available
            if (cachedEntry) {
                console.log(`🔄 Returning cached data due to API error`);
                return {
                    success: true,
                    data: cachedEntry.data,
                    cached: true,
                    error: error.message
                };
            }
            
            throw error;
        }
    }

    /**
     * Get cache key from URL
     */
    getCacheKeyFromUrl(url) {
        if (url.includes('/dashboard-data')) return 'dashboard';
        if (url.includes('/cases')) return 'cases';
        if (url.includes('/clients')) return 'clients';
        if (url.includes('/calendar-events')) return 'calendar-events';
        return 'unknown';
    }

    /**
     * Optimistic update - update cache immediately, sync with server later
     */
    optimisticUpdate(key, updateFn, apiCall) {
        const cachedData = this.get(key);
        if (!cachedData) {
            console.warn(`Cannot perform optimistic update - no cached data for ${key}`);
            return apiCall();
        }
        
        // Create optimistic version
        const optimisticData = updateFn(cachedData);
        
        // Update cache immediately
        this.set(key, optimisticData);
        
        // Sync with server
        return apiCall().then(response => {
            if (response.success) {
                // Server confirmed, update with real data
                this.set(key, response.data, response.cache_version);
                return response;
            } else {
                // Server rejected, rollback to previous state
                console.log(`🔄 Rolling back optimistic update for ${key}`);
                this.set(key, cachedData);
                throw new Error(response.error || 'Server rejected update');
            }
        }).catch(error => {
            // API failed, rollback to previous state
            console.log(`🔄 Rolling back optimistic update for ${key} due to error`);
            this.set(key, cachedData);
            throw error;
        });
    }

    /**
     * Get cache statistics
     */
    getStats() {
        const stats = {
            memoryEntries: this.cache.size,
            localStorageEntries: 0,
            totalSize: 0,
            entries: []
        };
        
        // Count localStorage entries
        try {
            Object.values(this.CACHE_KEYS).forEach(key => {
                const item = localStorage.getItem(key);
                if (item) {
                    stats.localStorageEntries++;
                    stats.totalSize += item.length;
                }
            });
        } catch (e) {
            console.warn('Failed to calculate localStorage stats:', e);
        }
        
        // Get entry details
        this.cache.forEach((entry, key) => {
            stats.entries.push({
                key,
                version: entry.version,
                age: Date.now() - entry.timestamp,
                compressed: entry.compressed
            });
        });
        
        return stats;
    }
}

// Create global instance
window.LegalCache = new LegalCache();

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LegalCache;
}
