/**
 * Unified Cache Management System
 * Handles add/update/delete operations consistently
 */

class CacheManager {
    constructor() {
        this.CACHE_KEY = 'userDashboardData';
        this.CACHE_VERSION_KEY = 'cacheVersion';
        this.CACHE_UPDATED_KEY = 'cacheUpdated';
        this.MAX_CACHE_AGE = 5 * 60 * 1000; // 5 minutes
    }

    /**
     * Get cached dashboard data
     */
    getCachedData() {
        try {
            const cachedData = localStorage.getItem(this.CACHE_KEY);
            if (cachedData) {
                return JSON.parse(cachedData);
            }
        } catch (error) {
            console.error('❌ CacheManager: Error parsing cached data:', error);
        }
        return null;
    }

    /**
     * Check if cache is valid and not recently updated
     */
    isCacheValid() {
        const cacheVersion = localStorage.getItem(this.CACHE_VERSION_KEY) || '0';
        const cacheAge = Date.now() - parseInt(cacheVersion);
        const cacheUpdateTime = localStorage.getItem(this.CACHE_UPDATED_KEY);
        const hasRecentUpdate = cacheUpdateTime && (Date.now() - parseInt(cacheUpdateTime)) < 10000;
        
        return cacheAge < this.MAX_CACHE_AGE && !hasRecentUpdate;
    }

    /**
     * Add a new case to the cache
     */
    addCaseToCache(newCase) {
        console.log('➕ CacheManager: Adding new case to cache');
        
        if (!newCase) {
            console.error('❌ CacheManager: Cannot add null/undefined case to cache');
            return false;
        }
        
        const cachedData = this.getCachedData();
        if (cachedData && cachedData.cases) {
            // Add new case to existing cache
            cachedData.cases.push(newCase);
            
            // Update cache timestamp
            cachedData.lastUpdated = Date.now();
            
            // Save updated cache
            this.saveCache(cachedData);
            
            console.log('✅ CacheManager: Added case to cache, total cases:', cachedData.cases.length);
            return true;
        }
        
        console.log('⚠️ CacheManager: No existing cache found, will trigger full reload');
        return false;
    }

    /**
     * Update a specific case in the cache
     */
    updateCaseInCache(cnrNumber, updatedCase) {
        console.log('✏️ CacheManager: Updating case in cache:', cnrNumber);
        
        if (!cnrNumber || !updatedCase) {
            console.error('❌ CacheManager: Cannot update case - missing cnrNumber or updatedCase');
            return false;
        }
        
        const cachedData = this.getCachedData();
        if (cachedData && cachedData.cases) {
            // Find and update the case
            const caseIndex = cachedData.cases.findIndex(c => c && c.cnr_number === cnrNumber);
            if (caseIndex !== -1) {
                cachedData.cases[caseIndex] = { ...cachedData.cases[caseIndex], ...updatedCase };
                
                // Update cache timestamp
                cachedData.lastUpdated = Date.now();
                
                // Save updated cache
                this.saveCache(cachedData);
                
                console.log('✅ CacheManager: Updated case in cache');
                return true;
            }
        }
        
        console.log('⚠️ CacheManager: Case not found in cache, will trigger full reload');
        return false;
    }

    /**
     * Remove a specific case from the cache
     */
    removeCaseFromCache(cnrNumber) {
        console.log('🗑️ CacheManager: Removing case from cache:', cnrNumber);
        
        if (!cnrNumber) {
            console.error('❌ CacheManager: Cannot remove case - missing cnrNumber');
            return false;
        }
        
        const cachedData = this.getCachedData();
        if (cachedData && cachedData.cases) {
            // Remove the case from cache
            const initialLength = cachedData.cases.length;
            cachedData.cases = cachedData.cases.filter(c => c && c.cnr_number !== cnrNumber);
            
            if (cachedData.cases.length < initialLength) {
                // Update cache timestamp
                cachedData.lastUpdated = Date.now();
                
                // Save updated cache
                this.saveCache(cachedData);
                
                console.log('✅ CacheManager: Removed case from cache, remaining cases:', cachedData.cases.length);
                return true;
            }
        }
        
        console.log('⚠️ CacheManager: Case not found in cache, will trigger full reload');
        return false;
    }

    /**
     * Save cache data to localStorage
     */
    saveCache(data) {
        try {
            localStorage.setItem(this.CACHE_KEY, JSON.stringify(data));
            localStorage.setItem(this.CACHE_VERSION_KEY, Date.now().toString());
            
            // Update global cache
            window.userDashboardData = data;
            
            console.log('💾 CacheManager: Cache saved successfully');
        } catch (error) {
            console.error('❌ CacheManager: Error saving cache:', error);
        }
    }

    /**
     * Clear all cache data
     */
    clearCache() {
        console.log('🧹 CacheManager: Clearing all cache data');
        
        localStorage.removeItem(this.CACHE_KEY);
        localStorage.removeItem(this.CACHE_VERSION_KEY);
        localStorage.removeItem(this.CACHE_UPDATED_KEY);
        
        if (window.userDashboardData) {
            delete window.userDashboardData;
        }
    }

    /**
     * Notify other pages of cache update
     */
    notifyCacheUpdate(operation, details = {}) {
        const cacheUpdateTime = Date.now().toString();
        localStorage.setItem(this.CACHE_UPDATED_KEY, cacheUpdateTime);
        
        console.log(`🔄 CacheManager: Notifying cache update - ${operation}:`, cacheUpdateTime);
        console.log(`🔄 CacheManager: Details:`, details);
        
        // Dispatch custom event for same-tab updates
        window.dispatchEvent(new CustomEvent('cacheUpdated', { 
            detail: { 
                timestamp: cacheUpdateTime,
                operation: operation,
                ...details
            } 
        }));
        
        console.log(`🔄 CacheManager: Custom event dispatched for ${operation}`);
        
        // Clear the flag after 5 seconds to allow all pages to detect it
        setTimeout(() => {
            localStorage.removeItem(this.CACHE_UPDATED_KEY);
            console.log('🔄 CacheManager: Cleared cacheUpdated flag after 5 seconds');
        }, 5000);
    }

    /**
     * Set cached data (used by pages that load fresh data)
     */
    setCachedData(data) {
        console.log('💾 CacheManager: Setting cached data');
        this.saveCache(data);
    }

    /**
     * Handle cache update notification
     */
    handleCacheUpdate(operation, details = {}) {
        console.log(`🔄 CacheManager: Handling cache update - ${operation}`);
        
        switch (operation) {
            case 'add':
                if (details.case) {
                    this.addCaseToCache(details.case);
                } else {
                    this.clearCache();
                }
                break;
            case 'update':
                if (details.cnrNumber && details.caseData) {
                    this.updateCaseInCache(details.cnrNumber, details.caseData);
                } else {
                    this.clearCache();
                }
                break;
            case 'delete':
                if (details.cnrNumber) {
                    this.removeCaseFromCache(details.cnrNumber);
                } else {
                    this.clearCache();
                }
                break;
            default:
                // Unknown operation, clear cache to be safe
                this.clearCache();
        }
    }
}

// Create global instance
window.cacheManager = new CacheManager();
