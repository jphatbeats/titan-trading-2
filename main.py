import requests
import pandas as pd
import time
import hmac
import hashlib
from datetime import datetime, timedelta
import pytz
import ccxt
import random

# ====== 🔐 INSERT YOUR API KEYS HERE ======
# BingX API Keys - Retrieved from Secrets
import os
bingx_api_key = os.getenv('BINGX_API_KEY', '')
bingx_api_secret = os.getenv('BINGX_API_SECRET', '')

# Blofin API Keys (CCXT) - Retrieved from Secrets
import os
blofin_api_key = os.getenv('BLOFIN_API_KEY', '')
blofin_api_secret = os.getenv('BLOFIN_API_SECRET', '')
blofin_passphrase = os.getenv('BLOFIN_PASSPHRASE', '')

# Kraken API Keys (CCXT) - Retrieved from Secrets
kraken_api_key = os.getenv('KRAKEN_API_KEY', '')
kraken_api_secret = os.getenv('KRAKEN_API_SECRET', '')
# ================================================

# Generate timestamp and signature
def get_signature(params, secret):
    sorted_params = sorted(params.items())
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()
    return signature

# Fetch open positions from BingX Futures (using correct v2 API endpoint)
def fetch_positions():
    if not bingx_api_key or not bingx_api_secret:
        print("❌ BingX API keys not configured. Please set BINGX_API_KEY and BINGX_API_SECRET in Secrets.")
        return {'code': -1, 'msg': 'API keys not configured'}

    base_url = 'https://open-api.bingx.com'
    endpoint = '/openApi/swap/v2/user/positions'  # Fixed: positions (plural)
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'

    # Create query string for signature
    query_string = f"timestamp={timestamp}&recvWindow={recv_window}"
    signature = hmac.new(bingx_api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {
        'X-BX-APIKEY': bingx_api_key
    }

    # Build final URL with signature
    url = f"{base_url}{endpoint}?timestamp={timestamp}&recvWindow={recv_window}&signature={signature}"

    print(f"🔍 BingX API Request URL: {base_url}{endpoint}")
    print(f"🔍 Headers: {headers}")
    print(f"🔍 Query params: timestamp={timestamp}, recvWindow={recv_window}")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"🔍 BingX API Response Status: {response.status_code}")
        print(f"🔍 BingX API Response: {response.text}")

        if response.status_code != 200:
            print(f"❌ BingX API HTTP Error: {response.status_code}")
            return {'code': response.status_code, 'msg': f'HTTP Error: {response.text}'}

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ BingX API Request Error: {str(e)}")
        return {'code': -1, 'msg': f'Request failed: {str(e)}'}

# Fetch open orders to get SL/TP information
def fetch_open_orders(symbol=None):
    if not bingx_api_key or not bingx_api_secret:
        print("❌ BingX API keys not configured for orders fetch.")
        return {'code': -1, 'msg': 'API keys not configured'}

    base_url = 'https://open-api.bingx.com'
    endpoint = '/openApi/swap/v2/trade/openOrders'
    timestamp = str(int(time.time() * 1000))
    recv_window = '5000'

    # Create query string for signature
    params = {'timestamp': timestamp, 'recvWindow': recv_window}
    if symbol:
        params['symbol'] = symbol

    sorted_params = sorted(params.items())
    query_string = '&'.join([f"{k}={v}" for k, v in sorted_params])
    signature = hmac.new(bingx_api_secret.encode(), query_string.encode(), hashlib.sha256).hexdigest()

    headers = {
        'X-BX-APIKEY': bingx_api_key
    }

    # Build final URL with signature
    url = f"{base_url}{endpoint}?{query_string}&signature={signature}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"🔍 BingX Orders API Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ BingX Orders API HTTP Error: {response.status_code} - {response.text}")
            return {'code': response.status_code, 'msg': f'HTTP Error: {response.text}'}

        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ BingX Orders API Request Error: {str(e)}")
        return {'code': -1, 'msg': f'Request failed: {str(e)}'}

# Initialize Blofin exchange using CCXT
def initialize_blofin():
    try:
        if not blofin_api_key or not blofin_api_secret:
            print("⚠️ Blofin API keys not configured - skipping Blofin data")
            return None

        blofin = ccxt.blofin({
            'apiKey': blofin_api_key,
            'secret': blofin_api_secret,
            'password': blofin_passphrase,
            'sandbox': False,  # Set to True for testnet
            'enableRateLimit': True,
        })
        return blofin
    except Exception as e:
        print(f"❌ Error initializing Blofin: {e}")
        return None

# Initialize Kraken exchange using CCXT
def initialize_kraken():
    try:
        if not kraken_api_key or not kraken_api_secret:
            print("⚠️ Kraken API keys not configured - skipping Kraken data")
            return None

        kraken = ccxt.kraken({
            'apiKey': kraken_api_key,
            'secret': kraken_api_secret,
            'sandbox': False,  # Set to True for testnet
            'enableRateLimit': True,
        })
        return kraken
    except Exception as e:
        print(f"❌ Error initializing Kraken: {e}")
        return None

# Fetch Blofin positions using CCXT
def fetch_blofin_positions(blofin_exchange):
    try:
        if not blofin_exchange:
            return []

        print("📋 Fetching Blofin positions...")
        positions = blofin_exchange.fetch_positions()

        # Filter out positions with zero size
        active_positions = [pos for pos in positions if pos['contracts'] != 0]
        print(f"🔍 Found {len(active_positions)} active Blofin positions")

        return active_positions
    except Exception as e:
        print(f"❌ Error fetching Blofin positions: {e}")
        return []

# Fetch Blofin orders using CCXT
def fetch_blofin_orders(blofin_exchange):
    try:
        if not blofin_exchange:
            return []

        print("📋 Fetching Blofin open orders...")
        orders = blofin_exchange.fetch_open_orders()
        print(f"🔍 Found {len(orders)} Blofin open orders")

        return orders
    except Exception as e:
        print(f"❌ Error fetching Blofin orders: {e}")
        return []

# Fetch Kraken positions using CCXT with enhanced data (handles both futures positions and spot balances)
def fetch_kraken_positions(kraken_exchange):
    try:
        if not kraken_exchange:
            return []

        print("📋 Fetching enhanced Kraken positions and balances...")

        # Get futures positions
        positions = []
        try:
            positions = kraken_exchange.fetch_positions()
            print(f"📊 Found {len([p for p in positions if p['contracts'] != 0])} active futures positions")
        except Exception as e:
            print(f"⚠️ Could not fetch futures positions (normal for spot-only accounts): {e}")

        # Get balance for spot holdings
        balance = kraken_exchange.fetch_balance()
        print(f"📊 Found balances for {len([k for k, v in balance.items() if isinstance(v, dict) and v.get('total', 0) > 0])} assets")

        # Get trading history for entry analysis
        trades = []
        try:
            trades = kraken_exchange.fetch_my_trades(limit=50)
            print(f"📊 Retrieved {len(trades)} recent trades for analysis")
        except Exception as e:
            print(f"⚠️ Could not fetch trade history: {e}")

        enhanced_positions = []

        # Process futures positions
        for pos in positions:
            if pos['contracts'] == 0:
                continue

            symbol = pos['symbol']

            # Calculate USD values using current balance
            token_amount = abs(pos['contracts'])
            current_price = pos['markPrice'] or 0
            usd_value = token_amount * current_price if current_price else 0

            # Find related trades for this symbol
            symbol_trades = [t for t in trades if t['symbol'] == symbol]

            # Calculate average entry price and time in trade
            entry_price = pos['entryPrice'] or 0
            earliest_trade = None
            total_cost = 0
            total_quantity = 0

            if symbol_trades:
                symbol_trades.sort(key=lambda x: x['timestamp'])
                earliest_trade = symbol_trades[0]

                for trade in symbol_trades:
                    if trade['side'] == ('buy' if pos['side'] == 'long' else 'sell'):
                        total_cost += trade['cost']
                        total_quantity += trade['amount']

                if total_quantity > 0:
                    avg_entry = total_cost / total_quantity
                    if avg_entry > 0:
                        entry_price = avg_entry

            # Calculate time in trade
            time_in_trade = "Unknown"
            if earliest_trade:
                try:
                    from datetime import datetime
                    trade_time = datetime.fromtimestamp(earliest_trade['timestamp'] / 1000)
                    current_time = datetime.now()
                    time_diff = current_time - trade_time

                    days = time_diff.days
                    hours = time_diff.seconds // 3600

                    if days > 0:
                        time_in_trade = f"{days}d {hours}h"
                    else:
                        time_in_trade = f"{hours}h"
                except:
                    time_in_trade = "Unknown"

            unrealized_pnl = pos.get('unrealizedPnl', 0) or 0
            pnl_percentage = pos.get('percentage', 0) or 0

            enhanced_pos = {
                **pos,
                'enhanced_data': {
                    'token_amount': round(token_amount, 6),
                    'usd_value': round(usd_value, 2),
                    'entry_price_calculated': round(entry_price, 6) if entry_price else 0,
                    'current_price': round(current_price, 6) if current_price else 0,
                    'unrealized_pnl_usd': round(unrealized_pnl, 2),
                    'pnl_percentage': round(pnl_percentage, 2),
                    'time_in_trade': time_in_trade,
                    'trade_count': len(symbol_trades),
                    'avg_trade_size': round(sum(t['amount'] for t in symbol_trades) / len(symbol_trades), 6) if symbol_trades else 0,
                    'total_fees_paid': round(sum(t.get('fee', {}).get('cost', 0) for t in symbol_trades), 4)
                }
            }

            enhanced_positions.append(enhanced_pos)

        # Process spot balances as positions (for accounts without futures)
        if len(enhanced_positions) == 0:
            print("📊 No futures positions found, converting spot balances to positions...")

            for currency, amounts in balance.items():
                if not isinstance(amounts, dict) or amounts.get('total', 0) <= 0:
                    continue

                if currency in ['USD', 'EUR', 'GBP']:  # Skip fiat currencies
                    continue

                try:
                    # Get current price for this asset
                    symbol_to_check = f"{currency}/USD"
                    current_price = 0

                    try:
                        ticker = kraken_exchange.fetch_ticker(symbol_to_check)
                        current_price = ticker.get('last', 0)
                    except:
                        # Try alternative symbols
                        alt_symbols = [f"{currency}/USDT", f"{currency}/EUR"]
                        for alt_symbol in alt_symbols:
                            try:
                                ticker = kraken_exchange.fetch_ticker(alt_symbol)
                                current_price = ticker.get('last', 0)
                                symbol_to_check = alt_symbol
                                break
                            except:
                                continue

                    if current_price <= 0:
                        print(f"⚠️ Could not get price for {currency}")
                        continue

                    token_amount = amounts['total']
                    usd_value = token_amount * current_price

                    # Find trades for this currency
                    currency_trades = [t for t in trades if currency in t['symbol']]

                    # Calculate entry analysis
                    avg_entry_price = 0
                    time_in_trade = "Unknown"
                    total_cost = 0
                    total_quantity = 0

                    if currency_trades:
                        currency_trades.sort(key=lambda x: x['timestamp'])
                        earliest_trade = currency_trades[0]

                        # Calculate weighted average entry price
                        for trade in currency_trades:
                            if trade['side'] == 'buy':
                                total_cost += trade['cost']
                                total_quantity += trade['amount']

                        if total_quantity > 0:
                            avg_entry_price = total_cost / total_quantity

                        # Calculate time holding
                        try:
                            from datetime import datetime
                            trade_time = datetime.fromtimestamp(earliest_trade['timestamp'] / 1000)
                            current_time = datetime.now()
                            time_diff = current_time - trade_time

                            days = time_diff.days
                            if days > 0:
                                time_in_trade = f"{days} days"
                            else:
                                hours = time_diff.seconds // 3600
                                time_in_trade = f"{hours} hours"
                        except:
                            time_in_trade = "Unknown"

                    # Calculate unrealized PnL
                    unrealized_pnl = 0
                    pnl_percentage = 0

                    if avg_entry_price > 0:
                        price_change = current_price - avg_entry_price
                        unrealized_pnl = price_change * token_amount
                        pnl_percentage = (price_change / avg_entry_price) * 100

                    # Create position-like object for spot holding
                    spot_position = {
                        'symbol': symbol_to_check,
                        'side': 'long',  # Spot holdings are always long
                        'contracts': token_amount,
                        'contractSize': 1,
                        'entryPrice': avg_entry_price,
                        'markPrice': current_price,
                        'unrealizedPnl': unrealized_pnl,
                        'percentage': pnl_percentage,
                        'timestamp': int(datetime.now().timestamp() * 1000),
                        'enhanced_data': {
                            'token_amount': round(token_amount, 6),
                            'usd_value': round(usd_value, 2),
                            'entry_price_calculated': round(avg_entry_price, 6),
                            'current_price': round(current_price, 6),
                            'unrealized_pnl_usd': round(unrealized_pnl, 2),
                            'pnl_percentage': round(pnl_percentage, 2),
                            'time_in_trade': time_in_trade,
                            'trade_count': len(currency_trades),
                            'avg_trade_size': round(sum(t['amount'] for t in currency_trades) / len(currency_trades), 6) if currency_trades else 0,
                            'total_fees_paid': round(sum(t.get('fee', {}).get('cost', 0) for t in currency_trades), 4),
                            'position_type': 'spot_holding'
                        }
                    }

                    enhanced_positions.append(spot_position)

                except Exception as e:
                    print(f"⚠️ Error processing {currency} balance: {e}")
                    continue

        print(f"🔍 Enhanced {len(enhanced_positions)} Kraken positions/holdings with trading data")
        return enhanced_positions

    except Exception as e:
        print(f"❌ Error fetching enhanced Kraken positions: {e}")
        return []

# Fetch Kraken orders using CCXT
def fetch_kraken_orders(kraken_exchange):
    try:
        if not kraken_exchange:
            return []

        print("📋 Fetching Kraken open orders...")
        orders = kraken_exchange.fetch_open_orders()
        print(f"🔍 Found {len(orders)} Kraken open orders")

        return orders
    except Exception as e:
        print(f"❌ Error fetching Kraken orders: {e}")
        return []

# Clean up old CSV files - keep only the latest
def cleanup_old_csv_files(current_filename):
    """Remove old positions CSV files, keeping only the latest one"""
    try:
        import glob
        import os

        # Find all positions CSV files
        csv_files = glob.glob("positions_*.csv")

        if len(csv_files) <= 1:
            return  # Nothing to clean up

        # Remove all except the current file
        deleted_count = 0
        for csv_file in csv_files:
            if csv_file != current_filename:
                try:
                    os.remove(csv_file)
                    deleted_count += 1
                except Exception as e:
                    print(f"⚠️ Could not delete {csv_file}: {e}")

        if deleted_count > 0:
            print(f"🧹 Cleaned up {deleted_count} old CSV files - keeping only {current_filename}")

    except Exception as e:
        print(f"⚠️ Error during CSV cleanup: {e}")

# Fetch BingX candlestick/OHLCV data
def fetch_bingx_klines(symbol, interval='1h', limit=100, extend=False):
    """
    Fetch candlestick/OHLCV data from BingX public API

    Args:
        symbol: Trading pair symbol (e.g., 'BTC-USDT')
        interval: Kline interval (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
        limit: Number of klines to return (default: 100, max: 1000)
        extend: Extend the data by creating mock candles (useful for backtesting)

    Returns:
        List of candlestick data with OHLCV information
    """
    try:
        if extend:
            print("⚠️ Warning: Extending klines with mock data! This is for testing only.")
            import random
            from datetime import timedelta

            # Create extended data by going backwards from current time
            base_time = datetime.now(pytz.timezone('US/Central'))
            extended_data = []

            for i in range(limit):
                # Calculate time for this candle (going backwards)
                if interval.endswith('m'):
                    minutes = int(interval[:-1])
                    candle_time = base_time - timedelta(minutes=minutes * i)
                elif interval.endswith('h'):
                    hours = int(interval[:-1])
                    candle_time = base_time - timedelta(hours=hours * i)
                elif interval == '1d':
                    candle_time = base_time - timedelta(days=i)
                else:
                    candle_time = base_time - timedelta(hours=i)  # Default to hours

                # Ensure candle_time is valid and properly formatted
                candle_time = candle_time.replace(second=0, microsecond=0)

                # Generate realistic OHLCV data
                base_price = 119000 + (i * 50)  # Simulate price movement
                open_price = base_price + random.uniform(-200, 200)
                high_price = open_price + random.uniform(0, 500)
                low_price = open_price - random.uniform(0, 300)
                close_price = open_price + random.uniform(-250, 250)
                volume = random.uniform(100, 1000)

                # Properly format timestamps to avoid negative hours
                timestamp_ms = int(candle_time.timestamp() * 1000)
                readable_time = candle_time.strftime('%Y-%m-%d %H:%M:%S CST')

                kline_data = {
                    'open': round(open_price, 1),
                    'high': round(high_price, 1),
                    'low': round(low_price, 1),
                    'close': round(close_price, 1),
                    'volume': round(volume, 2),
                    'open_time': timestamp_ms,
                    'close_time': timestamp_ms,
                    'open_time_readable': readable_time,
                    'close_time_readable': readable_time,
                    'count': 0,
                    'quote_volume': 0
                }

                extended_data.append(kline_data)

            return {'code': 0, 'data': extended_data}

        base_url = 'https://open-api.bingx.com'
        endpoint = '/openApi/swap/v3/quote/klines'

        # Build query parameters
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }

        # Make request to public API (no authentication needed)
        url = f"{base_url}{endpoint}"
        response = requests.get(url, params=params, timeout=10)

        print(f"🕯️ BingX Klines Request: {url}")
        print(f"🔍 Parameters: {params}")
        print(f"📊 Response Status: {response.status_code}")

        if response.status_code != 200:
            print(f"❌ BingX Klines API Error: {response.status_code} - {response.text}")
            return {'code': response.status_code, 'msg': f'HTTP Error: {response.text}', 'data': []}

        data = response.json()

        if data.get('code') == 0:
            klines = data.get('data', [])
            processed_klines = []

            # Process klines into readable format
            # The API returns objects, not arrays
            for kline in klines:
                try:
                    # Handle both array format [timestamp, open, high, low, close, volume] 
                    # and object format {"time": timestamp, "open": price, ...}
                    if isinstance(kline, list):
                        # Array format
                        processed_kline = {
                            'open_time': int(kline[0]),
                            'open_time_readable': datetime.fromtimestamp(int(kline[0])/1000, tz=pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S CST'),
                            'open': float(kline[1]),
                            'high': float(kline[2]),
                            'low': float(kline[3]),
                            'close': float(kline[4]),
                            'volume': float(kline[5]),
                            'close_time': int(kline[6]) if len(kline) > 6 else int(kline[0]),
                            'close_time_readable': datetime.fromtimestamp((int(kline[6]) if len(kline) > 6 else int(kline[0]))/1000, tz=pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S CST'),
                            'quote_volume': float(kline[7]) if len(kline) > 7 else 0,
                            'count': int(kline[8]) if len(kline) > 8 else 0
                        }
                    else:
                        # Object format (what we're actually getting)
                        processed_kline = {
                            'open_time': int(kline['time']),
                            'open_time_readable': datetime.fromtimestamp(int(kline['time'])/1000, tz=pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S CST'),
                            'open': float(kline['open']),
                            'high': float(kline['high']),
                            'low': float(kline['low']),
                            'close': float(kline['close']),
                            'volume': float(kline['volume']),
                            'close_time': int(kline['time']),  # Use same time for close
                            'close_time_readable': datetime.fromtimestamp(int(kline['time'])/1000, tz=pytz.timezone('US/Central')).strftime('%Y-%m-%d %H:%M:%S CST'),
                            'quote_volume': 0,  # Not provided in this format
                            'count': 0  # Not provided in this format
                        }
                    processed_klines.append(processed_kline)
                except Exception as e:
                    print(f"❌ Error processing kline {kline}: {e}")
                    continue

            print(f"📈 Successfully fetched {len(processed_klines)} candlesticks for {symbol}")
            return {'code': 0, 'data': processed_klines}
        else:
            print(f"❌ BingX Klines API returned error: {data}")
            return data

    except requests.exceptions.RequestException as e:
        print(f"❌ BingX Klines Request Error: {str(e)}")
        return {'code': -1, 'msg': f'Request failed: {str(e)}', 'data': []}
    except Exception as e:
        print(f"❌ BingX Klines Processing Error: {str(e)}")
        return {'code': -1, 'msg': f'Processing failed: {str(e)}', 'data': []}

def get_bingx_market_data(symbol):
    """
    Get comprehensive market data including 24hr ticker and recent klines

    Args:
        symbol: Trading pair symbol (e.g., 'BTC-USDT')

    Returns:
        Dictionary with ticker and klines data
    """
    try:
        base_url = 'https://open-api.bingx.com'

        # Get 24hr ticker data
        ticker_endpoint = '/openApi/swap/v2/quote/ticker'
        ticker_response = requests.get(f"{base_url}{ticker_endpoint}", params={'symbol': symbol}, timeout=10)

        # Get recent klines (last 24 hours)
        klines_1h = fetch_bingx_klines(symbol, interval='1h', limit=24)
        klines_15m = fetch_bingx_klines(symbol, interval='15m', limit=96)  # Last 24 hours in 15m intervals

        result = {
            'symbol': symbol,
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'ticker_24hr': {},
            'klines_1h': klines_1h.get('data', []),
            'klines_15m': klines_15m.get('data', []),
            'market_analysis': {}
        }

        # Process ticker data
        if ticker_response.status_code == 200:
            ticker_data = ticker_response.json()
            if ticker_data.get('code') == 0 and ticker_data.get('data'):
                ticker = ticker_data['data']
                result['ticker_24hr'] = ticker

                # Add some basic analysis
                if klines_1h.get('data'):
                    latest_kline = klines_1h['data'][-1]
                    result['market_analysis'] = {
                        'current_price': latest_kline['close'],
                        '24h_change': float(ticker.get('priceChangePercent', 0)),
                        '24h_high': latest_kline['high'],
                        '24h_low': latest_kline['low'],
                        '24h_volume': float(ticker.get('volume', 0)),
                        'price_trend': 'bullish' if float(ticker.get('priceChangePercent', 0)) > 0 else 'bearish'
                    }

        return result

    except Exception as e:
        print(f"❌ Error fetching BingX market data: {str(e)}")
        return {'error': str(e)}

def analyze_candlestick_patterns(symbol, interval='1h', limit=50):
    """Analyze BingX candlestick patterns and provide trading signals"""
    try:
        print(f"🔍 Analyzing candlestick patterns for {symbol} ({interval}, {limit} candles)")

        # Fetch klines data
        klines_result = fetch_bingx_klines(symbol, interval, limit)

        if klines_result.get('code') != 0:
            return {'error': f'Failed to fetch klines: {klines_result}'}

        klines = klines_result.get('data', [])
        if not klines:
            return {'error': 'No candlestick data available'}

        # Convert to numerical data for analysis
        prices = [float(k['close']) for k in klines]
        highs = [float(k['high']) for k in klines]
        lows = [float(k['low']) for k in klines]
        volumes = [float(k['volume']) for k in klines]

        # Calculate technical indicators
        def simple_moving_average(data, period):
            if len(data) < period:
                return None
            return sum(data[-period:]) / period

        sma_20 = simple_moving_average(prices, 20)
        sma_50 = simple_moving_average(prices, 50) if len(prices) >= 50 else None

        current_price = prices[-1]

        # Support and resistance levels
        recent_highs = highs[-20:] if len(highs) >= 20 else highs
        recent_lows = lows[-20:] if len(lows) >= 20 else lows
        resistance_level = max(recent_highs)
        support_level = min(recent_lows)

        # Trend analysis
        recent_candles = klines[-10:]  # Last 10 candles
        bullish_candles = sum(1 for k in recent_candles if float(k['close']) > float(k['open']))
        bearish_candles = len(recent_candles) - bullish_candles

        # Momentum analysis
        if len(prices) >= 5:
            recent_momentum = (prices[-1] - prices[-5]) / prices[-5] * 100
            momentum = 'strong_bullish' if recent_momentum > 2 else 'bullish' if recent_momentum > 0.5 else 'strong_bearish' if recent_momentum < -2 else 'bearish' if recent_momentum < -0.5 else 'neutral'
        else:
            momentum = 'neutral'

        # Volatility analysis
        price_changes = [abs(prices[i] - prices[i-1]) / prices[i-1] * 100 for i in range(1, len(prices))]
        avg_volatility = sum(price_changes) / len(price_changes) if price_changes else 0
        volatility = 'high' if avg_volatility > 3 else 'medium' if avg_volatility > 1 else 'low'

        # Generate trading signals
        trend_signal = 'neutral'
        if sma_20:
            if current_price > sma_20 * 1.02:  # 2% above SMA20
                trend_signal = 'bullish'
            elif current_price < sma_20 * 0.98:  # 2% below SMA20
                trend_signal = 'bearish'

        price_vs_sma20 = 'above' if sma_20 and current_price > sma_20 else 'below' if sma_20 else 'unknown'

        result = {
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'interval': interval,
            'candlesticks_analyzed': len(klines),
            'current_price': current_price,
            'technical_signals': {
                'trend_signal': trend_signal,
                'price_vs_sma20': price_vs_sma20,
                'momentum': momentum,
                'support_level': support_level,
                'resistance_level': resistance_level,
                'sma_20': sma_20,
                'sma_50': sma_50
            },
            'trend_analysis': {
                'recent_bullish_candles': bullish_candles,
                'recent_bearish_candles': bearish_candles,
                'momentum': momentum,
                'volatility': volatility,
                'avg_volatility_percent': round(avg_volatility, 2)
            },
            'key_levels': {
                'current_price': current_price,
                'support': support_level,
                'resistance': resistance_level,
                'distance_to_support': round((current_price - support_level) / current_price * 100, 2),
                'distance_to_resistance': round((resistance_level - current_price) / current_price * 100, 2)
            },
            'raw_data': {
                'latest_candles': klines[-5:],  # Last 5 candles for reference
                'price_history': prices[-20:]   # Last 20 prices
            }
        }

        return result

    except Exception as e:
        print(f"❌ Error analyzing candlestick patterns: {str(e)}")
        return {'error': str(e)}

# Calculate Risk-to-Reward Ratio
def calculate_risk_reward(entry_price, mark_price, sl_price, tp_price, side):
    if not sl_price or not tp_price:
        return None

    try:
        entry_price = float(entry_price)
        mark_price = float(mark_price)
        sl_price = float(sl_price)
        tp_price = float(tp_price)

        if side == 'LONG':
            distance_to_sl = abs(mark_price - sl_price)
            distance_to_tp = abs(tp_price - mark_price)
        else:  # SHORT
            distance_to_sl = abs(sl_price - mark_price)
            distance_to_tp = abs(mark_price - tp_price)

        if distance_to_sl == 0:
            return None

        risk_reward = distance_to_tp / distance_to_sl
        return round(risk_reward, 2)
    except (ValueError, ZeroDivisionError):
        return None

# Process and export
def export_positions():
    # Fetch BingX positions
    result = fetch_positions()
    print("🔍 BingX API Response:", result)  # Debug: see actual response

    bingx_positions = []
    if result and result.get('code') == 0:
        bingx_positions = result.get('data', [])
        print(f"🔍 Found {len(bingx_positions)} BingX positions")
    else:
        error_msg = result.get('msg', 'Unknown error') if result else 'No response from API'
        print(f"⚠️ Warning: Could not fetch BingX positions - {error_msg}")

    # Initialize and fetch Blofin positions
    blofin_exchange = initialize_blofin()
    blofin_positions = fetch_blofin_positions(blofin_exchange)
    blofin_orders = fetch_blofin_orders(blofin_exchange)

    # Initialize and fetch Kraken positions
    kraken_exchange = initialize_kraken()
    kraken_positions = fetch_kraken_positions(kraken_exchange)
    kraken_orders = fetch_kraken_orders(kraken_exchange)

    # Combine positions for processing
    all_positions = []

    # Process BingX positions (existing logic)
    if bingx_positions:
        print("🔍 First BingX position structure:", bingx_positions[0] if bingx_positions else "No positions")  # Debug: see structure

    # Fetch all open orders to get SL/TP information
    print("📋 Fetching open orders for SL/TP data...")
    orders_result = fetch_open_orders()
    print("🔍 Orders API Response:", orders_result)  # Debug: see orders response

    # Extract orders from the nested structure with better error handling
    orders_data = []
    if orders_result and orders_result.get('code') == 0 and 'data' in orders_result:
        data_obj = orders_result['data']
        if isinstance(data_obj, dict) and 'orders' in data_obj:
            orders_data = data_obj['orders']
        elif isinstance(data_obj, list):
            orders_data = data_obj
    else:
        error_msg = orders_result.get('msg', 'Unknown error') if orders_result else 'No response from orders API'
        print(f"⚠️ Warning: Could not fetch orders - {error_msg}")

    print(f"🔍 Number of orders found: {len(orders_data)}")  # Debug: count orders

    # Create a mapping of symbol to SL/TP orders
    sl_tp_map = {}
    if orders_data and len(orders_data) > 0:
        print("🔍 First order structure:", orders_data[0])  # Debug: see structure

        for order in orders_data:
            # Check if order is a dictionary
            if isinstance(order, dict):
                symbol = order.get('symbol', '')
                order_type = order.get('type', '')
                stop_price = order.get('stopPrice', '')

                if symbol not in sl_tp_map:
                    sl_tp_map[symbol] = {'SL': None, 'TP': None}

                # Check for takeProfit and stopLoss nested objects (BingX API structure)
                take_profit = order.get('takeProfit', {})
                stop_loss = order.get('stopLoss', {})

                # Extract TP from nested takeProfit object
                if take_profit and take_profit.get('stopPrice'):
                    sl_tp_map[symbol]['TP'] = take_profit.get('stopPrice')

                # Extract SL from nested stopLoss object  
                if stop_loss and stop_loss.get('stopPrice'):
                    sl_tp_map[symbol]['SL'] = stop_loss.get('stopPrice')

                # Also check for direct order types
                if order_type in ['STOP_MARKET', 'STOP'] and stop_price:
                    sl_tp_map[symbol]['SL'] = stop_price
                elif order_type in ['TAKE_PROFIT_MARKET', 'TAKE_PROFIT'] and stop_price:
                    sl_tp_map[symbol]['TP'] = stop_price
            else:
                print(f"⚠️ Unexpected order format: {order}")
    else:
        print("📝 No open orders found")

    print(f"🔍 Number of BingX positions found: {len(bingx_positions)}")  # Debug: count positions

    # Process BingX positions
    data = []
    for p in bingx_positions:
        symbol = p.get('symbol', '')
        side = p.get('positionSide', '')
        entry_price = p.get('avgPrice', '')
        mark_price = p.get('markPrice', '')

        # Get SL/TP for this position
        sl_price = sl_tp_map.get(symbol, {}).get('SL', '')
        tp_price = sl_tp_map.get(symbol, {}).get('TP', '')

        # Calculate Risk-to-Reward ratio
        risk_reward = calculate_risk_reward(entry_price, mark_price, sl_price, tp_price, side)

        # Convert all numeric fields with proper error handling
        try:
            unrealized_pnl = float(p.get('unrealizedProfit', 0))
            position_value = float(p.get('positionValue', 1))
            leverage = pd.to_numeric(p.get('leverage', 1), errors='coerce')
            if pd.isna(leverage):
                leverage = 1

            entry_price_float = pd.to_numeric(entry_price, errors='coerce')
            if pd.isna(entry_price_float):
                entry_price_float = 0

            mark_price_float = pd.to_numeric(mark_price, errors='coerce')
            if pd.isna(mark_price_float):
                mark_price_float = 0

            amount = pd.to_numeric(p.get('positionAmt', 0), errors='coerce')
            if pd.isna(amount):
                amount = 0

            # Regular PnL percentage
            pnl_percentage = round((unrealized_pnl / position_value) * 100, 2) if position_value != 0 else 0

            # Unrealized PnL calculations per your specifications
            if entry_price_float > 0 and leverage > 0:
                # Formula: ((Mark Price - Entry Price) / Entry Price) * Leverage * 100
                unrealized_pnl_percentage = round(((mark_price_float - entry_price_float) / entry_price_float) * leverage * 100, 2)
                # Formula: (Unrealized PnL % / 100) * (Entry Price * Amount / Leverage)
                unrealized_pnl_dollar = round((unrealized_pnl_percentage / 100) * (entry_price_float * amount / leverage), 3)
            else:
                unrealized_pnl_percentage = 0
                unrealized_pnl_dollar = 0

            # Calculate Margin Size ($) = Position Value / Leverage
            margin_size = round(position_value / leverage, 2) if leverage > 0 else 0

        except (ValueError, ZeroDivisionError):
            pnl_percentage = 0
            unrealized_pnl_percentage = 0
            unrealized_pnl_dollar = 0

        # Convert timestamp to readable format (Central Time)
        create_time = p.get('createTime', 0)
        if create_time:
            try:
                central_tz = pytz.timezone('US/Central')
                dt = datetime.fromtimestamp(create_time / 1000, tz=pytz.UTC)
                dt_central = dt.astimezone(central_tz)
                timestamp_readable = dt_central.strftime('%Y-%m-%d %I:%M %p CST')
            except:
                timestamp_readable = str(create_time)
        else:
            timestamp_readable = ''

        # Get position mode (isolated/cross)
        position_mode = 'Isolated' if p.get('isolated', True) else 'Cross'

        # Parse TP and SL values using pd.to_numeric for consistent handling
        tp_numeric = pd.to_numeric(tp_price, errors='coerce')
        if pd.isna(tp_numeric):
            tp_numeric = 0

        sl_numeric = pd.to_numeric(sl_price, errors='coerce')
        if pd.isna(sl_numeric):
            sl_numeric = 0

        # Calculate Distance to TP and SL percentages
        distance_to_tp = 0
        distance_to_sl = 0

        if tp_numeric > 0 and mark_price_float > 0:
            if side == 'LONG':
                distance_to_tp = round(((tp_numeric - mark_price_float) / mark_price_float) * 10, 2)
            else:  # SHORT
                distance_to_tp = round(((mark_price_float - tp_numeric) / mark_price_float) * 100, 2)

        if sl_numeric > 0 and mark_price_float > 0:
            if side == 'LONG':
                distance_to_sl = round(((sl_numeric - mark_price_float) / mark_price_float) * 100, 2)
            else:  # SHORT
                distance_to_sl = round(((mark_price_float - sl_numeric) / mark_price_float) * 100, 2)

        # Trend Status based on Unrealized PnL%
        if unrealized_pnl_percentage > 30:
            trend_status = "Uptrend"
        elif unrealized_pnl_percentage < -20:
            trend_status = "Downtrend"
        else:
            trend_status = "Sideways"

        # Enhanced Risk Flag
        if sl_numeric == 0 and margin_size > 100:
            risk_flag_new = "High Risk"
        else:
            risk_flag_new = "OK"

        # Use the actual field names from BingX API
        data.append({
            'Platform': 'BingX',
            'Symbol': symbol,
            'Position Type': 'Rotation',  # Default value, manually update to "Runner" as needed
            'Entry Price': entry_price,
            'Mark Price': mark_price,
            'Leverage': p.get('leverage', ''),
            'Position Mode': position_mode,
            'Amount': p.get('positionAmt', ''),
            'PnL $': p.get('unrealizedProfit', ''),
            'PnL %': pnl_percentage,
            'Unrealized PnL %': unrealized_pnl_percentage,
            'Unrealized PnL $': unrealized_pnl_dollar,
            'Margin Size ($)': margin_size,
            'Liquidation Price': p.get('liquidationPrice', ''),
            'Side (LONG/SHORT)': side,
            'SL (Stop Loss)': sl_price if sl_price else 0,
            'TP (Take Profit)': tp_price if tp_price else 0,
            'Distance to TP (%)': distance_to_tp,
            'Distance to SL (%)': distance_to_sl,
            'TP Set?': '✅' if tp_numeric > 0 else '❌',
            'SL Set?': '✅' if sl_numeric > 0 else '❌',
            'TP Price': tp_price if tp_price else 0,
            'SL Price': sl_price if sl_price else 0,
            'Risk-to-Reward Ratio': risk_reward if risk_reward else 'N/A',
            'Trend Status': trend_status,
            'Risk Flag (New)': risk_flag_new,
            'Entry Timestamp': timestamp_readable
        })

    # Process Blofin positions
    if blofin_positions:
        print(f"🔍 Processing {len(blofin_positions)} Blofin positions...")

        # Create SL/TP mapping for Blofin orders
        blofin_sl_tp_map = {}
        for order in blofin_orders:
            symbol = order['symbol']
            if symbol not in blofin_sl_tp_map:
                blofin_sl_tp_map[symbol] = {'SL': None, 'TP': None}

            # CCXT order types
            if order['type'] == 'stop' or 'stop' in order['type'].lower():
                blofin_sl_tp_map[symbol]['SL'] = order.get('triggerPrice', order.get('stopPrice'))
            elif order['type'] == 'take_profit' or 'profit' in order['type'].lower():
                blofin_sl_tp_map[symbol]['TP'] = order.get('triggerPrice', order.get('stopPrice'))

        for pos in blofin_positions:
            try:
                symbol = pos['symbol']
                side = 'LONG' if pos['side'] == 'long' else 'SHORT'

                # Fix NoneType errors by properly handling None values
                entry_price = float(pos['entryPrice']) if pos.get('entryPrice') is not None else 0.0
                mark_price = float(pos['markPrice']) if pos.get('markPrice') is not None else 0.0

                # Get SL/TP for this position
                sl_price = blofin_sl_tp_map.get(symbol, {}).get('SL', 0)
                tp_price = blofin_sl_tp_map.get(symbol, {}).get('TP', 0)

                # CCXT position fields with proper None handling
                unrealized_pnl = float(pos['unrealizedPnl']) if pos.get('unrealizedPnl') is not None else 0.0
                notional = float(pos['notional']) if pos.get('notional') is not None else 1.0
                leverage = float(pos.get('leverage')) if pos.get('leverage') is not None else 1.0
                amount = float(pos['contracts']) if pos.get('contracts') is not None else 0.0
                liquidation_price = float(pos.get('liquidationPrice')) if pos.get('liquidationPrice') is not None else 0.0
                margin_mode = pos.get('marginMode', 'cross')

                # Calculate margin size for Blofin
                margin_size = abs(notional / leverage) if leverage > 0 else 0.0

                # Calculate PnL percentage based on margin
                pnl_percentage = round((unrealized_pnl / margin_size) * 100, 2) if margin_size > 0 else 0

                # Format timestamp
                timestamp = pos.get('timestamp', 0)
                if timestamp:
                    try:
                        central_tz = pytz.timezone('US/Central')
                        dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
                        dt_central = dt.astimezone(central_tz)
                        timestamp_readable = dt_central.strftime('%Y-%m-%d %I:%M %p CST')
                    except:
                        timestamp_readable = str(timestamp)
                else:
                    timestamp_readable = ''

                # Check TP/SL status
                tp_numeric = float(tp_price) if tp_price else 0
                sl_numeric = float(sl_price) if sl_price else 0

                # Calculate Distance to TP and SL percentages for Blofin
                distance_to_tp_blofin = 0
                distance_to_sl_blofin = 0

                if tp_numeric > 0 and mark_price > 0:
                    if side == 'LONG':
                        distance_to_tp_blofin = round(((tp_numeric - mark_price) / mark_price) * 100, 2)
                    else:  # SHORT
                        distance_to_tp_blofin = round(((mark_price - tp_numeric) / mark_price) * 100, 2)

                if sl_numeric > 0 and mark_price > 0:
                    if side == 'LONG':
                        distance_to_sl_blofin = round(((sl_numeric - mark_price) / mark_price) * 100, 2)
                    else:  # SHORT
                        distance_to_sl_blofin = round(((mark_price - sl_numeric) / mark_price) * 100, 2)

                # Trend Status based on Unrealized PnL%
                if pnl_percentage > 30:
                    trend_status_blofin = "Uptrend"
                elif pnl_percentage < -20:
                    trend_status_blofin = "Downtrend"
                else:
                    trend_status_blofin = "Sideways"

                # Enhanced Risk Flag for Blofin
                if sl_numeric == 0 and margin_size > 100:
                    risk_flag_blofin = "High Risk"
                else:
                    risk_flag_blofin = "OK"

                data.append({
                    'Platform': 'Blofin',
                    'Symbol': symbol,
                    'Position Type': 'Rotation',  # Default value, manually update to "Runner" as needed
                    'Entry Price': entry_price,
                    'Mark Price': mark_price,
                    'Leverage': leverage,
                    'Position Mode': margin_mode,
                    'Amount': amount,
                    'PnL $': unrealized_pnl,
                    'PnL %': pnl_percentage,
                    'Unrealized PnL %': pnl_percentage,  # Use same calculation
                    'Unrealized PnL $': unrealized_pnl,
                    'Margin Size ($)': margin_size,
                    'Initial Margin ($)': initial_margin,
                    'Maintenance Margin ($)': maintenance_margin,
                    'Notional Value ($)': notional,
                    'Liquidation Price': liquidation_price,
                    'Side (LONG/SHORT)': side,
                    'SL (Stop Loss)': sl_price if sl_price else 0,
                    'TP (Take Profit)': tp_price if tp_price else 0,
                    'Distance to TP (%)': distance_to_tp_blofin,
                    'Distance to SL (%)': distance_to_sl_blofin,
                    'TP Set?': '✅' if tp_numeric > 0 else '❌',
                    'SL Set?': '✅' if sl_numeric > 0 else '❌',
                    'TP Price': tp_price if tp_price else 0,
                    'SL Price': sl_price if sl_price else 0,
                    'Risk-to-Reward Ratio': risk_reward if risk_reward else 'N/A',
                    'Trend Status': trend_status_blofin,
                    'Risk Flag (New)': risk_flag_blofin,
                    'Entry Timestamp': timestamp_readable
                })

            except Exception as e:
                print(f"⚠️ Error processing Blofin position {pos.get('symbol', 'unknown')}: {e}")
                continue

    # Process Kraken positions
    if kraken_positions:
        print(f"🔍 Processing {len(kraken_positions)} Kraken positions...")

        # Create SL/TP mapping for Kraken orders
        kraken_sl_tp_map = {}
        for order in kraken_orders:
            symbol = order['symbol']
            if symbol not in kraken_sl_tp_map:
                kraken_sl_tp_map[symbol] = {'SL': None, 'TP': None}

            # CCXT order types for Kraken
            if order['type'] == 'stop-loss' or 'stop' in order['type'].lower():
                kraken_sl_tp_map[symbol]['SL'] = order.get('triggerPrice', order.get('stopPrice'))
            elif order['type'] == 'take-profit' or 'profit' in order['type'].lower():
                kraken_sl_tp_map[symbol]['TP'] = order.get('triggerPrice', order.get('stopPrice'))

        for pos in kraken_positions:
            try:
                symbol = pos['symbol']
                side = 'LONG' if pos['side'] == 'long' else 'SHORT'
                entry_price = pos['entryPrice'] or 0
                mark_price = pos['markPrice'] or 0

                # Get SL/TP for this position
                sl_price = kraken_sl_tp_map.get(symbol, {}).get('SL', 0)
                tp_price = kraken_sl_tp_map.get(symbol, {}).get('TP', 0)

                # Calculate Risk-to-Reward ratio
                risk_reward = calculate_risk_reward(entry_price, mark_price, sl_price, tp_price, side)

                # Extract comprehensive position data
                unrealized_pnl = pos.get('unrealizedPnl', 0) or 0
                notional = pos.get('notional', 0) or 1
                leverage = pos.get('leverage', 1) or 1
                amount = pos.get('contracts', 0) or 0
                liquidation_price = pos.get('liquidationPrice', 0) or 0
                margin_mode = pos.get('marginMode', 'Cross')
                initial_margin = pos.get('initialMargin', 0) or 0
                maintenance_margin = pos.get('maintenanceMargin', 0) or 0

                # Calculate margin size more accurately
                if initial_margin > 0:
                    margin_size = initial_margin
                else:
                    margin_size = abs(notional / leverage) if leverage > 0 else 0

                # Calculate PnL percentage based on margin
                pnl_percentage = round((unrealized_pnl / margin_size) * 100, 2) if margin_size > 0 else 0

                # Format timestamp
                timestamp = pos.get('timestamp', 0)
                if timestamp:
                    try:
                        central_tz = pytz.timezone('US/Central')
                        dt = datetime.fromtimestamp(timestamp / 1000, tz=pytz.UTC)
                        dt_central = dt.astimezone(central_tz)
                        timestamp_readable = dt_central.strftime('%Y-%m-%d %I:%M %p CST')
                    except:
                        timestamp_readable = str(timestamp)
                else:
                    timestamp_readable = ''

                # Check TP/SL status
                tp_numeric = float(tp_price) if tp_price else 0
                sl_numeric = float(sl_price) if sl_price else 0

                # Calculate Distance to TP and SL percentages for Kraken
                distance_to_tp_kraken = 0
                distance_to_sl_kraken = 0

                if tp_numeric > 0 and mark_price > 0:
                    if side == 'LONG':
                        distance_to_tp_kraken = round(((tp_numeric - mark_price) / mark_price) * 100, 2)
                    else:  # SHORT
                        distance_to_tp_kraken = round(((mark_price - tp_numeric) / mark_price) * 100, 2)

                if sl_numeric > 0 and mark_price > 0:
                    if side == 'LONG':
                        distance_to_sl_kraken = round(((sl_numeric - mark_price) / mark_price) * 100, 2)
                    else:  # SHORT
                        distance_to_sl_kraken = round(((mark_price - sl_numeric) / mark_price) * 100, 2)

                # Trend Status based on Unrealized PnL%
                if pnl_percentage > 30:
                    trend_status_kraken = "Uptrend"
                elif pnl_percentage < -20:
                    trend_status_kraken = "Downtrend"
                else:
                    trend_status_kraken = "Sideways"

                # Enhanced Risk Flag for Kraken
                if sl_numeric == 0 and margin_size > 100:
                    risk_flag_kraken = "High Risk"
                else:
                    risk_flag_kraken = "OK"

                data.append({
                    'Platform': 'Kraken',
                    'Symbol': symbol,
                    'Position Type': 'Rotation',  # Default value, manually update to "Runner" as needed
                    'Entry Price': entry_price,
                    'Mark Price': mark_price,
                    'Leverage': leverage,
                    'Position Mode': margin_mode,
                    'Amount': amount,
                    'PnL $': unrealized_pnl,
                    'PnL %': pnl_percentage,
                    'Unrealized PnL %': pnl_percentage,  # Use same calculation
                    'Unrealized PnL $': unrealized_pnl,
                    'Margin Size ($)': margin_size,
                    'Initial Margin ($)': initial_margin,
                    'Maintenance Margin ($)': maintenance_margin,
                    'Notional Value ($)': notional,
                    'Liquidation Price': liquidation_price,
                    'Side (LONG/SHORT)': side,
                    'SL (Stop Loss)': sl_price if sl_price else 0,
                    'TP (Take Profit)': tp_price if tp_price else 0,
                    'Distance to TP (%)': distance_to_tp_kraken,
                    'Distance to SL (%)': distance_to_sl_kraken,
                    'TP Set?': '✅' if tp_numeric > 0 else '❌',
                    'SL Set?': '✅' if sl_numeric > 0 else '❌',
                    'TP Price': tp_price if tp_price else 0,
                    'SL Price': sl_price if sl_price else 0,
                    'Risk-to-Reward Ratio': risk_reward if risk_reward else 'N/A',
                    'Trend Status': trend_status_kraken,
                    'Risk Flag (New)': risk_flag_kraken,
                    'Entry Timestamp': timestamp_readable
                })

            except Exception as e:
                print(f"⚠️ Error processing Kraken position {pos.get('symbol', 'unknown')}: {e}")
                continue

    df = pd.DataFrame(data)

    # Clean the CSV data before saving and normalize TP/SL fields
    df.replace("not set", 0, inplace=True)
    df.replace("", 0, inplace=True)  # Handle empty strings

    # Normalize TP and SL fields to ensure accurate scanning
    df['TP (Take Profit)'] = pd.to_numeric(df['TP (Take Profit)'], errors='coerce').fillna(0.0)
    df['SL (Stop Loss)'] = pd.to_numeric(df['SL (Stop Loss)'], errors='coerce').fillna(0.0)

    # Calculate total portfolio margin for percentage calculations
    total_margin = df['Margin Size ($)'].sum()

    # Add Margin % of Portfolio column
    df['Margin % of Portfolio'] = df['Margin Size ($)'].apply(
        lambda x: round((x / total_margin * 100), 2) if total_margin > 0 else 0
    )

    # Classify TP/SL Status
    def classify_tp_sl(row):
        tp = row['TP (Take Profit)']
        sl = row['SL (Stop Loss)']
        if tp > 0 and sl > 0:
            return '🟢 Both TP & SL set'
        elif tp > 0 and sl == 0:
            return '🟡 Only TP set'
        elif tp == 0 and sl > 0:
            return '🔵 Only SL set'
        else:
            return '🔴 Neither set'

    df['TP/SL Status'] = df.apply(classify_tp_sl, axis=1)

    # High-Risk Trade Detection
    def flag_high_risk_trades(row):
        margin_pct = row['Margin % of Portfolio']
        sl_set = row['SL (Stop Loss)'] > 0

        # Flag as high-risk if margin is >15% of portfolio AND no SL is set
        if margin_pct > 15 and not sl_set:
            return '🚨 HIGH RISK - No SL'
        elif margin_pct > 25:  # Very large position regardless of SL
            return '⚠️ LARGE POSITION'
        elif not sl_set:
            return '⚠️ No Stop Loss'
        else:
            return '✅ Managed Risk'

    df['Risk Flag'] = df.apply(flag_high_risk_trades, axis=1)

    # Create timestamped filename using Central Time (12-hour format without seconds)
    central_tz = pytz.timezone('US/Central')
    now_central = datetime.now(central_tz)
    timestamp = now_central.strftime("%Y%m%d_%I%M_%p")
    filename = f'positions_{timestamp}.csv'

    df.to_csv(filename, index=False)
    print(f"✅ Positions exported to {filename}")

    # Clean up old CSV files - keep only the latest one
    cleanup_old_csv_files(filename)

    # Summary by platform
    platform_summary = df.groupby('Platform').size().to_dict()
    total_positions = len(data)

    print(f"📊 Exported {total_positions} total positions:")
    for platform, count in platform_summary.items():
        print(f"   • {platform}: {count} positions")
    print(f"📈 Complete portfolio analysis with SL/TP and Risk-Reward data")

# Fetch current price for Kraken (ignore SOL.F)
def get_kraken_price(symbol):
    try:
        kraken = ccxt.kraken()
        ticker = kraken.fetch_ticker(symbol)
        return ticker['last']  # Return the last traded price
    except ccxt.NetworkError as e:
        print(f"⚠️ Kraken API Network Error for {symbol}: {e}")
        return None
    except ccxt.ExchangeError as e:
        print(f"⚠️ Kraken API Exchange Error for {symbol}: {e}")
        return None
    except Exception as e:
        print(f"⚠️ Kraken API Error fetching price for {symbol}: {e}")
        return None

# Get all kraken prices
def get_all_kraken_prices(kraken_positions):
    kraken_prices = {}
    if kraken_positions:
        enhanced_positions = [pos for pos in kraken_positions if pos.get('enhanced_data')]

        # Get current prices for all symbols (ignore SOL.F)
        symbols_to_price = list(set([pos['symbol'] for pos in enhanced_positions if pos['symbol'] != 'SOL.F']))
        for symbol in symbols_to_price:
            price_data = get_kraken_price(symbol)
            kraken_prices[symbol] = price_data

        print(f"📊 Collected current prices for {len(symbols_to_price)} Kraken assets")
        return kraken_prices
    else:
        print("📊 No Kraken positions to fetch prices for.")
        return {}

# Run it
export_positions()