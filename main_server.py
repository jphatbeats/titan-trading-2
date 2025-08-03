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
