/**
 * BFI Signals Page JavaScript
 * Handles filtering, search, and interactive functionality
 */

class SignalsPageManager {
    constructor() {
        this.currentFilter = 'all';
        this.searchTerm = '';
        this.signals = [];
        this.filteredSignals = [];
        
        this.init();
    }

    init() {
        console.log('🔧 Initializing Signals Page Manager...');
        
        // Initialize signals data
        this.loadSignalsData();
        
        // Update time displays
        this.updateTimeDisplays();
        
        // Setup auto-refresh
        this.setupAutoRefresh();
        
        // Update filter counts
        this.updateFilterCounts();
        
        console.log('✅ Signals Page Manager Ready');
    }

    loadSignalsData() {
        // Collect signal data from DOM
        const signalCards = document.querySelectorAll('.signal-card');
        this.signals = Array.from(signalCards).map(card => {
            return {
                id: card.dataset.id,
                symbol: card.dataset.symbol,
                type: card.dataset.type,
                risk: card.dataset.risk,
                outcome: card.dataset.outcome,
                timestamp: card.dataset.timestamp,
                riskyOutcome: card.dataset.riskyOutcome,
                element: card
            };
        });
        
        this.filteredSignals = [...this.signals];
        console.log(`📊 Loaded ${this.signals.length} signals`);
    }

    updateTimeDisplays() {
        // Update relative timestamps
        const timestampElements = document.querySelectorAll('.timestamp-value');
        timestampElements.forEach(element => {
            const timestamp = element.dataset.timestamp;
            if (timestamp) {
                const relativeTime = this.getRelativeTime(new Date(timestamp));
                element.title = timestamp; // Show full timestamp on hover
                element.textContent = relativeTime;
            }
        });
    }

    getRelativeTime(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(diff / 3600000);
        const days = Math.floor(diff / 86400000);

        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes}m ago`;
        if (hours < 24) return `${hours}h ago`;
        if (days < 7) return `${days}d ago`;
        return date.toLocaleDateString();
    }

    updateFilterCounts() {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const weekStart = new Date(today);
        weekStart.setDate(today.getDate() - today.getDay());

        let todayCount = 0;
        let weekCount = 0;

        this.signals.forEach(signal => {
            const signalDate = new Date(signal.timestamp);
            const signalDay = new Date(signalDate.getFullYear(), signalDate.getMonth(), signalDate.getDate());
            
            if (signalDay.getTime() === today.getTime()) {
                todayCount++;
            }
            if (signalDate >= weekStart) {
                weekCount++;
            }
        });

        // Update tab counts
        this.updateTabCount('today', todayCount);
        this.updateTabCount('week', weekCount);
    }

    updateTabCount(filter, count) {
        const countElement = document.getElementById(`${filter}-count`);
        if (countElement) {
            countElement.textContent = count;
        }
    }

    setActiveFilter(filter) {
        console.log(`🔍 Setting active filter: ${filter}`);
        
        // Update active tab
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        const activeTab = document.querySelector(`[data-filter="${filter}"]`);
        if (activeTab) {
            activeTab.classList.add('active');
        }

        this.currentFilter = filter;
        this.applyFilters();
    }

    performSearch() {
        const searchInput = document.getElementById('signalSearch');
        this.searchTerm = searchInput.value.toLowerCase().trim();
        console.log(`🔍 Searching for: "${this.searchTerm}"`);
        this.applyFilters();
    }

    applyFilters() {
        console.log(`🔧 Applying filters - Filter: ${this.currentFilter}, Search: "${this.searchTerm}"`);
        
        // Get advanced filter values
        const symbolFilter = document.getElementById('symbolFilter')?.value || '';
        const riskFilter = document.getElementById('riskFilter')?.value || '';
        const typeFilter = document.getElementById('typeFilter')?.value || '';

        // Show loading
        this.showLoading();

        // Filter signals
        this.filteredSignals = this.signals.filter(signal => {
            // Date-based filters
            if (this.currentFilter === 'today') {
                const today = new Date();
                const signalDate = new Date(signal.timestamp);
                const isToday = today.toDateString() === signalDate.toDateString();
                if (!isToday) return false;
            }

            if (this.currentFilter === 'week') {
                const now = new Date();
                const weekStart = new Date(now);
                weekStart.setDate(now.getDate() - now.getDay());
                const signalDate = new Date(signal.timestamp);
                if (signalDate < weekStart) return false;
            }

            // Outcome filters
            if (this.currentFilter === 'wins') {
                if (signal.outcome !== '1') return false;
            }

            if (this.currentFilter === 'pending') {
                if (signal.outcome && signal.outcome !== 'null' && signal.outcome !== '') return false;
            }

            // Search filter
            if (this.searchTerm) {
                const searchableText = `${signal.symbol} ${signal.type} ${signal.risk}`.toLowerCase();
                if (!searchableText.includes(this.searchTerm)) return false;
            }

            // Advanced filters
            if (symbolFilter && !signal.symbol.includes(symbolFilter)) return false;
            if (riskFilter && signal.risk !== riskFilter) return false;
            if (typeFilter && !signal.type.includes(typeFilter)) return false;

            return true;
        });

        // Update display
        setTimeout(() => {
            this.updateSignalsDisplay();
            this.hideLoading();
        }, 300);
    }

    updateSignalsDisplay() {
        console.log(`📊 Displaying ${this.filteredSignals.length} of ${this.signals.length} signals`);
        
        // Hide all signals
        this.signals.forEach(signal => {
            signal.element.classList.add('hidden');
        });

        // Show filtered signals
        this.filteredSignals.forEach(signal => {
            signal.element.classList.remove('hidden');
        });

        // Update empty state
        this.updateEmptyState();
    }

    updateEmptyState() {
        const signalsGrid = document.getElementById('signalsGrid');
        const emptyState = document.querySelector('.empty-state');
        
        if (this.filteredSignals.length === 0 && this.signals.length > 0) {
            // Show "no results" message
            if (signalsGrid) {
                signalsGrid.style.display = 'none';
            }
            
            if (!document.querySelector('.no-results-state')) {
                const noResults = document.createElement('div');
                noResults.className = 'empty-state no-results-state';
                noResults.innerHTML = `
                    <div class="empty-icon">🔍</div>
                    <h3 class="empty-title">No Signals Found</h3>
                    <p class="empty-message">
                        No signals match your current filters. Try adjusting your search criteria.
                    </p>
                    <button class="btn btn-secondary" onclick="signalsManager.clearAllFilters()">
                        <span class="btn-icon">🗑️</span>
                        Clear All Filters
                    </button>
                `;
                
                const container = document.getElementById('signalsContainer');
                container.appendChild(noResults);
            }
        } else {
            // Hide no results message
            const noResults = document.querySelector('.no-results-state');
            if (noResults) {
                noResults.remove();
            }
            
            if (signalsGrid) {
                signalsGrid.style.display = 'grid';
            }
        }
    }

    clearAllFilters() {
        console.log('🗑️ Clearing all filters');
        
        // Reset filter controls
        document.getElementById('signalSearch').value = '';
        document.getElementById('symbolFilter').value = '';
        document.getElementById('riskFilter').value = '';
        document.getElementById('typeFilter').value = '';
        
        // Reset internal state
        this.searchTerm = '';
        this.setActiveFilter('all');
    }

    showLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'flex';
        }
    }

    hideLoading() {
        const loadingOverlay = document.getElementById('loadingOverlay');
        if (loadingOverlay) {
            loadingOverlay.style.display = 'none';
        }
    }

    setupAutoRefresh() {
        // Auto-refresh every 5 minutes when page is visible
        setInterval(() => {
            if (!document.hidden) {
                console.log('🔄 Auto-refreshing signals...');
                this.refreshSignals();
            }
        }, 300000); // 5 minutes
    }

    refreshSignals() {
        console.log('🔄 Refreshing signals data...');
        this.showLoading();
        
        // Reload the page to get fresh data
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    exportSignals() {
        console.log('📤 Exporting signals data...');
        
        const visibleSignals = this.filteredSignals;
        if (visibleSignals.length === 0) {
            this.showNotification('No signals to export', 'warning');
            return;
        }

        // Prepare CSV data
        const headers = ['ID', 'Symbol', 'Type', 'Risk Level', 'Probability', 'Date', 'Main Outcome', 'Risky Play'];
        const csvData = [headers];

        visibleSignals.forEach(signal => {
            const card = signal.element;
            const row = [
                signal.id,
                signal.symbol,
                signal.type,
                signal.risk,
                card.querySelector('.probability-value')?.textContent || '',
                signal.timestamp,
                this.getOutcomeText(signal.outcome),
                this.getOutcomeText(signal.riskyOutcome)
            ];
            csvData.push(row);
        });

        // Create and download CSV
        const csvContent = csvData.map(row => 
            row.map(field => `"${field}"`).join(',')
        ).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `bfi_signals_${new Date().toISOString().slice(0, 10)}.csv`);
        link.style.visibility = 'hidden';
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        this.showNotification(`Exported ${visibleSignals.length} signals successfully!`, 'success');
    }

    getOutcomeText(outcome) {
        switch(outcome) {
            case '1': return 'Win';
            case '0': return 'Loss';
            case '2': return 'Breakeven';
            default: return 'Pending';
        }
    }

    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-icon">
                    ${type === 'success' ? '✅' : type === 'warning' ? '⚠️' : type === 'error' ? '❌' : 'ℹ️'}
                </span>
                <span class="notification-message">${message}</span>
            </div>
        `;
        
        // Style the notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 16px 20px;
            background: var(--card-bg);
            border: 1px solid var(--golden-accent);
            border-radius: 12px;
            color: var(--text-primary);
            box-shadow: var(--golden-glow);
            z-index: 10000;
            backdrop-filter: blur(10px);
            transform: translateX(100%);
            transition: transform 0.3s ease;
            max-width: 400px;
            word-wrap: break-word;
        `;

        // Add specific colors for types
        if (type === 'success') {
            notification.style.borderColor = 'var(--success-color)';
        } else if (type === 'error') {
            notification.style.borderColor = 'var(--danger-color)';
        } else if (type === 'warning') {
            notification.style.borderColor = 'var(--warning-color)';
        }

        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(0)';
        }, 100);

        // Auto-remove after 4 seconds
        setTimeout(() => {
            notification.style.transform = 'translateX(100%)';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 4000);
    }
}

// Global functions for template integration
let signalsManager;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    signalsManager = new SignalsPageManager();
    
    // Make functions globally available for onclick handlers
    window.setActiveFilter = (filter) => signalsManager.setActiveFilter(filter);
    window.performSearch = () => signalsManager.performSearch();
    window.applyFilters = () => signalsManager.applyFilters();
    window.refreshSignals = () => signalsManager.refreshSignals();
    window.exportSignals = () => signalsManager.exportSignals();
});

// Signal interaction functions
function updateOutcome(signalId, outcome, type) {
    if (!outcome) return;
    
    console.log(`🔄 Updating ${type} outcome for signal ${signalId}: ${outcome}`);
    
    const data = {
        signal_id: signalId,
        outcome: outcome,
        type: type
    };
    
    // Show loading
    signalsManager.showLoading();
    
    fetch('/api/update_outcome', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        signalsManager.hideLoading();
        
        if (result.success) {
            signalsManager.showNotification('Outcome updated successfully!', 'success');
            
            // Update the UI immediately
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            signalsManager.showNotification(result.error || 'Failed to update outcome', 'error');
        }
    })
    .catch(error => {
        signalsManager.hideLoading();
        console.error('Error updating outcome:', error);
        signalsManager.showNotification('Error updating outcome: ' + error.message, 'error');
    });
}

function deleteSignal(signalId) {
    if (!confirm('Are you sure you want to delete this signal? This action cannot be undone.')) {
        return;
    }
    
    console.log(`🗑️ Deleting signal ${signalId}`);
    
    // Show loading
    signalsManager.showLoading();
    
    fetch(`/api/delete_signal/${signalId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        signalsManager.hideLoading();
        
        if (result.success) {
            signalsManager.showNotification('Signal deleted successfully!', 'success');
            
            // Remove the signal card from DOM
            const signalCard = document.querySelector(`[data-id="${signalId}"]`);
            if (signalCard) {
                signalCard.style.animation = 'fadeOut 0.3s ease';
                setTimeout(() => {
                    signalCard.remove();
                    // Reload to update stats
                    location.reload();
                }, 300);
            }
        } else {
            signalsManager.showNotification(result.error || 'Failed to delete signal', 'error');
        }
    })
    .catch(error => {
        signalsManager.hideLoading();
        console.error('Error deleting signal:', error);
        signalsManager.showNotification('Error deleting signal: ' + error.message, 'error');
    });
}

function viewSignalDetails(signalId) {
    console.log(`👁️ Viewing details for signal ${signalId}`);
    
    const signalCard = document.querySelector(`[data-id="${signalId}"]`);
    if (!signalCard) return;
    
    // Extract signal data
    const signalData = {
        id: signalId,
        symbol: signalCard.dataset.symbol,
        type: signalCard.dataset.type,
        risk: signalCard.dataset.risk,
        outcome: signalCard.dataset.outcome,
        timestamp: signalCard.dataset.timestamp,
        riskyOutcome: signalCard.dataset.riskyOutcome,
        probability: signalCard.querySelector('.probability-value')?.textContent || 'N/A'
    };
    
    // Build modal content
    const modalBody = document.getElementById('signalModalBody');
    modalBody.innerHTML = `
        <div class="signal-detail-grid">
            <div class="detail-row">
                <strong>Signal ID:</strong>
                <span>#${signalData.id}</span>
            </div>
            <div class="detail-row">
                <strong>Symbol:</strong>
                <span class="symbol-highlight">${signalData.symbol}</span>
            </div>
            <div class="detail-row">
                <strong>Signal Type:</strong>
                <span class="type-badge ${signalData.type.toLowerCase()}">${signalData.type}</span>
            </div>
            <div class="detail-row">
                <strong>Risk Level:</strong>
                <span class="risk-badge risk-${signalData.risk}">${signalData.risk.charAt(0).toUpperCase() + signalData.risk.slice(1)}</span>
            </div>
            <div class="detail-row">
                <strong>Probability:</strong>
                <span class="probability-highlight">${signalData.probability}</span>
            </div>
            <div class="detail-row">
                <strong>Generated:</strong>
                <span>${new Date(signalData.timestamp).toLocaleString()}</span>
            </div>
            <div class="detail-row">
                <strong>Main Outcome:</strong>
                <span class="outcome-badge">${signalsManager.getOutcomeText(signalData.outcome)}</span>
            </div>
            <div class="detail-row">
                <strong>Risky Play:</strong>
                <span class="outcome-badge">${signalsManager.getOutcomeText(signalData.riskyOutcome)}</span>
            </div>
        </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .signal-detail-grid {
            display: grid;
            gap: 16px;
        }
        .detail-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 0;
            border-bottom: 1px solid var(--golden-accent);
        }
        .detail-row:last-child {
            border-bottom: none;
        }
        .symbol-highlight {
            font-weight: 700;
            color: var(--golden-primary);
        }
        .probability-highlight {
            font-weight: 700;
            color: var(--golden-primary);
        }
        .type-badge, .risk-badge, .outcome-badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
        }
    `;
    document.head.appendChild(style);
    
    // Show modal
    const modal = document.getElementById('signalModal');
    modal.style.display = 'flex';
    modal.classList.add('show');
}

function closeSignalModal() {
    const modal = document.getElementById('signalModal');
    modal.classList.remove('show');
    setTimeout(() => {
        modal.style.display = 'none';
    }, 300);
}

// Close modal when clicking outside
document.addEventListener('click', function(event) {
    const modal = document.getElementById('signalModal');
    if (event.target === modal) {
        closeSignalModal();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(event) {
    // ESC key closes modal
    if (event.key === 'Escape') {
        closeSignalModal();
    }
    
    // Ctrl/Cmd + F focuses search
    if ((event.ctrlKey || event.metaKey) && event.key === 'f') {
        event.preventDefault();
        const searchInput = document.getElementById('signalSearch');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Ctrl/Cmd + E exports data
    if ((event.ctrlKey || event.metaKey) && event.key === 'e') {
        event.preventDefault();
        exportSignals();
    }
});

// Add CSS for animations
const animationStyles = document.createElement('style');
animationStyles.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; transform: scale(1); }
        to { opacity: 0; transform: scale(0.8); }
    }
    
    .notification-content {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .notification-icon {
        font-size: 1.2rem;
    }
    
    .notification-message {
        flex: 1;
        font-weight: 500;
    }
`;
document.head.appendChild(animationStyles);