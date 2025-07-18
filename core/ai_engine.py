#!/usr/bin/env python3
"""
AI Engine Module for BFI Signals
Integrates free AI services for advanced sentiment analysis, learning, and risk assessment
"""

import json
import sqlite3
import requests
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import time
import logging
from dataclasses import dataclass
from statistics import mean
import hashlib


@dataclass
class SignalPerformance:
    """Track signal performance for learning"""
    symbol: str
    signal_type: str
    predicted_probability: float
    actual_outcome: Optional[bool] = None
    profit_loss: Optional[float] = None
    risk_level: str = "medium"
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AIEngine:
    """Advanced AI engine for sentiment analysis and learning"""
    
    def __init__(self, db_path: str = "ai_learning.db"):
        self.db_path = db_path
        self.setup_database()
        self.logger = logging.getLogger(__name__)
        
        # Free AI service configurations
        self.openai_api_key = os.getenv('OPENAI_API_KEY')  # Optional
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')  # Optional
        
        # Initialize local models (will download if not available)
        self.local_models_available = False
        self.try_initialize_local_models()
    
    def setup_database(self):
        """Initialize SQLite database for learning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Signal performance table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS signal_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT,
                signal_type TEXT,
                predicted_probability REAL,
                actual_outcome INTEGER,
                profit_loss REAL,
                risk_level TEXT,
                timestamp DATETIME,
                news_hash TEXT
            )
        ''')
        
        # News sentiment history
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS news_sentiment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                news_hash TEXT UNIQUE,
                headline TEXT,
                ai_sentiment REAL,
                confidence REAL,
                model_used TEXT,
                timestamp DATETIME
            )
        ''')
        
        # Pattern learning table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT,
                pattern_data TEXT,
                success_rate REAL,
                usage_count INTEGER,
                last_updated DATETIME
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def try_initialize_local_models(self):
        """Try to initialize local AI models (optional)"""
        try:
            # Try to import transformers - if not available, skip gracefully
            try:
                # Suppress verbose transformers warnings
                import warnings
                warnings.filterwarnings("ignore", category=UserWarning, module="transformers")
                
                from transformers import pipeline
                import logging
                logging.getLogger("transformers").setLevel(logging.ERROR)
                
                print("🤖 Loading AI models...")
                
                # Initialize sentiment analysis pipeline
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                    top_k=None  # Updated from deprecated return_all_scores=True
                )
                
                # Initialize text classification for financial news
                self.financial_sentiment_pipeline = pipeline(
                    "text-classification",
                    model="ProsusAI/finbert",
                    top_k=None  # Updated from deprecated return_all_scores=True
                )
                
                self.local_models_available = True
                print("✅ AI models ready!")
                
            except ImportError:
                self.local_models_available = False
                print("INFO: Transformers package not installed - using cloud AI and fallback methods")
            except Exception as model_error:
                self.local_models_available = False
                print(f"INFO: Could not load local AI models: {model_error}")
                print("INFO: This is normal if models aren't downloaded - using cloud AI instead")
            
        except Exception as e:
            self.local_models_available = False
            print(f"INFO: Local AI models initialization skipped: {e}")
            print("INFO: Using cloud AI (Gemini) and enhanced keyword analysis")
    
    def analyze_sentiment_ai(self, headlines: List[str], symbol: str = "") -> Dict:
        """
        Advanced AI-powered sentiment analysis
        
        Args:
            headlines (List[str]): List of news headlines
            symbol (str): Trading symbol for context
            
        Returns:
            Dict: Sentiment analysis results with confidence scores
        """
        if not headlines:
            return {"sentiment": 0.0, "confidence": 0.0, "model_used": "none"}
        
        # Combine headlines for analysis
        combined_text = " ".join(headlines[:10])  # Limit to first 10 headlines
        
        # Try multiple AI services in order of preference
        result = None
        
        # 1. Try local models first (free and fast)
        if self.local_models_available:
            result = self._analyze_with_local_models(combined_text, symbol)
        
        # 2. Try free cloud APIs as backup
        if not result:
            result = self._analyze_with_cloud_ai(combined_text, symbol)
        
        # 3. Fallback to improved keyword analysis
        if not result:
            result = self._analyze_with_enhanced_keywords(combined_text, symbol)
        
        # Store result in database for learning
        self._store_sentiment_result(headlines, result)
        
        return result
    
    def _analyze_with_local_models(self, text: str, symbol: str) -> Optional[Dict]:
        """Analyze sentiment using local AI models"""
        try:
            # Get general sentiment
            general_sentiment = self.sentiment_pipeline(text)[0]
            
            # Get financial sentiment
            financial_sentiment = self.financial_sentiment_pipeline(text)[0]
            
            # Combine results with weighting
            sentiment_score = 0.0
            confidence = 0.0
            
            for result in general_sentiment:
                if result['label'] == 'POSITIVE':
                    sentiment_score += result['score'] * 0.3
                elif result['label'] == 'NEGATIVE':
                    sentiment_score -= result['score'] * 0.3
                confidence += result['score'] * 0.3
            
            for result in financial_sentiment:
                if result['label'] == 'positive':
                    sentiment_score += result['score'] * 0.7
                elif result['label'] == 'negative':
                    sentiment_score -= result['score'] * 0.7
                confidence += result['score'] * 0.7
            
            return {
                "sentiment": max(-1.0, min(1.0, sentiment_score)),
                "confidence": min(1.0, confidence),
                "model_used": "local_ensemble"
            }
            
        except Exception as e:
            self.logger.error(f"Local model analysis failed: {e}")
            return None
    
    def _analyze_with_cloud_ai(self, text: str, symbol: str) -> Optional[Dict]:
        """Analyze sentiment using cloud AI services"""
        
        # Try OpenAI (free tier)
        if self.openai_api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                }
                
                prompt = f"""
                Analyze the financial sentiment of this news text for {symbol}:
                "{text}"
                
                Respond with only a JSON object:
                {{"sentiment": <number between -1 and 1>, "confidence": <number between 0 and 1>}}
                """
                
                data = {
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100
                }
                
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['choices'][0]['message']['content']
                    sentiment_data = json.loads(content)
                    
                    return {
                        "sentiment": sentiment_data.get("sentiment", 0.0),
                        "confidence": sentiment_data.get("confidence", 0.0),
                        "model_used": "openai_gpt"
                    }
                    
            except Exception as e:
                self.logger.error(f"OpenAI analysis failed: {e}")
        
        # Try Google Gemini (free tier) with new API
        if self.gemini_api_key:
            try:
                from google.genai import Client
                
                # Create the client
                client = Client(api_key=self.gemini_api_key)
                
                # Create the prompt
                prompt = f"""
                Analyze the financial sentiment of this news text for {symbol}:
                "{text}"
                
                Consider:
                1. Overall market sentiment (bullish, bearish, neutral)
                2. Impact on the specific symbol
                3. Confidence level based on clarity of the news
                
                Respond with only a JSON object (no markdown, no explanation):
                {{"sentiment": <number between -1 and 1>, "confidence": <number between 0 and 1>}}
                
                Where:
                - sentiment: -1 (very bearish) to +1 (very bullish)
                - confidence: 0 (low confidence) to 1 (high confidence)
                """
                
                # Generate content
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt
                )
                
                if response.text:
                    # Clean the response text
                    clean_response = response.text.strip()
                    if clean_response.startswith('```json'):
                        clean_response = clean_response[7:-3]
                    elif clean_response.startswith('```'):
                        clean_response = clean_response[3:-3]
                    
                    sentiment_data = json.loads(clean_response)
                    
                    return {
                        "sentiment": sentiment_data.get("sentiment", 0.0),
                        "confidence": sentiment_data.get("confidence", 0.0),
                        "model_used": "gemini_new_api"
                    }
                    
            except ImportError:
                self.logger.error("google-genai package not installed")
            except Exception as e:
                self.logger.error(f"Gemini analysis failed: {e}")
                
        # Fallback to old REST API if new SDK not available
        if self.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key={self.gemini_api_key}"
                
                data = {
                    "contents": [{
                        "parts": [{
                            "text": f"Analyze financial sentiment for {symbol}: {text}. Return JSON: {{\"sentiment\": <-1 to 1>, \"confidence\": <0 to 1>}}"
                        }]
                    }]
                }
                
                response = requests.post(url, json=data, timeout=10)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    sentiment_data = json.loads(content)
                    
                    return {
                        "sentiment": sentiment_data.get("sentiment", 0.0),
                        "confidence": sentiment_data.get("confidence", 0.0),
                        "model_used": "gemini_rest_api"
                    }
                    
            except Exception as e:
                self.logger.error(f"Gemini REST API analysis failed: {e}")
        
        return None
    
    def _analyze_with_enhanced_keywords(self, text: str, symbol: str) -> Dict:
        """Enhanced keyword-based sentiment analysis as fallback"""
        text_lower = text.lower()
        
        # Enhanced keyword sets with weights
        bullish_keywords = {
            'rally': 3, 'surge': 3, 'breakout': 3, 'bullish': 2, 'gain': 2,
            'rise': 2, 'climb': 2, 'advance': 2, 'boost': 2, 'strong': 2,
            'positive': 1, 'optimistic': 1, 'upgrade': 2, 'growth': 2,
            'recovery': 2, 'momentum': 2, 'support': 1, 'buying': 2,
            'uptrend': 2, 'bull market': 3, 'earnings beat': 3, 'profit': 2
        }
        
        bearish_keywords = {
            'crash': 3, 'plunge': 3, 'breakdown': 3, 'bearish': 2, 'fall': 2,
            'drop': 2, 'decline': 2, 'sell-off': 2, 'weak': 2, 'negative': 1,
            'pessimistic': 1, 'downgrade': 2, 'recession': 3, 'crisis': 3,
            'resistance': 1, 'selling': 2, 'downtrend': 2, 'bear market': 3,
            'earnings miss': 3, 'loss': 2, 'layoffs': 2, 'bankruptcy': 3
        }
        
        # Calculate weighted sentiment
        bullish_score = sum(weight for keyword, weight in bullish_keywords.items() if keyword in text_lower)
        bearish_score = sum(weight for keyword, weight in bearish_keywords.items() if keyword in text_lower)
        
        total_score = bullish_score + bearish_score
        if total_score > 0:
            sentiment = (bullish_score - bearish_score) / total_score
            confidence = min(1.0, total_score / 20)  # Normalize confidence
        else:
            sentiment = 0.0
            confidence = 0.0
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "model_used": "enhanced_keywords"
        }
    
    def _store_sentiment_result(self, headlines: List[str], result: Dict):
        """Store sentiment analysis result for learning"""
        try:
            # Create hash of headlines for deduplication
            headlines_text = " ".join(headlines)
            news_hash = hashlib.md5(headlines_text.encode()).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO news_sentiment 
                (news_hash, headline, ai_sentiment, confidence, model_used, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                news_hash,
                headlines_text[:500],  # Limit headline length
                result['sentiment'],
                result['confidence'],
                result['model_used'],
                datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to store sentiment result: {e}")
    
    def assess_risk_level(self, signal_data: Dict, sentiment: Dict) -> str:
        """
        AI-powered risk assessment
        
        Args:
            signal_data (Dict): Technical signal data
            sentiment (Dict): Sentiment analysis results
            
        Returns:
            str: Risk level (low, medium, high, extreme)
        """
        risk_score = 0.0
        
        # Technical factors
        probability = signal_data.get('probability', 50.0)
        if probability < 40:
            risk_score += 2
        elif probability < 50:
            risk_score += 1
        elif probability > 70:
            risk_score -= 1
        
        # Sentiment factors
        sentiment_score = sentiment.get('sentiment', 0.0)
        confidence = sentiment.get('confidence', 0.0)
        
        # Conflicting signals increase risk
        if signal_data.get('signal_type') == 'BUY' and sentiment_score < -0.3:
            risk_score += 2
        elif signal_data.get('signal_type') == 'SELL' and sentiment_score > 0.3:
            risk_score += 2
        
        # Low confidence increases risk
        if confidence < 0.3:
            risk_score += 1
        
        # Check historical performance
        historical_risk = self._get_historical_risk(signal_data.get('symbol', ''))
        risk_score += historical_risk
        
        # Determine risk level
        if risk_score <= 0:
            return "low"
        elif risk_score <= 2:
            return "medium"
        elif risk_score <= 4:
            return "high"
        else:
            return "extreme"
    
    def _get_historical_risk(self, symbol: str) -> float:
        """Get historical risk score for symbol"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent performance
            cursor.execute('''
                SELECT actual_outcome, profit_loss FROM signal_performance
                WHERE symbol = ? AND timestamp > datetime('now', '-30 days')
                ORDER BY timestamp DESC
                LIMIT 20
            ''', (symbol,))
            
            results = cursor.fetchall()
            conn.close()
            
            if not results:
                return 0.0  # No history = neutral risk
            
            # Calculate success rate and average P&L
            successful_trades = sum(1 for outcome, _ in results if outcome == 1)
            success_rate = successful_trades / len(results)
            
            avg_pl = mean([pl for _, pl in results if pl is not None])
            
            # Higher risk for lower success rate and negative P&L
            risk_adjustment = 0.0
            if success_rate < 0.4:
                risk_adjustment += 1.0
            if avg_pl < 0:
                risk_adjustment += 0.5
            
            return risk_adjustment
            
        except Exception as e:
            self.logger.error(f"Failed to get historical risk: {e}")
            return 0.0
    
    def learn_from_outcome(self, signal_id: str, outcome: bool, profit_loss: float):
        """
        Learn from trading outcome to improve future predictions
        
        Args:
            signal_id (str): Unique signal identifier
            outcome (bool): True if profitable, False if loss
            profit_loss (float): Actual profit/loss amount
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update signal performance
            cursor.execute('''
                UPDATE signal_performance 
                SET actual_outcome = ?, profit_loss = ?
                WHERE id = ?
            ''', (1 if outcome else 0, profit_loss, signal_id))
            
            # Update learned patterns
            self._update_learned_patterns(cursor, signal_id, outcome, profit_loss)
            
            conn.commit()
            conn.close()
            
            print(f"SUCCESS: Learned from outcome - {'Profit' if outcome else 'Loss'}: {profit_loss}")
            
        except Exception as e:
            self.logger.error(f"Failed to learn from outcome: {e}")
    
    def _update_learned_patterns(self, cursor, signal_id: str, outcome: bool, profit_loss: float):
        """Update learned patterns based on outcome"""
        # This would be expanded with more sophisticated pattern recognition
        # For now, just track basic symbol performance
        
        cursor.execute('''
            SELECT symbol, signal_type, risk_level FROM signal_performance
            WHERE id = ?
        ''', (signal_id,))
        
        result = cursor.fetchone()
        if result:
            symbol, signal_type, risk_level = result
            pattern_key = f"{symbol}_{signal_type}_{risk_level}"
            
            # Update or create pattern
            cursor.execute('''
                SELECT success_rate, usage_count FROM learned_patterns
                WHERE pattern_type = ?
            ''', (pattern_key,))
            
            existing = cursor.fetchone()
            if existing:
                old_success_rate, usage_count = existing
                new_count = usage_count + 1
                new_success_rate = (old_success_rate * usage_count + (1 if outcome else 0)) / new_count
                
                cursor.execute('''
                    UPDATE learned_patterns
                    SET success_rate = ?, usage_count = ?, last_updated = ?
                    WHERE pattern_type = ?
                ''', (new_success_rate, new_count, datetime.now(), pattern_key))
            else:
                cursor.execute('''
                    INSERT INTO learned_patterns 
                    (pattern_type, pattern_data, success_rate, usage_count, last_updated)
                    VALUES (?, ?, ?, 1, ?)
                ''', (pattern_key, json.dumps({"symbol": symbol, "signal_type": signal_type, "risk_level": risk_level}), 
                     1 if outcome else 0, datetime.now()))
    
    def get_ai_enhanced_probability(self, base_probability: float, signal_data: Dict, sentiment: Dict) -> float:
        """
        Use AI learning to enhance probability calculation
        
        Args:
            base_probability (float): Original probability from strategy
            signal_data (Dict): Technical signal data
            sentiment (Dict): Sentiment analysis results
            
        Returns:
            float: Enhanced probability
        """
        try:
            # Start with base probability
            enhanced_prob = base_probability
            
            # Apply sentiment adjustment
            sentiment_score = sentiment.get('sentiment', 0.0)
            confidence = sentiment.get('confidence', 0.0)
            
            # Strong positive sentiment boosts probability
            if sentiment_score > 0.5 and confidence > 0.6:
                enhanced_prob += 10 * sentiment_score * confidence
            # Strong negative sentiment reduces probability
            elif sentiment_score < -0.5 and confidence > 0.6:
                enhanced_prob += 10 * sentiment_score * confidence  # This will be negative
            
            # Apply historical learning
            symbol = signal_data.get('symbol', '')
            historical_adjustment = self._get_historical_adjustment(symbol, signal_data.get('signal_type', ''))
            enhanced_prob += historical_adjustment
            
            # Ensure probability stays within bounds
            enhanced_prob = max(5.0, min(95.0, enhanced_prob))
            
            return enhanced_prob
            
        except Exception as e:
            self.logger.error(f"Failed to enhance probability: {e}")
            return base_probability
    
    def _get_historical_adjustment(self, symbol: str, signal_type: str) -> float:
        """Get historical adjustment based on past performance"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent performance for this symbol and signal type
            cursor.execute('''
                SELECT AVG(CASE WHEN actual_outcome = 1 THEN 1.0 ELSE 0.0 END) as success_rate,
                       COUNT(*) as total_count
                FROM signal_performance
                WHERE symbol = ? AND signal_type = ? 
                AND timestamp > datetime('now', '-30 days')
                AND actual_outcome IS NOT NULL
            ''', (symbol, signal_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[1] >= 5:  # Need at least 5 historical trades
                success_rate = result[0]
                if success_rate > 0.7:
                    return 5.0  # Boost for historically successful patterns
                elif success_rate < 0.3:
                    return -5.0  # Penalty for historically unsuccessful patterns
            
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Failed to get historical adjustment: {e}")
            return 0.0
    
    def get_learning_stats(self) -> Dict:
        """Get AI learning statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get total signals processed
            cursor.execute('SELECT COUNT(*) FROM signal_performance')
            total_signals = cursor.fetchone()[0]
            
            # Get success rate
            cursor.execute('''
                SELECT AVG(CASE WHEN actual_outcome = 1 THEN 1.0 ELSE 0.0 END)
                FROM signal_performance
                WHERE actual_outcome IS NOT NULL
            ''')
            result = cursor.fetchone()
            success_rate = result[0] if result[0] else 0.0
            
            # Get model usage stats
            cursor.execute('''
                SELECT model_used, COUNT(*) 
                FROM news_sentiment 
                GROUP BY model_used
            ''')
            model_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                "total_signals": total_signals,
                "success_rate": success_rate,
                "model_usage": model_stats,
                "models_available": self.local_models_available
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get learning stats: {e}")
            return {"error": str(e)} 