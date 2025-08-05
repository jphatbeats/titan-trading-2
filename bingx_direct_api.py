#!/usr/bin/env python3
"""
Direct BingX API integration using official endpoints
Fixes pricing accuracy issues by bypassing CCXT
"""

import requests
import time
import hmac
import hashlib
from typing import Dict, Optional

class BingXDirectAPI:
    """Direct BingX API client using official documentation"""
    
    def __init__(self, api_key: str = "", secret_key: str = ""):
        self.base_url = "https://open-api.bingx.com"
        self.api_key = api_key
        self.secret_key = secret_key
    
    def get_ticker(self, symbol: str) -> Dict:
        """
        Get 24hr ticker statistics using official BingX API
        Endpoint: /openApi/swap/v2/quote/ticker
        """
        try:
            # Convert symbol format if needed (BTC/USDT -> BTC-USDT)
            bingx_symbol = symbol.replace('/', '-')
            
            # Use V2 ticker endpoint (recommended by BingX)
            path = '/openApi/swap/v2/quote/ticker'
            params = {
                'symbol': bingx_symbol,
                'timestamp': str(int(time.time() * 1000))
            }
            
            url = f"{self.base_url}{path}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    ticker_data = data['data']
                    
                    # Convert to CCXT-like format for compatibility
                    return {
                        'symbol': symbol,
                        'last': float(ticker_data.get('lastPrice', 0)),
                        'bid': float(ticker_data.get('bidPrice', 0)),
                        'ask': float(ticker_data.get('askPrice', 0)),
                        'high': float(ticker_data.get('highPrice', 0)),
                        'low': float(ticker_data.get('lowPrice', 0)),
                        'volume': float(ticker_data.get('volume', 0)),
                        'baseVolume': float(ticker_data.get('volume', 0)),
                        'change': float(ticker_data.get('priceChange', 0)),
                        'percentage': float(ticker_data.get('priceChangePercent', 0)),
                        'timestamp': ticker_data.get('time'),
                        'datetime': None,
                        'info': ticker_data,
                        'source': 'bingx_direct_api'
                    }
                else:
                    raise Exception(f"BingX API error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"BingX ticker fetch failed: {str(e)}")
    
    def get_price(self, symbol: str) -> Dict:
        """
        Get simple price using BingX price endpoint
        Endpoint: /openApi/swap/v1/ticker/price
        """
        try:
            # Convert symbol format
            bingx_symbol = symbol.replace('/', '-')
            
            path = '/openApi/swap/v1/ticker/price'
            params = {
                'symbol': bingx_symbol,
                'timestamp': str(int(time.time() * 1000))
            }
            
            url = f"{self.base_url}{path}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    price_data = data['data']
                    return {
                        'symbol': symbol,
                        'price': float(price_data.get('price', 0)),
                        'timestamp': int(time.time() * 1000),
                        'source': 'bingx_direct_api',
                        'info': price_data
                    }
                else:
                    raise Exception(f"BingX API error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"BingX price fetch failed: {str(e)}")
    
    def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book using BingX depth endpoint
        Endpoint: /openApi/swap/v2/quote/depth
        """
        try:
            bingx_symbol = symbol.replace('/', '-')
            
            path = '/openApi/swap/v2/quote/depth'
            params = {
                'symbol': bingx_symbol,
                'limit': str(min(limit, 100)),  # BingX max limit
                'timestamp': str(int(time.time() * 1000))
            }
            
            url = f"{self.base_url}{path}"
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 0 and 'data' in data:
                    depth_data = data['data']
                    
                    # Convert to CCXT format
                    bids = [[float(bid[0]), float(bid[1])] for bid in depth_data.get('bids', [])]
                    asks = [[float(ask[0]), float(ask[1])] for ask in depth_data.get('asks', [])]
                    
                    return {
                        'symbol': symbol,
                        'bids': bids,
                        'asks': asks,
                        'timestamp': int(time.time() * 1000),
                        'datetime': None,
                        'nonce': None,
                        'source': 'bingx_direct_api',
                        'info': depth_data
                    }
                else:
                    raise Exception(f"BingX API error: {data.get('msg', 'Unknown error')}")
            else:
                raise Exception(f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            raise Exception(f"BingX orderbook fetch failed: {str(e)}")

# Create global instance
bingx_direct = BingXDirectAPI()

def test_direct_api():
    """Test the direct BingX API implementation"""
    print("Testing BingX Direct API...")
    
    try:
        # Test ticker
        print("\n1. Testing BTC-USDT ticker:")
        ticker = bingx_direct.get_ticker('BTC/USDT')
        print(f"   Last: ${ticker['last']:,.2f}")
        print(f"   Bid/Ask: ${ticker['bid']:,.2f} / ${ticker['ask']:,.2f}")
        print(f"   24h Change: {ticker['percentage']:+.2f}%")
        
        # Test price
        print("\n2. Testing BTC-USDT price:")
        price_data = bingx_direct.get_price('BTC/USDT')
        print(f"   Price: ${price_data['price']:,.2f}")
        
        # Test orderbook
        print("\n3. Testing BTC-USDT orderbook:")
        orderbook = bingx_direct.get_orderbook('BTC/USDT', 5)
        if orderbook['bids'] and orderbook['asks']:
            print(f"   Best bid: ${orderbook['bids'][0][0]:,.2f}")
            print(f"   Best ask: ${orderbook['asks'][0][0]:,.2f}")
        
        print("\n✅ BingX Direct API test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ BingX Direct API test failed: {e}")
        return False

if __name__ == "__main__":
    test_direct_api()