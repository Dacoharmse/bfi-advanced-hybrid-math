#!/usr/bin/env python3
"""
AI Manager Script for BFI Signals
Helps users set up AI features and manage learning data
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class AIManager:
    """Manager for AI features and learning data"""
    
    def __init__(self, db_path: str = "ai_learning.db"):
        self.db_path = db_path
    
    def setup_ai_features(self):
        """Set up AI features for the first time"""
        print("Setting up AI features for BFI Signals...")
        
        # Check if transformers is available
        try:
            import transformers
            print("SUCCESS: transformers library is available")
            models_available = True
        except ImportError:
            print("INFO: transformers library not found")
            models_available = False
        
        # Create environment variables for AI APIs
        env_path = "../.env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                content = f.read()
            
            # Add AI API keys if not present
            if "OPENAI_API_KEY" not in content:
                content += "\n# Optional: OpenAI API Key for enhanced sentiment analysis\n"
                content += "OPENAI_API_KEY=your_openai_key_here\n"
            
            if "GEMINI_API_KEY" not in content:
                content += "\n# Optional: Google Gemini API Key for enhanced sentiment analysis\n"
                content += "GEMINI_API_KEY=your_gemini_key_here\n"
            
            with open(env_path, 'w') as f:
                f.write(content)
            
            print("SUCCESS: Updated .env file with AI API key placeholders")
        
        # Initialize database
        try:
            from ai_engine import AIEngine
            ai_engine = AIEngine(self.db_path)
            print("SUCCESS: AI learning database initialized")
        except Exception as e:
            print(f"ERROR: Failed to initialize AI engine: {e}")
            return False
        
        # Provide setup instructions
        print("\nAI SETUP INSTRUCTIONS:")
        print("======================")
        
        if not models_available:
            print("1. INSTALL AI MODELS (Optional but recommended):")
            print("   pip install transformers torch sentencepiece")
            print("   This enables local AI sentiment analysis (free and fast)")
            print()
        
        print("2. OPTIONAL: Get free AI API keys for enhanced analysis:")
        print("   - OpenAI (Free tier): https://platform.openai.com/")
        print("   - Google Gemini (Free tier): https://ai.google.dev/")
        print("   - Add these to your .env file")
        print()
        
        print("3. AI FEATURES ENABLED:")
        print("   - Advanced sentiment analysis using multiple AI models")
        print("   - Learning system that improves over time")
        print("   - Risk assessment for each signal")
        print("   - Enhanced probability calculations")
        print()
        
        return True
    
    def show_learning_stats(self):
        """Show AI learning statistics"""
        try:
            from ai_engine import AIEngine
            ai_engine = AIEngine(self.db_path)
            stats = ai_engine.get_learning_stats()
            
            print("AI LEARNING STATISTICS:")
            print("=======================")
            print(f"Total signals processed: {stats.get('total_signals', 0)}")
            print(f"Success rate: {stats.get('success_rate', 0):.1%}")
            print(f"Local models available: {'Yes' if stats.get('models_available', False) else 'No'}")
            print()
            
            model_usage = stats.get('model_usage', {})
            if model_usage:
                print("AI MODEL USAGE:")
                for model, count in model_usage.items():
                    print(f"  {model}: {count} times")
            else:
                print("No AI model usage data yet")
            
        except Exception as e:
            print(f"ERROR: Failed to get learning stats: {e}")
    
    def clear_learning_data(self):
        """Clear all AI learning data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear all tables
            cursor.execute("DELETE FROM signal_performance")
            cursor.execute("DELETE FROM news_sentiment")
            cursor.execute("DELETE FROM learned_patterns")
            
            conn.commit()
            conn.close()
            
            print("SUCCESS: All AI learning data cleared")
            
        except Exception as e:
            print(f"ERROR: Failed to clear learning data: {e}")
    
    def export_learning_data(self, filename: Optional[str] = None):
        """Export AI learning data to JSON file"""
        if filename is None:
            filename = f"ai_learning_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all data
            cursor.execute("SELECT * FROM signal_performance")
            signal_data = cursor.fetchall()
            
            cursor.execute("SELECT * FROM news_sentiment")
            sentiment_data = cursor.fetchall()
            
            cursor.execute("SELECT * FROM learned_patterns")
            pattern_data = cursor.fetchall()
            
            conn.close()
            
            # Create export structure
            export_data = {
                "export_date": datetime.now().isoformat(),
                "signal_performance": signal_data,
                "news_sentiment": sentiment_data,
                "learned_patterns": pattern_data
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            print(f"SUCCESS: Learning data exported to {filename}")
            
        except Exception as e:
            print(f"ERROR: Failed to export learning data: {e}")
    
    def add_manual_outcome(self, symbol: str, signal_type: str, outcome: bool, profit_loss: float):
        """Manually add a trading outcome for learning"""
        try:
            from ai_engine import AIEngine
            ai_engine = AIEngine(self.db_path)
            
            # Find the most recent signal for this symbol
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id FROM signal_performance 
                WHERE symbol = ? AND signal_type = ? AND actual_outcome IS NULL
                ORDER BY timestamp DESC LIMIT 1
            ''', (symbol, signal_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                signal_id = result[0]
                ai_engine.learn_from_outcome(signal_id, outcome, profit_loss)
                print(f"SUCCESS: Added outcome for {symbol} {signal_type}")
            else:
                print(f"ERROR: No pending signal found for {symbol} {signal_type}")
                
        except Exception as e:
            print(f"ERROR: Failed to add manual outcome: {e}")
    
    def show_recent_signals(self, days: int = 7):
        """Show recent signals for manual outcome entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, symbol, signal_type, predicted_probability, timestamp, actual_outcome
                FROM signal_performance 
                WHERE timestamp > datetime('now', '-{} days')
                ORDER BY timestamp DESC
            '''.format(days))
            
            results = cursor.fetchall()
            conn.close()
            
            print(f"RECENT SIGNALS (Last {days} days):")
            print("=" * 50)
            
            for row in results:
                signal_id, symbol, signal_type, prob, timestamp, outcome = row
                outcome_str = "Pending" if outcome is None else ("Profit" if outcome == 1 else "Loss")
                print(f"ID: {signal_id} | {symbol} {signal_type} | {prob:.1f}% | {timestamp} | {outcome_str}")
            
            if not results:
                print("No recent signals found")
            
        except Exception as e:
            print(f"ERROR: Failed to get recent signals: {e}")
    
    def install_ai_models(self):
        """Install AI models with user confirmation"""
        print("This will install AI models (requires ~2GB download):")
        print("- transformers (Hugging Face library)")
        print("- torch (PyTorch)")
        print("- sentencepiece (for tokenization)")
        print()
        
        confirm = input("Continue with installation? (y/n): ").lower().strip()
        if confirm != 'y':
            print("Installation cancelled")
            return
        
        try:
            import subprocess
            import sys
            
            print("Installing AI dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "transformers", "torch", "sentencepiece"])
            
            print("SUCCESS: AI models installed")
            print("Models will be downloaded automatically on first use")
            
        except Exception as e:
            print(f"ERROR: Failed to install AI models: {e}")


def main():
    """Main function for AI manager"""
    if len(sys.argv) < 2:
        print("AI Manager for BFI Signals")
        print("Usage: python ai_manager.py [command]")
        print()
        print("Commands:")
        print("  setup         - Set up AI features for first time")
        print("  stats         - Show AI learning statistics")
        print("  clear         - Clear all learning data")
        print("  export        - Export learning data to JSON")
        print("  recent        - Show recent signals for manual outcome entry")
        print("  install       - Install AI models")
        print("  outcome       - Add manual trading outcome")
        print("                  Usage: python ai_manager.py outcome SYMBOL TYPE OUTCOME PROFIT_LOSS")
        print("                  Example: python ai_manager.py outcome US30 BUY true 150.50")
        return
    
    command = sys.argv[1].lower()
    manager = AIManager()
    
    if command == "setup":
        manager.setup_ai_features()
    elif command == "stats":
        manager.show_learning_stats()
    elif command == "clear":
        confirm = input("Are you sure you want to clear all learning data? (y/n): ").lower().strip()
        if confirm == 'y':
            manager.clear_learning_data()
        else:
            print("Clear operation cancelled")
    elif command == "export":
        filename = sys.argv[2] if len(sys.argv) > 2 else None
        manager.export_learning_data(filename)
    elif command == "recent":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        manager.show_recent_signals(days)
    elif command == "install":
        manager.install_ai_models()
    elif command == "outcome":
        if len(sys.argv) < 6:
            print("Usage: python ai_manager.py outcome SYMBOL TYPE OUTCOME PROFIT_LOSS")
            print("Example: python ai_manager.py outcome US30 BUY true 150.50")
            return
        
        symbol = sys.argv[2]
        signal_type = sys.argv[3]
        outcome = sys.argv[4].lower() == 'true'
        profit_loss = float(sys.argv[5])
        
        manager.add_manual_outcome(symbol, signal_type, outcome, profit_loss)
    else:
        print(f"Unknown command: {command}")
        print("Use 'python ai_manager.py' for help")


if __name__ == "__main__":
    main() 