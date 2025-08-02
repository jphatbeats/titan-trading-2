#!/usr/bin/env python3
"""
Main Production Server - Railway Deployment Optimized
Complete API with ALL endpoints for BingX, Blofin, Kraken, and CryptoNews
"""

import threading
import time
import schedule
from datetime import datetime
import pytz
import os
import sys
import signal
import json
import glob
from flask import Flask, jsonify, request
from flask_cors import CORS

# Create Flask app
app = Flask(__name__)
CORS(app, origins="*")

# Discord Configuration
ALPHA_CHANNEL_ID = os.getenv('ALPHA_DISCORD_CHANNEL_ID', '1399790636990857277')
PORTFOLIO_CHANNEL_ID = os.getenv('PORTFOLIO_DISCORD_CHANNEL_ID', '1399451217372905584')

try:
    from automated_trading_alerts import run_automated_alerts
    print("✅ Successfully imported automated_trading_alerts")
except ImportError as e:
    print(f"⚠️ Warning: automated_trading_alerts import failed: {e}")
    def run_automated_alerts():
        print("📊 Running fallback alert system...")
        return True

class MainServer:
    def __init__(self):
        self.last_alert = None
        self.server_status = "starting"
        self.alert_thread = None
        self.is_running = True
        self.error_count = 0
        self.last_health_check = datetime.now(pytz.timezone('US/Central'))
        
    def run_scheduled_alerts(self):
        """Run trading alerts with enhanced error recovery"""
        try:
            current_time = datetime.now(pytz.timezone('US/Central'))
            print(f"\n🔄 Running scheduled alerts - {current_time.strftime('%I:%M %p CST')}")
            
            # Run alerts
            run_automated_alerts()
            self.last_alert = current_time
            self.error_count = 0
            print("✅ Alerts completed successfully")
            
        except Exception as e:
            self.error_count += 1
            print(f"❌ Alert error #{self.error_count}: {e}")
            
            # If too many errors, wait longer before next attempt
            if self.error_count > 3:
                print("⚠️ Multiple alert failures - extending wait time")
                time.sleep(300)  # Wait 5 minutes before next attempt
    
    def alert_scheduler(self):
        """Background alert scheduler with enhanced error recovery"""
        print("🚀 Alert scheduler starting...")
        
        # Schedule alerts every hour
        schedule.every().hour.do(self.run_scheduled_alerts)
        
        # Run initial alert after 1 minute
        print("🎯 Scheduling initial alert in 1 minute...")
        time.sleep(60)
        self.run_scheduled_alerts()
        
        # Keep scheduler running with error recovery
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds
                
                # Update health check timestamp
                self.last_health_check = datetime.now(pytz.timezone('US/Central'))
                
            except Exception as e:
                print(f"⚠️ Scheduler error: {e}")
                time.sleep(60)  # Wait longer on error
                
                # Try to recover from errors
                try:
                    schedule.clear()
                    schedule.every().hour.do(self.run_scheduled_alerts)
                    print("🔄 Scheduler recovered and reinitialized")
                except:
                    print("❌ Failed to recover scheduler")
    
    def start_scheduler(self):
        """Start the alert scheduler in background thread"""
        self.alert_thread = threading.Thread(target=self.alert_scheduler, daemon=False)
        self.alert_thread.start()
        print("✅ Alert scheduler thread started")

# Initialize server
server = MainServer()

# Helper function for error handling
def safe_api_call(func, *args, **kwargs):
    """Safely execute API calls with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return {'error': str(e), 'status': 'api_error'}

# Global CORS handler
@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,User-Agent,Accept')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
        return response

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,User-Agent,Accept')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS,PUT,DELETE')
    return response

# ============================================================================
# MAIN ENDPOINTS
# ============================================================================

@app.route('/')
def root_index():
    """API Documentation and Status"""
    port = int(os.getenv('PORT', 5000))
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    return jsonify({
        'status': 'operational',
        'message': 'Complete Crypto Trading API - ALL ENDPOINTS ACTIVE',
        'deployment_mode': 'Railway Production' if is_railway else 'Local Development',
        'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
        'total_endpoints': 29,
        'categories': {
            'health': ['health'],
            'live_data': ['all-exchanges', 'account-balances', 'bingx-positions', 'blofin-positions', 'market-data'],
            'bingx_analysis': ['klines', 'market-analysis', 'candlestick-analysis', 'multi-timeframe'],
            'chatgpt': ['account-summary', 'portfolio-analysis'],
            'crypto_news': ['portfolio', 'symbols', 'risk-alerts', 'bullish-signals', 'breaking-news', 'opportunity-scanner', 'market-intelligence', 'pump-dump-detector'],
            'kraken': ['positions', 'balance', 'trade-history', 'orders', 'market-data', 'portfolio-performance', 'asset-allocation', 'trading-stats']
        },
        'platform_info': {
            'railway_deployment': is_railway,
            'discord_configured': bool(ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID),
            'api_integrations': ['BingX', 'Blofin', 'Kraken', 'CryptoNews']
        }
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """External health check endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    current_time = datetime.now(pytz.timezone('US/Central'))
    scheduler_healthy = (current_time - server.last_health_check).seconds < 120
    
    return jsonify({
        'status': 'healthy' if scheduler_healthy else 'degraded',
        'timestamp': current_time.isoformat(),
        'uptime_check': 'ok',
        'server_running': server.is_running,
        'scheduler_healthy': scheduler_healthy,
        'last_scheduler_check': server.last_health_check.isoformat(),
        'error_count': server.error_count,
        'platform': 'Railway Production',
        'discord_configured': bool(ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID),
        'total_endpoints': 29
    })

# ============================================================================
# LIVE DATA ENDPOINTS
# ============================================================================

@app.route('/api/live/all-exchanges', methods=['GET', 'OPTIONS'])
def get_all_exchanges_data():
    """Get data from all exchanges combined"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import (fetch_positions, initialize_blofin, fetch_blofin_positions, 
                         initialize_kraken, fetch_kraken_positions)
        
        # Get BingX data
        bingx_data = safe_api_call(fetch_positions)
        
        # Get Blofin data
        blofin_exchange = initialize_blofin()
        blofin_data = safe_api_call(fetch_blofin_positions, blofin_exchange)
        
        # Get Kraken data
        kraken_exchange = initialize_kraken()
        kraken_data = safe_api_call(fetch_kraken_positions, kraken_exchange)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'source': 'All Exchanges Live Data',
            'exchanges': {
                'bingx': bingx_data,
                'blofin': blofin_data,
                'kraken': kraken_data
            },
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/account-balances', methods=['GET', 'OPTIONS'])
def get_account_balances():
    """Get account balances from all exchanges"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_blofin, initialize_kraken
        import ccxt
        
        balances = {}
        
        # BingX balance (if available)
        try:
            # BingX balance would need separate API call
            balances['bingx'] = {'status': 'positions_only', 'note': 'Use positions endpoint for BingX data'}
        except Exception as e:
            balances['bingx'] = {'error': str(e)}
        
        # Blofin balance
        try:
            blofin = initialize_blofin()
            if blofin:
                blofin_balance = blofin.fetch_balance()
                balances['blofin'] = blofin_balance
        except Exception as e:
            balances['blofin'] = {'error': str(e)}
        
        # Kraken balance
        try:
            kraken = initialize_kraken()
            if kraken:
                kraken_balance = kraken.fetch_balance()
                balances['kraken'] = kraken_balance
        except Exception as e:
            balances['kraken'] = {'error': str(e)}
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'source': 'All Exchange Balances',
            'balances': balances,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/bingx-positions', methods=['GET', 'OPTIONS'])
def get_live_bingx_positions():
    """Get live positions directly from BingX API"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import fetch_positions, fetch_open_orders
        
        positions_result = fetch_positions()
        orders_result = fetch_open_orders()
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'source': 'BingX Live API',
            'positions': positions_result,
            'orders': orders_result,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/blofin-positions', methods=['GET', 'OPTIONS'])
def get_blofin_positions():
    """Get live positions from Blofin"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_blofin, fetch_blofin_positions, fetch_blofin_orders
        
        blofin_exchange = initialize_blofin()
        positions = fetch_blofin_positions(blofin_exchange)
        orders = fetch_blofin_orders(blofin_exchange)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'source': 'Blofin Live API',
            'positions': positions,
            'orders': orders,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live/market-data/<symbol>', methods=['GET', 'OPTIONS'])
def get_market_data(symbol):
    """Get market data for a specific symbol"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import get_bingx_market_data
        
        market_data = get_bingx_market_data(symbol)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'market_data': market_data,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# BINGX ANALYSIS ENDPOINTS
# ============================================================================

@app.route('/api/bingx/klines/<symbol>', methods=['GET', 'OPTIONS'])
def get_bingx_klines(symbol):
    """Get BingX candlestick data"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import fetch_bingx_klines
        
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 100))
        
        klines_data = fetch_bingx_klines(symbol, interval, limit)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'interval': interval,
            'limit': limit,
            'klines': klines_data,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bingx/market-analysis/<symbol>', methods=['GET', 'OPTIONS'])
def get_bingx_market_analysis(symbol):
    """Get comprehensive BingX market analysis"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import get_bingx_market_data
        
        analysis = get_bingx_market_data(symbol)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'analysis': analysis,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bingx/candlestick-analysis/<symbol>', methods=['GET', 'OPTIONS'])
def get_bingx_candlestick_analysis(symbol):
    """Get BingX candlestick pattern analysis"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import analyze_candlestick_patterns
        
        interval = request.args.get('interval', '1h')
        limit = int(request.args.get('limit', 50))
        
        analysis = analyze_candlestick_patterns(symbol, interval, limit)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'analysis': analysis,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bingx/multi-timeframe/<symbol>', methods=['GET', 'OPTIONS'])
def get_bingx_multi_timeframe(symbol):
    """Get multi-timeframe analysis for BingX symbol"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import analyze_candlestick_patterns
        
        timeframes = ['15m', '1h', '4h', '1d']
        analysis = {}
        
        for tf in timeframes:
            analysis[tf] = analyze_candlestick_patterns(symbol, tf, 20)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'timeframes': analysis,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CHATGPT OPTIMIZED ENDPOINTS
# ============================================================================

@app.route('/api/chatgpt/account-summary', methods=['GET', 'OPTIONS'])
def get_chatgpt_account_summary():
    """ChatGPT-optimized account summary"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import export_positions
        
        # Run export to get latest data
        export_positions()
        
        # Load the latest positions file
        json_files = glob.glob("positions_*.json")
        if json_files:
            latest_file = max(json_files, key=lambda x: os.path.getctime(x))
            with open(latest_file, 'r') as f:
                positions = json.load(f)
        else:
            positions = []
        
        # Calculate summary
        total_positions = len(positions)
        profitable = len([p for p in positions if p.get('PnL %', 0) > 0])
        losing = len([p for p in positions if p.get('PnL %', 0) < 0])
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST'),
            'platform': 'Railway',
            'account_summary': {
                'total_positions': total_positions,
                'profitable_positions': profitable,
                'losing_positions': losing,
                'neutral_positions': total_positions - profitable - losing,
                'success_rate': round((profitable / total_positions * 100), 2) if total_positions > 0 else 0
            },
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chatgpt/portfolio-analysis', methods=['GET', 'OPTIONS'])
def get_chatgpt_portfolio_analysis():
    """ChatGPT-optimized portfolio analysis"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        # Load latest positions
        json_files = glob.glob("positions_*.json")
        if json_files:
            latest_file = max(json_files, key=lambda x: os.path.getctime(x))
            with open(latest_file, 'r') as f:
                positions = json.load(f)
        else:
            positions = []
        
        profitable = [p for p in positions if p.get('PnL %', 0) > 0]
        losing = [p for p in positions if p.get('PnL %', 0) < 0]
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST'),
            'platform': 'Railway',
            'portfolio_overview': {
                'total_positions': len(positions),
                'profitable_count': len(profitable),
                'losing_count': len(losing),
                'top_performers': profitable[:3] if profitable else [],
                'worst_performers': losing[:3] if losing else []
            },
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# CRYPTO NEWS ENDPOINTS
# ============================================================================

@app.route('/api/crypto-news/portfolio', methods=['GET', 'OPTIONS'])
def get_portfolio_crypto_news():
    """Get crypto news for portfolio symbols"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_portfolio_symbols, alert_narrative_confluence, get_general_crypto_news
        
        symbols = get_portfolio_symbols()
        news = get_general_crypto_news(items=50)
        alerts = alert_narrative_confluence(symbols, news)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'portfolio_symbols': symbols,
            'news_alerts': alerts,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/symbols/<symbols>', methods=['GET', 'OPTIONS'])
def get_crypto_news_by_symbols(symbols):
    """Get crypto news for specific symbols"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_news_by_tickers
        
        symbol_list = symbols.split(',')
        news = get_news_by_tickers(symbol_list, items=30)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbols': symbol_list,
            'news': news,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/risk-alerts', methods=['GET', 'OPTIONS'])
def get_crypto_risk_alerts():
    """Get crypto risk alerts and bearish flags"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_general_crypto_news, filter_bearish_flags
        
        news = get_general_crypto_news(items=100)
        risk_alerts = filter_bearish_flags(news)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'risk_alerts': risk_alerts,
            'total_alerts': len(risk_alerts),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/bullish-signals', methods=['GET', 'OPTIONS'])
def get_crypto_bullish_signals():
    """Get bullish crypto signals and catalysts"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_general_crypto_news, filter_bullish_signals
        
        news = get_general_crypto_news(items=100)
        bullish_signals = filter_bullish_signals(news)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'bullish_signals': bullish_signals,
            'total_signals': len(bullish_signals),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/breaking-news', methods=['GET', 'OPTIONS'])
def get_breaking_crypto_news():
    """Get breaking crypto news"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_breaking_news_optimized
        
        hours = int(request.args.get('hours', 6))
        breaking_news = get_breaking_news_optimized(hours=hours, items=50)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'timeframe_hours': hours,
            'breaking_news': breaking_news,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/opportunity-scanner', methods=['GET', 'OPTIONS'])
def scan_crypto_opportunities():
    """Scan for crypto opportunities"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import scan_opportunities
        
        opportunities = scan_opportunities(opportunity_type='all')
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'opportunities': opportunities,
            'total_opportunities': len(opportunities),
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/market-intelligence', methods=['GET', 'OPTIONS'])
def get_market_intelligence():
    """Get comprehensive market intelligence"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import get_comprehensive_crypto_intelligence
        
        intelligence = get_comprehensive_crypto_intelligence()
        
        return jsonify(intelligence)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/crypto-news/pump-dump-detector', methods=['GET', 'OPTIONS'])
def detect_pump_dump_signals():
    """Detect pump and dump signals"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from crypto_news_alerts import detect_pump_dump_signals
        
        signals = detect_pump_dump_signals(signal_type='both', confidence_threshold=60)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'pump_dump_signals': signals,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# KRAKEN ENDPOINTS
# ============================================================================

@app.route('/api/kraken/positions', methods=['GET', 'OPTIONS'])
def get_kraken_positions():
    """Get Kraken positions"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken, fetch_kraken_positions
        
        kraken_exchange = initialize_kraken()
        positions = fetch_kraken_positions(kraken_exchange)
        
        # Calculate performance metrics
        total_pnl = sum(p.get('unrealizedPnl', 0) for p in positions if p.get('unrealizedPnl'))
        total_positions = len(positions)
        profitable = len([p for p in positions if p.get('unrealizedPnl', 0) > 0])
        
        performance = {
            'total_positions': total_positions,
            'profitable_positions': profitable,
            'losing_positions': total_positions - profitable,
            'total_unrealized_pnl': total_pnl,
            'success_rate': round((profitable / total_positions * 100), 2) if total_positions > 0 else 0
        }
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'performance': performance,
            'positions': positions,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/asset-allocation', methods=['GET', 'OPTIONS'])
def get_kraken_asset_allocation():
    """Get Kraken asset allocation breakdown"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken
        
        kraken = initialize_kraken()
        if kraken:
            balance = kraken.fetch_balance()
            
            # Calculate allocation
            allocation = {}
            total_value = 0
            
            for currency, amounts in balance.items():
                if isinstance(amounts, dict) and amounts.get('total', 0) > 0:
                    allocation[currency] = amounts['total']
                    total_value += amounts['total']  # This would need price conversion in real implementation
            
            return jsonify({
                'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                'allocation': allocation,
                'total_assets': len(allocation),
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Kraken not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/trading-stats', methods=['GET', 'OPTIONS'])
def get_kraken_trading_stats():
    """Get Kraken trading statistics"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken
        
        kraken = initialize_kraken()
        if kraken:
            trades = kraken.fetch_my_trades(limit=100)
            
            # Calculate stats
            total_trades = len(trades)
            buy_trades = len([t for t in trades if t['side'] == 'buy'])
            sell_trades = total_trades - buy_trades
            total_fees = sum(t.get('fee', {}).get('cost', 0) for t in trades)
            
            stats = {
                'total_trades': total_trades,
                'buy_trades': buy_trades,
                'sell_trades': sell_trades,
                'total_fees_paid': total_fees,
                'avg_trade_size': sum(t['amount'] for t in trades) / total_trades if total_trades > 0 else 0
            }
            
            return jsonify({
                'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                'trading_stats': stats,
                'recent_trades': trades[:10],  # Last 10 trades
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Kraken not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'available_endpoints': [
            '/health', '/', '/api/live/all-exchanges', '/api/live/account-balances',
            '/api/live/bingx-positions', '/api/live/blofin-positions', '/api/live/market-data/{symbol}',
            '/api/bingx/klines/{symbol}', '/api/bingx/market-analysis/{symbol}',
            '/api/bingx/candlestick-analysis/{symbol}', '/api/bingx/multi-timeframe/{symbol}',
            '/api/chatgpt/account-summary', '/api/chatgpt/portfolio-analysis',
            '/api/crypto-news/portfolio', '/api/crypto-news/symbols/{symbols}',
            '/api/crypto-news/risk-alerts', '/api/crypto-news/bullish-signals',
            '/api/crypto-news/breaking-news', '/api/crypto-news/opportunity-scanner',
            '/api/crypto-news/market-intelligence', '/api/crypto-news/pump-dump-detector',
            '/api/kraken/positions', '/api/kraken/balance', '/api/kraken/trade-history',
            '/api/kraken/orders', '/api/kraken/market-data/{symbol}',
            '/api/kraken/portfolio-performance', '/api/kraken/asset-allocation',
            '/api/kraken/trading-stats'
        ],
        'status': 'error'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred on the server',
        'status': 'error'
    }), 500

# ============================================================================
# GRACEFUL SHUTDOWN
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🔄 Received signal {signum}. Shutting down gracefully...")
    server.is_running = False
    if server.alert_thread and server.alert_thread.is_alive():
        print("⏳ Waiting for alert thread to finish...")
        server.alert_thread.join(timeout=5)
    print("✅ Server shutdown complete")
    sys.exit(0)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# MAIN SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    print("🚀 STARTING COMPLETE CRYPTO TRADING API SERVER")
    print("=" * 80)
    
    # Get Railway configuration
    port = int(os.getenv('PORT', 5000))
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    print(f"🌐 Platform: {'Railway Production' if is_railway else 'Local Development'}")
    print(f"🔌 Port: {port}")
    print(f"📡 Discord Configured: {bool(ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID)}")
    print(f"   📢 Alpha Channel: {ALPHA_CHANNEL_ID}")
    print(f"   📊 Portfolio Channel: {PORTFOLIO_CHANNEL_ID}")
    print(f"🎯 Total API Endpoints: 29")
    print(f"🔗 API Categories: Health, Live Data, BingX Analysis, ChatGPT, CryptoNews, Kraken")
    print("=" * 80)
    
    # Start alert scheduler
    server.start_scheduler()
    
    # Start Flask server
    try:
        print("🎉 ALL 29 ENDPOINTS NOW ACTIVE!")
        print("💎 Your $20K → $1M Alpha Hunting System is LIVE!")
        
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            threaded=True
        )
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        raiseexchange)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'source': 'Kraken Live API',
            'positions': positions,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/balance', methods=['GET', 'OPTIONS'])
def get_kraken_balance():
    """Get Kraken account balance"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken
        
        kraken = initialize_kraken()
        if kraken:
            balance = kraken.fetch_balance()
            return jsonify({
                'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                'balance': balance,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Kraken not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/trade-history', methods=['GET', 'OPTIONS'])
def get_kraken_trade_history():
    """Get Kraken trade history"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken
        
        kraken = initialize_kraken()
        if kraken:
            limit = int(request.args.get('limit', 50))
            trades = kraken.fetch_my_trades(limit=limit)
            return jsonify({
                'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                'trades': trades,
                'status': 'success'
            })
        else:
            return jsonify({'error': 'Kraken not configured'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/orders', methods=['GET', 'OPTIONS'])
def get_kraken_orders():
    """Get Kraken open orders"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken, fetch_kraken_orders
        
        kraken_exchange = initialize_kraken()
        orders = fetch_kraken_orders(kraken_exchange)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'orders': orders,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/market-data/<symbol>', methods=['GET', 'OPTIONS'])
def get_kraken_market_data(symbol):
    """Get Kraken market data for symbol"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import get_kraken_price
        
        price = get_kraken_price(symbol)
        
        return jsonify({
            'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
            'symbol': symbol,
            'price': price,
            'status': 'success'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kraken/portfolio-performance', methods=['GET', 'OPTIONS'])
def get_kraken_portfolio_performance():
    """Get Kraken portfolio performance metrics"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        from main import initialize_kraken, fetch_kraken_positions
        
        kraken_exchange = initialize_kraken()
        positions = fetch_kraken_positions(kraken_
