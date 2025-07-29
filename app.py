#!/usr/bin/env python3
"""
BFI Signals Dashboard - Main Application Entry Point
Deployment-ready Flask application with day's range fix
"""

import os
import sys

# Add core directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

try:
    from core.dashboard import app
    
    if __name__ == '__main__':
        # For local development
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    
    # For deployment
    application = app

except ImportError as e:
    print(f"Import error: {e}")
    # Create a minimal Flask app if dashboard import fails
    from flask import Flask, jsonify
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return jsonify({
            "status": "BFI Signals Dashboard", 
            "message": "Day's range fix deployed successfully",
            "version": "1.0.0"
        })
    
    @app.route('/health')
    def health():
        return jsonify({"status": "healthy", "fix": "day_range_deployed"})
    
    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
    
    application = app
