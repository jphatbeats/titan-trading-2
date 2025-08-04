"""
Real Crypto News API Integration
Using the CryptoNews API for intelligent news filtering and processing
"""
import requests
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class CryptoNewsAPI:
    """Integrates with CryptoNews API for real-time crypto news intelligence"""
    
    def __init__(self, api_token: str = "ayimav7nlptgzetysg9dwhqteampvoirtfx5orqk"):
        self.base_url = "https://cryptonews-api.com/api/v1"
        self.api_token = api_token
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make API request with error handling"""
        try:
            params['token'] = self.api_token
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"CryptoNews API error: {e}")
            return {'error': str(e), 'data': []}
    
    def get_breaking_news(self, limit: int = 10, sentiment: str = None, 
                         date_filter: str = "last60min") -> Dict[str, Any]:
        """Get breaking crypto news with filtering"""
        params = {
            'section': 'general',
            'items': min(limit, 50),
            'sortby': 'rank',
            'source': 'Coindesk,CryptoSlate,The+Block,Decrypt'  # Tier 1 sources from docs
        }
        
        # Only add date filter if it's one of the valid options from docs
        valid_dates = ['last5min', 'last10min', 'last15min', 'last30min', 'last45min', 
                      'last60min', 'today', 'yesterday', 'last7days', 'last30days']
        if date_filter in valid_dates:
            params['date'] = date_filter
            
        if sentiment:
            params['sentiment'] = sentiment.lower()
            
        return self._make_request('/category', params)
    
    def get_portfolio_news(self, tickers: List[str], limit: int = 15) -> Dict[str, Any]:
        """Get news specific to user's portfolio holdings using search workaround"""
        if not tickers:
            return {'data': [], 'message': 'No tickers provided'}
        
        # WORKAROUND: API requires tickers parameter but search parameter actually works
        # Use BTC as dummy ticker + search for actual symbols
        search_terms = ','.join(tickers)
        params = {
            'tickers': 'BTC',  # Required by API (dummy value)
            'search': search_terms,  # Actual search that finds results
            'items': min(limit, 50),
            'date': 'today',
            'sortby': 'rank'
        }
        
        return self._make_request('', params)
    
    def get_news_by_symbols(self, symbols: List[str], limit: int = 10, 
                           mode: str = "broad") -> Dict[str, Any]:
        """Get news by specific symbols using tickers+search workaround"""
        if not symbols:
            return {'data': [], 'message': 'No symbols provided'}
        
        if mode == "laser" and len(symbols) == 1:
            # Single symbol search - try direct ticker first, then search fallback
            symbol = symbols[0]
            
            # Try direct ticker search first (works for MAMO)
            params = {
                'items': min(limit, 50),
                'tickers': symbol
            }
            result = self._make_request('', params)
            
            # If direct ticker fails, try search workaround (works for ENA)
            if not result.get('data'):
                params = {
                    'items': min(limit, 50),
                    'tickers': 'BTC',  # Required dummy parameter
                    'search': symbol
                }
                result = self._make_request('', params)
            
            return result
        
        elif mode == "broad" and len(symbols) > 1:
            # Multi-symbol search - combine individual results
            all_articles = []
            seen_titles = set()
            
            for symbol in symbols:
                # Try direct ticker first, then search fallback
                params = {
                    'items': min(limit, 20),
                    'tickers': symbol
                }
                result = self._make_request('', params)
                
                # If direct ticker fails, try search workaround
                if not result.get('data'):
                    params = {
                        'items': min(limit, 20),
                        'tickers': 'BTC',
                        'search': symbol
                    }
                    result = self._make_request('', params)
                
                if 'data' in result:
                    for article in result['data']:
                        title = article.get('title', '')
                        # Avoid duplicates and add symbol context
                        if title not in seen_titles:
                            article['search_symbol'] = symbol
                            all_articles.append(article)
                            seen_titles.add(title)
            
            # Sort by date and limit results
            all_articles = sorted(all_articles, 
                                key=lambda x: x.get('published_at', ''), 
                                reverse=True)[:limit]
            
            return {
                'data': all_articles,
                'symbols_searched': symbols,
                'total_found': len(all_articles)
            }
        
        else:
            # Fallback for other modes
            params = {
                'items': min(limit, 50),
                'tickers': 'BTC',
                'search': ' AND '.join(symbols) if mode == "intersection" else ','.join(symbols)
            }
            return self._make_request('', params)
    
    def get_risk_alerts(self, limit: int = 20, severity: str = "high") -> Dict[str, Any]:
        """Get risk-related crypto news and alerts"""
        params = {
            'section': 'general',
            'items': min(limit, 50),
            'sentiment': 'negative',
            'search': 'hack,exploit,rug+pull,delisting,SEC,regulation,lawsuit,scam,vulnerability',
            'date': 'today',  # Use valid date from docs
            'sortby': 'rank',
            'source': 'Coindesk,CryptoSlate,The+Block,Decrypt,Forbes'
        }
        
        return self._make_request('/category', params)
    
    def get_bullish_signals(self, limit: int = 15, timeframe: str = "today") -> Dict[str, Any]:
        """Get bullish sentiment and positive catalyst news"""
        params = {
            'section': 'general',
            'items': min(limit, 50),
            'sentiment': 'positive',
            'search': 'partnership,listing,binance,coinbase,institutional,adoption,breakthrough',
            'sortby': 'rank',
            'source': 'Coindesk,CryptoSlate,The+Block,Decrypt'
        }
        
        # Only add valid date filters
        valid_dates = ['last5min', 'last10min', 'last15min', 'last30min', 'last45min', 
                      'last60min', 'today', 'yesterday', 'last7days', 'last30days']
        if timeframe in valid_dates:
            params['date'] = timeframe
            
        return self._make_request('/category', params)
    
    def scan_opportunities(self, sectors: List[str] = None, limit: int = 25) -> Dict[str, Any]:
        """Scan for trading opportunities across sectors using predefined topics"""
        if not sectors:
            # Use actual topic parameters from API docs
            sectors = ['NFT', 'Mining', 'pricemovement', 'Institutions', 'Upgrade']
            
        params = {
            'section': 'alltickers',
            'items': min(limit, 50),
            'sentiment': 'positive',
            'topicOR': ','.join(sectors),  # Topics use comma separation
            'date': 'today',
            'sortby': 'rank'
        }
        
        return self._make_request('/category', params)
    
    def get_by_topic(self, topics: List[str], limit: int = 20, 
                     logic: str = "OR") -> Dict[str, Any]:
        """Get news by specific topics using AND or OR logic"""
        if not topics:
            return {'data': [], 'message': 'No topics provided'}
            
        params = {
            'section': 'general',
            'items': min(limit, 50),
            'sortby': 'rank',
            'date': 'today'
        }
        
        # Use topicOR or topic based on logic preference
        if logic.upper() == "OR":
            params['topicOR'] = ','.join(topics)
        else:
            params['topic'] = ','.join(topics)  # AND logic
            
        return self._make_request('/category', params)
    
    def get_market_intelligence(self, comprehensive: bool = True) -> Dict[str, Any]:
        """Get comprehensive market intelligence analysis"""
        params = {
            'section': 'general',
            'items': 30 if comprehensive else 15,
            'date': 'last24hours',
            'sortby': 'rank',
            'source': 'Coindesk,CryptoSlate,The+Block,Decrypt,Forbes'
        }
        
        return self._make_request('/category', params)
    
    def detect_pump_dump_signals(self, limit: int = 20) -> Dict[str, Any]:
        """Detect potential pump and dump patterns in news"""
        params = {
            'section': 'general',
            'items': min(limit, 50),
            'search': 'pump,dump,manipulation,whale,unusual+volume,massive+buy,coordinated',
            'date': 'today',  # Use valid date from docs
            'sortby': 'rank'
        }
        
        return self._make_request('/category', params)
    
    def get_ultra_fresh_news(self, minutes: int = 5) -> Dict[str, Any]:
        """Get ultra-fresh news for immediate opportunities"""
        date_filter = f"last{minutes}min" if minutes <= 60 else "last60min"
        
        params = {
            'items': 20,
            'date': date_filter,
            'sortby': 'rank',
            'sentiment': 'positive',
            'source': 'Coindesk,CryptoSlate,The+Block'
        }
        
        return self._make_request('', params)
    
    def get_prioritized_alerts(self, limit: int = 20, urgency_filter: str = None) -> Dict[str, Any]:
        """Get news with urgency prioritization based on source quality and timeframe"""
        params = {
            'items': min(limit, 50),
            'date': 'last2hours',  # Recent for urgency
            'sortby': 'rank',
            'source': 'Coindesk,CryptoSlate,The+Block,Decrypt'  # Tier 1 only
        }
        
        result = self._make_request('', params)
        
        # Add urgency scoring to each article
        if result.get('data'):
            for article in result['data']:
                source = article.get('source_name', article.get('source', ''))
                sentiment = article.get('sentiment', 'neutral').lower()
                
                # Calculate urgency score
                urgency_score = 0
                if source in ['Coindesk', 'CryptoSlate', 'The Block', 'Decrypt']:
                    urgency_score += 3  # Tier 1 sources
                elif source in ['NewsBTC', 'CryptoPotato', 'BeInCrypto']:
                    urgency_score += 2  # Tier 2 sources
                else:
                    urgency_score += 1  # Tier 3 sources
                
                if sentiment == 'positive':
                    urgency_score += 2
                elif sentiment == 'negative':
                    urgency_score += 3  # Negative news is more urgent
                
                # Assign urgency level
                if urgency_score >= 5:
                    article['urgency'] = 'HIGH'
                elif urgency_score >= 3:
                    article['urgency'] = 'MEDIUM'
                else:
                    article['urgency'] = 'LOW'
                
                article['urgency_score'] = urgency_score
        
        return result
    
    def monitor_portfolio_threats(self, holdings: List[str], limit: int = 15) -> Dict[str, Any]:
        """Monitor specific threats to portfolio holdings"""
        if not holdings:
            return {'data': [], 'message': 'No holdings provided'}
            
        threat_keywords = "hack,exploit,delisting,lawsuit,investigation,frozen,stolen"
        
        params = {
            'tickers': ','.join(holdings),
            'items': min(limit, 50),
            'sentiment': 'negative',
            'search': threat_keywords,
            'date': 'last12hours',
            'sortby': 'rank'
        }
        
        return self._make_request('', params)
    
    def find_correlation_plays(self, primary_tickers: List[str], limit: int = 10) -> Dict[str, Any]:
        """Find news affecting multiple correlated assets"""
        if not primary_tickers:
            return {'data': [], 'message': 'No tickers provided'}
            
        params = {
            'tickers-include': ','.join(primary_tickers),  # Must mention ALL tickers
            'items': min(limit, 50),
            'sentiment': 'positive',
            'date': 'last24hours',
            'search': 'institutional,etf,partnership,adoption'
        }
        
        return self._make_request('', params)

# Singleton instance for easy importing
crypto_news_api = CryptoNewsAPI()

# Helper functions for backward compatibility with existing code
def get_breaking_crypto_news(limit: int = 10, sentiment: str = None) -> Dict[str, Any]:
    """Get breaking crypto news (backward compatible)"""
    return crypto_news_api.get_breaking_news(limit=limit, sentiment=sentiment)

def get_crypto_risk_alerts(limit: int = 20) -> Dict[str, Any]:
    """Get crypto risk alerts (backward compatible)"""
    return crypto_news_api.get_risk_alerts(limit=limit)

def get_crypto_bullish_signals(limit: int = 15) -> Dict[str, Any]:
    """Get bullish crypto signals (backward compatible)"""
    return crypto_news_api.get_bullish_signals(limit=limit)

def scan_crypto_opportunities(limit: int = 25) -> Dict[str, Any]:
    """Scan crypto opportunities (backward compatible)"""
    return crypto_news_api.scan_opportunities(limit=limit)

def get_market_intelligence() -> Dict[str, Any]:
    """Get market intelligence (backward compatible)"""
    return crypto_news_api.get_market_intelligence()

def detect_pump_dump_signals(limit: int = 20) -> Dict[str, Any]:
    """Detect pump dump signals (backward compatible)"""
    return crypto_news_api.detect_pump_dump_signals(limit=limit)
