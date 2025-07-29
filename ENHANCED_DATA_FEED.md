# Enhanced Data Feed System

## Overview

The BFI Signals AI Dashboard now uses an enhanced data feed system that provides more reliable market data through multiple data sources with automatic fallback mechanisms.

## Key Improvements

### 1. Multiple Data Sources
- **Alpha Vantage API** (Primary) - Professional-grade market data
- **Yahoo Finance** (Fallback) - Reliable backup data source
- **Finnhub** (Optional) - Additional data source for redundancy
- **Polygon.io** (Optional) - High-frequency data source

### 2. Automatic Fallback
- If one data source fails, automatically switches to the next available source
- Maintains data continuity even during API outages
- Graceful degradation with stored data as final fallback

### 3. Rate Limiting
- Built-in rate limiting to respect API quotas
- Prevents API key suspension
- Optimized request timing

### 4. Data Persistence
- Stores market data locally for offline access
- Maintains historical data for analysis
- Automatic cleanup of old data

## Configuration

### Environment Variables
```bash
# Alpha Vantage API Key (Recommended)
ALPHA_VANTAGE_API_KEY=your_api_key_here

# Finnhub API Key (Optional)
FINNHUB_API_KEY=your_finnhub_key_here

# Polygon API Key (Optional)
POLYGON_API_KEY=your_polygon_key_here

# Discord Configuration (Optional)
DISCORD_ENABLED=true
DISCORD_WEBHOOK_URL=your_webhook_url_here
```

### API Keys Setup

#### Alpha Vantage (Recommended)
1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Get a free API key (500 requests/day)
3. Set environment variable: `ALPHA_VANTAGE_API_KEY=your_key`

#### Finnhub (Optional)
1. Visit [Finnhub](https://finnhub.io/register)
2. Get a free API key (60 requests/minute)
3. Set environment variable: `FINNHUB_API_KEY=your_key`

#### Polygon.io (Optional)
1. Visit [Polygon.io](https://polygon.io/)
2. Get a free API key (5 requests/minute)
3. Set environment variable: `POLYGON_API_KEY=your_key`

## Data Sources Comparison

| Source | Free Tier | Rate Limit | Data Quality | Reliability |
|--------|-----------|------------|--------------|-------------|
| Alpha Vantage | 500 req/day | 5 req/min | High | Excellent |
| Yahoo Finance | Unlimited | 100 req/min | Medium | Good |
| Finnhub | 60 req/min | 60 req/min | High | Good |
| Polygon.io | 5 req/min | 5 req/min | Very High | Excellent |

## Supported Symbols

### Current Symbols
- **NASDAQ Composite** (`^IXIC`) - Technology index
- **Gold Futures** (`GC=F`) - Precious metals
- **Dow Jones** (`^DJI`) - Industrial average

### Symbol Mapping
Each symbol is mapped to different data sources:

```python
symbols = {
    'nasdaq': {
        'alpha_vantage': 'IXIC',
        'yahoo_finance': '^IXIC',
        'finnhub': 'IXIC'
    },
    'gold': {
        'alpha_vantage': 'XAUUSD',
        'yahoo_finance': 'GC=F',
        'finnhub': 'XAUUSD'
    },
    'dow': {
        'alpha_vantage': 'DJI',
        'yahoo_finance': '^DJI',
        'finnhub': 'DJI'
    }
}
```

## Error Handling

### Fallback Chain
1. **Alpha Vantage** → Primary source
2. **Yahoo Finance** → First fallback
3. **Finnhub** → Second fallback (if enabled)
4. **Stored Data** → Final fallback

### Error Types Handled
- Network timeouts
- API rate limiting
- Invalid symbols
- Data format errors
- Service outages

## Performance Features

### Rate Limiting
- Automatic request spacing
- Respects API quotas
- Prevents service suspension

### Caching
- Stores successful responses
- Reduces API calls
- Improves response time

### Data Validation
- Validates price data
- Checks for reasonable values
- Filters out bad data

## Monitoring

### Console Output
```
📊 Fetching NASDAQ data...
✅ NASDAQ data from Alpha Vantage
📊 Fetching GOLD data...
✅ GOLD data from Yahoo Finance (fallback)
📊 Fetching DOW data...
✅ DOW data from Alpha Vantage
```

### Error Logging
```
❌ Alpha Vantage error for nasdaq: API key limit exceeded
⚠️ Alpha Vantage failed for nasdaq, trying Yahoo Finance...
✅ NASDAQ data from Yahoo Finance (fallback)
```

## Troubleshooting

### Common Issues

1. **"API key limit exceeded"**
   - Wait for rate limit reset
   - Upgrade to paid API plan
   - Use fallback sources

2. **"No data available"**
   - Check symbol validity
   - Verify API key
   - Check network connection

3. **"Symbol not found"**
   - Update symbol mapping
   - Check symbol format
   - Verify data source support

### Debug Mode
Enable debug logging by setting:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
- Real-time WebSocket connections
- Advanced technical indicators
- Custom symbol support
- Data source health monitoring
- Automatic failover optimization

### API Integrations
- IEX Cloud
- Quandl
- Bloomberg (if available)
- Reuters (if available)

## Support

For issues with the enhanced data feed:
1. Check console output for error messages
2. Verify API keys are set correctly
3. Test individual data sources
4. Review rate limiting settings

The enhanced data feed provides much more reliable market data compared to the previous Yahoo Finance-only approach, ensuring your trading signals are based on the most accurate and up-to-date information available. 