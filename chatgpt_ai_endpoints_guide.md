# ChatGPT AI Trading Intelligence Endpoints

**Real OpenAI GPT-4o integration providing intelligent trading analysis**

## Available Endpoints

### 1. Portfolio Analysis - `GET /api/chatgpt/portfolio-analysis`
**Real AI-powered portfolio analysis using your live exchange data**

**Response includes:**
- `overall_assessment`: Portfolio health score (1-10)
- `risk_level`: LOW/MEDIUM/HIGH with detailed explanation
- `recommendations`: Specific actionable trading recommendations
- `position_analysis`: Analysis of each major position
- `diversification_score`: Portfolio diversification rating (1-10)
- `next_actions`: Immediate actions to take
- `market_outlook`: AI assessment of market conditions for your assets

### 2. News Sentiment Analysis - `POST /api/chatgpt/news-sentiment`
**Grade news articles for market impact and sentiment**

**Request body:**
```json
{
  "articles": [
    {
      "title": "Article title",
      "text": "Article content",
      "tickers": ["BTC", "ETH"],
      "source_name": "Source"
    }
  ]
}
```

**Response includes:**
- `sentiment`: BULLISH/BEARISH/NEUTRAL for each article
- `impact_score`: 1-10 market impact potential
- `trading_signal`: BUY/SELL/HOLD recommendations
- `confidence`: AI confidence level (1-10)
- `overall_market_sentiment`: Aggregated market outlook

### 3. Trade Grader - `POST /api/chatgpt/trade-grader`
**Get A-F grades for your trades with improvement suggestions**

**Request body:**
```json
{
  "symbol": "BTC/USDT",
  "entry_price": 65000,
  "exit_price": 67000,
  "position_size": 0.1,
  "trade_duration": "2 days",
  "stop_loss": 63000,
  "take_profit": 68000
}
```

**Response includes:**
- `trade_grade`: Letter grade (A-F)
- `execution_score`: Entry/exit timing score (1-10)
- `risk_management_score`: Position sizing and risk control (1-10)
- `what_went_right`: Positive aspects of the trade
- `improvement_suggestions`: Specific advice for better trades
- `lessons_learned`: Key takeaways

### 4. Hourly Insights - `GET /api/chatgpt/hourly-insights`
**Time-sensitive trading insights for current market conditions**

**Response includes:**
- `market_pulse`: Current market condition summary
- `immediate_opportunities`: Trading opportunities right now
- `risk_alerts`: Immediate risks to watch
- `portfolio_adjustments`: Suggested position changes
- `next_hour_outlook`: What to expect in next 1-4 hours
- `action_items`: Specific actions to take this hour

### 5. Risk Assessment - `GET /api/chatgpt/risk-assessment`
**Comprehensive AI-powered risk analysis of your portfolio**

**Response includes:**
- `overall_risk_score`: Portfolio risk level (1-10)
- `risk_factors`: Current risk factors identified
- `position_risks`: Risk analysis for each position
- `correlation_risks`: Assets that move together dangerously
- `recommended_hedges`: Specific hedging strategies
- `stress_test_scenarios`: How portfolio performs in crashes

### 6. Opportunity Scanner - `GET /api/chatgpt/opportunity-scanner`
**AI-powered scanner for new trading opportunities**

**Response includes:**
- `high_probability_setups`: Best trading setups right now
- `breakout_candidates`: Assets near key breakout levels
- `momentum_plays`: Assets with strong momentum
- `entry_strategies`: Specific entry methods
- `risk_reward_analysis`: Risk/reward ratios
- `probability_of_success`: AI-calculated success probability

### 7. Account Summary - `GET /api/chatgpt/account-summary`
**Comprehensive AI analysis of your entire trading account**

**Response includes:**
- Complete portfolio overview with AI insights
- Multi-exchange account analysis
- Performance assessment and recommendations
- Strategic guidance for account optimization

## Key Features

**Real AI Analysis:**
- Uses OpenAI GPT-4o (latest model) for genuine intelligence
- Analyzes your actual live trading data
- Provides specific, actionable recommendations
- Includes confidence scores and risk assessments

**Professional Trading Focus:**
- Expert-level market analysis and insights
- Risk management recommendations
- Opportunity identification with probability scoring
- Trade performance grading and improvement suggestions

**Integration Ready:**
- Works with live exchange data (BingX, Kraken, Blofin)
- Combines with CryptoNews API for comprehensive analysis
- JSON responses for easy integration
- Error handling for production reliability

## Usage Examples

**Get portfolio insights:**
```bash
curl "https://your-railway-url/api/chatgpt/portfolio-analysis"
```

**Grade news sentiment:**
```bash
curl -X POST "https://your-railway-url/api/chatgpt/news-sentiment" \
  -H "Content-Type: application/json" \
  -d '{"articles": [{"title": "Bitcoin hits new highs", "tickers": ["BTC"]}]}'
```

**Get hourly trading insights:**
```bash
curl "https://your-railway-url/api/chatgpt/hourly-insights"
```

## Technical Implementation

- **Model**: OpenAI GPT-4o (latest, most capable model)
- **Response Format**: Structured JSON with consistent schemas
- **Error Handling**: Graceful degradation when AI unavailable  
- **Performance**: Optimized prompts for fast, relevant responses
- **Security**: API key properly secured in environment variables

Transform your trading system from basic alerts into an AI-powered intelligence platform!