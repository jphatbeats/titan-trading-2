from flask import Flask, jsonify, request
import logging
import os
from datetime import datetime
import traceback

# Import our custom modules with error handling
from logger_config import setup_logging
from error_handler import handle_exchange_error, ExchangeNotAvailableError
from exchange_manager import ExchangeManager
from trading_functions import TradingFunctions

# Setup logging
setup_logging()
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
        'version': '1.0.0',
        'status': 'running',
        'available_endpoints': 29,
        'available_exchanges': exchange_manager.get_available_exchanges(),
        'total_exchanges': len(exchange_manager.get_available_exchanges()),
        'endpoints': {
            'health': '/health',
            'exchange_status': '/exchanges/status',
            'market_data': '/api/ticker/{exchange}/{symbol}, /api/orderbook/{exchange}/{symbol}, /api/trades/{exchange}/{symbol}',
            'trading': '/api/order (POST), /api/orders/{exchange}, /api/order/{exchange}/{order_id} (DELETE)',
            'account': '/api/balance/{exchange}, /api/account-info/{exchange}, /api/transfer (POST)',
            'portfolio': '/api/portfolio/{exchange}, /api/positions/{exchange}',
            'history': '/api/order-history/{exchange}, /api/trade-history/{exchange}, /api/deposit-history/{exchange}',
            'derivatives': '/api/funding-rate/{exchange}/{symbol}, /api/leverage/{exchange}/{symbol} (POST)',
            'documentation': 'Visit /health for health check and /exchanges/status for exchange status'
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
    logger.info("Starting crypto trading server...")
    logger.info(f"Available exchanges: {exchange_manager.get_available_exchanges()}")
    
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
