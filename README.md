# BFI Signals - Hybrid Math Trading Bot

An automated trading signal generator that implements the "Hybrid Math" 1-hour strategy for NASDAQ-100 and other financial instruments. The bot analyzes market data and posts trading signals to Discord channels when you run it manually each morning.

## 📋 What This Project Does

This is a sophisticated Python trading bot that:
- **Fetches real-time market data** using Yahoo Finance API
- **Analyzes price action** using the Hybrid Math 1-hour strategy
- **Generates trading signals** with entry points, take profits, and stop losses
- **Posts signals to Discord** with beautiful formatting and risk analysis
- **Runs when you want** - execute manually each morning for fresh signals
- **Supports multiple symbols** (NASDAQ-100, stocks, ETFs, etc.)

## 🚀 Quick Start (Automatic Setup)

### Option 1: Use the Setup Script (Recommended)

1. **Run the setup script:**
   
   **On Windows (PowerShell):**
   ```powershell
   .\setup.bat
   ```
   
   **On macOS/Linux:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

2. **Configure Discord webhook** (see [Discord Setup Guide](DISCORD_SETUP.md))

3. **Test the bot:**
   ```bash
   # Activate virtual environment
   source venv/bin/activate    # macOS/Linux
   venv\Scripts\activate       # Windows
   
   # Test signal generation
   python main.py --test
   
   # Start the daily scheduler
   python main.py
   ```

### Option 2: Manual Setup

If you prefer to understand each step, follow the manual instructions below.

## 🛠️ Manual Setup Instructions

### Step 1: Check if Python is Installed

1. Open your terminal/command prompt
2. Type: `python --version` or `python3 --version`
3. You should see something like "Python 3.8.x" or newer
4. If not installed, download Python from [python.org](https://python.org)

### Step 2: Create Project Directory and Virtual Environment

```bash
# Create project directory
mkdir bfi-signals
cd bfi-signals

# Initialize git repository
git init

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a file named `.env` in the project root:

```env
# Environment Variables for BFI Signals Project
# This file stores sensitive configuration data
# Never commit this file to version control!

# Discord Integration (REQUIRED)
# Get your webhook URL from Discord: Server Settings > Integrations > Webhooks
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE

# Trading Configuration
# Comma-separated list of symbols to analyze (default: ^NDX for NASDAQ-100)
TRADING_SYMBOLS=^NDX

# Discord Formatting
# Use enhanced Discord formatting with embeds (true/false)
USE_ENHANCED_DISCORD=true
```

**⚠️ IMPORTANT**: You MUST configure your Discord webhook URL! See [Discord Setup Guide](DISCORD_SETUP.md) for detailed instructions.

## 🏃‍♂️ Running the Bot

### Test Discord Connection
```bash
python main.py --test-connection
```

### Generate Signals (Main Usage)
```bash
python main.py
```

### Help
```bash
python main.py --help
```

## 📊 Trading Strategy: Hybrid Math

The bot implements a sophisticated 1-hour trading strategy:

### Strategy Logic:
1. **Fetches last two 1-hour bars** for each symbol
2. **Calculates key metrics:**
   - CV (Current Value) = Last bar's close price
   - PrevClose = Previous bar's close price
   - NetChange = CV - PrevClose
3. **Determines bias:**
   - LONG if NetChange > 0
   - SHORT if NetChange < 0
4. **Calculates entry points:**
   - Entry1 = Last bar's Low (LONG) or High (SHORT)
   - Entry2 = CV (current close)
5. **Sets take profit levels:**
   - TP1 = CV
   - TP2 = CV + NetChange (LONG) or CV - NetChange (SHORT)
6. **Sets stop loss levels:**
   - SL_tight = CV - (abs(NetChange) - 2) buffer
   - SL_wide = Last bar's Low/High extreme

### Risk Analysis:
- **Confidence scoring** (0-100%) based on multiple factors
- **Risk-reward ratios** for all entry/exit combinations
- **Signal quality assessment** (HIGH/MEDIUM/LOW)
- **Recommended entry and exit points**

## 📁 Project Structure

```
bfi-signals/
├── venv/                 # Virtual environment (created after setup)
├── main.py              # Main application and scheduler
├── data_fetch.py        # Yahoo Finance data fetching
├── strategy.py          # Hybrid Math strategy implementation
├── discord_post.py      # Discord webhook posting
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (you create this)
├── setup.sh            # Setup script for Unix/macOS
├── setup.bat           # Setup script for Windows
├── README.md           # This file
├── DISCORD_SETUP.md    # Discord setup instructions
└── .gitignore          # Git ignore file
```

## 🔧 Daily Workflow

Every morning when you want to generate signals:

1. **Activate the virtual environment:**
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

2. **Generate signals:**
   ```bash
   python main.py          # Generate and send signals
   ```

3. **When done, deactivate:**
   ```bash
   deactivate
   ```

## ⚙️ Configuration Options

### Environment Variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_WEBHOOK_URL` | Discord webhook URL (required) | None |
| `TRADING_SYMBOLS` | Comma-separated symbols to analyze | `^NDX` |
| `USE_ENHANCED_DISCORD` | Use rich Discord embeds | `true` |

### Adding More Symbols:
```env
TRADING_SYMBOLS=^NDX,AAPL,TSLA,SPY,QQQ
```

### Supported Symbols:
- **Indices**: ^NDX (NASDAQ-100), ^GSPC (S&P 500), ^DJI (Dow Jones)
- **Stocks**: AAPL, MSFT, GOOGL, TSLA, AMZN, etc.
- **ETFs**: SPY, QQQ, IWM, XLK, etc.
- **Crypto**: BTC-USD, ETH-USD, etc.

## 🕐 Optional: Automate with Task Scheduler (Windows) or Cron (Linux/macOS)

If you want to automate running the bot daily, you can set up your system to run it automatically:

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger to daily at your preferred time
4. Set action to start a program: `C:\path\to\bfi-signals\venv\Scripts\python.exe`
5. Add arguments: `C:\path\to\bfi-signals\main.py`

**Linux/macOS Cron:**
```bash
# Edit crontab
crontab -e

# Add this line (adjust paths as needed) - runs at 7:00 AM daily
0 7 * * * /path/to/bfi-signals/venv/bin/python /path/to/bfi-signals/main.py >> /path/to/bfi-signals/bot.log 2>&1
```

## 🆘 Troubleshooting

### "Python not found" error
- Install Python from [python.org](https://python.org)
- Make sure to check "Add to PATH" during installation

### "Discord webhook URL not configured"
- Edit your `.env` file and add the webhook URL
- See [Discord Setup Guide](DISCORD_SETUP.md) for help

### "No data available for symbol"
- Check that the symbol is correct (e.g., `^NDX` for NASDAQ-100)
- Verify internet connection
- Try a different symbol

### Import errors
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Signal generation fails
- Check that markets are open (bot works best during trading hours)
- Verify symbol format is correct
- Check log messages for specific errors

## 📦 Dependencies

- **yfinance**: Downloads stock market data from Yahoo Finance
- **python-dotenv**: Loads environment variables from .env files
- **requests**: Makes HTTP requests to Discord webhooks
- **schedule**: Handles daily scheduling
- **pytz**: Timezone handling for Namibia time

## 🔒 Security Notes

- **Never commit your `.env` file** to version control
- **Keep your Discord webhook URL private** - treat it like a password
- **Use rate limiting** - don't spam Discord with too many messages
- **Test in a private channel** first before using in public servers

## 📈 Sample Signal Output

```
🚀 ^NDX - LONG Signal ⭐
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Current Value: $15234.5600
📊 Net Change: +$123.4500 (+0.81%)
🎯 Confidence: 85% (HIGH)

📍 Entry Points:
   Entry 1: $15200.0000
   Entry 2: $15234.5600

🎯 Take Profits:
   TP1: $15234.5600 (R:R 2.1)
   TP2: $15358.0100 (R:R 3.4)

🛡️ Stop Loss:
   Tight: $15111.1100
   Wide: $15200.0000

📊 Recommendations:
   Entry: Entry1
   TP: TP2
   SL: SL_tight
```

## 🎯 Next Steps

1. **Set up Discord webhook** using the [Discord Setup Guide](DISCORD_SETUP.md)
2. **Test the bot** with `python main.py --test`
3. **Start the daily scheduler** with `python main.py`
4. **Monitor signals** in your Discord channel
5. **Customize symbols** in the `.env` file
6. **Implement your own trading logic** based on the signals

## 🤝 Contributing

Feel free to fork this project and submit pull requests! Some ideas for improvements:

- Add more technical indicators
- Implement backtesting
- Add database logging
- Create a web dashboard
- Add email notifications
- Implement paper trading

## ⚖️ Disclaimer

This bot is for educational and informational purposes only. It does not constitute financial advice. Always do your own research and consult with a qualified financial advisor before making investment decisions. Trading involves risk and you can lose money.

**Trade at your own risk!**

---

Happy trading! 🚀📈 