#!/usr/bin/env python3
"""
Automated Trading Alerts System
Reads positions.csv, analyzes trading conditions, and sends Discord alerts every hour
"""

import pandas as pd
import json
import time
import glob
import os
from datetime import datetime
import pytz
import schedule
import threading
import asyncio
import aiohttp
import requests

# Discord Multi-Channel Configuration
DISCORD_WEBHOOKS = {
    'alerts': os.getenv('DISCORD_ALERTS_WEBHOOK'),        # Breaking news, risks (1398000506068009032)
    'portfolio': os.getenv('DISCORD_PORTFOLIO_WEBHOOK'),  # Portfolio analysis (1399451217372905584)  
    'alpha_scans': os.getenv('DISCORD_ALPHA_WEBHOOK')     # Trading opportunities (1399790636990857277)
}

# Legacy single webhook support (backward compatible)
LEGACY_DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')

# Google Sheets NoCode API URL
GOOGLE_SHEETS_API_URL = "https://v1.nocodeapi.com/computerguy81/google_sheets/QxNdANWVhHvvXSzL"

# Railway API Configuration  
RAILWAY_API_URL = "https://titan-trading-2-production.up.railway.app"


def cleanup_old_files(keep_count=3):
    """Remove old CSV and JSON files, keeping only the most recent ones"""
    try:
        print(f"🧹 Cleaning up old files, keeping {keep_count} most recent...")
        
        # Clean up CSV files
        csv_files = glob.glob("positions_*.csv")
        if len(csv_files) > keep_count:
            # Sort by modification time (oldest first)
            csv_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_delete = csv_files[:-keep_count]  # Keep last N files
            
            for file in files_to_delete:
                os.remove(file)
                print(f"🗑️ Deleted old CSV: {file}")
        
        # Clean up JSON files
        json_files = glob.glob("positions_*.json")
        if len(json_files) > keep_count:
            # Sort by modification time (oldest first)
            json_files.sort(key=lambda x: os.path.getmtime(x))
            files_to_delete = json_files[:-keep_count]  # Keep last N files
            
            for file in files_to_delete:
                os.remove(file)
                print(f"🗑️ Deleted old JSON: {file}")
                
        print(f"✅ Cleanup completed - kept {keep_count} most recent files of each type")
        
    except Exception as e:
        print(f"⚠️ Error during cleanup: {e}")


def find_latest_positions_csv():
    """Find the most recent positions CSV file"""
    try:
        csv_files = glob.glob("positions_*.csv")
        if not csv_files:
            print("❌ No positions CSV files found")
            return None

        # Sort by modification time to get the latest
        latest_file = max(csv_files,
                          key=lambda x: time.ctime(os.path.getmtime(x)))
        print(f"📄 Found latest positions file: {latest_file}")
        return latest_file
    except Exception as e:
        print(f"❌ Error finding CSV file: {e}")
        return None


async def fetch_live_positions():
    """Fetch live positions directly from Railway API"""
    try:
        print("📡 Fetching live positions from Railway API...")
        
        all_positions = []
        
        # Fetch BingX positions
        try:
            bingx_data = await fetch_railway_api("/api/live/bingx-positions")
            if bingx_data and bingx_data.get('positions'):
                for pos in bingx_data['positions']:
                    all_positions.append({
                        'Symbol': pos.get('symbol', ''),
                        'Platform': 'BingX',
                        'Entry Price': pos.get('avgPrice', 0),
                        'Mark Price': pos.get('markPrice', 0),
                        'Unrealized PnL %': pos.get('unrealizedPnl_percent', 0),
                        'Side (LONG/SHORT)': pos.get('side', ''),
                        'Margin Size ($)': pos.get('initialMargin', 0),
                        'Leverage': pos.get('leverage', 1),
                        'SL Set?': '❌'  # Default, would need additional API call to check
                    })
                print(f"✅ Fetched {len(bingx_data['positions'])} BingX positions")
        except Exception as e:
            print(f"⚠️ BingX positions error: {e}")
        
        # Fetch Kraken positions
        try:
            kraken_data = await fetch_railway_api("/api/kraken/positions")
            if kraken_data and kraken_data.get('positions'):
                for symbol, pos in kraken_data['positions'].items():
                    if float(pos.get('size', 0)) != 0:  # Only active positions
                        all_positions.append({
                            'Symbol': symbol,
                            'Platform': 'Kraken',
                            'Entry Price': pos.get('avgPrice', 0),
                            'Mark Price': pos.get('markPrice', 0),
                            'Unrealized PnL %': pos.get('unrealizedPnl_percent', 0),
                            'Side (LONG/SHORT)': 'LONG' if float(pos.get('size', 0)) > 0 else 'SHORT',
                            'Margin Size ($)': abs(float(pos.get('cost', 0))),
                            'Leverage': pos.get('leverage', 1),
                            'SL Set?': '❌'
                        })
                print(f"✅ Fetched {len([p for p in kraken_data['positions'].values() if float(p.get('size', 0)) != 0])} Kraken positions")
        except Exception as e:
            print(f"⚠️ Kraken positions error: {e}")
            
        # Fetch Blofin positions  
        try:
            blofin_data = await fetch_railway_api("/api/live/blofin-positions")
            if blofin_data and blofin_data.get('positions'):
                for pos in blofin_data['positions']:
                    all_positions.append({
                        'Symbol': pos.get('symbol', ''),
                        'Platform': 'Blofin',
                        'Entry Price': pos.get('avgPrice', 0),
                        'Mark Price': pos.get('markPrice', 0),
                        'Unrealized PnL %': pos.get('unrealizedPnl_percent', 0),
                        'Side (LONG/SHORT)': pos.get('side', ''),
                        'Margin Size ($)': pos.get('initialMargin', 0),
                        'Leverage': pos.get('leverage', 1),
                        'SL Set?': '❌'
                    })
                print(f"✅ Fetched {len(blofin_data['positions'])} Blofin positions")
        except Exception as e:
            print(f"⚠️ Blofin positions error: {e}")
        
        print(f"📊 Total live positions fetched: {len(all_positions)}")
        return all_positions
        
    except Exception as e:
        print(f"❌ Error fetching live positions: {e}")
        return []


def calculate_simulated_rsi(pnl_percentage):
    """Calculate simulated RSI based on PnL percentage"""
    try:
        pnl = float(pnl_percentage)

        # Simulate RSI based on PnL trends
        if pnl > 25:
            return min(85, 50 + (pnl * 1.2))  # Strong uptrend = high RSI
        elif pnl < -15:
            return max(15, 50 + (pnl * 1.8))  # Strong downtrend = low RSI
        else:
            return 50 + (pnl * 0.6)  # Neutral zone

    except (ValueError, TypeError):
        return 50  # Neutral RSI if calculation fails


def analyze_trading_conditions(positions):
    """Analyze positions for trading alerts"""
    alerts = []

    if not positions:
        print("❌ No positions to analyze")
        return alerts

    print(f"🔍 Analyzing {len(positions)} positions...")

    for position in positions:
        try:
            symbol = position.get('Symbol', '')
            platform = position.get('Platform', '')
            pnl_pct = float(position.get('Unrealized PnL %', 0))
            side = position.get('Side (LONG/SHORT)', '')
            margin_size = float(position.get('Margin Size ($)', 0))
            entry_price = float(position.get('Entry Price', 0))
            mark_price = float(position.get('Mark Price', 0))

            # Skip if symbol is empty
            if not symbol:
                continue

            # Calculate simulated RSI
            rsi = calculate_simulated_rsi(pnl_pct)

            print(f"📊 {symbol}: PnL {pnl_pct:.1f}%, RSI {rsi:.1f}")

            # Condition 1: RSI Overbought (RSI > 72) - Optimized threshold
            if rsi > 72:
                alerts.append({
                    'type':
                    'overbought',
                    'symbol':
                    symbol,
                    'platform':
                    platform,
                    'rsi':
                    round(rsi, 1),
                    'pnl':
                    pnl_pct,
                    'message':
                    f"🟥 Alert! ${symbol} RSI is {rsi:.1f}. Consider exiting or trailing stop."
                })

            # Condition 2: RSI Oversold (RSI < 28) - Optimized threshold
            elif rsi < 28:
                alerts.append({
                    'type':
                    'oversold',
                    'symbol':
                    symbol,
                    'platform':
                    platform,
                    'rsi':
                    round(rsi, 1),
                    'pnl':
                    pnl_pct,
                    'message':
                    f"🟩 ${symbol} is oversold at RSI {rsi:.1f}. Clean reversal setup detected."
                })

            # Condition 3: Unrealized PnL < -8% (Losing trade) - More sensitive threshold
            if pnl_pct < -8:
                alerts.append({
                    'type':
                    'losing_trade',
                    'symbol':
                    symbol,
                    'platform':
                    platform,
                    'pnl':
                    pnl_pct,
                    'margin':
                    margin_size,
                    'message':
                    f"🚨 ${symbol} is down {pnl_pct:.1f}%. Capital preservation - review position."
                })

            # Additional Condition: Large position without stop loss (>$150)
            sl_set = position.get('SL Set?', '❌')
            if margin_size > 150 and sl_set == '❌':
                alerts.append({
                    'type':
                    'no_stop_loss',
                    'symbol':
                    symbol,
                    'platform':
                    platform,
                    'margin':
                    margin_size,
                    'message':
                    f"🛡️ ${symbol} position (${margin_size:.0f}) needs STOP LOSS for fast rotation!"
                })

            # Additional Condition: High profit opportunity (>35%) - Let winners run
            if pnl_pct > 35:
                alerts.append({
                    'type':
                    'high_profit',
                    'symbol':
                    symbol,
                    'platform':
                    platform,
                    'pnl':
                    pnl_pct,
                    'message':
                    f"💰 ${symbol} up {pnl_pct:.1f}%! Consider rotating or trailing stops."
                })

        except Exception as e:
            print(
                f"⚠️ Error analyzing position {position.get('Symbol', 'unknown')}: {e}"
            )
            continue

    print(f"🎯 Analysis complete. Found {len(alerts)} alerts.")
    return alerts


def send_to_google_sheets():
    """Send portfolio data to Google Sheets API using simplified format"""
    try:
        import pandas as pd
        import requests
        import glob
        import os

        # Find the latest positions CSV
        csv_files = glob.glob("positions_*.csv")
        if not csv_files:
            print("❌ No positions CSV files found for Google Sheets")
            return False

        latest_file = max(csv_files, key=lambda x: os.path.getmtime(x))
        print(f"📄 Using {latest_file} for Google Sheets sync")

        # Read and format the data
        df = pd.read_csv(latest_file)

        # Filter out summary rows
        df_filtered = df[df['Platform'].notna() & (df['Platform'] != 'PORTFOLIO SUMMARY')]

        if df_filtered.empty:
            print("⚠️ No trading positions found for Google Sheets")
            return False

        # Create simplified data format for Google Sheets
        sheet_data = []
        
        # Add timestamp header
        from datetime import datetime
        import pytz
        central_tz = pytz.timezone('US/Central')
        timestamp = datetime.now(central_tz).strftime('%Y-%m-%d %I:%M %p CST')
        
        # Headers row
        headers = ["Symbol", "Platform", "Entry", "Current", "PnL%", "Size$", "Side", "Leverage"]
        sheet_data.append(headers)

        # Data rows
        for _, row in df_filtered.iterrows():
            try:
                symbol = str(row.get('Symbol', 'N/A')).replace('-USDT', '').replace('USDT', '')
                platform = str(row.get('Platform', 'N/A'))
                entry_price = float(row.get('Entry Price', 0))
                mark_price = float(row.get('Mark Price', 0))
                pnl_pct = float(row.get('PnL %', 0))
                margin_size = float(row.get('Margin Size ($)', 0))
                side = str(row.get('Side (LONG/SHORT)', 'UNKNOWN'))
                leverage = float(row.get('Leverage', 1))

                data_row = [
                    symbol,
                    platform,
                    f"{entry_price:.6f}" if entry_price > 0 else "0",
                    f"{mark_price:.6f}" if mark_price > 0 else "0",
                    f"{pnl_pct:+.1f}%",
                    f"${margin_size:.0f}",
                    side,
                    f"{leverage:.0f}x"
                ]
                
                sheet_data.append(data_row)

            except Exception as e:
                print(f"⚠️ Error processing {row.get('Symbol', 'unknown')} for sheets: {e}")
                continue

        # Try different API endpoint format
        print(f"📤 Sending {len(sheet_data)-1} positions to Google Sheets...")
        print(f"📋 Data preview: {sheet_data[:2]}")

        # Try the NoCode API with proper format
        url = "https://v1.nocodeapi.com/computerguy81/google_sheets/QxNdANWVhHvvXSzL?tabId=Sheet1"
        
        # Send as raw 2D array (not wrapped in data object)
        response = requests.post(url, json=sheet_data, timeout=30, headers={
            'Content-Type': 'application/json'
        })

        print(f"📋 Response status: {response.status_code}")
        print(f"📋 Response text: {response.text[:200]}...")

        if response.status_code == 200:
            print("✅ Google Sheets updated successfully!")
            return True
        elif response.status_code == 400:
            print("❌ Bad request - trying alternative format...")
            # Try with data wrapper
            alt_payload = {"data": sheet_data}
            alt_response = requests.post(url, json=alt_payload, timeout=30)
            if alt_response.status_code == 200:
                print("✅ Google Sheets updated with alternative format!")
                return True
            else:
                print(f"❌ Alternative format also failed: {alt_response.status_code} - {alt_response.text}")
                return False
        else:
            print(f"❌ Google Sheets API error: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error sending to Google Sheets: {e}")
        import traceback
        print(f"📋 Full error: {traceback.format_exc()}")
        return False


async def fetch_railway_api(endpoint):
    """Fetch data from Railway API"""
    try:
        url = f"{RAILWAY_API_URL}{endpoint}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    print(f"❌ Railway API error {response.status} for {endpoint}")
                    return None
    except Exception as e:
        print(f"❌ Railway API fetch error: {e}")
        return None

async def send_discord_alert(message, channel='portfolio'):
    """Send alert to Discord channel via webhook"""
    try:
        # Get webhook URL
        webhook_url = DISCORD_WEBHOOKS.get(channel) or LEGACY_DISCORD_WEBHOOK
        if not webhook_url:
            print(f"❌ No Discord webhook configured for {channel}")
            return False
        
        # Channel-specific bot names
        bot_names = {
            'alerts': 'Market Alerts Bot',
            'portfolio': 'Portfolio Analysis Bot',
            'alpha_scans': 'Alpha Scanner Bot'
        }
        
        payload = {
            "content": message,
            "username": bot_names.get(channel, "Trading Alerts Bot")
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                if response.status == 204:
                    print(f"✅ Discord alert sent to #{channel}")
                    return True
                else:
                    print(f"❌ Discord webhook failed: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Discord send error: {e}")
        return False

def prepare_alert_data(alerts):
    """Prepare alert data for Discord bot integration"""
    if not alerts:
        print("✅ No alerts to send - all positions look good!")
        return None

    try:
        # Create timestamp
        central_tz = pytz.timezone('US/Central')
        timestamp = datetime.now(central_tz).strftime('%Y-%m-%d %I:%M %p CST')

        # Group alerts by type for summary
        alert_types = {}
        for alert in alerts:
            alert_type = alert['type']
            alert_types[alert_type] = alert_types.get(alert_type, 0) + 1

        # Prepare alert data that the Discord bot can use
        alert_data = {
            "timestamp": timestamp,
            "total_alerts": len(alerts),
            "alert_types": alert_types,
            "alerts": alerts,
            "summary_parts": []
        }

        # Create summary parts
        if 'overbought' in alert_types:
            alert_data["summary_parts"].append(f"⚠️ Overbought: {alert_types['overbought']}")
        if 'oversold' in alert_types:
            alert_data["summary_parts"].append(f"📉 Oversold: {alert_types['oversold']}")
        if 'losing_trade' in alert_types:
            alert_data["summary_parts"].append(f"❗Losing: {alert_types['losing_trade']}")
        if 'no_stop_loss' in alert_types:
            alert_data["summary_parts"].append(f"🚨 No SL: {alert_types['no_stop_loss']}")
        if 'high_profit' in alert_types:
            alert_data["summary_parts"].append(f"💰 High Profit: {alert_types['high_profit']}")
        if 'confluence' in alert_types:
            alert_data["summary_parts"].append(f"📰 News: {alert_types['confluence']}")
        if 'risk' in alert_types:
            alert_data["summary_parts"].append(f"🚨 Risk News: {alert_types['risk']}")
        if 'bullish' in alert_types:
            alert_data["summary_parts"].append(f"🚀 Bullish News: {alert_types['bullish']}")

        print(f"📋 Prepared {len(alerts)} alerts for Discord bot")
        return alert_data

    except Exception as e:
        print(f"❌ Error preparing alert data: {e}")
        return None

async def generate_enhanced_alerts(positions_df):
    """Generate enhanced alerts using Railway API intelligence"""
    enhanced_alerts = []
    
    try:
        # Extract unique symbols from positions
        if positions_df is not None and not positions_df.empty:
            symbols = positions_df['symbol'].unique().tolist()
            portfolio_symbols = [symbol.replace('-USDT', '').replace('/USD', '') for symbol in symbols[:10]]  # Top 10
        else:
            portfolio_symbols = ['BTC', 'ETH', 'SOL']  # Default portfolio
        
        print(f"🔍 Analyzing {len(portfolio_symbols)} symbols: {', '.join(portfolio_symbols)}")
        
        async with aiohttp.ClientSession() as session:
            # Get portfolio-specific news
            portfolio_url = f"{RAILWAY_API_URL}/api/crypto-news/portfolio"
            portfolio_params = {'symbols': ','.join(portfolio_symbols)}
            
            async with session.get(portfolio_url, params=portfolio_params) as response:
                if response.status == 200:
                    portfolio_news = await response.json()
                    if portfolio_news.get('success') and portfolio_news.get('data', {}).get('articles'):
                        articles = portfolio_news['data']['articles'][:3]  # Top 3
                        for article in articles:
                            enhanced_alerts.append({
                                'type': 'portfolio_news',
                                'symbol': 'PORTFOLIO',
                                'platform': 'News',
                                'message': f"📰 {article.get('title', 'News update')[:80]}... ({article.get('source_name', 'Unknown')})"
                            })
            
            # Get risk alerts  
            risk_url = f"{RAILWAY_API_URL}/api/crypto-news/risk-alerts"
            async with session.get(risk_url) as response:
                if response.status == 200:
                    risk_data = await response.json()
                    if risk_data.get('success') and risk_data.get('data', {}).get('alerts'):
                        risk_articles = risk_data['data']['alerts'][:2]  # Top 2
                        for article in risk_articles:
                            enhanced_alerts.append({
                                'type': 'risk_alert',
                                'symbol': 'MARKET',
                                'platform': 'Risk',
                                'message': f"⚠️ {article.get('title', 'Risk warning')[:80]}..."
                            })
            
            # Get bullish signals
            bullish_url = f"{RAILWAY_API_URL}/api/crypto-news/bullish-signals"
            async with session.get(bullish_url) as response:
                if response.status == 200:
                    bullish_data = await response.json()
                    if bullish_data.get('success') and bullish_data.get('data', {}).get('signals'):
                        bullish_articles = bullish_data['data']['signals'][:2]  # Top 2
                        for article in bullish_articles:
                            enhanced_alerts.append({
                                'type': 'bullish_signal',
                                'symbol': 'MARKET',
                                'platform': 'Signals',
                                'message': f"📈 {article.get('title', 'Bullish signal')[:80]}..."
                            })
            
            # Get trading opportunities
            opp_url = f"{RAILWAY_API_URL}/api/crypto-news/opportunity-scanner"
            async with session.get(opp_url) as response:
                if response.status == 200:
                    opp_data = await response.json()
                    if opp_data.get('success') and opp_data.get('data', {}).get('opportunities'):
                        opportunities = opp_data['data']['opportunities'][:2]  # Top 2
                        for opp in opportunities:
                            enhanced_alerts.append({
                                'type': 'opportunity',
                                'symbol': 'MARKET',
                                'platform': 'Opportunities',
                                'message': f"🔍 {opp.get('title', 'Trading opportunity')[:80]}..."
                            })
        
        return enhanced_alerts
        
    except Exception as e:
        print(f"❌ Error in enhanced alerts: {e}")
        return []

def save_alerts_for_bot(alerts):
    """Save alerts to a file that the Discord bot can read"""
    if not alerts:
        return True

    try:
        alert_data = prepare_alert_data(alerts)
        if not alert_data:
            return False

        # Save to JSON file for bot to read
        alerts_file = "latest_alerts.json"
        with open(alerts_file, 'w') as f:
            json.dump(alert_data, f, indent=2, default=str)

        print(f"✅ Saved {len(alerts)} alerts to {alerts_file} for Discord bot")
        return True

    except Exception as e:
        print(f"❌ Error saving alerts for bot: {e}")
        return False


async def run_trading_analysis_async():
    """Async version of trading analysis with enhanced alerts"""
    print(f"\n🎯 ANALYSIS STARTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Step 1: Fetch live positions from Railway API
        print("\n📡 Step 1: Fetching live positions from Railway API...")
        positions = await fetch_live_positions()
        if not positions:
            print("❌ No live positions available - skipping analysis")
            return

        print(f"✅ Loaded {len(positions)} live positions for analysis")
        
        # Convert to DataFrame for enhanced analysis
        positions_df = pd.DataFrame(positions) if positions else None

        # Step 2: Analyze trading conditions
        print("\n🔍 Step 2: Analyzing trading conditions...")
        alerts = analyze_trading_conditions(positions)

        # Step 3: Process alerts for Discord bot
        print("\n📤 Step 3: Processing alerts...")
        if alerts:
            print(f"🚨 Found {len(alerts)} trading alerts!")
        else:
            print("✅ No alerts triggered - all positions within normal parameters")
            alerts = []  # Initialize empty list

        # Step 4: Google Sheets sync disabled
        print("\n📊 Step 4: Google Sheets sync disabled by user")

        # Step 5: Generate enhanced news and market alerts using Railway API
        print("\n📰 Step 5: Fetching enhanced crypto intelligence...")
        try:
            enhanced_alerts = await generate_enhanced_alerts(positions_df)
            if enhanced_alerts:
                print(f"📰 Found {len(enhanced_alerts)} enhanced alerts from Railway API")
                alerts.extend(enhanced_alerts)
            else:
                print("📰 No relevant enhanced alerts found")
        except Exception as e:
            print(f"❌ Enhanced alerts error: {e}")
            # Fallback to original news alerts
            try:
                from crypto_news_alerts import generate_news_alerts
                news_alerts = generate_news_alerts()
                if news_alerts:
                    print(f"📰 Fallback: Found {len(news_alerts)} news alerts")
                    alerts.extend(news_alerts)
            except Exception as fallback_e:
                print(f"❌ Fallback news alerts error: {fallback_e}")

        # Save all alerts
        if alerts:
            success = save_alerts_for_bot(alerts)
            if success:
                print(f"✅ Saved {len(alerts)} total alerts for Discord bot")
            else:
                print("❌ Failed to save alerts")

        # Step 6: GitHub upload disabled
        print("\n📤 Step 6: GitHub upload disabled by user")

        # Step 7: Clean up old files
        print("\n🧹 Step 7: Cleaning up old files...")
        cleanup_old_files(keep_count=3)  # Keep 3 most recent files

        print("\n🎯 Enhanced trading analysis completed successfully!")
        print("⏰ Next analysis in 1 hour...")

    except Exception as e:
        print(f"❌ Error in trading analysis: {e}")

async def run_trading_analysis():
    """Main function to run complete trading analysis"""
    print("\n" + "=" * 60)
    print("🤖 AUTOMATED TRADING ANALYSIS STARTING")
    print(
        f"🕐 Time: {datetime.now(pytz.timezone('US/Central')).strftime('%Y-%m-%d %I:%M %p CST')}"
    )
    print("=" * 60)

    try:
        # Step 1: Fetch live positions from Railway API
        print("\n📡 Step 1: Fetching live positions from Railway API...")
        positions = await fetch_live_positions()
        if not positions:
            print("❌ No live positions available - skipping analysis")
            return

        print(f"✅ Loaded {len(positions)} live positions for analysis")

        # Step 2: Analyze trading conditions
        print("\n🔍 Step 2: Analyzing trading conditions...")
        alerts = analyze_trading_conditions(positions)

        # Step 3: Process alerts for Discord bot and send to channels
        print("\n📤 Step 3: Processing alerts...")
        if alerts:
            print(f"🚨 Found {len(alerts)} trading alerts!")
            
            # Save alerts to JSON (existing functionality)
            success = save_alerts_for_bot(alerts)
            if success:
                print("✅ Alerts saved for Discord bot")
            else:
                print("❌ Failed to save alerts")
            
            # Send portfolio alerts to #portfolio channel
            try:
                alert_data = prepare_alert_data(alerts)
                if alert_data and alert_data.get('message'):
                    portfolio_message = f"💼 **PORTFOLIO ANALYSIS** 💼\n{alert_data['message']}"
                    await send_discord_alert(portfolio_message, 'portfolio')
            except Exception as e:
                print(f"❌ Error sending portfolio alerts: {e}")
                
        else:
            print("✅ No alerts triggered - all positions within normal parameters")

        # Step 4: Google Sheets sync disabled
        print("\n📊 Step 4: Google Sheets sync disabled by user")

        # Step 5: Generate enhanced news and market alerts using Railway API
        print("\n📰 Step 5: Fetching enhanced crypto intelligence...")
        try:
            # Get breaking news and risk alerts for #alerts channel
            breaking_news = await fetch_railway_api("/api/crypto-news/breaking-news")
            risk_alerts = await fetch_railway_api("/api/crypto-news/risk-alerts")
            opportunities = await fetch_railway_api("/api/crypto-news/opportunity-scanner")
            
            # Send breaking news to #alerts channel
            if breaking_news and breaking_news.get('news'):
                news_message = f"🚨 **BREAKING CRYPTO NEWS** 🚨\n"
                for item in breaking_news['news'][:3]:  # Top 3 news
                    news_message += f"• {item.get('title', 'Market Update')}\n"
                await send_discord_alert(news_message, 'alerts')
            
            # Send risk alerts to #alerts channel  
            if risk_alerts and risk_alerts.get('alerts'):
                risk_message = f"⚠️ **RISK ALERTS** ⚠️\n"
                for alert in risk_alerts['alerts'][:3]:  # Top 3 risks
                    risk_message += f"• {alert.get('message', 'Risk detected')}\n"
                await send_discord_alert(risk_message, 'alerts')
            
            # Send opportunities to #alpha-scans channel
            if opportunities and opportunities.get('opportunities'):
                opp_message = f"🎯 **TRADING OPPORTUNITIES** 🎯\n"
                for opp in opportunities['opportunities'][:3]:  # Top 3 opportunities
                    opp_message += f"• {opp.get('symbol', '')} - {opp.get('signal', 'Signal detected')}\n"
                await send_discord_alert(opp_message, 'alpha_scans')
                
            print("📰 Enhanced alerts sent to appropriate Discord channels")
            
        except Exception as e:
            print(f"❌ Enhanced alerts error: {e}")
            # Fallback to original news alerts for #alerts channel
            try:
                from crypto_news_alerts import generate_news_alerts
                news_alerts = generate_news_alerts()
                if news_alerts:
                    print(f"📰 Fallback: Found {len(news_alerts)} news alerts")
                    fallback_message = f"📰 **CRYPTO NEWS UPDATE** 📰\n{str(news_alerts)[:500]}..."
                    await send_discord_alert(fallback_message, 'alerts')
            except Exception as fallback_e:
                print(f"❌ Fallback news alerts error: {fallback_e}")

        # Step 6: GitHub upload disabled
        print("\n📤 Step 6: GitHub upload disabled by user")

        # Step 7: Clean up old files
        print("\n🧹 Step 7: Cleaning up old files...")
        cleanup_old_files(keep_count=3)  # Keep 3 most recent files

        print("\n🎯 Trading analysis completed successfully!")
        print("⏰ Next analysis in 1 hour...")

    except Exception as e:
        print(f"❌ Error in trading analysis: {e}")


def run_scheduler():
    """Run the scheduler in a separate thread"""
    while True:
        schedule.run_pending()
        time.sleep(1)


def main():
    """Main function with hourly scheduling"""
    print("🚀 AUTOMATED TRADING ALERTS SYSTEM")
    print("=" * 50)
    print("📊 Features (OPTIMIZED THRESHOLDS):")
    print("  • RSI Analysis (Overbought > 72, Oversold < 28)")
    print("  • PnL Monitoring (Loss alerts < -8%)")
    print("  • Risk Management (No SL warnings > $150)")
    print("  • High Profit Alerts (> +35%)")
    print("  • Hourly automated analysis")
    print("=" * 50)

    print("🤖 Trading Alert System integrates with Discord bot")
    print("📋 Alerts will be saved to JSON file for bot processing")

    # Run initial analysis
    print("\n🎯 Running initial analysis...")
    asyncio.run(run_trading_analysis())

    # Schedule hourly runs
    print("\n⏰ Setting up hourly schedule...")
    schedule.every().hour.do(lambda: asyncio.run(run_trading_analysis()))

    # Start scheduler in background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    print("✅ Scheduler started! Running every hour...")
    print("🔄 Keep this process running for automated alerts")

    try:
        # Keep main thread alive with simple loop
        while True:
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        print("\n🛑 Trading alerts system stopped by user")
    except Exception as e:
        print(f"\n❌ System error: {e}")


def run_automated_alerts():
    """Simple function to run alerts once - for scheduled deployment"""
    print("🚀 Running automated trading alerts...")
    print("📋 Alerts will be processed by Discord bot integration")
    
    # Run the analysis
    asyncio.run(run_trading_analysis())
    print("✅ Automated alerts completed!")


if __name__ == "__main__":
    import sys
    
    # Check if running in automated mode
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        run_automated_alerts()
    else:
        main()
