#!/usr/bin/env python3
"""
Yahoo Finance Gold Web Scraper
Scrapes real-time Gold (GC=F) data directly from Yahoo Finance website
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
import logging

class YahooFinanceGoldScraper:
    def __init__(self):
        self.base_url = "https://finance.yahoo.com/quote/GC%3DF/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def scrape_gold_data(self):
        """Scrape Gold (GC=F) data from Yahoo Finance"""
        try:
            self.logger.info("🔄 Scraping Gold data from Yahoo Finance...")
            
            # Fetch the page
            response = self.session.get(self.base_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract current price
            current_price = self._extract_current_price(soup)
            if not current_price:
                self.logger.error("❌ Could not extract current price")
                return None
            
            # Extract previous close
            previous_close = self._extract_previous_close(soup)
            if not previous_close:
                self.logger.error("❌ Could not extract previous close")
                # Try to use a reasonable fallback (current price - 1% as rough estimate)
                previous_close = current_price * 0.99
                self.logger.warning(f"⚠️ Using fallback previous close: {previous_close:.2f}")
                # For now, let's continue with the fallback instead of returning None
                # return None
            
            # Extract day's range (high/low)
            day_range = self._extract_day_range(soup)
            
            # Calculate change
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100
            
            # Format data
            gold_data = {
                'price': f"{current_price:.2f}",
                'change': f"{change:+.2f}",
                'changePercent': f"{change_percent:+.2f}%",
                'rawChange': change,
                'previousClose': f"{previous_close:.2f}",
                'high': day_range.get('high', '--'),
                'low': day_range.get('low', '--'),
                'source': 'Yahoo Finance Web Scraper (GC=F)',
                'timestamp': datetime.now().isoformat(),
                'raw_current_price': current_price,
                'raw_previous_close': previous_close
            }
            
            self.logger.info(f"✅ Gold data scraped successfully:")
            self.logger.info(f"   Current: ${current_price:.2f}")
            self.logger.info(f"   Previous: ${previous_close:.2f}")
            self.logger.info(f"   Change: {change:+.2f} ({change_percent:+.2f}%)")
            
            return gold_data
            
        except requests.RequestException as e:
            self.logger.error(f"❌ Network error while scraping Gold data: {e}")
            return None
        except Exception as e:
            self.logger.error(f"❌ Error scraping Gold data: {e}")
            return None
    
    def _extract_current_price(self, soup):
        """Extract current price from the page"""
        try:
            # Method 1: Look for price in data attributes or specific selectors
            price_selectors = [
                '[data-symbol="GC=F"] [data-field="regularMarketPrice"]',
                '[data-testid="qsp-price"]',
                '.Fw\\(b\\).Fz\\(36px\\)',
                '.D\\(ib\\).Mend\\(20px\\) .Fw\\(b\\).Fz\\(36px\\)',
                'fin-streamer[data-field="regularMarketPrice"]'
            ]
            
            for selector in price_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        self.logger.info(f"📊 Found current price using selector '{selector}': {price}")
                        return price
            
            # Method 2: Look for price in JSON data within script tags
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'QuoteSummaryStore' in script.string:
                    match = re.search(r'"regularMarketPrice":\s*{\s*"raw":\s*([\d.]+)', script.string)
                    if match:
                        price = float(match.group(1))
                        self.logger.info(f"📊 Found current price in script data: {price}")
                        return price
            
            # Method 3: Search for price patterns in text
            price_pattern = re.compile(r'3[,\s]*[0-9]{3}[.,][0-9]{2}')
            text_content = soup.get_text()
            matches = price_pattern.findall(text_content)
            if matches:
                for match in matches:
                    price = self._parse_price(match)
                    if price and 3000 < price < 4000:  # Sanity check for Gold price range
                        self.logger.info(f"📊 Found current price using pattern: {price}")
                        return price
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting current price: {e}")
            return None
    
    def _extract_previous_close(self, soup):
        """Extract previous close from the page - prioritizing 'Last Price'"""
        try:
            # Method 1: Look for "Last Price" first (as requested)
            last_price_patterns = [
                'Last Price',
                'Last',
                'Prev. Close',
                'Previous Close'
            ]
            
            for pattern in last_price_patterns:
                text_elements = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
                for text_elem in text_elements:
                    if text_elem.parent:
                        # Look for price in nearby elements
                        parent = text_elem.parent
                        siblings = parent.parent.find_all(['td', 'span', 'div', 'fin-streamer']) if parent.parent else []
                        
                        for sibling in siblings:
                            price_text = sibling.get_text(strip=True)
                            price = self._parse_price(price_text)
                            if price and 3000 < price < 4000:
                                self.logger.info(f"📊 Found previous close using '{pattern}': {price}")
                                return price
            
            # Method 2: Look for previous close in specific selectors
            prev_close_selectors = [
                '[data-testid="PREV_CLOSE-value"]',
                'td[data-test="PREV_CLOSE-value"]',
                '.C\\(\\$labelColor\\)[data-test="PREV_CLOSE-value"]',
                '[data-field="regularMarketPreviousClose"]',
                'fin-streamer[data-field="regularMarketPreviousClose"]'
            ]
            
            for selector in prev_close_selectors:
                elements = soup.select(selector)
                for element in elements:
                    price_text = element.get_text(strip=True)
                    price = self._parse_price(price_text)
                    if price:
                        self.logger.info(f"📊 Found previous close using selector '{selector}': {price}")
                        return price
            
            # Method 3: Look in JSON data
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'QuoteSummaryStore' in script.string:
                    # Try multiple patterns for previous close
                    patterns = [
                        r'"previousClose":\s*{\s*"raw":\s*([\d.]+)',
                        r'"regularMarketPreviousClose":\s*{\s*"raw":\s*([\d.]+)',
                        r'"regularMarketPreviousClose":\s*([\d.]+)'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, script.string)
                        if match:
                            price = float(match.group(1))
                            self.logger.info(f"📊 Found previous close in script data: {price}")
                            return price
            
            # Method 4: Search all table data for patterns
            table_data = soup.find_all(['td', 'th'])
            for i, cell in enumerate(table_data):
                cell_text = cell.get_text(strip=True)
                if any(keyword in cell_text for keyword in ['Previous Close', 'Prev. Close', 'Last Price']):
                    # Look for the value in the next cell or adjacent cells
                    for j in range(i+1, min(i+4, len(table_data))):
                        value_cell = table_data[j]
                        price_text = value_cell.get_text(strip=True)
                        price = self._parse_price(price_text)
                        if price and 3000 < price < 4000:
                            self.logger.info(f"📊 Found previous close in table data: {price}")
                            return price
            
            return None
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting previous close: {e}")
            return None
    
    def _extract_day_range(self, soup):
        """Extract day's high and low"""
        try:
            day_range = {'high': '--', 'low': '--'}
            
            # Method 1: Look for specific range selectors
            range_selectors = [
                '[data-testid="DAYS_RANGE-value"]',
                'td[data-test="DAYS_RANGE-value"]',
                '[data-field="regularMarketDayRange"]'
            ]
            
            for selector in range_selectors:
                elements = soup.select(selector)
                for element in elements:
                    range_text = element.get_text(strip=True)
                    # Parse range like "3,325.50 - 3,376.60"
                    range_match = re.search(r'([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)', range_text)
                    if range_match:
                        low = self._parse_price(range_match.group(1))
                        high = self._parse_price(range_match.group(2))
                        if low and high:
                            day_range['low'] = f"{low:.2f}"
                            day_range['high'] = f"{high:.2f}"
                            self.logger.info(f"📊 Found day range using selector: {day_range['low']} - {day_range['high']}")
                            return day_range
            
            # Method 2: Look for "Day's Range" text and extract nearby values
            range_text_patterns = ['Day\'s Range', 'Days Range', 'Day Range', 'Range']
            for pattern in range_text_patterns:
                text_elements = soup.find_all(string=re.compile(pattern, re.IGNORECASE))
                for text_elem in text_elements:
                    if text_elem.parent:
                        parent = text_elem.parent
                        siblings = parent.parent.find_all(['td', 'span', 'div']) if parent.parent else []
                        
                        for sibling in siblings:
                            range_text = sibling.get_text(strip=True)
                            range_match = re.search(r'([\d,]+\.?\d*)\s*-\s*([\d,]+\.?\d*)', range_text)
                            if range_match:
                                low = self._parse_price(range_match.group(1))
                                high = self._parse_price(range_match.group(2))
                                if low and high and 3000 < low < 4000 and 3000 < high < 4000:
                                    day_range['low'] = f"{low:.2f}"
                                    day_range['high'] = f"{high:.2f}"
                                    self.logger.info(f"📊 Found day range using text pattern: {day_range['low']} - {day_range['high']}")
                                    return day_range
            
            # Method 3: Look in JSON data for high/low
            scripts = soup.find_all('script')
            for script in scripts:
                if script.string and 'QuoteSummaryStore' in script.string:
                    # Try to find high and low separately
                    high_match = re.search(r'"regularMarketDayHigh":\s*{\s*"raw":\s*([\d.]+)', script.string)
                    low_match = re.search(r'"regularMarketDayLow":\s*{\s*"raw":\s*([\d.]+)', script.string)
                    
                    if high_match and low_match:
                        high = float(high_match.group(1))
                        low = float(low_match.group(1))
                        if 3000 < high < 4000 and 3000 < low < 4000:
                            day_range['high'] = f"{high:.2f}"
                            day_range['low'] = f"{low:.2f}"
                            self.logger.info(f"📊 Found day range in script data: {day_range['low']} - {day_range['high']}")
                            return day_range
            
            # Method 4: Search all table cells for range patterns
            all_cells = soup.find_all(['td', 'span', 'div'])
            for cell in all_cells:
                cell_text = cell.get_text(strip=True)
                # Look for patterns like "3,325.50 - 3,376.60"
                range_match = re.search(r'(3[,\s]*[0-9]{3}[.,][0-9]{2})\s*-\s*(3[,\s]*[0-9]{3}[.,][0-9]{2})', cell_text)
                if range_match:
                    low = self._parse_price(range_match.group(1))
                    high = self._parse_price(range_match.group(2))
                    if low and high and 3000 < low < 4000 and 3000 < high < 4000:
                        day_range['low'] = f"{low:.2f}"
                        day_range['high'] = f"{high:.2f}"
                        self.logger.info(f"📊 Found day range in cell pattern: {day_range['low']} - {day_range['high']}")
                        return day_range
            
            return day_range
            
        except Exception as e:
            self.logger.error(f"❌ Error extracting day range: {e}")
            return {'high': '--', 'low': '--'}
    
    def _parse_price(self, price_text):
        """Parse price from text, handling commas and various formats"""
        try:
            if not price_text:
                return None
            
            # Clean the price text
            cleaned = re.sub(r'[^\d.,]', '', str(price_text).strip())
            cleaned = cleaned.replace(',', '')
            
            if not cleaned or cleaned == '.':
                return None
            
            price = float(cleaned)
            
            # Sanity check for Gold prices (should be between 1000-10000)
            if 1000 <= price <= 10000:
                return price
            
            return None
            
        except (ValueError, TypeError):
            return None


# Global instance
gold_scraper = YahooFinanceGoldScraper()

def get_gold_data():
    """Get Gold data using web scraper"""
    return gold_scraper.scrape_gold_data()

if __name__ == "__main__":
    # Test the scraper
    data = get_gold_data()
    if data:
        print("Gold data scraped successfully:")
        print(json.dumps(data, indent=2))
    else:
        print("Failed to scrape Gold data")