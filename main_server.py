#!/usr/bin/env python3
"""
Main Production Server - Railway Deployment Optimized
Ensures 24/7 uptime with proper threading and health checks
"""

import threading
import time
import schedule
from datetime import datetime
import pytz
import os
import sys
import signal
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

@app.route('/')
def root_index():
    """Main landing page with deployment status"""
    port = int(os.getenv('PORT', 5000))
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    return jsonify({
        'status': 'operational',
        'message': 'Trading Portfolio API Server is Running Successfully on Railway!',
        'deployment_mode': 'Railway Production' if is_railway else 'Local Development',
        'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
        'server_info': {
            'port': port,
            'host': '0.0.0.0',
            'platform': 'Railway' if is_railway else 'Local',
            'discord_channels_configured': {
                'alpha_channel': ALPHA_CHANNEL_ID,
                'portfolio_channel': PORTFOLIO_CHANNEL_ID
            }
        },
        'endpoints': {
            'portfolio_analysis': '/api/chatgpt/portfolio-analysis',
            'live_positions': '/api/live/bingx-positions',
            'all_exchanges': '/api/live/all-exchanges',
            'health_check': '/health',
            'api_docs': '/api-docs'
        },
        'test_message': 'ChatGPT can now access this API reliably on Railway!'
    })

@app.route('/health', methods=['GET', 'OPTIONS'])
def health_check():
    """External health check endpoint for keep-alive monitoring"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
        
    current_time = datetime.now(pytz.timezone('US/Central'))
    scheduler_healthy = (current_time - server.last_health_check).seconds < 120
    
    health_data = {
        'status': 'healthy' if scheduler_healthy else 'degraded',
        'timestamp': current_time.isoformat(),
        'uptime_check': 'ok',
        'server_running': server.is_running,
        'scheduler_healthy': scheduler_healthy,
        'last_scheduler_check': server.last_health_check.isoformat(),
        'error_count': server.error_count,
        'platform': 'Railway Production',
        'discord_configured': bool(ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID)
    }
    
    return jsonify(health_data)

@app.route('/server-status')
def server_status():
    """Detailed server status for monitoring"""
    return jsonify({
        'status': 'operational',
        'platform': 'Railway',
        'last_alert': server.last_alert.isoformat() if server.last_alert else None,
        'uptime': datetime.now(pytz.timezone('US/Central')).isoformat(),
        'components': {
            'api_server': 'running',
            'alert_system': 'running' if server.is_running else 'stopped',
            'scheduler': 'healthy' if server.error_count < 3 else 'degraded',
            'discord_bot': 'configured' if ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID else 'needs_config'
        },
        'error_count': server.error_count,
        'thread_status': {
            'alert_thread_alive': server.alert_thread.is_alive() if server.alert_thread else False,
            'main_thread_running': server.is_running
        },
        'discord_channels': {
            'alpha_channel_id': ALPHA_CHANNEL_ID,
            'portfolio_channel_id': PORTFOLIO_CHANNEL_ID
        }
    })

@app.route('/ping')
def ping():
    """Simple ping endpoint for external monitoring"""
    return jsonify({
        'pong': True,
        'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
        'platform': 'Railway'
    })

@app.route('/api/live/bingx-positions', methods=['GET', 'OPTIONS'])
def get_live_bingx_positions():
    """Get live positions directly from BingX API"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        print("🔍 BingX Positions endpoint called")
        
        # Try to import and use the main module
        try:
            from main import fetch_positions, fetch_open_orders
            print("✅ Successfully imported from main module")
            
            positions_result = fetch_positions()
            orders_result = fetch_open_orders()
            
            response_data = {
                'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                'source': 'BingX Live API via Railway',
                'positions': positions_result,
                'orders': orders_result,
                'status': 'success'
            }
            
            print("✅ BingX data retrieved successfully")
            return jsonify(response_data)
            
        except ImportError as import_error:
            print(f"⚠️ Import error, using fallback: {import_error}")
            
            # Fallback: Try to load from latest positions file
            try:
                import json
                import glob
                
                json_files = glob.glob("positions_*.json")
                if json_files:
                    latest_file = max(json_files, key=lambda x: os.path.getctime(x))
                    with open(latest_file, 'r') as f:
                        positions_data = json.load(f)
                    
                    return jsonify({
                        'timestamp': datetime.now(pytz.timezone('US/Central')).isoformat(),
                        'source': f'Cached data from {latest_file}',
                        'positions': positions_data,
                        'orders': [],
                        'status': 'success_cached',
                        'note': 'Using cached data due to import issues'
                    })
                else:
                    raise Exception("No positions data available")
                    
            except Exception as fallback_error:
                print(f"❌ Fallback failed: {fallback_error}")
                return jsonify({
                    'error': 'Unable to fetch live data or cached data',
                    'import_error': str(import_error),
                    'fallback_error': str(fallback_error),
                    'status': 'error'
                }), 500

    except Exception as e:
        error_msg = f'Failed to fetch BingX data: {str(e)}'
        print(f"❌ BingX API Error: {error_msg}")
        return jsonify({'error': error_msg, 'status': 'api_error'}), 500

@app.route('/api/chatgpt/portfolio-analysis', methods=['GET', 'OPTIONS'])
def get_chatgpt_portfolio_analysis():
    """ChatGPT-optimized portfolio analysis endpoint"""
    if request.method == 'OPTIONS':
        return jsonify({'status': 'ok'})
    
    try:
        # Try to get analysis from various sources
        try:
            from discord_bot import analyze_portfolio
            analysis = analyze_portfolio()
        except ImportError:
            # Fallback analysis using positions data
            import json
            import glob
            
            json_files = glob.glob("positions_*.json")
            if json_files:
                latest_file = max(json_files, key=lambda x: os.path.getctime(x))
                with open(latest_file, 'r') as f:
                    positions = json.load(f)
                
                profitable = [p for p in positions if p.get('PnL %', 0) > 0]
                losing = [p for p in positions if p.get('PnL %', 0) < 0]
                
                analysis = {
                    'total_positions': len(positions),
                    'profitable': profitable,
                    'losing': losing
                }
            else:
                analysis = {'error': 'No positions data available'}
        
        if analysis.get('error'):
            return jsonify({'error': analysis['error']}), 500

        chatgpt_summary = {
            'timestamp': datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST'),
            'platform': 'Railway',
            'portfolio_overview': {
                'total_positions': analysis.get('total_positions', 0),
                'profitable_count': len(analysis.get('profitable', [])),
                'losing_count': len(analysis.get('losing', []))
            },
            'status': 'success'
        }

        return jsonify(chatgpt_summary)

    except Exception as e:
        return jsonify({'error': f'Failed to generate analysis: {str(e)}'}), 500

@app.route('/api-docs')
def api_docs():
    """API documentation"""
    return jsonify({
        'message': 'Trading Portfolio API with Live Exchange Access - Railway Deployment',
        'status': 'operational',
        'deployment': 'Railway Production Server',
        'live_endpoints': {
            '/api/live/bingx-positions': 'Get live positions from BingX',
            '/api/chatgpt/portfolio-analysis': 'ChatGPT portfolio analysis'
        },
        'health_endpoints': {
            '/health': 'External health check for monitoring',
            '/ping': 'Simple ping response',
            '/server-status': 'Detailed server status'
        },
        'features': [
            'Railway 24/7 deployment',
            'Discord alerts to correct channels',
            'Hourly automated trading alerts',
            'ChatGPT API integration',
            'Error recovery and retry logic'
        ]
    })

if __name__ == "__main__":
    print("🚀 STARTING RAILWAY PRODUCTION SERVER")
    print("=" * 60)
    
    # Get Railway configuration
    port = int(os.getenv('PORT', 5000))
    is_railway = os.getenv('RAILWAY_ENVIRONMENT') is not None
    
    print(f"🌐 Platform: {'Railway Production' if is_railway else 'Local Development'}")
    print(f"🔌 Port: {port}")
    print(f"📡 Discord Configured: {bool(ALPHA_CHANNEL_ID and PORTFOLIO_CHANNEL_ID)}")
    print(f"   📢 Alpha Channel: {ALPHA_CHANNEL_ID}")
    print(f"   📊 Portfolio Channel: {PORTFOLIO_CHANNEL_ID}")
    print("=" * 60)
    
    # Start alert scheduler
    server.start_scheduler()
    
    # Start Flask server
    try:
        app.run(
            host='0.0.0.0', 
            port=port, 
            debug=False, 
            threaded=True
        )
    except Exception as e:
        print(f"❌ Server startup error: {e}")
        raise