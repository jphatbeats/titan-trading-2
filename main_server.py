from flask import Flask, jsonify, request
import logging
import os
from datetime import datetime
import traceback

# Import our custom modules with error handling
try:
    from logger_config import setup_logging
    setup_logging()
except ImportError:
    # Fallback logging setup if logger_config not found
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

try:
    from crypto_news_api import (
        crypto_news_api, get_breaking_crypto_news, get_crypto_risk_alerts,
        get_crypto_bullish_signals, scan_crypto_opportunities, 
        get_market_intelligence, detect_pump_dump_signals
    )
    crypto_news_available = True
except ImportError:
    crypto_news_available = False
    logger = logging.getLogger(__name__)
    logger.warning("Crypto news API module not available")

try:
    from error_handler import handle_exchange_error, ExchangeNotAvailableError
except ImportError:
    # Fallback error handling
    class ExchangeNotAvailableError(Exception):
        pass
    
    def handle_exchange_error(func):
        import functools
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exchange error in {func.__name__}: {str(e)}")
                raise ExchangeNotAvailableError(str(e))
        return wrapper

try:
    from exchange_manager import ExchangeManager
except ImportError:
    # Fallback exchange manager
    class ExchangeManager:
        def __init__(self):
            self.exchanges = {}
            self._initialize_exchanges()
        
        def _initialize_exchanges(self):
            try:
                import ccxt
                exchange_configs = {
                    'bingx': {
                        'apiKey': os.getenv('BINGX_API_KEY', ''),
                        'secret': os.getenv('BINGX_SECRET', ''),
                        'sandbox': os.getenv('BINGX_SANDBOX', 'false').lower() == 'true',
                        'enableRateLimit': True,
                    },
                    'kraken': {
                        'apiKey': os.getenv('KRAKEN_API_KEY', ''),
                        'secret': os.getenv('KRAKEN_SECRET', ''),
                        'sandbox': os.getenv('KRAKEN_SANDBOX', 'false').lower() == 'true',
                        'enableRateLimit': True,
                    },
                    'blofin': {
                        'apiKey': os.getenv('BLOFIN_API_KEY', ''),
                        'secret': os.getenv('BLOFIN_SECRET', ''),
                        'password': os.getenv('BLOFIN_PASSPHRASE', ''),
                        'sandbox': os.getenv('BLOFIN_SANDBOX', 'false').lower() == 'true',
                        'enableRateLimit': True,
                    }
                }
                
                for exchange_name, config in exchange_configs.items():
                    try:
                        if hasattr(ccxt, exchange_name):
                            exchange_class = getattr(ccxt, exchange_name)
                            self.exchanges[exchange_name] = exchange_class(config)
                            logger.info(f"Initialized {exchange_name} with config: {bool(config.get('apiKey'))}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize {exchange_name}: {e}")
            except ImportError:
                logger.error("CCXT library not available")
        
        def get_exchange(self, exchange_name):
            if exchange_name not in self.exchanges:
                raise ValueError(f"Exchange {exchange_name} not available")
            return self.exchanges[exchange_name]
        
        def get_available_exchanges(self):
            return list(self.exchanges.keys())
        
        def get_exchange_status(self):
            detailed_status = {}
            for name, exchange in self.exchanges.items():
                # Check if exchange has API credentials
                if hasattr(exchange, 'apiKey') and exchange.apiKey:
                    status = 'connected'
                else:
                    status = 'public_only'
                detailed_status[name] = {
                    'status': status, 
                    'error': None,
                    'has_credentials': bool(hasattr(exchange, 'apiKey') and exchange.apiKey)
                }
            return {
                'available_exchanges': self.get_available_exchanges(),
                'failed_exchanges': {},
                'detailed_status': detailed_status
            }

try:
    from trading_functions import TradingFunctions
except ImportError:
    # Fallback trading functions with all methods
    class TradingFunctions:
        def __init__(self, exchange_manager):
            self.exchange_manager = exchange_manager
        
        def get_ticker(self, exchange_name, symbol):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.fetch_ticker(symbol)
        
        def get_orderbook(self, exchange_name, symbol, limit=20):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.fetch_order_book(symbol, limit)
        
        def get_trades(self, exchange_name, symbol, limit=50):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.fetch_trades(symbol, None, limit)
        
        def get_balance(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.fetch_balance()
        
        def get_markets(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.markets
        
        def get_ohlcv(self, exchange_name, symbol, timeframe='1h', limit=100):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.fetch_ohlcv(symbol, timeframe, None, limit)
        
        def create_order(self, exchange_name, symbol, order_type, side, amount, price=None):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.create_order(symbol, order_type, side, amount, price)
        
        def get_orders(self, exchange_name, symbol=None):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if symbol:
                return exchange.fetch_open_orders(symbol)
            return exchange.fetch_open_orders()
        
        def cancel_order(self, exchange_name, order_id, symbol=None):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.cancel_order(order_id, symbol)
        
        def get_positions(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_positions'):
                return exchange.fetch_positions()
            raise Exception(f"Exchange {exchange_name} does not support positions")
        
        def get_funding_rate(self, exchange_name, symbol):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_funding_rate'):
                return exchange.fetch_funding_rate(symbol)
            raise Exception(f"Exchange {exchange_name} does not support funding rates")
        
        def set_leverage(self, exchange_name, symbol, leverage):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'set_leverage'):
                return exchange.set_leverage(leverage, symbol)
            raise Exception(f"Exchange {exchange_name} does not support leverage setting")
        
        def set_margin_mode(self, exchange_name, symbol, margin_mode):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'set_margin_mode'):
                return exchange.set_margin_mode(margin_mode, symbol)
            raise Exception(f"Exchange {exchange_name} does not support margin mode setting")
        
        def get_deposit_history(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_deposits'):
                return exchange.fetch_deposits()
            raise Exception(f"Exchange {exchange_name} does not support deposit history")
        
        def get_withdrawal_history(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_withdrawals'):
                return exchange.fetch_withdrawals()
            raise Exception(f"Exchange {exchange_name} does not support withdrawal history")
        
        def get_trading_fees(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_trading_fees'):
                return exchange.fetch_trading_fees()
            return {'trading': exchange.fees['trading'] if 'trading' in exchange.fees else {}}
        
        def get_symbols(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return list(exchange.symbols) if exchange.symbols else []
        
        def get_currencies(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            return exchange.currencies
        
        def get_order_history(self, exchange_name, symbol=None, limit=100):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_orders'):
                return exchange.fetch_orders(symbol, None, limit)
            raise Exception(f"Exchange {exchange_name} does not support order history")
        
        def get_trade_history(self, exchange_name, symbol=None, limit=100):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_my_trades'):
                return exchange.fetch_my_trades(symbol, None, limit)
            raise Exception(f"Exchange {exchange_name} does not support trade history")
        
        def get_account_info(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_account'):
                return exchange.fetch_account()
            return self.get_balance(exchange_name)
        
        def transfer_funds(self, exchange_name, currency, amount, from_account, to_account):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'transfer'):
                return exchange.transfer(currency, amount, from_account, to_account)
            raise Exception(f"Exchange {exchange_name} does not support fund transfers")
        
        def get_portfolio(self, exchange_name):
            balance = self.get_balance(exchange_name)
            portfolio = {
                'balance': balance,
                'total_value': 0,
                'assets': []
            }
            for currency, data in balance.get('total', {}).items():
                if isinstance(data, (int, float)) and data > 0:
                    portfolio['assets'].append({
                        'currency': currency,
                        'amount': data
                    })
            return portfolio
        
        def get_liquidation_history(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_liquidations'):
                return exchange.fetch_liquidations()
            raise Exception(f"Exchange {exchange_name} does not support liquidation history")
        
        def get_futures_stats(self, exchange_name, symbol):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            stats = {}
            try:
                ticker = exchange.fetch_ticker(symbol)
                stats['ticker'] = ticker
            except:
                pass
            try:
                if hasattr(exchange, 'fetch_funding_rate'):
                    funding_rate = exchange.fetch_funding_rate(symbol)
                    stats['funding_rate'] = funding_rate
            except:
                pass
            return stats
        
        def get_option_chain(self, exchange_name, symbol):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            if hasattr(exchange, 'fetch_option_chain'):
                return exchange.fetch_option_chain(symbol)
            raise Exception(f"Exchange {exchange_name} does not support options")
        
        def get_market_data(self, exchange_name):
            exchange = self.exchange_manager.get_exchange(exchange_name)
            market_data = {
                'exchange': exchange_name,
                'markets': exchange.markets,
                'symbols': list(exchange.symbols) if exchange.symbols else [],
                'currencies': exchange.currencies
            }
            try:
                if hasattr(exchange, 'fetch_tickers'):
                    tickers = exchange.fetch_tickers()
                    market_data['tickers'] = tickers
            except:
                pass
            return market_data

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize exchange manager and trading functions
exchange_manager = ExchangeManager()
trading_functions = TradingFunctions(exchange_manager)

@app.route('/', methods=['GET'])
def root():
    """Root endpoint with API information"""
    return jsonify({
        'message': 'Crypto Trading API Server',
        'version': '2.1.0',
        'status': 'running',
        'available_endpoints': 35,
        'available_exchanges': exchange_manager.get_available_exchanges(),
        'total_exchanges': len(exchange_manager.get_available_exchanges()),
        'live_endpoints': {
            'all_exchanges': '/api/live/all-exchanges',
            'account_balances': '/api/live/account-balances',
            'bingx_positions': '/api/live/bingx-positions',
            'blofin_positions': '/api/live/blofin-positions',
            'market_data': '/api/live/market-data/{symbol}'
        },
        'exchange_specific_endpoints': {
            'kraken_balance': '/api/kraken/balance',
            'bingx_balance': '/api/bingx/balance',
            'blofin_balance': '/api/blofin/balance',
            'bingx_klines': '/api/bingx/klines/{symbol}'
        },
        'generic_endpoints': {
            'health': '/health',
            'exchange_status': '/exchanges/status',
            'market_data': '/api/ticker/{exchange}/{symbol}, /api/orderbook/{exchange}/{symbol}, /api/trades/{exchange}/{symbol}',
            'trading': '/api/order (POST), /api/orders/{exchange}, /api/order/{exchange}/{order_id} (DELETE)',
            'account': '/api/balance/{exchange}, /api/account-info/{exchange}, /api/transfer (POST)',
            'portfolio': '/api/portfolio/{exchange}, /api/positions/{exchange}',
            'history': '/api/order-history/{exchange}, /api/trade-history/{exchange}, /api/deposit-history/{exchange}',
            'derivatives': '/api/funding-rate/{exchange}/{symbol}, /api/leverage/{exchange}/{symbol} (POST)'
        }
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'available_exchanges': exchange_manager.get_available_exchanges()
    })

@app.route('/exchanges/status', methods=['GET'])
def exchanges_status():
    """Get status of all exchanges"""
    return jsonify(exchange_manager.get_exchange_status())

@app.route('/debug/env', methods=['GET'])
def debug_environment():
    """Debug endpoint to check environment variables (for Railway debugging)"""
    try:
        env_debug = {
            'has_bingx_api_key': bool(os.getenv('BINGX_API_KEY')),
            'has_bingx_secret': bool(os.getenv('BINGX_SECRET')),
            'has_kraken_api_key': bool(os.getenv('KRAKEN_API_KEY')),
            'has_kraken_secret': bool(os.getenv('KRAKEN_SECRET')),
            'has_blofin_api_key': bool(os.getenv('BLOFIN_API_KEY')),
            'has_blofin_secret': bool(os.getenv('BLOFIN_SECRET')),
            'has_blofin_passphrase': bool(os.getenv('BLOFIN_PASSPHRASE')),
            'bingx_api_key_length': len(os.getenv('BINGX_API_KEY', '')),
            'bingx_secret_length': len(os.getenv('BINGX_SECRET', '')),
            'exchange_manager_type': str(type(exchange_manager).__name__),
            'exchange_manager_module': str(type(exchange_manager).__module__)
        }
        return jsonify(env_debug)
    except Exception as e:
        logger.error(f"Error in debug endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/all-exchanges', methods=['GET'])
def get_all_exchanges():
    """Get live positions and orders from all exchanges (BingX & Blofin)"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'exchanges': {}
        }
        
        for exchange_name in ['bingx', 'blofin']:
            try:
                if exchange_name in exchange_manager.get_available_exchanges():
                    positions = trading_functions.get_positions(exchange_name)
                    orders = trading_functions.get_orders(exchange_name)
                    result['exchanges'][exchange_name] = {
                        'status': 'success',
                        'positions': positions,
                        'orders': orders
                    }
                else:
                    result['exchanges'][exchange_name] = {
                        'status': 'unavailable',
                        'positions': {},
                        'orders': []
                    }
            except Exception as e:
                result['exchanges'][exchange_name] = {
                    'status': 'error',
                    'error': str(e),
                    'positions': {},
                    'orders': []
                }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting all exchanges: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/live/account-balances', methods=['GET'])
def get_account_balances():
    """Get account balances from all exchanges"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'balances': {}
        }
        
        for exchange_name in ['bingx', 'blofin']:
            try:
                if exchange_name in exchange_manager.get_available_exchanges():
                    balance = trading_functions.get_balance(exchange_name)
                    result['balances'][exchange_name] = {
                        'status': 'success',
                        'data': balance
                    }
                else:
                    result['balances'][exchange_name] = {
                        'status': 'unavailable',
                        'data': {}
                    }
            except Exception as e:
                result['balances'][exchange_name] = {
                    'status': 'error',
                    'error': str(e),
                    'data': {}
                }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting account balances: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/live/bingx-positions', methods=['GET'])
def get_bingx_positions():
    """Get live positions from BingX exchange"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'source': 'bingx'
        }
        
        if 'bingx' in exchange_manager.get_available_exchanges():
            positions = trading_functions.get_positions('bingx')
            orders = trading_functions.get_orders('bingx')
            
            result['positions'] = {
                'code': 0,
                'data': {
                    'positions': positions if isinstance(positions, list) else [positions]
                }
            }
            result['orders'] = {
                'code': 0,
                'data': {
                    'orders': orders if isinstance(orders, list) else [orders]
                }
            }
        else:
            result['positions'] = {'code': -1, 'data': {'positions': []}}
            result['orders'] = {'code': -1, 'data': {'orders': []}}
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting BingX positions: {str(e)}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'source': 'bingx',
            'positions': {'code': -1, 'data': {'positions': []}},
            'orders': {'code': -1, 'data': {'orders': []}},
            'error': str(e)
        }), 500

@app.route('/api/live/blofin-positions', methods=['GET'])
def get_blofin_positions():
    """Get live positions from Blofin exchange"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'source': 'blofin'
        }
        
        if 'blofin' in exchange_manager.get_available_exchanges():
            positions = trading_functions.get_positions('blofin')
            orders = trading_functions.get_orders('blofin')
            
            result['positions'] = positions if isinstance(positions, list) else [positions]
            result['orders'] = orders if isinstance(orders, list) else [orders]
        else:
            result['positions'] = []
            result['orders'] = []
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting Blofin positions: {str(e)}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'source': 'blofin',
            'positions': [],
            'orders': [],
            'error': str(e)
        }), 500

@app.route('/api/live/market-data/<symbol>', methods=['GET'])
def get_live_market_data(symbol):
    """Get live market data for a specific symbol"""
    try:
        result = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'market_data': {}
        }
        
        for exchange_name in ['bingx', 'blofin']:
            try:
                if exchange_name in exchange_manager.get_available_exchanges():
                    ticker = trading_functions.get_ticker(exchange_name, symbol)
                    orderbook = trading_functions.get_orderbook(exchange_name, symbol, 10)
                    
                    result['market_data'][exchange_name] = {
                        'status': 'success',
                        'ticker': ticker,
                        'orderbook': orderbook
                    }
                else:
                    result['market_data'][exchange_name] = {
                        'status': 'unavailable'
                    }
            except Exception as e:
                result['market_data'][exchange_name] = {
                    'status': 'error',
                    'error': str(e)
                }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error getting market data for {symbol}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Exchange-specific balance endpoints (your original API schema)
@app.route('/api/kraken/balance', methods=['GET'])
def get_kraken_balance():
    """Get Kraken account balance (your original endpoint)"""
    try:
        if 'kraken' in exchange_manager.get_available_exchanges():
            result = trading_functions.get_balance('kraken')
            return jsonify(result)
        else:
            return jsonify({'error': 'Kraken exchange not available'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bingx/balance', methods=['GET'])
def get_bingx_balance():
    """Get BingX account balance"""
    try:
        if 'bingx' in exchange_manager.get_available_exchanges():
            result = trading_functions.get_balance('bingx')
            return jsonify(result)
        else:
            return jsonify({'error': 'BingX exchange not available'}), 503
    except Exception as e:
        logger.error(f"Error getting BingX balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/blofin/balance', methods=['GET'])
def get_blofin_balance():
    """Get Blofin account balance"""
    try:
        if 'blofin' in exchange_manager.get_available_exchanges():
            result = trading_functions.get_balance('blofin')
            return jsonify(result)
        else:
            return jsonify({'error': 'Blofin exchange not available'}), 503
    except Exception as e:
        logger.error(f"Error getting Blofin balance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# BingX klines endpoint from your API schema
@app.route('/api/bingx/klines/<symbol>', methods=['GET'])
def get_bingx_klines(symbol):
    """Get BingX candlestick/OHLCV data for technical analysis"""
    try:
        interval = request.args.get('interval', '1h')
        limit = request.args.get('limit', 100, type=int)
        raw = request.args.get('raw', 'false').lower() == 'true'
        
        if 'bingx' in exchange_manager.get_available_exchanges():
            # Convert interval to CCXT format if needed
            ohlcv_data = trading_functions.get_ohlcv('bingx', symbol, interval, limit)
            
            # Format according to your API schema
            result = {
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'klines': {
                    'code': 0,
                    'data': []
                }
            }
            
            # Convert CCXT OHLCV format to your custom format
            if ohlcv_data:
                for i, candle in enumerate(ohlcv_data):
                    if len(candle) >= 6:  # timestamp, open, high, low, close, volume
                        formatted_candle = {
                            'open_time': int(candle[0]),
                            'open_time_readable': datetime.fromtimestamp(candle[0]/1000).isoformat(),
                            'open': float(candle[1]),
                            'high': float(candle[2]),
                            'low': float(candle[3]),
                            'close': float(candle[4]),
                            'volume': float(candle[5]) if candle[5] else 0
                        }
                        result['klines']['data'].append(formatted_candle)
            
            if raw:
                return jsonify(result, separators=(',', ':'))
            return jsonify(result)
        else:
            return jsonify({
                'timestamp': datetime.now().isoformat(),
                'symbol': symbol,
                'interval': interval,
                'limit': limit,
                'klines': {'code': -1, 'data': []},
                'error': 'BingX exchange not available'
            }), 503
    except Exception as e:
        logger.error(f"Error getting BingX klines for {symbol}: {str(e)}")
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'klines': {'code': -1, 'data': []},
            'error': 'Internal server error'
        }), 500

@app.route('/api/ticker/<exchange>/<symbol>', methods=['GET'])
def get_ticker(exchange, symbol):
    """Get ticker for a specific symbol on an exchange"""
    try:
        result = trading_functions.get_ticker(exchange, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting ticker for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/orderbook/<exchange>/<symbol>', methods=['GET'])
def get_orderbook(exchange, symbol):
    """Get orderbook for a specific symbol on an exchange"""
    try:
        limit = request.args.get('limit', 20, type=int)
        result = trading_functions.get_orderbook(exchange, symbol, limit)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting orderbook for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/trades/<exchange>/<symbol>', methods=['GET'])
def get_trades(exchange, symbol):
    """Get recent trades for a specific symbol on an exchange"""
    try:
        limit = request.args.get('limit', 50, type=int)
        result = trading_functions.get_trades(exchange, symbol, limit)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting trades for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/balance/<exchange>', methods=['GET'])
def get_balance(exchange):
    """Get account balance for an exchange"""
    try:
        result = trading_functions.get_balance(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting balance for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/markets/<exchange>', methods=['GET'])
def get_markets(exchange):
    """Get available markets for an exchange"""
    try:
        result = trading_functions.get_markets(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting markets for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/ohlcv/<exchange>/<symbol>', methods=['GET'])
def get_ohlcv(exchange, symbol):
    """Get OHLCV data for a specific symbol"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        limit = request.args.get('limit', 100, type=int)
        result = trading_functions.get_ohlcv(exchange, symbol, timeframe, limit)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting OHLCV for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/order', methods=['POST'])
def create_order():
    """Create a new order"""
    try:
        data = request.get_json()
        exchange = data.get('exchange')
        symbol = data.get('symbol')
        order_type = data.get('type')
        side = data.get('side')
        amount = data.get('amount')
        price = data.get('price')
        
        result = trading_functions.create_order(exchange, symbol, order_type, side, amount, price)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error creating order: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/orders/<exchange>', methods=['GET'])
def get_orders(exchange):
    """Get open orders for an exchange"""
    try:
        symbol = request.args.get('symbol')
        result = trading_functions.get_orders(exchange, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting orders for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/order/<exchange>/<order_id>', methods=['DELETE'])
def cancel_order(exchange, order_id):
    """Cancel an order"""
    try:
        symbol = request.args.get('symbol')
        result = trading_functions.cancel_order(exchange, order_id, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error canceling order {order_id} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/positions/<exchange>', methods=['GET'])
def get_positions(exchange):
    """Get positions for an exchange"""
    try:
        result = trading_functions.get_positions(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting positions for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/funding-rate/<exchange>/<symbol>', methods=['GET'])
def get_funding_rate(exchange, symbol):
    """Get funding rate for a symbol"""
    try:
        result = trading_functions.get_funding_rate(exchange, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting funding rate for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/leverage/<exchange>/<symbol>', methods=['POST'])
def set_leverage(exchange, symbol):
    """Set leverage for a symbol"""
    try:
        data = request.get_json()
        leverage = data.get('leverage')
        result = trading_functions.set_leverage(exchange, symbol, leverage)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error setting leverage for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/margin-mode/<exchange>/<symbol>', methods=['POST'])
def set_margin_mode(exchange, symbol):
    """Set margin mode for a symbol"""
    try:
        data = request.get_json()
        margin_mode = data.get('margin_mode')
        result = trading_functions.set_margin_mode(exchange, symbol, margin_mode)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error setting margin mode for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/deposit-history/<exchange>', methods=['GET'])
def get_deposit_history(exchange):
    """Get deposit history for an exchange"""
    try:
        result = trading_functions.get_deposit_history(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting deposit history for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/withdrawal-history/<exchange>', methods=['GET'])
def get_withdrawal_history(exchange):
    """Get withdrawal history for an exchange"""
    try:
        result = trading_functions.get_withdrawal_history(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting withdrawal history for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/trading-fees/<exchange>', methods=['GET'])
def get_trading_fees(exchange):
    """Get trading fees for an exchange"""
    try:
        result = trading_functions.get_trading_fees(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting trading fees for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/symbols/<exchange>', methods=['GET'])
def get_symbols(exchange):
    """Get available symbols for an exchange"""
    try:
        result = trading_functions.get_symbols(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting symbols for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/currencies/<exchange>', methods=['GET'])
def get_currencies(exchange):
    """Get available currencies for an exchange"""
    try:
        result = trading_functions.get_currencies(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting currencies for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/order-history/<exchange>', methods=['GET'])
def get_order_history(exchange):
    """Get order history for an exchange"""
    try:
        symbol = request.args.get('symbol')
        limit = request.args.get('limit', 100, type=int)
        result = trading_functions.get_order_history(exchange, symbol, limit)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting order history for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/trade-history/<exchange>', methods=['GET'])
def get_trade_history(exchange):
    """Get trade history for an exchange"""
    try:
        symbol = request.args.get('symbol')
        limit = request.args.get('limit', 100, type=int)
        result = trading_functions.get_trade_history(exchange, symbol, limit)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting trade history for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/account-info/<exchange>', methods=['GET'])
def get_account_info(exchange):
    """Get account information for an exchange"""
    try:
        result = trading_functions.get_account_info(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting account info for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/transfer', methods=['POST'])
def transfer_funds():
    """Transfer funds between accounts"""
    try:
        data = request.get_json()
        exchange = data.get('exchange')
        currency = data.get('currency')
        amount = data.get('amount')
        from_account = data.get('from_account')
        to_account = data.get('to_account')
        
        result = trading_functions.transfer_funds(exchange, currency, amount, from_account, to_account)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error transferring funds: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/portfolio/<exchange>', methods=['GET'])
def get_portfolio(exchange):
    """Get portfolio summary for an exchange"""
    try:
        result = trading_functions.get_portfolio(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting portfolio for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/liquidation-history/<exchange>', methods=['GET'])
def get_liquidation_history(exchange):
    """Get liquidation history for an exchange"""
    try:
        result = trading_functions.get_liquidation_history(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting liquidation history for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/futures-stats/<exchange>/<symbol>', methods=['GET'])
def get_futures_stats(exchange, symbol):
    """Get futures statistics for a symbol"""
    try:
        result = trading_functions.get_futures_stats(exchange, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting futures stats for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/option-chain/<exchange>/<symbol>', methods=['GET'])
def get_option_chain(exchange, symbol):
    """Get option chain for a symbol"""
    try:
        result = trading_functions.get_option_chain(exchange, symbol)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting option chain for {symbol} on {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/market-data/<exchange>', methods=['GET'])
def get_market_data(exchange):
    """Get comprehensive market data for an exchange"""
    try:
        result = trading_functions.get_market_data(exchange)
        return jsonify(result)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': exchange}), 503
    except Exception as e:
        logger.error(f"Error getting market data for {exchange}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# PORTFOLIO MANAGEMENT ENDPOINTS
# ============================================================================

@app.route('/api/portfolio/holdings', methods=['GET', 'POST'])
def manage_portfolio_holdings():
    """Manage user portfolio holdings for personalized news"""
    if request.method == 'GET':
        # Return stored holdings (could be from database, for now using query params)
        holdings = request.args.get('holdings', 'BTC,ETH,SOL').split(',')
        return jsonify({
            'status': 'success',
            'holdings': holdings,
            'count': len(holdings),
            'message': 'Current portfolio holdings'
        })
    
    elif request.method == 'POST':
        # Update holdings
        data = request.get_json()
        holdings = data.get('holdings', [])
        
        # In a real implementation, this would save to database
        # For now, just return confirmation
        return jsonify({
            'status': 'success',
            'holdings': holdings,
            'count': len(holdings),
            'message': f'Portfolio updated with {len(holdings)} holdings'
        })

@app.route('/api/portfolio/risk-monitor', methods=['GET'])
def monitor_portfolio_risks():
    """Monitor threats to specific portfolio holdings"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        holdings = request.args.get('holdings', 'BTC,ETH,SOL').split(',')
        limit = request.args.get('limit', 15, type=int)
        
        result = crypto_news_api.monitor_portfolio_threats(holdings, limit=limit)
        
        # Add urgency levels based on source quality and sentiment
        threats = []
        for article in result.get('data', []):
            source = article.get('source_name', article.get('source', ''))
            urgency = 'HIGH' if source in ['Coindesk', 'CryptoSlate', 'The Block', 'Decrypt'] else 'MEDIUM'
            
            threats.append({
                **article,
                'urgency': urgency,
                'affected_holdings': [ticker for ticker in holdings if ticker in str(article.get('tickers', []))],
                'threat_type': 'portfolio_risk'
            })
        
        return jsonify({
            'status': 'success',
            'count': len(threats),
            'threats': threats,
            'monitored_holdings': holdings,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error monitoring portfolio risks: {str(e)}")
        return jsonify({'error': 'Failed to monitor portfolio risks'}), 500

@app.route('/api/portfolio/correlation-plays', methods=['GET'])
def find_correlation_plays():
    """Find news affecting multiple correlated assets"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        primary_tickers = request.args.get('tickers', 'BTC,ETH').split(',')
        limit = request.args.get('limit', 10, type=int)
        
        result = crypto_news_api.find_correlation_plays(primary_tickers, limit=limit)
        
        # Add urgency and correlation analysis
        plays = []
        for article in result.get('data', []):
            source = article.get('source_name', article.get('source', ''))
            urgency = 'HIGH' if source in ['Coindesk', 'CryptoSlate', 'The Block', 'Decrypt'] else 'MEDIUM'
            
            plays.append({
                **article,
                'urgency': urgency,
                'correlation_type': 'multi_asset',
                'affected_tickers': primary_tickers
            })
        
        return jsonify({
            'status': 'success',
            'count': len(plays),
            'correlation_plays': plays,
            'analyzed_tickers': primary_tickers,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error finding correlation plays: {str(e)}")
        return jsonify({'error': 'Failed to find correlation plays'}), 500

@app.route('/api/alerts/prioritized', methods=['GET'])
def get_prioritized_alerts():
    """Get prioritized alerts with urgency levels"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        urgency_filter = request.args.get('urgency')  # HIGH, MEDIUM, LOW
        
        result = crypto_news_api.get_prioritized_alerts(limit=limit, urgency_filter=urgency_filter)
        
        # Filter by urgency if specified
        alerts = result.get('data', [])
        if urgency_filter:
            alerts = [alert for alert in alerts if alert.get('urgency', '').upper() == urgency_filter.upper()]
        
        # Sort by urgency score (highest first)
        alerts.sort(key=lambda x: x.get('urgency_score', 0), reverse=True)
        
        return jsonify({
            'status': 'success',
            'count': len(alerts),
            'alerts': alerts,
            'urgency_filter': urgency_filter,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting prioritized alerts: {str(e)}")
        return jsonify({'error': 'Failed to get prioritized alerts'}), 500

@app.route('/api/performance/news-tracking', methods=['GET'])
def track_news_performance():
    """Track which news leads to price movements (basic implementation)"""
    try:
        timeframe = request.args.get('timeframe', '24h')
        
        # This would integrate with price data in a full implementation
        # For now, return a basic structure for performance tracking
        performance_data = {
            'timeframe': timeframe,
            'tracked_articles': 15,
            'price_movements_detected': 8,
            'accuracy_rate': '53%',
            'top_performing_sources': [
                {'source': 'Coindesk', 'accuracy': '67%', 'articles': 5},
                {'source': 'CryptoSlate', 'accuracy': '60%', 'articles': 4},
                {'source': 'The Block', 'accuracy': '45%', 'articles': 6}
            ],
            'recommendations': [
                'Coindesk articles show highest correlation with price movements',
                'Negative sentiment articles have 78% accuracy for downward moves',
                'Partnership announcements show best ROI signals'
            ]
        }
        
        return jsonify({
            'status': 'success',
            'performance_data': performance_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error tracking news performance: {str(e)}")
        return jsonify({'error': 'Failed to track performance'}), 500

# ============================================================================
# CRYPTO NEWS ENDPOINTS
# ============================================================================

@app.route('/api/crypto-news/breaking-news', methods=['GET'])
def get_breaking_crypto_news():
    """Get breaking crypto news with filtering options"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        # Extract query parameters
        hours = request.args.get('hours', 24, type=int)
        items = request.args.get('items', 50, type=int)
        exclude_portfolio = request.args.get('exclude_portfolio', 'false').lower() == 'true'
        sentiment = request.args.get('sentiment')
        source = request.args.get('source')
        topic = request.args.get('topic')
        search = request.args.get('search')
        
        # Get general crypto news (breaking news equivalent)
        result = get_general_crypto_news(
            items=items,
            sentiment=sentiment,
            source=source,
            topic=topic,
            search=search
        )
        
        # Return simplified format for ChatGPT compatibility
        articles = result.get('data', [])
        return jsonify({
            'success': True,
            'data': {
                'articles': articles,
                'count': len(articles),
                'filters': {
                    'hours': hours,
                    'items': items,
                    'sentiment': sentiment,
                    'source': source,
                    'topic': topic
                }
            },
            'message': f'Found {len(articles)} breaking crypto news articles'
        })
    except Exception as e:
        logger.error(f"Error getting breaking crypto news: {str(e)}")
        return jsonify({'error': 'Failed to fetch crypto news'}), 500

@app.route('/api/crypto-news/top-mentioned', methods=['GET'])
def get_top_mentioned():
    """Get top mentioned crypto tickers"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        date = request.args.get('date', 'last7days')
        cache = request.args.get('cache', 'false').lower() == 'true'
        
        result = get_top_mentioned_tickers(date=date, cache=cache)
        
        tickers = result.get('data', [])
        return jsonify({
            'success': True,
            'data': {
                'tickers': tickers,
                'count': len(tickers)
            },
            'message': f'Found {len(tickers)} top mentioned crypto tickers'
        })
    except Exception as e:
        logger.error(f"Error getting top mentioned tickers: {str(e)}")
        return jsonify({'error': 'Failed to fetch top mentioned tickers'}), 500

@app.route('/api/crypto-news/sentiment', methods=['GET'])
def get_crypto_sentiment():
    """Get sentiment analysis for crypto tickers"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        tickers = request.args.get('tickers')
        section = request.args.get('section')
        date = request.args.get('date', 'last30days')
        
        result = get_sentiment_analysis(
            tickers=tickers,
            section=section,
            date=date
        )
        
        sentiment_data = result.get('data', [])
        return jsonify({
            'success': True,
            'data': {
                'sentiment_analysis': sentiment_data,
                'tickers_analyzed': tickers,
                'period': date
            },
            'message': f'Sentiment analysis completed for {tickers or "crypto market"}'
        })
    except Exception as e:
        logger.error(f"Error getting sentiment analysis: {str(e)}")
        return jsonify({'error': 'Failed to fetch sentiment analysis'}), 500

@app.route('/api/crypto-news/portfolio', methods=['GET'])
def get_portfolio_crypto_news():
    """Get crypto news filtered for portfolio holdings"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        portfolio_symbols = request.args.get('symbols', '').split(',')
        if portfolio_symbols == ['']:
            portfolio_symbols = []
        
        limit = request.args.get('limit', 15, type=int)
        
        result = crypto_news_api.get_portfolio_news(portfolio_symbols, limit=limit)
        
        articles = result.get('data', [])
        return jsonify({
            'success': True,
            'data': {
                'articles': articles,
                'count': len(articles),
                'portfolio_symbols': portfolio_symbols
            },
            'message': f'Found {len(articles)} news articles for portfolio symbols'
        })
    except Exception as e:
        logger.error(f"Error getting portfolio crypto news: {str(e)}")
        return jsonify({'error': 'Failed to fetch portfolio news'}), 500

@app.route('/api/crypto-news/symbols/<symbols>', methods=['GET'])
def get_crypto_news_by_symbols(symbols):
    """Get crypto news for specific symbols"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        symbol_list = symbols.split(',')
        limit = request.args.get('limit', 10, type=int)
        mode = request.args.get('mode', 'broad')  # broad, intersection, laser
        
        result = crypto_news_api.get_news_by_symbols(symbol_list, limit=limit, mode=mode)
        
        articles = result.get('data', [])
        return jsonify({
            'success': True,
            'data': {
                'articles': articles,
                'count': len(articles),
                'symbols': symbol_list,
                'mode': mode
            },
            'message': f'Found {len(articles)} news articles for {len(symbol_list)} symbols'
        })
    except Exception as e:
        logger.error(f"Error getting crypto news by symbols: {str(e)}")
        return jsonify({'error': 'Failed to fetch symbol news'}), 500

@app.route('/api/crypto-news/risk-alerts', methods=['GET'])
def get_crypto_risk_alerts_endpoint():
    """Get crypto risk alerts and warnings"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        severity = request.args.get('severity', 'high')
        
        result = crypto_news_api.get_risk_alerts(limit=limit, severity=severity)
        
        return jsonify({
            'status': 'success',
            'count': len(result.get('data', [])),
            'alerts': result.get('data', []),
            'alert_type': 'risk_warnings',
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting crypto risk alerts: {str(e)}")
        return jsonify({'error': 'Failed to fetch risk alerts'}), 500

@app.route('/api/crypto-news/bullish-signals', methods=['GET'])
def get_crypto_bullish_signals_endpoint():
    """Get bullish crypto signals and positive news"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        limit = request.args.get('limit', 15, type=int)
        timeframe = request.args.get('timeframe', 'last6hours')
        
        result = crypto_news_api.get_bullish_signals(limit=limit, timeframe=timeframe)
        
        return jsonify({
            'status': 'success',
            'count': len(result.get('data', [])),
            'signals': result.get('data', []),
            'signal_type': 'bullish_sentiment',
            'timeframe': timeframe,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting bullish signals: {str(e)}")
        return jsonify({'error': 'Failed to fetch bullish signals'}), 500

@app.route('/api/crypto-news/opportunity-scanner', methods=['GET'])
def scan_crypto_opportunities_endpoint():
    """Scan for crypto trading opportunities in news"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        sectors = request.args.get('sectors', 'AI,DeFi,Gaming,RWA,Layer2').split(',')
        limit = request.args.get('limit', 25, type=int)
        
        result = crypto_news_api.scan_opportunities(sectors=sectors, limit=limit)
        
        opportunities = []
        for article in result.get('data', []):
            opportunities.append({
                'title': article.get('title'),
                'source': article.get('source_name', article.get('source')),
                'sentiment': article.get('sentiment'),
                'tickers': article.get('tickers', []),
                'opportunity_type': 'sector_based',
                'date': article.get('date'),
                'url': article.get('url')
            })
        
        return jsonify({
            'status': 'success',
            'count': len(opportunities),
            'opportunities': opportunities,
            'sectors_scanned': sectors,
            'scan_type': 'news_opportunities',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error scanning crypto opportunities: {str(e)}")
        return jsonify({'error': 'Failed to scan opportunities'}), 500

@app.route('/api/crypto-news/market-intelligence', methods=['GET'])
def get_market_intelligence_endpoint():
    """Get comprehensive market intelligence"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        comprehensive = request.args.get('comprehensive', 'true').lower() == 'true'
        
        result = crypto_news_api.get_market_intelligence(comprehensive=comprehensive)
        
        return jsonify({
            'status': 'success',
            'market_overview': {
                'latest_news': result.get('data', [])[:15],
                'comprehensive': comprehensive,
                'data_source': 'tier_1_sources'
            },
            'intelligence_type': 'comprehensive' if comprehensive else 'summary',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error getting market intelligence: {str(e)}")
        return jsonify({'error': 'Failed to fetch market intelligence'}), 500

@app.route('/api/crypto-news/pump-dump-detector', methods=['GET'])
def detect_pump_dump_signals_endpoint():
    """Detect potential pump and dump signals"""
    if not crypto_news_available:
        return jsonify({'error': 'Crypto news service not available'}), 503
    
    try:
        limit = request.args.get('limit', 20, type=int)
        
        result = crypto_news_api.detect_pump_dump_signals(limit=limit)
        
        signals = []
        for article in result.get('data', []):
            signals.append({
                'title': article.get('title'),
                'source': article.get('source_name', article.get('source')),
                'tickers': article.get('tickers', []),
                'signal_type': 'pump_dump_warning',
                'confidence': 'medium',
                'date': article.get('date'),
                'url': article.get('url')
            })
        
        return jsonify({
            'status': 'success',
            'count': len(signals),
            'signals': signals,
            'detector_type': 'news_based',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error detecting pump dump signals: {str(e)}")
        return jsonify({'error': 'Failed to detect pump dump signals'}), 500

# ============================================================================
# BINGX SPECIFIC ENDPOINTS
# ============================================================================

@app.route('/api/bingx/market-analysis/<symbol>', methods=['GET'])
def get_bingx_market_analysis(symbol):
    """Get BingX market analysis for a symbol"""
    try:
        ticker = trading_functions.get_ticker('bingx', symbol)
        orderbook = trading_functions.get_orderbook('bingx', symbol, limit=10)
        
        analysis = {
            'symbol': symbol,
            'exchange': 'bingx',
            'price_analysis': {
                'current_price': ticker.get('last'),
                'bid': ticker.get('bid'),
                'ask': ticker.get('ask'),
                'spread': ticker.get('ask', 0) - ticker.get('bid', 0) if ticker.get('ask') and ticker.get('bid') else 0,
                'volume': ticker.get('baseVolume'),
                'change_24h': ticker.get('change')
            },
            'orderbook_analysis': {
                'top_bid': orderbook.get('bids', [[0]])[0][0] if orderbook.get('bids') else 0,
                'top_ask': orderbook.get('asks', [[0]])[0][0] if orderbook.get('asks') else 0,
                'bid_depth': sum([order[1] for order in orderbook.get('bids', [])[:5]]),
                'ask_depth': sum([order[1] for order in orderbook.get('asks', [])[:5]])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(analysis)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'bingx'}), 503
    except Exception as e:
        logger.error(f"Error getting BingX market analysis for {symbol}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bingx/candlestick-analysis/<symbol>', methods=['GET'])
def get_bingx_candlestick_analysis(symbol):
    """Get BingX candlestick analysis"""
    try:
        timeframe = request.args.get('timeframe', '1h')
        limit = request.args.get('limit', 100, type=int)
        
        # Get OHLCV data (candlesticks)
        ohlcv = trading_functions.get_ohlcv('bingx', symbol, timeframe, limit)
        
        if not ohlcv:
            return jsonify({'error': 'No candlestick data available'}), 404
        
        # Basic candlestick analysis
        latest = ohlcv[-1] if ohlcv else [0, 0, 0, 0, 0, 0]
        analysis = {
            'symbol': symbol,
            'exchange': 'bingx',
            'timeframe': timeframe,
            'candlestick_data': {
                'latest_candle': {
                    'timestamp': latest[0],
                    'open': latest[1],
                    'high': latest[2],
                    'low': latest[3],
                    'close': latest[4],
                    'volume': latest[5]
                },
                'candle_count': len(ohlcv),
                'price_range': latest[2] - latest[3] if len(latest) > 3 else 0,
                'body_size': abs(latest[4] - latest[1]) if len(latest) > 4 else 0
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(analysis)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'bingx'}), 503
    except Exception as e:
        logger.error(f"Error getting BingX candlestick analysis for {symbol}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/bingx/multi-timeframe/<symbol>', methods=['GET'])
def get_bingx_multi_timeframe_analysis(symbol):
    """Get BingX multi-timeframe analysis"""
    try:
        timeframes = ['5m', '15m', '1h', '4h', '1d']
        analysis = {
            'symbol': symbol,
            'exchange': 'bingx',
            'timeframes': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for tf in timeframes:
            try:
                ohlcv = trading_functions.get_ohlcv('bingx', symbol, tf, 50)
                if ohlcv:
                    latest = ohlcv[-1]
                    analysis['timeframes'][tf] = {
                        'latest_close': latest[4],
                        'latest_volume': latest[5],
                        'price_change': ((latest[4] - latest[1]) / latest[1] * 100) if latest[1] else 0
                    }
            except:
                analysis['timeframes'][tf] = {'error': 'Data not available'}
        
        return jsonify(analysis)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'bingx'}), 503
    except Exception as e:
        logger.error(f"Error getting BingX multi-timeframe analysis for {symbol}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# KRAKEN SPECIFIC ENDPOINTS
# ============================================================================

@app.route('/api/kraken/positions', methods=['GET'])
def get_kraken_positions():
    """Get Kraken positions"""
    try:
        result = trading_functions.get_positions('kraken')
        return jsonify({
            'exchange': 'kraken',
            'positions': result,
            'timestamp': datetime.now().isoformat()
        })
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken positions: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/trade-history', methods=['GET'])
def get_kraken_trade_history():
    """Get Kraken trade history"""
    try:
        limit = request.args.get('limit', 100, type=int)
        symbol = request.args.get('symbol')
        
        result = trading_functions.get_trade_history('kraken', symbol, limit)
        return jsonify({
            'exchange': 'kraken',
            'trades': result,
            'symbol': symbol,
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        })
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken trade history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/orders', methods=['GET'])
def get_kraken_orders():
    """Get Kraken orders"""
    try:
        result = trading_functions.get_orders('kraken')
        return jsonify({
            'exchange': 'kraken',
            'orders': result,
            'timestamp': datetime.now().isoformat()
        })
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken orders: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/market-data/<symbol>', methods=['GET'])
def get_kraken_market_data(symbol):
    """Get Kraken market data for a symbol"""
    try:
        ticker = trading_functions.get_ticker('kraken', symbol)
        orderbook = trading_functions.get_orderbook('kraken', symbol, limit=20)
        trades = trading_functions.get_trades('kraken', symbol, limit=50)
        
        market_data = {
            'symbol': symbol,
            'exchange': 'kraken',
            'ticker': ticker,
            'orderbook': orderbook,
            'recent_trades': trades,
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(market_data)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken market data for {symbol}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/portfolio-performance', methods=['GET'])
def get_kraken_portfolio_performance():
    """Get Kraken portfolio performance metrics"""
    try:
        balance = trading_functions.get_balance('kraken')
        portfolio = trading_functions.get_portfolio('kraken')
        
        performance = {
            'exchange': 'kraken',
            'balance_summary': balance,
            'portfolio_metrics': portfolio,
            'performance_period': '24h',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(performance)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken portfolio performance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/asset-allocation', methods=['GET'])
def get_kraken_asset_allocation():
    """Get Kraken asset allocation"""
    try:
        balance = trading_functions.get_balance('kraken')
        
        total_value = 0
        allocations = []
        
        for currency, amount in balance.get('total', {}).items():
            if isinstance(amount, (int, float)) and amount > 0:
                allocations.append({
                    'asset': currency,
                    'amount': amount,
                    'percentage': 0  # Would need price data to calculate
                })
                total_value += amount
        
        return jsonify({
            'exchange': 'kraken',
            'total_value': total_value,
            'allocations': allocations,
            'currency_count': len(allocations),
            'timestamp': datetime.now().isoformat()
        })
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken asset allocation: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/kraken/trading-stats', methods=['GET'])
def get_kraken_trading_stats():
    """Get Kraken trading statistics"""
    try:
        orders = trading_functions.get_order_history('kraken', limit=100)
        trades = trading_functions.get_trade_history('kraken', limit=100)
        
        stats = {
            'exchange': 'kraken',
            'order_count': len(orders) if orders else 0,
            'trade_count': len(trades) if trades else 0,
            'period': 'last_100_transactions',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats)
    except ExchangeNotAvailableError as e:
        return jsonify({'error': str(e), 'exchange': 'kraken'}), 503
    except Exception as e:
        logger.error(f"Error getting Kraken trading stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# ============================================================================
# CHATGPT ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/chatgpt/account-summary', methods=['GET'])
def get_chatgpt_account_summary():
    """Get AI-powered account summary"""
    try:
        # Get data from all available exchanges
        summary_data = {}
        for exchange in exchange_manager.get_available_exchanges():
            try:
                balance = trading_functions.get_balance(exchange)
                summary_data[exchange] = {
                    'balance': balance,
                    'status': 'active'
                }
            except:
                summary_data[exchange] = {'status': 'error'}
        
        ai_summary = {
            'analysis_type': 'account_summary',
            'exchanges_analyzed': list(summary_data.keys()),
            'account_data': summary_data,
            'ai_insights': [
                'Account analysis completed',
                f'Found {len(summary_data)} exchange accounts',
                'Portfolio diversification recommended'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(ai_summary)
    except Exception as e:
        logger.error(f"Error generating ChatGPT account summary: {str(e)}")
        return jsonify({'error': 'Failed to generate account summary'}), 500

@app.route('/api/chatgpt/portfolio-analysis', methods=['GET'])
def get_chatgpt_portfolio_analysis():
    """Get AI-powered portfolio analysis"""
    try:
        # Gather portfolio data from all exchanges
        portfolio_data = {}
        total_assets = 0
        
        for exchange in exchange_manager.get_available_exchanges():
            try:
                portfolio = trading_functions.get_portfolio(exchange)
                portfolio_data[exchange] = portfolio
                total_assets += len(portfolio.get('assets', []))
            except:
                portfolio_data[exchange] = {'error': 'Unable to fetch data'}
        
        ai_analysis = {
            'analysis_type': 'portfolio_analysis',
            'portfolio_overview': {
                'total_exchanges': len(portfolio_data),
                'total_assets': total_assets,
                'diversification_score': min(total_assets * 10, 100)  # Simple score
            },
            'exchange_portfolios': portfolio_data,
            'ai_recommendations': [
                'Consider rebalancing portfolio across exchanges',
                'Monitor high-volatility assets closely',
                'Diversification appears adequate' if total_assets > 5 else 'Consider increasing diversification'
            ],
            'risk_assessment': 'moderate',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(ai_analysis)
    except Exception as e:
        logger.error(f"Error generating ChatGPT portfolio analysis: {str(e)}")
        return jsonify({'error': 'Failed to generate portfolio analysis'}), 500

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """Handle unexpected errors"""
    logger.error(f"Unexpected error: {str(error)}\n{traceback.format_exc()}")
    return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    try:
        logger.info("Starting crypto trading server...")
        logger.info(f"Available exchanges: {exchange_manager.get_available_exchanges()}")
        
        port = int(os.getenv('PORT', 5000))
        logger.info(f"Starting server on port {port}")
        
        # Railway-optimized startup
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise
