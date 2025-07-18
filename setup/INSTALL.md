# 🚀 BFI Signals - Installation Guide

Quick and easy setup for BFI Signals on any computer.

## 📋 Prerequisites

- **Python 3.8+** installed on your system
- **Internet connection** for downloading dependencies
- **Discord webhook URL** (see [Discord Setup Guide](DISCORD_SETUP.md))

## 🔧 Installation Methods

### Method 1: Automated Setup (Recommended)

**For Windows:**
1. Download or clone the project folder
2. Double-click `setup.bat`
3. Follow the prompts

**For Mac/Linux:**
1. Download or clone the project folder
2. Open terminal in project folder
3. Run: `python setup.py`

### Method 2: Manual Setup

1. **Download the project files** to your computer
2. **Open terminal/command prompt** in the project folder
3. **Create virtual environment:**
   ```bash
   python -m venv venv
   ```
4. **Activate virtual environment:**
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
6. **Copy and configure .env file:**
   - Copy the .env template
   - Add your Discord webhook URL
   - Configure trading symbols (optional)

## 📝 Configuration

1. **Edit `.env` file** in the project folder
2. **Add your Discord webhook URL:**
   ```
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE
   ```
3. **Configure symbols (optional):**
   ```
   TRADING_SYMBOLS=^NDX,US30
   ```

## 🧪 Testing

**Test Discord connection:**
```bash
python main.py --test-connection
```

**Generate sample signals:**
```bash
python main.py
```

## 🏃‍♂️ Running the Bot

### Quick Start (Windows)
Double-click `run_bfi_signals_auto.bat`

### Manual Start
1. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
2. Run: `python main.py`

## 📊 What You'll Get

- **Real-time trading signals** for configured symbols
- **Professional Discord formatting** with risk warnings
- **Hybrid Math Strategy** calculations
- **News sentiment analysis** (optional)
- **Weekend signal support** (shows Monday dates)

## 🔧 Customization

### Trading Symbols
Edit `TRADING_SYMBOLS` in `.env` file:
```
TRADING_SYMBOLS=^NDX,US30,^GSPC
```

### News Analysis
Enable/disable news sentiment:
```
INCLUDE_NEWS_ANALYSIS=true
```

### Discord Formatting
Use simple or enhanced formatting:
```
USE_SIMPLE_DISCORD=false
```

## 🆘 Troubleshooting

### "Python not found"
- Install Python from [python.org](https://python.org)
- Make sure to check "Add to PATH" during installation
- Restart terminal/command prompt

### "Discord webhook not configured"
- Edit `.env` file
- Add your webhook URL
- See [Discord Setup Guide](DISCORD_SETUP.md)

### "Import errors"
- Activate virtual environment first
- Run: `pip install -r requirements.txt`

### "No signals generated"
- Check internet connection
- Verify symbol names in `.env` file
- Check Discord webhook URL

## 📁 Project Structure

```
bfi-signals/
├── main.py                    # Main application
├── strategy.py                # Trading strategy logic
├── data_fetch.py              # Data fetching from MarketWatch
├── discord_post.py            # Discord integration
├── news_sentiment.py          # News sentiment analysis
├── requirements.txt           # Python dependencies
├── .env                       # Configuration file
├── setup.py                   # Automated setup script
├── setup.bat                  # Windows setup launcher
├── run_bfi_signals_auto.bat   # Auto-generated launcher
├── INSTALL.md                 # This file
├── DISCORD_SETUP.md           # Discord setup guide
├── README.md                  # Project documentation
└── venv/                      # Virtual environment
```

## 🔒 Security

- **Never share your `.env` file** - it contains sensitive webhook URLs
- **Keep your Discord webhook private** - treat it like a password
- **Use proper risk management** - signals are for educational purposes
- **Test with small amounts** before live trading

## 🎯 Next Steps

1. **Set up Discord webhook** following [Discord Setup Guide](DISCORD_SETUP.md)
2. **Run your first signal** with `run_bfi_signals_auto.bat`
3. **Schedule daily runs** or run manually each morning
4. **Monitor Discord channel** for signals
5. **Apply proper risk management** when trading

## ⚠️ Disclaimer

These signals are developed under the Bonang Finance Hybrid Math Strategy for educational purposes. Markets may behave differently depending on broker feeds. Always use strict risk management and only trade what you can afford to lose.

**Trade at your own risk!** 