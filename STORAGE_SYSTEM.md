# BFI Signals Storage System

## 📊 Overview

The BFI Signals Storage System provides a robust dual-storage solution for market data and signals:

- **Primary Storage:** Supabase (Cloud database)
- **Backup Storage:** Local files (JSON format)
- **Automatic Fallback:** Seamless switching between storage systems
- **Scheduled Capture:** Daily market close data at 23:05 GMT+2

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Market Data   │───▶│  Data Manager   │───▶│   Storage       │
│   (Live Feed)   │    │  (Dual System)  │    │   Systems       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────┐         ┌─────────────┐
                       │  Scheduler  │         │  Supabase   │
                       │ (23:05 GMT+2)│         │  + Local    │
                       └─────────────┘         └─────────────┘
```

## 🚀 Quick Start

### 1. Installation
```bash
# Install dependencies and setup
python setup_storage.py

# Or install manually
pip install supabase schedule pytz python-dateutil
```

### 2. Database Setup
1. Go to your Supabase dashboard
2. Navigate to SQL Editor
3. Execute the SQL script in `database_schema.sql`
4. Verify tables are created

### 3. Test the System
```bash
# Run comprehensive tests
python test_storage_system.py
```

### 4. Start Data Capture
```bash
# Start the scheduler (runs daily at 23:05 GMT+2)
python core/storage/scheduler.py --run

# Or test capture immediately
python core/storage/scheduler.py --test
```

## 📅 Trading Logic

### **Signal Timing:**
- **Data Capture:** 23:05 GMT+2 (market close)
- **Signal Period:** 23:05 (Day N) → 23:05 (Day N+1) uses Day N closing data
- **Today (30/07/2025):** Uses **29/07/2025 closing data** ✅

### **Example:**
```
29/07/2025 23:05 GMT+2 → Capture 29/07 closing data
30/07/2025 00:00-23:05 → All signals use 29/07 data
30/07/2025 23:05 GMT+2 → Capture 30/07 closing data
31/07/2025 00:00-23:05 → All signals use 30/07 data
```

## 🗄️ Database Schema

### **market_close_data**
```sql
- id: Primary key
- capture_date: Date of market close
- symbol: Trading symbol (NASDAQ, DOW, GOLD)
- price: Closing price
- change_amount: Net change
- change_percent: Percentage change
- previous_close: Previous closing price
- daily_high: Day's highest price
- daily_low: Day's lowest price
- raw_change: Raw change value
- captured_at: Timestamp of capture
- source: Data source identifier
```

### **signals**
```sql
- id: Primary key
- signal_date: Date signal was generated
- symbol: Trading symbol
- signal_type: auto/manual/semi_auto
- bias: LONG/SHORT
- current_value: Current market value
- take_profit: Take profit level
- entry1/entry2: Entry points
- sl_tight/sl_wide: Stop loss levels
- probability_percentage: Signal confidence
- cv_position: CV position in daily range
- signal_data: Complete signal (JSONB)
- posted_to_discord: Discord posting status
- created_at: Creation timestamp
```

## 💾 Local Storage Structure

```
data/
├── backups/          # Daily backups
│   ├── market_data_2025-07-29.json
│   ├── signals_2025-07-29.json
│   └── full_backup_2025-07-30.json
├── daily/            # Daily data files
│   ├── 2025-07-29.json
│   └── signals_2025-07-29.json
└── current/          # Latest data
    └── market_data.json
```

## 🔧 API Integration

### **Dashboard Integration**
The storage system integrates seamlessly with the existing dashboard:

```python
# Get yesterday's closing data (correct for signals)
from storage_integration import get_latest_market_close_data
market_data = get_latest_market_close_data()

# Save generated signals
from storage_integration import save_signal_to_storage
save_signal_to_storage(signal_data)
```

### **API Endpoints**
- `/api/market_close_data` - Returns yesterday's closing data
- Automatic fallback to old system if new storage unavailable

## 📊 Usage Examples

### **Manual Data Capture**
```bash
# Capture data for specific date
python core/storage/scheduler.py --manual 2025-07-29

# Test capture process
python core/storage/scheduler.py --test
```

### **Programmatic Usage**
```python
from storage.data_manager import data_manager
from datetime import date

# Save market data
market_data = {
    'nasdaq': {
        'price': '23,336.25',
        'change': '-20.02',
        'previousClose': '23,356.27'
    }
}
results = data_manager.save_market_close_data(date(2025, 7, 29), market_data)

# Retrieve data
data = data_manager.get_market_close_data(date(2025, 7, 29))
latest = data_manager.get_latest_market_close_data()
```

## 🔄 Automatic Features

### **Daily Schedule**
- **23:05 GMT+2:** Capture market close data
- **Automatic backup:** Create daily backup files
- **Cleanup:** Remove old backups (30+ days)
- **Sync:** Synchronize between Supabase and local storage

### **Fallback System**
1. **Primary:** Try Supabase for all operations
2. **Fallback:** Use local storage if Supabase unavailable
3. **Graceful:** Continue operation with reduced functionality
4. **Recovery:** Automatic sync when connection restored

## 🔍 Monitoring & Logging

### **Log Files**
- `logs/scheduler.log` - Data capture operations
- Console output with detailed status information

### **Status Checking**
```python
from storage_integration import get_storage_system_status
status = get_storage_system_status()
# Returns: {'supabase': True/False, 'local': True/False}
```

## 🛠️ Troubleshooting

### **Common Issues**

#### 1. Supabase Connection Failed
```bash
# Check credentials in core/storage/supabase_client.py
# Verify database schema is created
# Test connection: python test_storage_system.py
```

#### 2. Dependencies Missing
```bash
# Install required packages
pip install supabase schedule pytz python-dateutil
```

#### 3. Permission Errors
```bash
# Ensure write permissions for data/ directory
chmod -R 755 data/
```

#### 4. Timezone Issues
```bash
# System timezone should be set correctly
# Scheduler uses Europe/Berlin (GMT+2)
```

### **Testing Commands**
```bash
# Test complete system
python test_storage_system.py

# Test data manager only
python core/storage/data_manager.py

# Test scheduler
python core/storage/scheduler.py --test

# Test integration
python core/storage_integration.py
```

## 📋 Migration Notes

### **From Old System**
The new storage system is backward compatible:
- Existing dashboard continues to work
- Automatic fallback to old system
- Gradual migration of data
- No disruption to signals

### **Data Migration**
```bash
# Manual migration (if needed)
# Export from old system: market_data.pkl
# Import to new system: use data_manager.save_market_close_data()
```

## 🎯 Signal Accuracy

### **Correct Data Usage**
✅ **Today (30/07/2025):** Uses 29/07/2025 closing data
- NASDAQ: 23,336.25 (Change: -20.02)
- DOW: 44,603.18 (Change: -234.38)

❌ **Incorrect:** Using live data from 30/07/2025
- NASDAQ: 23,308.30 (Change: -47.97)

### **Verification**
```bash
# Verify signal data source
curl http://localhost:5000/api/market_close_data
# Should return yesterday's closing data, not live data
```

## 🚀 Future Enhancements

- [ ] Real-time Supabase subscriptions
- [ ] Advanced backup strategies
- [ ] Data analytics dashboard
- [ ] Historical data visualization
- [ ] Performance metrics
- [ ] Automated testing suite
- [ ] Multi-timezone support

## 📞 Support

For issues or questions:
1. Check logs in `logs/scheduler.log`
2. Run `python test_storage_system.py`
3. Verify Supabase dashboard settings
4. Check database schema creation

## 📜 License

Part of BFI Signals by Bonang Financial Institute - Trade at your own risk.