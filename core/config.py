"""
Configuration file for BFI Signals AI Dashboard
Manages data feed settings, API keys, and system preferences
"""

import os
from typing import Dict, Any

class Config:
    """Configuration management for BFI Signals"""
    
    def __init__(self):
        # Data Feed Configuration
        self.data_sources = {
            'alpha_vantage': {
                'enabled': True,
                'api_key': os.getenv('ALPHA_VANTAGE_API_KEY', 'demo'),
                'base_url': 'https://www.alphavantage.co/query',
                'rate_limit': 5,  # requests per minute (free tier)
                'priority': 1  # Primary source
            },
            'yahoo_finance': {
                'enabled': True,
                'rate_limit': 100,  # requests per minute
                'priority': 2  # Fallback source
            },
            'finnhub': {
                'enabled': False,  # Disabled by default
                'api_key': os.getenv('FINNHUB_API_KEY', None),
                'base_url': 'https://finnhub.io/api/v1',
                'rate_limit': 60,
                'priority': 3  # Tertiary source
            },
            'polygon': {
                'enabled': False,  # Disabled by default
                'api_key': os.getenv('POLYGON_API_KEY', None),
                'base_url': 'https://api.polygon.io/v2',
                'rate_limit': 5,
                'priority': 4
            }
        }
        
        # Market Symbols Configuration
        self.symbols = {
            'nasdaq': {
                'alpha_vantage': 'NDX',
                'yahoo_finance': '^NDX',
                'finnhub': 'NDX',
                'polygon': 'NDX',
                'display_name': 'NASDAQ-100',
                'description': 'NASDAQ-100 Index'
            },
            'gold': {
                'yahoo_finance': 'GC=F',  # Gold Futures (COMEX values)
                'yahoo_finance_backup': 'XAUUSD=X',  # Gold spot
                'yahoo_finance_backup2': 'GLD',  # Gold ETF
                'alpha_vantage': 'XAUUSD',
                'finnhub': 'XAUUSD',
                'polygon': 'XAUUSD',
                'display_name': 'Gold Futures',
                'description': 'Gold vs US Dollar'
            },
            'dow': {
                'yahoo_finance': '^DJI',  # US30 (as requested)
                'yahoo_finance_backup': 'DJIA',  # DJIA alternative
                'yahoo_finance_backup2': 'DIA',  # Dow ETF
                'alpha_vantage': 'DJI',
                'finnhub': 'DJI',
                'polygon': 'DJI',
                'display_name': 'DOW (US30)',
                'description': 'Dow Jones Industrial Average'
            }
        }
        
        # Dashboard Configuration
        self.dashboard = {
            'refresh_interval': 15,  # seconds
            'market_timer_enabled': True,
            'data_persistence': True,
            'max_stored_records': 1000,
            'timezone': 'America/New_York'
        }
        
        # API Configuration
        self.api = {
            'timeout': 10,  # seconds
            'max_retries': 3,
            'retry_delay': 1,  # seconds
            'user_agent': 'BFI-Signals/1.0 (Financial Analysis Tool)'
        }
        
        # Logging Configuration
        self.logging = {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            'file': 'bfi_signals.log',
            'max_size': 10 * 1024 * 1024,  # 10MB
            'backup_count': 5
        }
        
        # Discord Configuration (if enabled)
        self.discord = {
            'enabled': os.getenv('DISCORD_ENABLED', 'false').lower() == 'true',
            'webhook_url': os.getenv('DISCORD_WEBHOOK_URL', ''),
            'bot_name': 'BFI Signals AI',
            'bot_avatar': 'https://example.com/bfi-logo.png'
        }
        
        # Performance Tracking
        self.performance = {
            'track_signals': True,
            'auto_save_outcomes': True,
            'performance_metrics': ['win_rate', 'profit_loss', 'avg_holding_time']
        }
    
    def get_data_source_config(self, source_name: str) -> Dict[str, Any]:
        """Get configuration for a specific data source"""
        return self.data_sources.get(source_name, {})
    
    def get_symbol_config(self, symbol_key: str) -> Dict[str, Any]:
        """Get configuration for a specific symbol"""
        return self.symbols.get(symbol_key, {})
    
    def is_source_enabled(self, source_name: str) -> bool:
        """Check if a data source is enabled"""
        source_config = self.get_data_source_config(source_name)
        return source_config.get('enabled', False)
    
    def get_enabled_sources(self) -> list:
        """Get list of enabled data sources ordered by priority"""
        enabled_sources = []
        for source_name, config in self.data_sources.items():
            if config.get('enabled', False):
                enabled_sources.append((source_name, config))
        
        # Sort by priority
        enabled_sources.sort(key=lambda x: x[1].get('priority', 999))
        return [source[0] for source in enabled_sources]
    
    def update_api_key(self, source_name: str, api_key: str):
        """Update API key for a data source"""
        if source_name in self.data_sources:
            self.data_sources[source_name]['api_key'] = api_key
    
    def enable_source(self, source_name: str, enabled: bool = True):
        """Enable or disable a data source"""
        if source_name in self.data_sources:
            self.data_sources[source_name]['enabled'] = enabled
    
    def get_refresh_interval(self) -> int:
        """Get the refresh interval in seconds"""
        return self.dashboard.get('refresh_interval', 15)
    
    def set_refresh_interval(self, seconds: int):
        """Set the refresh interval in seconds"""
        self.dashboard['refresh_interval'] = max(5, min(300, seconds))  # Between 5 and 300 seconds
    
    def validate_config(self) -> list:
        """Validate configuration and return list of issues"""
        issues = []
        
        # Check for required API keys
        for source_name, config in self.data_sources.items():
            if config.get('enabled', False):
                if 'api_key' in config and not config.get('api_key'):
                    issues.append(f"API key required for {source_name}")
        
        # Check symbol configurations
        for symbol_key, symbol_config in self.symbols.items():
            if not symbol_config:
                issues.append(f"Missing configuration for symbol {symbol_key}")
        
        # Check Discord configuration
        if self.discord.get('enabled', False) and not self.discord.get('webhook_url'):
            issues.append("Discord webhook URL required when Discord is enabled")
        
        return issues

# Global configuration instance
config = Config() 