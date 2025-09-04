# 📱 WhatsApp Integration Setup Guide

This guide will help you set up your BFI Signals project to send trading signals to WhatsApp groups using third-party APIs.

## 📋 What You'll Need

1. A WhatsApp account
2. A WhatsApp group where you want to receive signals
3. Account with one of the supported API providers:
   - **GREEN API** (Recommended - most features)
   - **Wassenger** (Good for basic messaging)
   - **Whapi.Cloud** (Modern interface)

## 🔧 Step 1: Choose Your API Provider

### Option A: GREEN API (Recommended)

**Pros:**
- Full group management (create/delete groups, manage members)
- Reliable message delivery
- Good documentation
- Free tier available

**Cons:**
- Requires phone number verification
- Setup can be complex

**Setup Steps:**
1. Go to [green-api.com](https://green-api.com)
2. Register for an account
3. Create a new instance
4. Get your Instance ID and Access Token
5. Follow their WhatsApp connection process

### Option B: Wassenger

**Pros:**
- Simple setup
- Good for basic messaging
- Reliable service

**Cons:**
- Limited group management features
- Paid service only

**Setup Steps:**
1. Go to [wassenger.com](https://wassenger.com)
2. Sign up and create a device
3. Get your API key and Device ID
4. Connect your WhatsApp account

### Option C: Whapi.Cloud

**Pros:**
- Modern API interface
- Good documentation
- Multiple messaging features

**Cons:**
- Newer service
- Pricing can be higher

**Setup Steps:**
1. Go to [whapi.cloud](https://whapi.cloud)
2. Create an account
3. Set up a channel
4. Get your access token

## 🔐 Step 2: Configure Your Environment

1. **Open your `.env` file** in the project folder

2. **Enable WhatsApp and configure your chosen provider**:

### For GREEN API:
```env
# WhatsApp Integration (OPTIONAL)
WHATSAPP_ENABLED=true
WHATSAPP_API_PROVIDER=green

# GREEN API Configuration
GREEN_API_INSTANCE_ID=1101234567
GREEN_API_ACCESS_TOKEN=your_long_access_token_here

# WhatsApp Group ID (format: 120363025343298765@g.us)
WHATSAPP_GROUP_ID=120363025343298765@g.us
```

### For Wassenger:
```env
# WhatsApp Integration (OPTIONAL)
WHATSAPP_ENABLED=true
WHATSAPP_API_PROVIDER=wassenger

# Wassenger Configuration
WASSENGER_API_KEY=your_api_key_here
WASSENGER_DEVICE_ID=your_device_id_here

# WhatsApp Group ID (format varies - check Wassenger docs)
WHATSAPP_GROUP_ID=your_group_id_here
```

### For Whapi.Cloud:
```env
# WhatsApp Integration (OPTIONAL)
WHATSAPP_ENABLED=true
WHATSAPP_API_PROVIDER=whapi

# Whapi Configuration
WHAPI_ACCESS_TOKEN=your_access_token_here

# WhatsApp Group ID (format varies - check Whapi docs)
WHATSAPP_GROUP_ID=your_group_id_here
```

## 📱 Step 3: Get Your WhatsApp Group ID

### For GREEN API:

1. **Create a group** (or use existing):
   ```python
   from whatsapp_signals import WhatsAppSignals
   
   whatsapp = WhatsAppSignals(api_provider="green")
   group_id = whatsapp.create_group(
       group_name="BFI Trading Signals",
       participants=["1234567890"]  # Phone numbers with country code
   )
   print(f"Group ID: {group_id}")
   ```

2. **Or get existing group ID** using GREEN API's getChats endpoint

### For Other Providers:
- Check their documentation for group ID format
- Usually involves web interface or API calls to list groups

## 🧪 Step 4: Test Your Setup

1. **Install required packages** (if not already installed):
   ```bash
   pip install requests
   ```

2. **Test the connection**:
   ```python
   # Create a test file: test_whatsapp.py
   from core.whatsapp_signals import WhatsAppSignals
   
   # Initialize with your provider
   whatsapp = WhatsAppSignals(api_provider="green")  # or "wassenger" or "whapi"
   
   # Test sending a message
   success = whatsapp.send_message_to_group(
       group_id="YOUR_GROUP_ID_HERE",
       message="🚀 BFI Signals WhatsApp integration test!"
   )
   
   if success:
       print("✅ WhatsApp setup successful!")
   else:
       print("❌ WhatsApp setup failed!")
   ```

3. **Run the test**:
   ```bash
   python test_whatsapp.py
   ```

## 🎯 Step 5: Test Signal Sending

1. **Test with a trading signal**:
   ```python
   from core.whatsapp_signals import WhatsAppSignals
   
   whatsapp = WhatsAppSignals(api_provider="green")
   
   success = whatsapp.send_signal(
       group_id="YOUR_GROUP_ID_HERE",
       signal_type="BUY",
       symbol="AAPL",
       price=150.25,
       action="Strong Buy - Technical breakout",
       confidence="High",
       additional_info="RSI oversold, breaking resistance at $150"
   )
   
   print("Signal sent!" if success else "Failed to send signal")
   ```

2. **Check your WhatsApp group** - you should see a formatted trading signal!

## 📊 Signal Format in WhatsApp

Your signals will appear like this:

```
🚨 *BUY SIGNAL* 🚨

📊 *Symbol:* AAPL
💰 *Price:* $150.25
📈 *Action:* Strong Buy - Technical breakout
🎯 *Confidence:* High
⏰ *Time:* 2025-01-15 14:30:00
📝 *Info:* RSI oversold, breaking resistance at $150

⚠️ *BFI Signals • Trade at your own risk*
```

## 🚀 Step 6: Run with Both Discord and WhatsApp

Now when you run your main signals:

```bash
python core/main.py
```

Your signals will be sent to **both Discord and WhatsApp** automatically!

## 📋 Supported Features

### ✅ What Works:
- Send trading signals to WhatsApp groups
- Send market updates
- Send custom messages
- Create groups (GREEN API only)
- Unified notifications (Discord + WhatsApp)
- Rich text formatting with emojis

### ❌ Limitations:
- No official WhatsApp API (using third-party services)
- Costs money (most providers are paid)
- Rate limiting applies
- Group member management limited
- No end-to-end encryption guarantee

## 🔒 Security & Best Practices

1. **Keep credentials private** - never share API keys
2. **Test in private groups** first
3. **Respect rate limits** - don't spam
4. **Monitor costs** - API calls are usually paid
5. **Have fallbacks** - Discord should still work if WhatsApp fails

## 🆘 Troubleshooting

### "WhatsApp API credentials not configured"
- Check your `.env` file has the correct keys
- Verify API provider name is correct
- Make sure `WHATSAPP_ENABLED=true`

### "Failed to send WhatsApp message"
- Verify API credentials are valid
- Check group ID format
- Ensure you have credits/quota with provider
- Test with provider's web interface first

### "Group ID not found"
- Double-check group ID format
- Make sure you're admin of the group
- Try recreating the group
- Check provider documentation for ID format

### Messages not appearing
- Check WhatsApp is connected to API provider
- Verify group still exists
- Check rate limiting
- Look at provider's logs/dashboard

## 💰 Pricing Information

**GREEN API:**
- Free tier: Limited messages
- Paid plans: ~$10-50/month

**Wassenger:**
- Paid service: ~$29/month minimum
- Higher volume plans available

**Whapi.Cloud:**
- Free tier: Limited messages
- Paid plans: ~$19/month and up

## 🎉 You're Ready!

Your BFI Signals project can now:
- ✅ Send trading signals to Discord
- ✅ Send trading signals to WhatsApp groups
- ✅ Use unified notification system
- ✅ Format messages beautifully with emojis
- ✅ Handle multiple symbols and markets
- ✅ Provide fallback if one service fails

## 🚀 Next Steps

1. **Set up automation** - Use cron/scheduler for regular signals
2. **Create multiple groups** - Different groups for different markets
3. **Add more symbols** - Expand to crypto, forex, commodities
4. **Monitor performance** - Track which signals perform best
5. **Add alerts** - Price alerts, news alerts, etc.

Happy trading! 📈💬

---

**Need Help?**
- Check provider documentation
- Join our Discord for support
- Read the main README for general setup
- Test with simple messages first before complex signals