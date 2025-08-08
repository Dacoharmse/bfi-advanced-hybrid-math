#!/usr/bin/env python3
"""
Configuration for BFI Signals Storage System
"""

import os
from datetime import time

# Supabase Configuration
SUPABASE_URL = "https://kiiugsmjybncvtrdshdk.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtpaXVnc21qeWJuY3Z0cmRzaGRrIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM4NzY2ODIsImV4cCI6MjA2OTQ1MjY4Mn0.4GRc469_WzsUERgsqikeGQ2SQZwJpR4HPW1kkqXR3Sw"

# Storage Directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
BACKUPS_DIR = os.path.join(DATA_DIR, 'backups')
DAILY_DIR = os.path.join(DATA_DIR, 'daily')
CURRENT_DIR = os.path.join(DATA_DIR, 'current')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Scheduling Configuration
CAPTURE_TIME = time(23, 5)  # 23:05
TIMEZONE = 'Europe/Berlin'  # GMT+2

# Symbols to capture
SYMBOLS_TO_CAPTURE = ['nasdaq', 'dow', 'gold']

# Backup Configuration
BACKUP_RETENTION_DAYS = 30
AUTO_BACKUP_ENABLED = True

# Sync Configuration
AUTO_SYNC_ENABLED = True
SYNC_INTERVAL_HOURS = 6

# Create directories
for directory in [DATA_DIR, BACKUPS_DIR, DAILY_DIR, CURRENT_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)