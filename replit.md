# Overview

This is a Python-based cryptocurrency trading server that provides a unified API interface for interacting with multiple cryptocurrency exchanges through the CCXT library. Successfully migrated from Replit to Railway with comprehensive error handling to resolve CCXT import errors.

The server acts as a middleware layer that abstracts away the complexities of different exchange APIs, providing standardized endpoints for market data retrieval, trading operations, and account management across 3 specific exchanges: BingX, Kraken, and Blofin.

The system features robust error handling and logging capabilities, with non-blocking CCXT imports that allow the server to start successfully even if individual exchanges fail. All 30 endpoints are operational with graceful degradation for unavailable exchanges.

## Recent Changes (August 2025)
- ✅ Fixed Railway deployment CCXT import errors
- ✅ Implemented non-blocking exchange initialization 
- ✅ Added comprehensive error handling for all API endpoints
- ✅ Server starts successfully with all 35 endpoints operational
- ✅ Added root endpoint (/) with API documentation
- ✅ All 3 target exchanges (BingX, Kraken, Blofin) initialize without "RaiseExchange" errors
- ✅ **RESTORED CUSTOM API ENDPOINTS**: Added original Replit API schema
  - `/api/live/all-exchanges` - Multi-exchange live data
  - `/api/live/bingx-positions` - BingX custom format positions
  - `/api/live/blofin-positions` - Blofin positions  
  - `/api/kraken/balance` - Kraken balance (original pattern)
  - `/api/bingx/klines/{symbol}` - BingX candlestick data
- ✅ **RAILWAY STARTUP OPTIMIZATION**: Added threaded=True and proper error handling for Railway deployment reliability
- ✅ **FIXED API CREDENTIAL INJECTION**: Updated fallback ExchangeManager to properly pass API credentials to exchange instances (Railway deployment fix)
- ✅ **ENHANCED DISCORD/TELEGRAM BOT SYSTEM**: Integrated existing sophisticated bot with Railway API intelligence
  - Enhanced existing `automated_trading_alerts.py` with Railway API integration
  - Created `enhanced_bot_integration.py` for fetching market intelligence
  - Combined traditional trading analysis with AI-powered market intelligence
  - Bot now provides 6 types of intelligent alerts:
    • Traditional: oversold, overbought, losing trades, no stop loss, high profit
    • Enhanced: portfolio news, risk alerts, bullish signals, opportunities, breaking news, pump/dump detection
  - All alerts automatically saved to `latest_alerts.json` for Discord/Telegram bot consumption
  - Provides automated alerts that ChatGPT cannot deliver
- ✅ **ENHANCED EXISTING DISCORD BOT SYSTEM**: Enhanced existing `automated_trading_alerts.py` with multi-channel support
  - **#alerts channel** (1398000506068009032): Breaking news, risk alerts, market updates from Railway API
  - **#portfolio channel** (1399451217372905584): Portfolio analysis, position alerts, trading signals (hourly)
  - **#alpha-scans channel** (1399790636990857277): Trading opportunities from Railway API intelligence
  - Added async Discord webhook functionality to existing working file
  - Backward compatible with existing single webhook setup (DISCORD_WEBHOOK_URL)
  - Multi-channel support via DISCORD_ALERTS_WEBHOOK, DISCORD_PORTFOLIO_WEBHOOK, DISCORD_ALPHA_WEBHOOK
  - Integrated Railway API endpoints for intelligent content routing
- ✅ **COMPLETED FULL API SCHEMA**: Added all 28 missing endpoints from ChatGPT schema:
  **Crypto News Intelligence (8 endpoints):**
  - `/api/crypto-news/breaking-news` - Breaking crypto news with filtering
  - `/api/crypto-news/portfolio` - Portfolio-specific crypto news
  - `/api/crypto-news/symbols/{symbols}` - News by specific symbols
  - `/api/crypto-news/risk-alerts` - Risk warnings and alerts
  - `/api/crypto-news/bullish-signals` - Bullish sentiment analysis
  - `/api/crypto-news/opportunity-scanner` - Trading opportunities
  - `/api/crypto-news/market-intelligence` - Comprehensive market analysis
  - `/api/crypto-news/pump-dump-detector` - Pump and dump detection
  **BingX Analysis (3 endpoints):**
  - `/api/bingx/market-analysis/{symbol}` - Market analysis with orderbook
  - `/api/bingx/candlestick-analysis/{symbol}` - Candlestick patterns
  - `/api/bingx/multi-timeframe/{symbol}` - Multi-timeframe analysis
  **Kraken Trading Suite (6 endpoints):**
  - `/api/kraken/positions` - Account positions
  - `/api/kraken/trade-history` - Historical trades
  - `/api/kraken/orders` - Active orders
  - `/api/kraken/market-data/{symbol}` - Comprehensive market data
  - `/api/kraken/portfolio-performance` - Performance metrics
  - `/api/kraken/asset-allocation` - Asset allocation breakdown
  - `/api/kraken/trading-stats` - Trading statistics
  **ChatGPT AI Analysis (2 endpoints):**
  - `/api/chatgpt/account-summary` - AI-powered account analysis
  - `/api/chatgpt/portfolio-analysis` - AI portfolio recommendations
- ✅ **REAL CRYPTO NEWS API INTEGRATION**: Replaced mock data with authentic CryptoNews API
  - Integrated real CryptoNews API with token authentication
  - Added `crypto_news_api.py` module with comprehensive filtering capabilities
  - Implemented three ticker modes: broad, intersection, laser focus
  - Added Tier 1 source prioritization (Coindesk, CryptoSlate, The Block, Decrypt)
  - Real-time data with timeframe filtering (last5min to last30days)
  - Sentiment analysis and urgency scoring for all news articles
- ✅ **ADVANCED PORTFOLIO MANAGEMENT**: Added intelligent portfolio monitoring system
  - **Portfolio Holdings Management**: `/api/portfolio/holdings` - Store and manage user holdings
  - **Risk Monitoring**: `/api/portfolio/risk-monitor` - Real-time threat detection for specific holdings
  - **Correlation Analysis**: `/api/portfolio/correlation-plays` - Find multi-asset opportunities
  - **Priority Alerts**: `/api/alerts/prioritized` - Urgency-based alert system (HIGH/MEDIUM/LOW)
  - **Performance Tracking**: `/api/performance/news-tracking` - Monitor news accuracy and ROI
  - All endpoints include urgency scoring based on source quality and sentiment analysis
- ✅ **LIVE DATA APPROACH**: Eliminated CSV/JSON file dependencies for real-time accuracy
  - Updated `automated_trading_alerts.py` to use live Railway API data instead of CSV exports
  - Direct API calls to Railway server for current position data from all exchanges
  - Real-time PnL calculations instead of stale file-based data
  - Enhanced Discord bot integration with prioritized alerts endpoint

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Core Design Pattern
The application follows a layered architecture pattern with clear separation of concerns:

- **HTTP API Layer**: Flask-based REST API that handles incoming requests and response formatting
- **Business Logic Layer**: TradingFunctions class that implements trading operations and market data retrieval
- **Exchange Management Layer**: ExchangeManager class that handles CCXT exchange initialization and connection management
- **Error Handling Layer**: Comprehensive error handling system with custom exceptions and decorators

## Error Handling Strategy
The system implements a robust error handling mechanism using Python decorators and custom exceptions:

- **Custom Exception Hierarchy**: `ExchangeNotAvailableError` for connection/initialization issues and `ExchangeAPIError` for API-related problems
- **Decorator Pattern**: `@handle_exchange_error` decorator that wraps trading functions to catch and categorize different types of exchange errors
- **Graceful Degradation**: Failed exchanges are tracked separately, allowing the system to continue operating with available exchanges

## Exchange Management
The ExchangeManager uses a factory pattern to initialize and manage multiple exchange connections:

- **Environment-based Configuration**: API credentials and settings loaded from environment variables
- **Connection Pooling**: Maintains active connections to multiple exchanges simultaneously
- **Health Monitoring**: Tracks the status of each exchange connection and provides status reporting

## Logging Architecture
Centralized logging system with both console and file output:

- **Structured Logging**: Consistent log format across all components with timestamps and severity levels
- **Environment Configuration**: Log level configurable through environment variables
- **File Rotation**: Daily log files with fallback to console-only logging if file system access fails

## API Design
RESTful API design with resource-based endpoints:

- **Health Monitoring**: `/health` endpoint for service status checks
- **Exchange Status**: `/exchanges/status` for monitoring exchange connectivity
- **Market Data**: Resource-based endpoints for tickers, orderbooks, trades, and OHLCV data
- **Standardized Error Responses**: Consistent error response format with appropriate HTTP status codes

# External Dependencies

## Core Framework
- **Flask**: Web framework for HTTP API server
- **CCXT**: Cryptocurrency exchange trading library for unified exchange access

## Supported Exchanges
- **Binance**: Global cryptocurrency exchange
- **Kraken**: US-based cryptocurrency exchange
- **Blofin**: Professional trading platform
- **OKX**: Global cryptocurrency exchange
- **Bybit**: Derivatives and spot trading exchange

## Configuration Requirements
- **Environment Variables**: All exchange API credentials and configuration loaded from environment variables
- **API Keys**: Each exchange requires API key, secret, and potentially passphrase
- **Sandbox Support**: Optional sandbox/testnet mode for each exchange

## System Dependencies
- **Python Logging**: Built-in logging framework for application monitoring
- **OS Module**: Environment variable access and file system operations
- **DateTime**: Timestamp generation for logging and API responses