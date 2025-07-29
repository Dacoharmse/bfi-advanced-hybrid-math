# 🚀 Discord Integration Setup Guide

This guide will help you set up your BFI Signals project to send trading signals to Discord.

## 📋 What You'll Need

1. A Discord account
2. A Discord server where you want to receive signals
3. Admin permissions on that server (or know someone who does)

## 🔧 Step 1: Create a Discord Webhook

### What is a Webhook?
A webhook is a simple way to send messages to Discord without creating a full bot. It's perfect for sending signals!

### Creating the Webhook:

1. **Open Discord** and go to the server where you want to receive signals

2. **Right-click on the channel** where you want signals to appear (e.g., #trading-signals)

3. **Select "Edit Channel"** from the menu

4. **Click "Integrations"** in the left sidebar

5. **Click "Create Webhook"**

6. **Give it a name** (e.g., "BFI Signals")

7. **Optional: Upload an avatar** (you can use any trading-related image)

8. **Copy the Webhook URL** - this is VERY important! It should look like:
   ```
   https://discord.com/api/webhooks/1234567890/abcdefghijklmnopqrstuvwxyz
   ```

9. **Click "Save Changes"**

## 🔐 Step 2: Add Webhook to Your Project

1. **Open your `.env` file** in the project folder

2. **Add the Discord webhook URL**:
   ```env
   # Environment Variables for BFI Signals Project
   # This file stores sensitive configuration data
   # Never commit this file to version control!

   # Test variable to verify .env loading works
   TEST_VARIABLE=Hello from .env file!

   # Discord Integration
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_URL_HERE

   # Add your API keys and configuration here
   # Example:
   # API_KEY=your_api_key_here
   # DATABASE_URL=your_database_url_here
   # DEBUG=True
   ```

3. **Replace `YOUR_WEBHOOK_URL_HERE`** with the actual webhook URL you copied

4. **Save the file**

## 🧪 Step 3: Update and Test Your Project

1. **Update your packages**:
   ```powershell
   # Activate virtual environment
   venv\Scripts\activate
   
   # Install new packages
   pip install -r requirements.txt
   ```

2. **Test the setup**:
   ```powershell
   python main.py
   ```

   You should see:
   - ✅ Discord webhook configured!
   - A test message should appear in your Discord channel!

## 🎯 Step 4: Send Your First Signal

1. **Edit main.py** and uncomment the demo line:
   ```python
   if __name__ == "__main__":
       main()
       
       # Uncomment the line below to run the demo
       demo_signals()  # <-- Remove the # to uncomment
   ```

2. **Run it**:
   ```powershell
   python main.py
   ```

3. **Check Discord** - you should see beautiful formatted signals appear!

## 📊 Types of Signals You Can Send

### 1. Trading Signals
```python
from discord_signals import DiscordSignals

discord = DiscordSignals()
discord.send_signal(
    signal_type="BUY",      # BUY, SELL, HOLD, ALERT
    symbol="AAPL",          # Stock symbol
    price=150.25,           # Current price
    action="Strong Buy",    # Your recommendation
    confidence="High",      # Low, Medium, High
    additional_info="Technical breakout detected"
)
```

### 2. Market Updates
```python
discord.send_market_update(
    title="Daily Market Summary",
    updates={
        "📊 S&P 500": "+0.85%",
        "🏦 NASDAQ": "+1.20%",
        "💼 DOW": "+0.45%"
    }
)
```

### 3. Simple Messages
```python
discord.send_webhook_message("🚨 Market alert: High volatility detected!")
```

## 🛠️ Real-World Example: Stock Price Alert

Here's how to create a real stock price alert:

```python
#!/usr/bin/env python3
import yfinance as yf
from discord_signals import DiscordSignals

def check_stock_price(symbol, target_price):
    """Check if stock hits target price and send alert"""
    
    # Get current stock price
    stock = yf.Ticker(symbol)
    current_price = stock.history(period="1d")['Close'].iloc[-1]
    
    # Check if we hit the target
    if current_price >= target_price:
        discord = DiscordSignals()
        discord.send_signal(
            signal_type="ALERT",
            symbol=symbol,
            price=current_price,
            action=f"Target price ${target_price} reached!",
            confidence="High",
            additional_info=f"Stock is now trading at ${current_price:.2f}"
        )
        return True
    return False

# Example usage
if __name__ == "__main__":
    # Alert when Apple hits $155
    check_stock_price("AAPL", 155.00)
```

## 🔒 Security Tips

1. **Never share your webhook URL** - it's like a password!
2. **Keep your .env file private** - never commit it to git
3. **Test in a private channel first** before using in public servers
4. **Use rate limiting** - don't spam Discord with too many messages

## 🆘 Troubleshooting

### "Discord webhook URL not configured"
- Check that your `.env` file has the webhook URL
- Make sure there are no extra spaces or quotes around the URL

### "Failed to send Discord message"
- Verify the webhook URL is correct
- Check your internet connection
- Make sure the Discord channel still exists

### Messages not appearing
- Check you're looking at the right channel
- Make sure the webhook wasn't deleted
- Try recreating the webhook

## 🎉 You're Ready!

Your BFI Signals project can now:
- ✅ Send trading signals to Discord
- ✅ Post market updates
- ✅ Send alerts and notifications
- ✅ Use beautiful formatted messages with colors and emojis

## 🚀 Next Steps

1. **Connect real data** - use yfinance to get live stock prices
2. **Add scheduling** - use Python's schedule library to send regular updates
3. **Create your own strategies** - build custom trading signal logic
4. **Expand to crypto** - add cryptocurrency signals
5. **Add more channels** - create different webhooks for different types of signals

Happy trading! 📈 