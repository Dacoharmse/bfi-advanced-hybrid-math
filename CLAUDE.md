# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Core Application Architecture

### System Overview
This is a **BFI Signals AI Trading Dashboard** - an advanced Flask-based web application that generates automated trading signals using the "Hybrid Math Strategy" for financial markets (NASDAQ-100, Dow Jones, Gold, etc.). The system combines real-time data fetching, AI-powered analysis, signal generation, and Discord integration.

### Main Application Entry Points

#### Web Dashboard
- **Primary Entry**: `python core/dashboard.py` or `python app.py`
- **Dashboard URL**: http://localhost:5000
- **Launcher Scripts**:
  - Windows: `start_dashboard.bat`
  - Linux/Mac: `python3 scripts/start_dashboard.py`

#### Signal Generation
- **Manual Signals**: `python core/main.py` (standalone signal generation)
- **Auto Signals**: `python trigger_auto_signals.py`
- **Test Mode**: `python core/main.py --test-connection`

### Development Commands

#### Setup and Installation
```bash
# Automated setup
python scripts/easy_install.py

# Manual setup
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

#### Running the Application
```bash
# Start the web dashboard (primary method)
cd core && python dashboard.py

# Alternative entry points
python app.py                    # Main Flask app
python core/main.py             # Standalone signal generation
python trigger_auto_signals.py  # Automated signal generation
```

#### Database Management
```bash
# Database is SQLite-based (ai_learning.db)
# Located in: core/ai_learning.db
# No migration commands needed - auto-created on first run
```

## Project Structure

### Core Architecture Components

#### `/core/` - Main Application Directory
- **dashboard.py** - Primary Flask web application (40,000+ lines)
  - Routes: `/`, `/signals`, `/journal`, `/admin`, `/api/*`
  - Authentication system with session management
  - Real-time market data integration
  - AI signal generation interface
  
- **ai_engine.py** - AI/ML processing engine
  - Sentiment analysis using local transformers models
  - Signal probability calculation
  - Learning from historical performance
  - Risk assessment algorithms

- **strategy.py** - Hybrid Math Trading Strategy
  - Implementation of Prophet Bonang's "Hybrid Math Strategy"
  - Calculates entry/exit points, take profits, stop losses
  - Risk-reward ratio analysis
  - Multi-timeframe analysis

- **data_fetch.py** - Market Data Acquisition
  - Yahoo Finance API integration
  - Real-time price data fetching
  - Historical data analysis
  - Fallback data sources (MarketWatch scraping)

- **discord_*.py** - Discord Integration
  - `discord_working.py` - Main Discord posting functionality
  - `discord_signals.py` - Signal formatting for Discord
  - `discord_post.py` - Legacy Discord functions

#### `/templates/` - Flask Templates
- Modern responsive design with multiple themes
- `base_modern.html` - Main layout template
- Component-based architecture in `/components/`
- Pages: dashboard, signals, journal, admin panel

#### `/static/` - Frontend Assets
- CSS: Modern styling with animations (`main.css`, `subtle_animations.css`)
- JavaScript: Real-time updates, AJAX functionality
- Images: Trading icons, favicons, logos

### Key Configuration Files

#### Environment Configuration
- **`.env`** - Environment variables (created by installer)
  ```
  DISCORD_WEBHOOK_URL=your_webhook_here
  DATABASE_URL=sqlite:///ai_learning.db
  FLASK_ENV=production
  ```

- **`config.py`** - Application configuration
  - Data source settings (Alpha Vantage, Yahoo Finance, Finnhub)
  - Symbol mappings and display names
  - API rate limits and fallback configurations

#### Database Schema
- **SQLite database**: `core/ai_learning.db`
- Tables: signal_performance, users, journal_entries
- Auto-created on first run with proper schema

## Data Flow Architecture

### Signal Generation Pipeline
1. **Data Acquisition** (`data_fetch.py`) → Market data from multiple sources
2. **Strategy Analysis** (`strategy.py`) → Apply Hybrid Math calculations
3. **AI Enhancement** (`ai_engine.py`) → Sentiment analysis and risk assessment
4. **Signal Output** → Dashboard display and Discord posting

### Web Dashboard Flow
1. **Authentication** → Session-based login system
2. **Real-time Data** → WebSocket-like updates every 15 seconds
3. **Signal Management** → Manual and automated signal generation
4. **Performance Tracking** → Historical analysis and learning

## Integration Points

### External APIs
- **Yahoo Finance** - Primary data source (yfinance library)
- **Alpha Vantage** - Secondary data source (API key required)
- **Discord Webhooks** - Signal notifications
- **Google Gemini** - Optional AI enhancements (API key optional)

### Database Integration
- **SQLite** - Primary storage (ai_learning.db)
- **Supabase** - Optional cloud storage (see `storage/` directory)
- Auto-migration and schema updates on startup

## Common Development Tasks

### Adding New Trading Symbols
1. Update `config.py` symbols configuration
2. Add display name mapping in `strategy.py:get_display_name()`
3. Test data fetching with new symbol

### Modifying Trading Strategy
1. Core logic in `strategy.py:calculate_signal()`
2. Risk calculations in `ai_engine.py`
3. Update Discord formatting in `discord_signals.py`

### Custom AI Models
1. Local models loaded in `ai_engine.py:try_initialize_local_models()`
2. Sentiment analysis in `ai_engine.py:analyze_sentiment_ai()`
3. Performance learning in database for continuous improvement

## Deployment Architecture

### Production Deployment
- **App Entry**: `app.py` (WSGI-compatible)
- **Port**: 5000 (configurable via PORT env var)
- **Static Files**: Served by Flask (consider nginx for production)
- **Database**: SQLite (migrate to PostgreSQL for scaling)

### Environment Variables for Production
```bash
FLASK_ENV=production
DEBUG=False
DISCORD_WEBHOOK_URL=your_production_webhook
ALPHA_VANTAGE_API_KEY=your_api_key  # Optional
GEMINI_API_KEY=your_api_key         # Optional
```

## Testing and Debugging

### Test Commands
```bash
# Test Discord connection
python core/main.py --test-connection

# Test signal generation (no Discord posting)
python core/main.py --dry-run

# Test specific components
python core/test_manual_journal.py
python core/test_flask_routes.py
```

### Debug Mode
- Set `FLASK_ENV=development` in `.env`
- Enable debug logging in `core/dashboard.py`
- Use browser dev tools for frontend debugging

## Security Considerations

### Authentication
- Session-based authentication (Flask-Session)
- Admin panel with role-based access control
- User registration/login system with password hashing

### API Security
- Rate limiting on external API calls
- Webhook URL validation for Discord
- Input sanitization for user data

### Data Protection
- SQLite database file permissions
- Environment variable isolation
- No hardcoded secrets in codebase