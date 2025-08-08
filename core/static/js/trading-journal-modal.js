/**
 * Modern Trading Journal Modal System
 * Complete rebuild with addEventListener, validation, and API integration
 */

class TradingJournalModal {
    constructor() {
        this.modal = null;
        this.isEdit = false;
        this.currentTradeData = null;
        
        console.log('🚀 TradingJournalModal initialized');
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.bindEvents());
        } else {
            this.bindEvents();
        }
    }
    
    bindEvents() {
        console.log('🔗 Binding modal events...');
        
        // Add New Trade button (for when there are existing trades)
        const addTradeBtn = document.querySelector('[data-action="add-trade"]');
        if (addTradeBtn) {
            console.log('✅ Found Add Trade button');
            addTradeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openModal();
            });
        }
        
        // Add First Trade button (for empty state)
        const addFirstTradeBtn = document.querySelector('[data-action="add-first-trade"]');
        if (addFirstTradeBtn) {
            console.log('✅ Found Add First Trade button');
            addFirstTradeBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.openModal();
            });
        }
        
        // Event delegation for dynamic trade action buttons
        document.body.addEventListener('click', (e) => {
            if (e.target.matches('[data-action="view-trade"]')) {
                e.preventDefault();
                const entryId = e.target.getAttribute('data-entry-id');
                this.viewTrade(entryId);
            }
            
            if (e.target.matches('[data-action="edit-trade"]')) {
                e.preventDefault();
                const entryId = e.target.getAttribute('data-entry-id');
                this.editTrade(entryId);
            }
            
            if (e.target.matches('[data-action="delete-trade"]')) {
                e.preventDefault();
                const entryId = e.target.getAttribute('data-entry-id');
                this.deleteTrade(entryId);
            }
        });
        
        console.log('✅ Modal events bound successfully');
    }
    
    openModal(tradeData = null) {
        console.log('🔧 Opening trade modal...', tradeData);
        
        this.isEdit = tradeData !== null;
        this.currentTradeData = tradeData;
        
        // Remove existing modal
        this.closeModal();
        
        // Create modal
        this.createModal();
        
        // Populate form if editing
        if (this.isEdit && tradeData) {
            this.populateForm(tradeData);
        } else {
            this.setDefaults();
        }
        
        // Setup form interactions
        this.setupFormInteractions();
        
        // Focus on first input
        setTimeout(() => {
            const symbolInput = document.getElementById('modal-symbol');
            if (symbolInput) symbolInput.focus();
        }, 100);
    }
    
    createModal() {
        this.modal = document.createElement('div');
        this.modal.setAttribute('data-modal', 'trade-modal');
        this.modal.className = 'trade-modal-overlay';
        
        this.modal.innerHTML = `
            <div class="trade-modal-container">
                <div class="trade-modal-header">
                    <h3>
                        ${this.isEdit ? '✏️ Edit Trade' : '➕ Add New Trade'}
                    </h3>
                    <button type="button" class="modal-close-btn" aria-label="Close">×</button>
                </div>
                
                <div class="trade-modal-body">
                    <form id="tradeModalForm" novalidate>
                        <!-- Trade Details Section -->
                        <div class="form-section">
                            <h4>📊 Trade Details</h4>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="modal-symbol">Symbol *</label>
                                    <select id="modal-symbol" name="symbol" required class="enhanced-dropdown">
                                        <option value="">📊 Select Symbol</option>
                                        <option value="XAUUSD">🥇 XAUUSD (Gold)</option>
                                        <option value="US30">🏭 US30 (Dow Jones)</option>
                                        <option value="NAS100">💻 NAS100 (Nasdaq)</option>
                                        <option value="GER40">🇩🇪 GER40 (DAX)</option>
                                    </select>
                                    <div class="field-error"></div>
                                </div>
                                <div class="form-group">
                                    <label for="modal-trade-type">Trade Type *</label>
                                    <select id="modal-trade-type" name="trade_type" required class="enhanced-dropdown">
                                        <option value="">📊 Select Trade Type</option>
                                        <option value="LONG">📈 Long Position</option>
                                        <option value="SHORT">📉 Short Position</option>
                                    </select>
                                    <div class="field-error"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Price Information Section -->
                        <div class="form-section">
                            <h4>💰 Price Information</h4>
                            <div class="entry-prices-container">
                                <div class="entry-price-header">
                                    <label>Entry Prices *</label>
                                    <button type="button" class="btn-add-entry" id="addEntryPriceBtn">
                                        ➕ Add Entry (DCA)
                                    </button>
                                </div>
                                <div id="entryPricesContainer" class="entry-prices-list">
                                    <div class="entry-price-row" data-entry-index="0">
                                        <div class="form-group entry-price-group">
                                            <input type="number" class="entry-price-input" name="entry_prices[]" 
                                                   step="0.01" min="0" required placeholder="Entry Price">
                                            <div class="field-error"></div>
                                        </div>
                                        <div class="form-group position-size-group">
                                            <input type="number" class="position-size-input" name="position_sizes[]" 
                                                   step="0.01" min="0.01" max="9999999" required placeholder="Position Size" value="1">
                                            <div class="field-error"></div>
                                        </div>
                                        <button type="button" class="btn-remove-entry" style="display: none;">🗑️</button>
                                    </div>
                                </div>
                                <div class="avg-entry-display">
                                    <small>Average Entry: $<span id="avgEntryPrice">0.00</span></small>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="modal-exit-price">Exit Price</label>
                                    <input type="number" id="modal-exit-price" name="exit_price" 
                                           step="0.01" min="0">
                                    <div class="field-error"></div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trade Outcome Section -->
                        <div class="form-section">
                            <h4>📈 Trade Outcome</h4>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="modal-outcome">Outcome</label>
                                    <select id="modal-outcome" name="outcome" class="enhanced-dropdown">
                                        <option value="PENDING">⏳ Pending</option>
                                        <option value="WIN">✅ Win</option>
                                        <option value="LOSS">❌ Loss</option>
                                        <option value="BREAKEVEN">⚖️ Breakeven</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="modal-profit-loss">Profit/Loss ($)</label>
                                    <input type="number" id="modal-profit-loss" name="profit_loss" 
                                           step="0.01" placeholder="Enter P&L amount">
                                    <small>Enter your actual profit or loss amount</small>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trade Timing Section -->
                        <div class="form-section">
                            <h4>⏰ Trade Timing</h4>
                            <div class="form-row form-row-3">
                                <div class="form-group">
                                    <label for="modal-trade-date">Trade Date *</label>
                                    <input type="date" id="modal-trade-date" name="trade_date" required>
                                    <div class="field-error"></div>
                                </div>
                                <div class="form-group">
                                    <label for="modal-entry-time">Entry Time</label>
                                    <input type="time" id="modal-entry-time" name="entry_time">
                                </div>
                                <div class="form-group">
                                    <label for="modal-exit-time">Exit Time</label>
                                    <input type="time" id="modal-exit-time" name="exit_time">
                                </div>
                            </div>
                        </div>
                        
                        <!-- Chart Section -->
                        <div class="form-section">
                            <h4>📊 Trade Chart</h4>
                            <div class="form-group">
                                <label for="modal-chart-link">TradingView Chart Link</label>
                                <input type="url" id="modal-chart-link" name="chart_link" 
                                       placeholder="https://tradingview.com/x/... or https://tradingview.com/chart/... or image URL">
                                <small>Paste TradingView chart snapshot link (/x/), regular chart link (/chart/), or direct image URL</small>
                            </div>
                            <div class="chart-preview-container" id="chartPreviewContainer" style="display: none;">
                                <div class="chart-preview-header">
                                    <span>Chart Preview</span>
                                    <button type="button" class="btn-remove-chart" id="removeChartBtn">🗑️ Remove</button>
                                </div>
                                <div class="chart-preview" id="chartPreview">
                                    <img id="chartImage" src="" alt="Trade Chart" style="display: none;">
                                    <div id="chartPlaceholder" class="chart-placeholder">
                                        <span>📊</span>
                                        <p>Chart will appear here</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Notes Section -->
                        <div class="form-section">
                            <h4>📝 Trade Notes</h4>
                            <div class="form-group">
                                <textarea id="modal-notes" name="notes" rows="3" 
                                          placeholder="Trade analysis, lessons learned, strategy notes..." 
                                          maxlength="1000"></textarea>
                                <small><span id="notes-count">0</span>/1000 characters</small>
                            </div>
                        </div>
                        
                        <input type="hidden" id="modal-entry-id" name="entry_id" value="${this.isEdit && this.currentTradeData ? this.currentTradeData.id : ''}">
                    </form>
                </div>
                
                <div class="trade-modal-footer">
                    <button type="button" class="btn btn-secondary modal-cancel-btn">Cancel</button>
                    <button type="submit" class="btn btn-primary modal-submit-btn" form="tradeModalForm">
                        ${this.isEdit ? '💾 Update Trade' : '💾 Save Trade'}
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Bind modal-specific events
        this.bindModalEvents();
    }
    
    bindModalEvents() {
        // Close modal events
        const closeBtn = this.modal.querySelector('.modal-close-btn');
        const cancelBtn = this.modal.querySelector('.modal-cancel-btn');
        
        closeBtn.addEventListener('click', () => this.closeModal());
        cancelBtn.addEventListener('click', () => this.closeModal());
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal) this.closeModal();
        });
        
        // Form submission
        const form = document.getElementById('tradeModalForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });
    }
    
    setupFormInteractions() {
        // Setup DCA entry price functionality
        this.setupDCAFunctionality();
        
        // Auto-set outcome based on P&L input (optional helper)
        const profitLoss = document.getElementById('modal-profit-loss');
        const outcome = document.getElementById('modal-outcome');
        
        const updateOutcomeFromPnL = () => {
            const pnl = parseFloat(profitLoss.value) || 0;
            
            // Only auto-set outcome if it's currently pending and user entered a P&L
            if (outcome.value === 'PENDING' && profitLoss.value.trim() !== '') {
                if (pnl > 0) outcome.value = 'WIN';
                else if (pnl < 0) outcome.value = 'LOSS';
                else outcome.value = 'BREAKEVEN';
            }
        };
        
        // Add event listener for P&L input to optionally set outcome
        profitLoss.addEventListener('blur', updateOutcomeFromPnL);
        
        // Notes character counter
        const notesField = document.getElementById('modal-notes');
        const notesCount = document.getElementById('notes-count');
        
        notesField.addEventListener('input', () => {
            notesCount.textContent = notesField.value.length;
        });
        
        // Chart link functionality
        this.setupChartFunctionality();
    }
    
    setupDCAFunctionality() {
        const addEntryBtn = document.getElementById('addEntryPriceBtn');
        const entryContainer = document.getElementById('entryPricesContainer');
        
        // Add new entry price row
        addEntryBtn.addEventListener('click', () => {
            this.addEntryPriceRow();
        });
        
        // Event delegation for remove buttons and input changes
        entryContainer.addEventListener('click', (e) => {
            if (e.target.classList.contains('btn-remove-entry')) {
                this.removeEntryPriceRow(e.target.closest('.entry-price-row'));
            }
        });
        
        entryContainer.addEventListener('input', () => {
            this.updateAverageEntry();
        });
        
        // Handle spinner button clicks specifically for position size inputs
        entryContainer.addEventListener('change', (e) => {
            if (e.target.classList.contains('position-size-input')) {
                this.updateAverageEntry();
            }
        });
        
        // Handle manual value changes and ensure minimum value
        entryContainer.addEventListener('blur', (e) => {
            if (e.target.classList.contains('position-size-input')) {
                const minValue = parseFloat(e.target.getAttribute('min')) || 0.01;
                const currentValue = parseFloat(e.target.value) || 0;
                
                if (currentValue < minValue) {
                    e.target.value = minValue;
                    this.updateAverageEntry();
                }
            }
        });
    }
    
    addEntryPriceRow() {
        const container = document.getElementById('entryPricesContainer');
        const rows = container.querySelectorAll('.entry-price-row');
        const newIndex = rows.length;
        
        const newRow = document.createElement('div');
        newRow.className = 'entry-price-row';
        newRow.setAttribute('data-entry-index', newIndex);
        
        newRow.innerHTML = `
            <div class="form-group entry-price-group">
                <input type="number" class="entry-price-input" name="entry_prices[]" 
                       step="0.01" min="0" required placeholder="Entry Price ${newIndex + 1}">
                <div class="field-error"></div>
            </div>
            <div class="form-group position-size-group">
                <input type="number" class="position-size-input" name="position_sizes[]" 
                       step="0.01" min="0.01" max="9999999" required placeholder="Position Size" value="1">
                <div class="field-error"></div>
            </div>
            <button type="button" class="btn-remove-entry">🗑️</button>
        `;
        
        container.appendChild(newRow);
        
        // Show remove buttons when there's more than one row
        this.updateRemoveButtons();
        
        // Focus on the new entry price input
        const newInput = newRow.querySelector('.entry-price-input');
        newInput.focus();
    }
    
    removeEntryPriceRow(row) {
        const container = document.getElementById('entryPricesContainer');
        const rows = container.querySelectorAll('.entry-price-row');
        
        // Don't remove if it's the last row
        if (rows.length > 1) {
            row.remove();
            this.updateRemoveButtons();
            this.updateAverageEntry();
        }
    }
    
    updateRemoveButtons() {
        const container = document.getElementById('entryPricesContainer');
        const rows = container.querySelectorAll('.entry-price-row');
        const removeButtons = container.querySelectorAll('.btn-remove-entry');
        
        removeButtons.forEach(btn => {
            btn.style.display = rows.length > 1 ? 'flex' : 'none';
        });
    }
    
    calculateAverageEntry() {
        const entryInputs = document.querySelectorAll('.entry-price-input');
        const sizeInputs = document.querySelectorAll('.position-size-input');
        
        let totalCost = 0;
        let totalSize = 0;
        
        for (let i = 0; i < entryInputs.length; i++) {
            const price = parseFloat(entryInputs[i].value) || 0;
            const size = parseFloat(sizeInputs[i].value) || 0;
            
            if (price > 0 && size > 0) {
                totalCost += price * size;
                totalSize += size;
            }
        }
        
        return totalSize > 0 ? totalCost / totalSize : 0;
    }
    
    calculateTotalPositionSize() {
        const sizeInputs = document.querySelectorAll('.position-size-input');
        let total = 0;
        
        sizeInputs.forEach(input => {
            const size = parseFloat(input.value) || 0;
            total += size;
        });
        
        return total;
    }
    
    updateAverageEntry() {
        const avgEntry = this.calculateAverageEntry();
        document.getElementById('avgEntryPrice').textContent = avgEntry.toFixed(2);
        
        // No automatic P&L calculation - user enters their own P&L
    }
    
    setupChartFunctionality() {
        const chartLinkInput = document.getElementById('modal-chart-link');
        const chartPreviewContainer = document.getElementById('chartPreviewContainer');
        const chartImage = document.getElementById('chartImage');
        const chartPlaceholder = document.getElementById('chartPlaceholder');
        const removeChartBtn = document.getElementById('removeChartBtn');
        
        // Handle chart link input
        chartLinkInput.addEventListener('blur', () => {
            this.loadChartPreview();
        });
        
        chartLinkInput.addEventListener('paste', () => {
            // Small delay to allow paste to complete
            setTimeout(() => {
                this.loadChartPreview();
            }, 100);
        });
        
        // Remove chart functionality
        removeChartBtn.addEventListener('click', () => {
            this.removeChart();
        });
    }
    
    async loadChartPreview() {
        const chartLinkInput = document.getElementById('modal-chart-link');
        const chartPreviewContainer = document.getElementById('chartPreviewContainer');
        const chartImage = document.getElementById('chartImage');
        const chartPlaceholder = document.getElementById('chartPlaceholder');
        
        const url = chartLinkInput.value.trim();
        
        if (!url) {
            chartPreviewContainer.style.display = 'none';
            return;
        }
        
        try {
            // Show preview container with loading state
            chartPreviewContainer.style.display = 'block';
            chartImage.style.display = 'none';
            chartPlaceholder.style.display = 'flex';
            chartPlaceholder.innerHTML = `
                <span>⏳</span>
                <p>Loading chart preview...</p>
            `;
            
            // Handle different URL types
            let imageUrl = url;
            let isDirectImage = false;
            
            // Check if it's already a direct image URL
            if (url.match(/\.(jpg|jpeg|png|gif|webp)(\?.*)?$/i)) {
                isDirectImage = true;
            }
            // Convert TradingView chart links to image URLs
            else if (url.includes('tradingview.com')) {
                const convertedUrl = this.convertTradingViewUrl(url);
                if (convertedUrl) {
                    imageUrl = convertedUrl;
                } else {
                    // Unable to convert, show as link
                    this.showChartAsLink();
                    return;
                }
            }
            
            // Test if the URL is a valid image
            const testImage = new Image();
            testImage.onload = () => {
                chartImage.src = imageUrl;
                chartImage.style.display = 'block';
                chartPlaceholder.style.display = 'none';
                console.log('✅ Chart image loaded successfully:', imageUrl);
            };
            
            testImage.onerror = () => {
                console.warn('❌ Failed to load chart image:', imageUrl);
                this.showChartAsLink();
            };
            
            // Set timeout for image loading
            setTimeout(() => {
                if (chartPlaceholder.innerHTML.includes('Loading')) {
                    console.warn('⏰ Chart image loading timeout');
                    this.showChartAsLink();
                }
            }, 10000); // 10 second timeout
            
            testImage.src = imageUrl;
            
        } catch (error) {
            console.error('❌ Error loading chart preview:', error);
            this.showChartAsLink();
        }
    }
    
    convertTradingViewUrl(url) {
        try {
            console.log('🔄 Converting TradingView URL:', url);
            
            // Handle TradingView snapshot URLs: tradingview.com/x/[ID]
            const snapshotMatch = url.match(/tradingview\.com\/x\/([a-zA-Z0-9]+)/);
            if (snapshotMatch) {
                const chartId = snapshotMatch[1];
                const firstLetter = chartId.charAt(0).toLowerCase();
                const convertedUrl = `https://s3.tradingview.com/snapshots/${firstLetter}/${chartId}.png`;
                console.log('📊 Snapshot URL converted:', convertedUrl);
                return convertedUrl;
            }
            
            // Handle TradingView chart URLs: tradingview.com/chart/[symbol]/[ID]
            const chartMatch = url.match(/tradingview\.com\/chart\/[^\/]+\/([a-zA-Z0-9]+)/);
            if (chartMatch) {
                const chartId = chartMatch[1];
                const firstLetter = chartId.charAt(0).toLowerCase();
                const convertedUrl = `https://s3.tradingview.com/snapshots/${firstLetter}/${chartId}.png`;
                console.log('📈 Chart URL converted:', convertedUrl);
                return convertedUrl;
            }
            
            // Handle TradingView share URLs with layout IDs
            const layoutMatch = url.match(/tradingview\.com\/chart\/([a-zA-Z0-9]+)/);
            if (layoutMatch) {
                const chartId = layoutMatch[1];
                const firstLetter = chartId.charAt(0).toLowerCase();
                const convertedUrl = `https://s3.tradingview.com/snapshots/${firstLetter}/${chartId}.png`;
                console.log('🔗 Layout URL converted:', convertedUrl);
                return convertedUrl;
            }
            
            // Handle direct S3 TradingView URLs
            if (url.includes('s3.tradingview.com/snapshots/')) {
                console.log('🎯 Direct S3 URL detected:', url);
                return url;
            }
            
            // Handle other TradingView image URLs
            if (url.includes('tradingview.com') && url.includes('.png')) {
                console.log('🖼️ Direct TradingView image URL detected:', url);
                return url;
            }
            
            console.warn('❓ Unable to convert TradingView URL - no matching pattern:', url);
            return null;
        } catch (error) {
            console.error('❌ Error converting TradingView URL:', error);
            return null;
        }
    }
    
    showChartAsLink() {
        const chartImage = document.getElementById('chartImage');
        const chartPlaceholder = document.getElementById('chartPlaceholder');
        
        chartImage.style.display = 'none';
        chartPlaceholder.style.display = 'flex';
        chartPlaceholder.innerHTML = `
            <span>🔗</span>
            <p>Chart link saved<br><small>Preview not available - Click "View Chart" in the table to open</small></p>
        `;
    }
    
    removeChart() {
        const chartLinkInput = document.getElementById('modal-chart-link');
        const chartPreviewContainer = document.getElementById('chartPreviewContainer');
        const chartImage = document.getElementById('chartImage');
        const chartPlaceholder = document.getElementById('chartPlaceholder');
        
        chartLinkInput.value = '';
        chartPreviewContainer.style.display = 'none';
        chartImage.src = '';
        chartImage.style.display = 'none';
        chartPlaceholder.style.display = 'flex';
        chartPlaceholder.innerHTML = `
            <span>📊</span>
            <p>Chart will appear here</p>
        `;
    }
    
    populateForm(tradeData) {
        const fields = {
            'modal-symbol': tradeData.symbol,
            'modal-trade-type': tradeData.trade_type,
            'modal-entry-price': tradeData.entry_price,
            'modal-exit-price': tradeData.exit_price,
            'modal-quantity': tradeData.quantity,
            'modal-outcome': tradeData.outcome,
            'modal-profit-loss': tradeData.profit_loss,
            'modal-trade-date': tradeData.trade_date,
            'modal-entry-time': tradeData.entry_time,
            'modal-exit-time': tradeData.exit_time,
            'modal-notes': tradeData.notes,
            'modal-chart-link': tradeData.chart_link,
            'modal-entry-id': tradeData.id
        };
        
        Object.entries(fields).forEach(([fieldId, value]) => {
            const field = document.getElementById(fieldId);
            if (field && value !== null && value !== undefined) {
                field.value = value;
            }
        });
        
        // Update notes counter
        const notesField = document.getElementById('modal-notes');
        const notesCount = document.getElementById('notes-count');
        if (notesField && notesCount) {
            notesCount.textContent = notesField.value.length;
        }
        
        // Load chart preview if chart link exists
        const chartLink = document.getElementById('modal-chart-link');
        if (chartLink && chartLink.value) {
            setTimeout(() => {
                this.loadChartPreview();
            }, 100);
        }
    }
    
    setDefaults() {
        // Set today's date
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('modal-trade-date').value = today;
        
        // Set default outcome
        document.getElementById('modal-outcome').value = 'PENDING';
        
        // Initialize first entry with default position size
        const firstPositionInput = document.querySelector('.position-size-input');
        if (firstPositionInput && !firstPositionInput.value) {
            firstPositionInput.value = '1';
        }
    }
    
    validateForm() {
        const form = document.getElementById('tradeModalForm');
        const errors = {};
        
        // Clear previous errors
        form.querySelectorAll('.field-error').forEach(el => el.textContent = '');
        form.querySelectorAll('.error').forEach(el => el.classList.remove('error'));
        
        // Required field validation
        const requiredFields = {
            'modal-symbol': 'Symbol is required',
            'modal-trade-type': 'Trade type is required',
            'modal-trade-date': 'Trade date is required'
        };
        
        Object.entries(requiredFields).forEach(([fieldId, message]) => {
            const field = document.getElementById(fieldId);
            if (!field.value.trim()) {
                errors[fieldId] = message;
            }
        });
        
        // Validate entry prices
        const entryInputs = document.querySelectorAll('.entry-price-input');
        const sizeInputs = document.querySelectorAll('.position-size-input');
        let hasValidEntry = false;
        
        for (let i = 0; i < entryInputs.length; i++) {
            const entryPrice = parseFloat(entryInputs[i].value) || 0;
            const positionSize = parseFloat(sizeInputs[i].value) || 0;
            
            if (entryPrice > 0 && positionSize > 0) {
                hasValidEntry = true;
            }
            
            if (entryPrice <= 0 && entryInputs[i].value.trim()) {
                errors[`entry-price-${i}`] = 'Entry price must be greater than 0';
                entryInputs[i].classList.add('error');
            }
            
            if (positionSize <= 0 && sizeInputs[i].value.trim()) {
                errors[`position-size-${i}`] = 'Position size must be greater than 0';
                sizeInputs[i].classList.add('error');
            }
        }
        
        if (!hasValidEntry) {
            errors['entry-prices'] = 'At least one valid entry price and position size is required';
        }
        
        // Exit price validation
        const exitPrice = parseFloat(document.getElementById('modal-exit-price').value);
        
        if (exitPrice && exitPrice <= 0) {
            errors['modal-exit-price'] = 'Exit price must be greater than 0';
        }
        
        // Display errors
        Object.entries(errors).forEach(([fieldId, message]) => {
            const field = document.getElementById(fieldId);
            const errorEl = field.parentNode.querySelector('.field-error');
            if (errorEl) {
                errorEl.textContent = message;
                field.classList.add('error');
            }
        });
        
        return Object.keys(errors).length === 0;
    }
    
    async submitForm() {
        console.log('📤 Submitting trade form...');
        
        if (!this.validateForm()) {
            this.showNotification('Please fix the errors above', 'error');
            return;
        }
        
        const form = document.getElementById('tradeModalForm');
        const formData = new FormData(form);
        const tradeData = {};
        
        // Convert FormData to object (excluding array fields)
        for (let [key, value] of formData.entries()) {
            if (value.trim() && !key.includes('[]')) {
                tradeData[key] = value.trim();
            }
        }
        
        // Handle multiple entry prices and position sizes
        const entryInputs = document.querySelectorAll('.entry-price-input');
        const sizeInputs = document.querySelectorAll('.position-size-input');
        
        const entryPrices = [];
        const positionSizes = [];
        
        for (let i = 0; i < entryInputs.length; i++) {
            const price = parseFloat(entryInputs[i].value);
            const size = parseFloat(sizeInputs[i].value);
            
            if (price > 0 && size > 0) {
                entryPrices.push(price);
                positionSizes.push(size);
            }
        }
        
        // Calculate average entry price and total position size for storage
        let totalCost = 0;
        let totalSize = 0;
        
        for (let i = 0; i < entryPrices.length; i++) {
            totalCost += entryPrices[i] * positionSizes[i];
            totalSize += positionSizes[i];
        }
        
        const avgEntryPrice = totalSize > 0 ? totalCost / totalSize : 0;
        
        tradeData.entry_price = avgEntryPrice;
        tradeData.quantity = totalSize;
        tradeData.entry_prices = entryPrices;
        tradeData.position_sizes = positionSizes;
        
        // Convert numeric fields
        if (tradeData.exit_price) tradeData.exit_price = parseFloat(tradeData.exit_price);
        if (tradeData.profit_loss) tradeData.profit_loss = parseFloat(tradeData.profit_loss);
        
        console.log('📊 Trade data:', tradeData);
        
        try {
            const submitBtn = document.querySelector('.modal-submit-btn');
            submitBtn.disabled = true;
            submitBtn.textContent = this.isEdit ? 'Updating...' : 'Saving...';
            
            const url = this.isEdit ? 
                `/journal/api/entry/${tradeData.entry_id}` : 
                '/journal/api/create';
            
            const method = this.isEdit ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(tradeData)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showNotification(
                    this.isEdit ? 'Trade updated successfully!' : 'Trade added successfully!', 
                    'success'
                );
                this.closeModal();
                
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(result.message || 'Failed to save trade');
            }
            
        } catch (error) {
            console.error('❌ Error submitting trade:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            const submitBtn = document.querySelector('.modal-submit-btn');
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.textContent = this.isEdit ? '💾 Update Trade' : '💾 Save Trade';
            }
        }
    }
    
    async viewTrade(entryId) {
        console.log('👁️ Viewing trade:', entryId);
        
        try {
            const response = await fetch(`/journal/api/entry/${entryId}`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.openViewModal(result.data);
            } else {
                throw new Error(result.message || 'Failed to load trade data');
            }
        } catch (error) {
            console.error('❌ Error loading trade:', error);
            this.showNotification(`Error loading trade: ${error.message}`, 'error');
        }
    }
    
    async editTrade(entryId) {
        console.log('✏️ Editing trade:', entryId);
        
        try {
            const response = await fetch(`/journal/api/entry/${entryId}`);
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.openModal(result.data);
            } else {
                throw new Error(result.message || 'Failed to load trade data');
            }
        } catch (error) {
            console.error('❌ Error loading trade:', error);
            this.showNotification(`Error loading trade: ${error.message}`, 'error');
        }
    }
    
    async deleteTrade(entryId) {
        if (!confirm('Are you sure you want to delete this trade? This action cannot be undone.')) {
            return;
        }
        
        console.log('🗑️ Deleting trade:', entryId);
        
        try {
            const response = await fetch(`/journal/api/entry/${entryId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showNotification('Trade deleted successfully!', 'success');
                
                // Refresh the page to show updated data
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error(result.message || 'Failed to delete trade');
            }
        } catch (error) {
            console.error('❌ Error deleting trade:', error);
            this.showNotification(`Error deleting trade: ${error.message}`, 'error');
        }
    }
    
    closeModal() {
        if (this.modal) {
            this.modal.remove();
            this.modal = null;
            this.isEdit = false;
            this.currentTradeData = null;
        }
    }
    
    openViewModal(tradeData) {
        console.log('👁️ Opening view modal for trade:', tradeData);
        
        // Remove existing modal
        this.closeModal();
        
        // Create view modal
        this.modal = document.createElement('div');
        this.modal.setAttribute('data-modal', 'view-modal');
        this.modal.className = 'trade-modal-overlay';
        
        const entryPrices = tradeData.entry_prices && tradeData.entry_prices.length > 0 ? tradeData.entry_prices : [tradeData.entry_price || 0];
        const positionSizes = tradeData.position_sizes && tradeData.position_sizes.length > 0 ? tradeData.position_sizes : [tradeData.quantity || 1];
        
        // Calculate average entry if multiple entries
        let avgEntry = 0;
        let totalSize = 0;
        for (let i = 0; i < entryPrices.length; i++) {
            const price = parseFloat(entryPrices[i]) || 0;
            const size = parseFloat(positionSizes[i]) || 0;
            avgEntry += price * size;
            totalSize += size;
        }
        avgEntry = totalSize > 0 ? avgEntry / totalSize : 0;
        
        const formatPrice = (price) => price ? `$${parseFloat(price).toFixed(2)}` : 'N/A';
        const formatPnL = (pnl) => {
            if (pnl === null || pnl === undefined) return 'N/A';
            const value = parseFloat(pnl);
            const sign = value > 0 ? '+' : '';
            return `${sign}$${value.toFixed(2)}`;
        };
        
        this.modal.innerHTML = `
            <div class="trade-modal-container">
                <div class="trade-modal-header">
                    <h3>👁️ View Trade Details</h3>
                    <button type="button" class="modal-close-btn" aria-label="Close">×</button>
                </div>
                
                <div class="trade-modal-body">
                    <div class="view-trade-content">
                        <!-- Trade Overview -->
                        <div class="view-section">
                            <h4>📊 Trade Overview</h4>
                            <div class="view-grid">
                                <div class="view-item">
                                    <label>Symbol</label>
                                    <span class="value symbol-value">${tradeData.symbol || 'N/A'}</span>
                                </div>
                                <div class="view-item">
                                    <label>Type</label>
                                    <span class="value type-value ${(tradeData.trade_type || '').toLowerCase()}">${tradeData.trade_type || 'N/A'}</span>
                                </div>
                                <div class="view-item">
                                    <label>Date</label>
                                    <span class="value">${tradeData.trade_date || 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Entry Information -->
                        <div class="view-section">
                            <h4>💰 Entry Information</h4>
                            ${entryPrices.length > 1 ? `
                                <div class="view-entries">
                                    ${entryPrices.map((price, i) => `
                                        <div class="view-entry-row">
                                            <span>Entry ${i + 1}: ${formatPrice(price)} × ${positionSizes[i] || 1}</span>
                                        </div>
                                    `).join('')}
                                </div>
                                <div class="view-item avg-entry">
                                    <label>Average Entry</label>
                                    <span class="value">${formatPrice(avgEntry)}</span>
                                </div>
                            ` : `
                                <div class="view-grid">
                                    <div class="view-item">
                                        <label>Entry Price</label>
                                        <span class="value">${formatPrice(tradeData.entry_price)}</span>
                                    </div>
                                    <div class="view-item">
                                        <label>Position Size</label>
                                        <span class="value">${tradeData.quantity || 1}</span>
                                    </div>
                                </div>
                            `}
                            <div class="view-grid">
                                <div class="view-item">
                                    <label>Exit Price</label>
                                    <span class="value">${formatPrice(tradeData.exit_price)}</span>
                                </div>
                                <div class="view-item">
                                    <label>Total Position Size</label>
                                    <span class="value">${totalSize}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Trade Outcome -->
                        <div class="view-section">
                            <h4>📈 Trade Outcome</h4>
                            <div class="view-grid">
                                <div class="view-item">
                                    <label>Outcome</label>
                                    <span class="value outcome-value ${(tradeData.outcome || 'pending').toLowerCase()}">${tradeData.outcome || 'Pending'}</span>
                                </div>
                                <div class="view-item">
                                    <label>Profit/Loss</label>
                                    <span class="value pnl-value ${tradeData.profit_loss > 0 ? 'positive' : tradeData.profit_loss < 0 ? 'negative' : 'neutral'}">${formatPnL(tradeData.profit_loss)}</span>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Timing Information -->
                        <div class="view-section">
                            <h4>⏰ Timing</h4>
                            <div class="view-grid">
                                <div class="view-item">
                                    <label>Entry Time</label>
                                    <span class="value">${tradeData.entry_time || 'N/A'}</span>
                                </div>
                                <div class="view-item">
                                    <label>Exit Time</label>
                                    <span class="value">${tradeData.exit_time || 'N/A'}</span>
                                </div>
                            </div>
                        </div>
                        
                        ${tradeData.chart_link ? `
                        <!-- Chart -->
                        <div class="view-section">
                            <h4>📊 Trade Chart</h4>
                            <div class="view-chart">
                                <div class="chart-preview-view" id="viewChartPreview">
                                    <div class="chart-loading">Loading chart preview...</div>
                                </div>
                                <div class="chart-actions">
                                    <a href="${tradeData.chart_link}" target="_blank" class="chart-link">
                                        🔗 View Full Chart on TradingView
                                    </a>
                                </div>
                            </div>
                        </div>
                        ` : ''}
                        
                        ${tradeData.notes ? `
                        <!-- Notes -->
                        <div class="view-section">
                            <h4>📝 Trade Notes</h4>
                            <div class="view-notes">
                                ${tradeData.notes.replace(/\n/g, '<br>')}
                            </div>
                        </div>
                        ` : ''}
                    </div>
                </div>
                
                <div class="trade-modal-footer">
                    <button type="button" class="btn btn-secondary modal-close-btn">Close</button>
                    <button type="button" class="btn btn-primary edit-from-view-btn" data-entry-id="${tradeData.id}">
                        ✏️ Edit Trade
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.modal);
        
        // Bind modal events
        this.bindViewModalEvents(tradeData.id);
        
        // Load chart preview if chart link exists
        if (tradeData.chart_link) {
            this.loadViewChartPreview(tradeData.chart_link);
        }
    }
    
    bindViewModalEvents(entryId) {
        // Close modal events
        const closeBtns = this.modal.querySelectorAll('.modal-close-btn');
        closeBtns.forEach(btn => {
            btn.addEventListener('click', () => this.closeModal());
        });
        
        // Edit from view button
        const editBtn = this.modal.querySelector('.edit-from-view-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.closeModal();
                this.editTrade(entryId);
            });
        }
        
        // Close on overlay click
        this.modal.addEventListener('click', (e) => {
            if (e.target === this.modal) this.closeModal();
        });
        
        // Close on Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal) this.closeModal();
        });
    }
    
    async loadViewChartPreview(chartUrl) {
        const previewContainer = document.getElementById('viewChartPreview');
        if (!previewContainer) return;
        
        try {
            // Show loading state
            previewContainer.innerHTML = '<div class="chart-loading">⏳ Loading chart preview...</div>';
            
            // Convert TradingView URL to image URL using the same logic as the main modal
            let imageUrl = chartUrl;
            
            if (chartUrl.includes('tradingview.com')) {
                // Extract chart ID from various TradingView URL formats
                const patterns = [
                    /tradingview\.com\/x\/([a-zA-Z0-9]+)/,
                    /tradingview\.com\/chart\/[^\/]+\/([a-zA-Z0-9]+)/,
                    /tradingview\.com\/chart\/([a-zA-Z0-9]+)/
                ];
                
                let chartId = null;
                for (const pattern of patterns) {
                    const match = chartUrl.match(pattern);
                    if (match) {
                        chartId = match[1];
                        break;
                    }
                }
                
                if (chartId) {
                    const firstLetter = chartId.charAt(0).toLowerCase();
                    imageUrl = `https://s3.tradingview.com/snapshots/${firstLetter}/${chartId}.png`;
                }
            }
            
            // Test if the image loads
            const testImage = new Image();
            
            // Set up timeout
            const timeoutId = setTimeout(() => {
                previewContainer.innerHTML = `
                    <div class="chart-fallback">
                        <div class="chart-icon">📊</div>
                        <p>Chart preview not available</p>
                        <small>Click link below to view on TradingView</small>
                    </div>
                `;
            }, 10000);
            
            testImage.onload = () => {
                clearTimeout(timeoutId);
                previewContainer.innerHTML = `
                    <img src="${imageUrl}" alt="Trade Chart Preview" class="chart-preview-image">
                `;
            };
            
            testImage.onerror = () => {
                clearTimeout(timeoutId);
                previewContainer.innerHTML = `
                    <div class="chart-fallback">
                        <div class="chart-icon">🔗</div>
                        <p>Chart image not available</p>
                        <small>Click link below to view on TradingView</small>
                    </div>
                `;
            };
            
            testImage.src = imageUrl;
            
        } catch (error) {
            console.error('Error loading chart preview:', error);
            previewContainer.innerHTML = `
                <div class="chart-fallback">
                    <div class="chart-icon">⚠️</div>
                    <p>Error loading chart preview</p>
                    <small>Click link below to view on TradingView</small>
                </div>
            `;
        }
    }
    
    showNotification(message, type = 'info') {
        // Remove existing notifications
        document.querySelectorAll('.notification').forEach(n => n.remove());
        
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 10001;
            background: ${type === 'success' ? '#28a745' : type === 'error' ? '#dc3545' : '#ffc107'};
            color: white; padding: 16px 24px; border-radius: 8px;
            font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: slideInRight 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            if (notification.parentNode) {
                notification.style.animation = 'slideOutRight 0.3s ease';
                setTimeout(() => notification.remove(), 300);
            }
        }, 4000);
    }
}

// Initialize the modal system
const tradingJournalModal = new TradingJournalModal();

// Export for global access (backward compatibility)
window.openTradeModal = (tradeData) => tradingJournalModal.openModal(tradeData);
window.closeModal = () => tradingJournalModal.closeModal();

console.log('✅ Trading Journal Modal System loaded successfully');
