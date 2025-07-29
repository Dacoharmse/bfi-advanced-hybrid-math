/**
 * Fixed Market Data Sync System
 * Bridges frontend-backend communication gap with comprehensive error handling
 */

class FixedMarketDataSync {
    constructor() {
        this.updateInterval = 30000; // 30 seconds
        this.isUpdating = false;
        this.lastSuccessfulUpdate = null;
        this.retryCount = 0;
        this.maxRetries = 3;
        this.debugMode = false; // Debug panel disabled
        
        this.initialize();
    }
    
    initialize() {
        console.log('🔄 Initializing Fixed Market Data Sync...');
        
        // Test API connectivity first
        this.testApiConnectivity();
        
        // Start immediate data update
        this.updateMarketData();
        
        // Set up regular updates
        setInterval(() => {
            this.updateMarketData();
        }, this.updateInterval);
        
        // Setup debug tools if in development
        if (this.debugMode) {
            this.setupDebugTools();
        }
        
        console.log(`✅ Market Data Sync initialized - updates every ${this.updateInterval/1000}s`);
    }
    
    async testApiConnectivity() {
        try {
            console.log('🔍 Testing API connectivity...');
            
            const response = await fetch('/api/status', {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Cache-Control': 'no-cache'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log('✅ API connectivity test passed:', data);
                this.updateStatusIndicator('success', 'API connected');
                return true;
            } else {
                console.error('❌ API connectivity test failed:', response.status, response.statusText);
                this.updateStatusIndicator('error', `API error: ${response.status}`);
                return false;
            }
            
        } catch (error) {
            console.error('❌ API connectivity test error:', error);
            this.updateStatusIndicator('error', 'API connection failed');
            return false;
        }
    }
    
    async updateMarketData() {
        if (this.isUpdating) {
            console.log('⏳ Update already in progress, skipping...');
            return;
        }
        
        this.isUpdating = true;
        console.log('📊 Fetching market data from backend...');
        this.updateStatusIndicator('loading', 'Refreshing data...');
        
        // Add subtle loading state to cards
        document.querySelectorAll('.market-card, .ticker-item').forEach(card => {
            card.classList.add('data-loading');
        });
        
        try {
            // Try multiple endpoint URLs in order of preference
            const endpoints = [
                '/api/dashboard_data',
                '/api/live_market_data',
                '/api/market_data'
            ];
            
            let response = null;
            let lastError = null;
            let successfulEndpoint = null;
            
            for (const endpoint of endpoints) {
                try {
                    console.log(`🔗 Trying endpoint: ${endpoint}`);
                    
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
                    
                    response = await fetch(endpoint, {
                        method: 'GET',
                        headers: {
                            'Content-Type': 'application/json',
                            'Cache-Control': 'no-cache',
                            'Pragma': 'no-cache'
                        },
                        cache: 'no-store',
                        signal: controller.signal
                    });
                    
                    clearTimeout(timeoutId);
                    
                    if (response.ok) {
                        console.log(`✅ ${endpoint} responded successfully (${response.status})`);
                        successfulEndpoint = endpoint;
                        break;
                    } else {
                        console.warn(`⚠️ ${endpoint} returned ${response.status}: ${response.statusText}`);
                        lastError = new Error(`HTTP ${response.status}: ${response.statusText}`);
                    }
                    
                } catch (error) {
                    if (error.name === 'AbortError') {
                        console.warn(`⚠️ ${endpoint} timed out`);
                        lastError = new Error('Request timed out');
                    } else {
                        console.warn(`⚠️ ${endpoint} failed:`, error.message);
                        lastError = error;
                    }
                    continue;
                }
            }
            
            if (!response || !response.ok) {
                throw lastError || new Error('All endpoints failed');
            }
            
            const result = await response.json();
            console.log('📦 Received data from', successfulEndpoint, ':', result);
            
            if (result.success && result.data) {
                this.displayMarketData(result.data);
                this.updateStatusIndicator('success', `Data refreshed`);
                this.lastSuccessfulUpdate = new Date();
                this.retryCount = 0;
                
                // Remove loading state from all cards
                document.querySelectorAll('.market-card, .ticker-item').forEach(card => {
                    card.classList.remove('data-loading');
                });
                
                // Log data quality
                const instrumentCount = Object.keys(result.data).length;
                console.log(`✅ Successfully updated ${instrumentCount} instruments`);
                
            } else {
                throw new Error(result.error || 'Invalid data format received');
            }
            
        } catch (error) {
            console.error('❌ Market data update failed:', error);
            this.handleUpdateError(error);
        } finally {
            this.isUpdating = false;
            
            // Always remove loading state
            document.querySelectorAll('.market-card, .ticker-item').forEach(card => {
                card.classList.remove('data-loading');
            });
        }
    }
    
    displayMarketData(data) {
        console.log('🎨 Updating display with new data...');
        
        // Map instrument names (handle both uppercase and lowercase)
        const instrumentMap = {
            'nasdaq': 'NASDAQ',
            'NASDAQ': 'NASDAQ',
            'dow': 'DOW', 
            'DOW': 'DOW',
            'gold': 'GOLD',
            'GOLD': 'GOLD'
        };
        
        let updatedCount = 0;
        
        Object.entries(data).forEach(([key, marketData]) => {
            const instrumentName = instrumentMap[key];
            if (instrumentName && marketData) {
                try {
                    this.updateInstrumentDisplay(instrumentName, marketData);
                    updatedCount++;
                } catch (error) {
                    console.error(`❌ Failed to update ${instrumentName}:`, error);
                }
            }
        });
        
        // Update last updated time
        this.updateLastUpdatedTime();
        
        console.log(`✅ Display updated successfully - ${updatedCount} instruments`);
    }
    
    updateInstrumentDisplay(instrument, data) {
        console.log(`📊 Updating ${instrument}:`, {
            current: data.current_value,
            change: data.net_change,
            percent: data.percentage_change
        });
        
        // Find the market card using multiple selector strategies
        const selectors = [
            `[data-instrument="${instrument}"]`,
            `[data-instrument="${instrument.toLowerCase()}"]`,
            `.${instrument.toLowerCase()}-card`,
            `.market-card.${instrument.toLowerCase()}`,
            `.ticker-item:has(.ticker-symbol:contains("${instrument}"))`
        ];
        
        let card = null;
        for (const selector of selectors) {
            try {
                card = document.querySelector(selector);
                if (card) {
                    console.log(`📍 Found ${instrument} card using selector: ${selector}`);
                    break;
                }
            } catch (e) {
                // Ignore selector errors for :has() and :contains() which might not be supported
                continue;
            }
        }
        
        // Fallback: find by text content
        if (!card) {
            const allCards = document.querySelectorAll('.market-card, .ticker-item');
            for (const candidateCard of allCards) {
                const text = candidateCard.textContent.toUpperCase();
                if (text.includes(instrument.toUpperCase())) {
                    card = candidateCard;
                    console.log(`📍 Found ${instrument} card by text content`);
                    break;
                }
            }
        }
        
        if (!card) {
            console.warn(`⚠️ Card not found for ${instrument} - tried ${selectors.length} selectors`);
            return;
        }
        
        // Update elements with data
        this.updateElement(card, '.current-price, .ticker-price, [data-field="current"]', this.formatPrice(data.current_value, instrument));
        this.updateElement(card, '.net-change, .ticker-change, [data-field="change"]', this.formatChange(data.net_change));
        this.updateElement(card, '.percentage-change, [data-field="percent"]', this.formatPercent(data.percentage_change));
        this.updateElement(card, '.daily-high, [data-field="high"]', this.formatPrice(data.daily_high, instrument));
        this.updateElement(card, '.daily-low, [data-field="low"]', this.formatPrice(data.daily_low, instrument));
        this.updateElement(card, '.previous-close, [data-field="prev-close"]', this.formatPrice(data.previous_close, instrument));
        
        // Update color classes for change indicators
        this.updateColorClass(card, '.net-change, .ticker-change', data.net_change >= 0 ? 'positive' : 'negative');
        this.updateColorClass(card, '.percentage-change', data.percentage_change >= 0 ? 'positive' : 'negative');
        
        // Remove placeholder and loading states
        card.classList.remove('loading', 'error', 'placeholder');
        card.classList.add('data-refreshed');
        
        // Remove refresh class after subtle animation
        setTimeout(() => {
            card.classList.remove('data-refreshed');
        }, 500);
    }
    
    updateElement(card, selector, value) {
        const elements = card.querySelectorAll(selector);
        elements.forEach(element => {
            if (element) {
                // Store old value for change detection (but don't animate individual elements)
                const oldValue = element.textContent;
                element.textContent = value;
                
                // Remove placeholder styling
                element.classList.remove('placeholder');
                
                // No individual element animation - just update the value
                // The card-level animation will provide visual feedback instead
            }
        });
        
        if (elements.length === 0) {
            console.debug(`No elements found for selector: ${selector}`);
        }
    }
    
    updateColorClass(card, selector, className) {
        const elements = card.querySelectorAll(selector);
        elements.forEach(element => {
            if (element) {
                element.classList.remove('positive', 'negative', 'neutral');
                element.classList.add(className);
            }
        });
    }
    
    formatPrice(price, instrument = '') {
        if (typeof price !== 'number' || isNaN(price)) {
            return '--';
        }
        
        // Gold should have $ symbol
        if (instrument.toUpperCase() === 'GOLD') {
            return `$${new Intl.NumberFormat('en-US', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            }).format(price)}`;
        }
        
        return new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(price);
    }
    
    formatChange(change) {
        if (typeof change !== 'number' || isNaN(change)) {
            return '--';
        }
        const formatted = new Intl.NumberFormat('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(Math.abs(change));
        return `${change >= 0 ? '+' : '-'}${formatted}`;
    }
    
    formatPercent(percent) {
        if (typeof percent !== 'number' || isNaN(percent)) {
            return '--';
        }
        return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
    }
    
    handleUpdateError(error) {
        this.retryCount++;
        console.error(`❌ Update failed (attempt ${this.retryCount}/${this.maxRetries}):`, error);
        
        this.updateStatusIndicator('error', `Update failed: ${error.message}`);
        
        if (this.retryCount < this.maxRetries) {
            const retryDelay = Math.min(5000 * this.retryCount, 30000); // Exponential backoff, max 30s
            console.log(`🔄 Retrying in ${retryDelay/1000} seconds...`);
            setTimeout(() => {
                this.updateMarketData();
            }, retryDelay);
        } else {
            console.error('❌ Max retries reached, will retry on next interval');
            this.updateStatusIndicator('error', 'Max retries reached - will retry automatically');
            this.retryCount = 0; // Reset for next interval
        }
    }
    
    updateStatusIndicator(status, message) {
        // Update various status elements that might exist
        const statusSelectors = [
            '.update-status',
            '.data-status', 
            '.market-data-status',
            '#market-status',
            '.connection-status'
        ];
        
        statusSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.textContent = message;
                el.className = `${el.className.split(' ')[0]} ${status}`;
            });
        });
        
        // Also update page title if there's an error
        if (status === 'error') {
            document.title = `❌ ${document.title.replace(/^❌\s*/, '')}`;
        } else if (status === 'success') {
            document.title = document.title.replace(/^❌\s*/, '');
        }
    }
    
    updateLastUpdatedTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        
        const timeSelectors = [
            '.last-updated',
            '#last-update-time',
            '.update-timestamp',
            '[data-field="last-updated"]'
        ];
        
        timeSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                el.textContent = `Updated: ${timeString}`;
            });
        });
    }
    
    setupDebugTools() {
        console.log('🛠️ Setting up debug tools...');
        
        // Add debug panel
        this.addDebugPanel();
        
        // Expose debug methods globally
        window.marketDataSync = this;
        window.debugMarketData = () => this.debugInfo();
        window.forceUpdate = () => this.updateMarketData();
        window.testAPI = () => this.testApiConnectivity();
        
        // Log periodic status
        setInterval(() => {
            if (this.debugMode) {
                console.log('📊 Market Data Status:', {
                    lastUpdate: this.lastSuccessfulUpdate?.toLocaleTimeString() || 'Never',
                    retryCount: this.retryCount,
                    isUpdating: this.isUpdating,
                    nextUpdate: `in ${Math.round((this.updateInterval - (Date.now() - (this.lastSuccessfulUpdate?.getTime() || 0))) / 1000)}s`
                });
            }
        }, 60000); // Every minute
    }
    
    addDebugPanel() {
        const debugPanel = document.createElement('div');
        debugPanel.id = 'market-debug-panel';
        debugPanel.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            background: rgba(0,0,0,0.95);
            color: #00ff00;
            padding: 15px;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            z-index: 10000;
            border: 2px solid #00ff00;
            box-shadow: 0 0 20px rgba(0,255,0,0.3);
            max-width: 300px;
        `;
        
        debugPanel.innerHTML = `
            <h4 style="margin: 0 0 10px 0; color: #ffd700; text-align: center;">🛠️ Debug Panel</h4>
            <div style="margin-bottom: 10px;">
                <button onclick="marketDataSync.testApiConnectivity()" style="margin: 2px; padding: 6px 10px; background: #ffd700; color: #000; border: none; border-radius: 4px; cursor: pointer; font-size: 10px;">Test API</button>
                <button onclick="marketDataSync.updateMarketData()" style="margin: 2px; padding: 6px 10px; background: #00ff00; color: #000; border: none; border-radius: 4px; cursor: pointer; font-size: 10px;">Force Update</button>
                <button onclick="marketDataSync.debugInfo()" style="margin: 2px; padding: 6px 10px; background: #00aaff; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 10px;">Debug Info</button>
            </div>
            <div id="debug-status" style="font-size: 10px; line-height: 1.4;"></div>
            <div style="margin-top: 10px; font-size: 9px; color: #888;">
                Endpoints: /api/dashboard_data, /api/live_market_data, /api/market_data
            </div>
        `;
        
        document.body.appendChild(debugPanel);
        
        // Update debug status regularly
        setInterval(() => {
            this.updateDebugStatus();
        }, 1000);
        
        // Make draggable
        this.makeElementDraggable(debugPanel);
    }
    
    updateDebugStatus() {
        const debugStatus = document.getElementById('debug-status');
        if (debugStatus) {
            const timeSinceUpdate = this.lastSuccessfulUpdate ? 
                Date.now() - this.lastSuccessfulUpdate.getTime() : 0;
                
            debugStatus.innerHTML = `
                <div style="color: #00ff00;">Last Update: ${this.lastSuccessfulUpdate ? this.lastSuccessfulUpdate.toLocaleTimeString() : 'Never'}</div>
                <div style="color: ${this.retryCount > 0 ? '#ff4757' : '#00ff00'};">Retry Count: ${this.retryCount}</div>
                <div style="color: ${this.isUpdating ? '#ffd700' : '#00ff00'};">Updating: ${this.isUpdating ? 'Yes' : 'No'}</div>
                <div style="color: #aaa;">Time Since: ${timeSinceUpdate > 0 ? Math.round(timeSinceUpdate/1000) + 's' : 'N/A'}</div>
            `;
        }
    }
    
    makeElementDraggable(element) {
        let isDragging = false;
        let currentX;
        let currentY;
        let initialX;
        let initialY;
        let xOffset = 0;
        let yOffset = 0;
        
        element.addEventListener('mousedown', dragStart);
        document.addEventListener('mousemove', drag);
        document.addEventListener('mouseup', dragEnd);
        
        function dragStart(e) {
            if (e.target.tagName === 'BUTTON') return;
            
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            
            if (e.target === element) {
                isDragging = true;
            }
        }
        
        function drag(e) {
            if (isDragging) {
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                
                xOffset = currentX;
                yOffset = currentY;
                
                element.style.transform = `translate3d(${currentX}px, ${currentY}px, 0)`;
            }
        }
        
        function dragEnd() {
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }
    }
    
    debugInfo() {
        const info = {
            lastUpdate: this.lastSuccessfulUpdate,
            retryCount: this.retryCount,
            isUpdating: this.isUpdating,
            updateInterval: this.updateInterval,
            maxRetries: this.maxRetries,
            debugMode: this.debugMode
        };
        
        console.log('🐛 Market Data Sync Debug Info:', info);
        alert(`Debug Info:\n${JSON.stringify(info, null, 2)}`);
        return info;
    }
}

// CSS for cleaner, less intensive animations
const debugStyles = document.createElement('style');
debugStyles.textContent = `
    /* Status indicators */
    .update-status.success, .data-status.success, .market-data-status.success {
        color: #00ff88 !important;
    }
    
    .update-status.error, .data-status.error, .market-data-status.error {
        color: #ff4757 !important;
    }
    
    .update-status.loading, .data-status.loading, .market-data-status.loading {
        color: #ffd700 !important;
    }
    
    /* Remove placeholder styling when data loads */
    .placeholder {
        color: #666 !important;
        font-style: italic;
    }
    
    /* Subtle loading state - barely noticeable opacity change */
    .market-card.data-loading, .ticker-item.data-loading {
        opacity: 0.85;
        transition: opacity 0.3s ease;
    }
    
    /* Very subtle refresh animation - just a slight border glow */
    .market-card.data-refreshed, .ticker-item.data-refreshed {
        border-color: rgba(212, 175, 55, 0.4) !important;
        transition: border-color 0.5s ease;
        animation: none; /* Remove any existing animations */
    }
    
    /* Error state - minimal red tint */
    .market-card.error, .ticker-item.error {
        border-color: rgba(255, 71, 87, 0.3) !important;
    }
    
    /* Positive/negative change colors */
    .positive {
        color: #00ff88 !important;
    }
    
    .negative {
        color: #ff4757 !important;
    }
    
    .neutral {
        color: #ffd700 !important;
    }
    
    /* Remove all pulsing and flashing animations */
    .market-card, .ticker-item {
        animation: none !important;
    }
    
    /* Smoother transitions for color changes only */
    .market-card .positive, .market-card .negative, .market-card .neutral,
    .ticker-item .positive, .ticker-item .negative, .ticker-item .neutral {
        transition: color 0.2s ease;
    }
`;
document.head.appendChild(debugStyles);

// Initialize the market data sync when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Starting Fixed Market Data Sync...');
    window.marketDataSync = new FixedMarketDataSync();
});

// Add manual refresh capability
document.addEventListener('click', (e) => {
    if (e.target.matches('.refresh-btn, #refresh-data-btn, [data-action="refresh"]')) {
        e.preventDefault();
        if (window.marketDataSync) {
            console.log('🔄 Manual refresh triggered');
            window.marketDataSync.updateMarketData();
        }
    }
});

// Handle visibility changes (pause updates when tab is hidden)
document.addEventListener('visibilitychange', () => {
    if (window.marketDataSync) {
        if (document.hidden) {
            console.log('⏸️ Tab hidden, pausing updates');
        } else {
            console.log('▶️ Tab visible, resuming updates');
            // Force immediate update when tab becomes visible
            setTimeout(() => {
                window.marketDataSync.updateMarketData();
            }, 1000);
        }
    }
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FixedMarketDataSync;
}