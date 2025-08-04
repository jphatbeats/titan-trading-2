#!/usr/bin/env python3
"""
OpenAI Trading Intelligence Module
Real ChatGPT integration for crypto trading analysis
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
from openai import OpenAI

logger = logging.getLogger(__name__)

class TradingIntelligence:
    """AI-powered trading analysis using OpenAI GPT-4"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o"  # Latest model for best analysis
        
    def analyze_portfolio(self, portfolio_data: Dict) -> Dict:
        """Generate AI-powered portfolio analysis"""
        try:
            prompt = f"""
            As an expert crypto trading analyst, analyze this portfolio data and provide intelligent insights:

            Portfolio Data:
            {json.dumps(portfolio_data, indent=2)}

            Provide analysis in JSON format with:
            1. overall_assessment: Overall portfolio health (1-10 score)
            2. risk_level: LOW/MEDIUM/HIGH with explanation
            3. recommendations: List of specific actionable recommendations
            4. position_analysis: Analysis of each major position
            5. diversification_score: How well diversified (1-10)
            6. next_actions: Immediate actions to take
            7. market_outlook: Current market sentiment for held assets

            Focus on practical trading advice, risk management, and profit optimization.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert cryptocurrency trading analyst with years of experience in portfolio management, risk assessment, and market analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500
            )

            analysis = json.loads(response.choices[0].message.content or "{}")
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['ai_powered'] = True
            analysis['analysis_type'] = 'portfolio_analysis'
            
            return analysis

        except Exception as e:
            logger.error(f"Portfolio analysis error: {e}")
            return {
                'error': 'AI analysis temporarily unavailable',
                'fallback_message': 'Portfolio data received but AI processing failed',
                'timestamp': datetime.now().isoformat()
            }

    def analyze_alerts_for_discord(self, alerts: List[Dict], portfolio_data: Dict = None) -> Dict:
        """Generate AI insights for Discord alerts"""
        try:
            alert_summary = "\n".join([f"- {alert.get('message', alert.get('type', 'Alert'))}" for alert in alerts[:5]])
            
            prompt = f"""
            As a crypto trading expert, analyze these trading alerts and provide Discord-ready insights:

            Current Alerts:
            {alert_summary}

            Portfolio Context:
            {json.dumps(portfolio_data, indent=2) if portfolio_data else 'No portfolio data available'}

            Provide response in JSON format with:
            1. urgency_level: LOW/MEDIUM/HIGH based on alert severity
            2. key_insight: One sentence summary of main concern/opportunity
            3. action_recommendation: Specific next step for trader
            4. risk_warning: Any immediate risks to highlight
            5. opportunity_flag: Any opportunities detected
            6. confidence_score: Your confidence in analysis (1-10)

            Keep responses concise for Discord format (under 200 chars per field).
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a crypto trading expert providing concise Discord-ready analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=800
            )

            analysis = json.loads(response.choices[0].message.content or "{}")
            analysis['timestamp'] = datetime.now().isoformat()
            analysis['ai_powered'] = True
            analysis['analysis_type'] = 'discord_alert_analysis'
            
            return analysis

        except Exception as e:
            logger.error(f"Discord alert analysis error: {e}")
            return {
                'error': 'AI alert analysis temporarily unavailable',
                'fallback_insight': 'Trading alerts detected - review manually',
                'timestamp': datetime.now().isoformat()
            }

    def grade_news_sentiment(self, news_articles: List[Dict]) -> Dict:
        """Grade news articles for market sentiment impact"""
        try:
            articles_text = []
            for i, article in enumerate(news_articles[:5]):  # Analyze top 5 articles
                articles_text.append(f"""
                Article {i+1}:
                Title: {article.get('title', 'No title')}
                Source: {article.get('source_name', 'Unknown')}
                Tickers: {', '.join(article.get('tickers', []))}
                Content: {article.get('text', article.get('description', 'No content'))[:500]}
                """)

            prompt = f"""
            As a crypto market analyst, grade these news articles for trading impact:

            {chr(10).join(articles_text)}

            For each article, provide JSON analysis with:
            1. sentiment: BULLISH/BEARISH/NEUTRAL
            2. impact_score: 1-10 (how much this could move markets)
            3. affected_tickers: List of crypto symbols most affected
            4. trading_signal: BUY/SELL/HOLD recommendation
            5. time_horizon: SHORT/MEDIUM/LONG term impact
            6. confidence: 1-10 how confident in this analysis
            7. key_factors: What makes this bullish/bearish

            Return as: {{"articles": [analysis for each article], "overall_market_sentiment": "BULLISH/BEARISH/NEUTRAL", "summary": "brief market outlook"}}
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert cryptocurrency market analyst specializing in news sentiment analysis and market impact assessment."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.6,
                max_tokens=2000
            )

            sentiment_analysis = json.loads(response.choices[0].message.content or "{}")
            sentiment_analysis['timestamp'] = datetime.now().isoformat()
            sentiment_analysis['ai_powered'] = True
            sentiment_analysis['analysis_type'] = 'news_sentiment'
            
            return sentiment_analysis

        except Exception as e:
            logger.error(f"News sentiment analysis error: {e}")
            return {
                'error': 'AI sentiment analysis temporarily unavailable',
                'articles_count': len(news_articles),
                'timestamp': datetime.now().isoformat()
            }

    def grade_trade_performance(self, trade_data: Dict) -> Dict:
        """Grade individual trades and provide improvement suggestions"""
        try:
            prompt = f"""
            As a professional trading coach, analyze this trade performance:

            Trade Data:
            {json.dumps(trade_data, indent=2)}

            Provide detailed JSON analysis with:
            1. trade_grade: A-F letter grade for this trade
            2. execution_score: 1-10 for entry/exit timing
            3. risk_management_score: 1-10 for position sizing and stops
            4. what_went_right: Positive aspects of the trade
            5. what_went_wrong: Areas that need improvement
            6. lessons_learned: Key takeaways for future trades
            7. improvement_suggestions: Specific actionable advice
            8. next_trade_recommendations: How to apply lessons

            Be honest but constructive in feedback.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional trading coach with expertise in crypto markets, risk management, and trade psychology."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1200
            )

            trade_grade = json.loads(response.choices[0].message.content or "{}")
            trade_grade['timestamp'] = datetime.now().isoformat()
            trade_grade['ai_powered'] = True
            trade_grade['analysis_type'] = 'trade_grading'
            
            return trade_grade

        except Exception as e:
            logger.error(f"Trade grading error: {e}")
            return {
                'error': 'AI trade grading temporarily unavailable',
                'trade_received': bool(trade_data),
                'timestamp': datetime.now().isoformat()
            }

    def generate_hourly_insights(self, market_data: Dict, portfolio_data: Dict) -> Dict:
        """Generate AI-powered hourly trading insights"""
        try:
            prompt = f"""
            As a crypto trading strategist, provide hourly market insights:

            Current Market Data:
            {json.dumps(market_data, indent=2)}

            Current Portfolio:
            {json.dumps(portfolio_data, indent=2)}

            Generate JSON insights with:
            1. market_pulse: Current market condition summary
            2. immediate_opportunities: Trading opportunities right now
            3. risk_alerts: Any immediate risks to watch
            4. portfolio_adjustments: Suggested position changes
            5. next_hour_outlook: What to expect in next 1-4 hours
            6. key_levels: Important support/resistance to watch
            7. action_items: Specific actions to take this hour
            8. market_sentiment_shift: Any sentiment changes detected

            Focus on actionable, time-sensitive insights for active trading.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an active crypto trading strategist specializing in short-term market analysis and tactical trading decisions."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.8,
                max_tokens=1500
            )

            insights = json.loads(response.choices[0].message.content or "{}")
            insights['timestamp'] = datetime.now().isoformat()
            insights['ai_powered'] = True
            insights['analysis_type'] = 'hourly_insights'
            insights['next_update'] = (datetime.now().hour + 1) % 24
            
            return insights

        except Exception as e:
            logger.error(f"Hourly insights error: {e}")
            return {
                'error': 'AI insights temporarily unavailable',
                'next_retry': '15 minutes',
                'timestamp': datetime.now().isoformat()
            }

    def assess_risk_profile(self, portfolio_data: Dict, market_conditions: Dict) -> Dict:
        """AI-powered risk assessment of current positions"""
        try:
            prompt = f"""
            As a risk management expert, assess the risk profile:

            Portfolio:
            {json.dumps(portfolio_data, indent=2)}

            Market Conditions:
            {json.dumps(market_conditions, indent=2)}

            Provide comprehensive JSON risk assessment:
            1. overall_risk_score: 1-10 (10 = highest risk)
            2. risk_factors: List of current risk factors
            3. position_risks: Risk analysis for each major position
            4. correlation_risks: Assets that move together dangerously
            5. liquidity_risks: Positions that might be hard to exit
            6. market_risks: Broader market risks affecting portfolio
            7. recommended_hedges: Specific hedging strategies
            8. risk_mitigation_actions: Immediate actions to reduce risk
            9. stress_test_scenarios: How portfolio performs in crashes

            Focus on practical risk management for crypto trading.
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a quantitative risk management expert specializing in cryptocurrency portfolio risk assessment and mitigation strategies."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.5,
                max_tokens=1800
            )

            risk_assessment = json.loads(response.choices[0].message.content or "{}")
            risk_assessment['timestamp'] = datetime.now().isoformat()
            risk_assessment['ai_powered'] = True
            risk_assessment['analysis_type'] = 'risk_assessment'
            
            return risk_assessment

        except Exception as e:
            logger.error(f"Risk assessment error: {e}")
            return {
                'error': 'AI risk assessment temporarily unavailable',
                'manual_review_recommended': True,
                'timestamp': datetime.now().isoformat()
            }

    def scan_opportunities(self, market_data: Dict, news_data: Dict) -> Dict:
        """AI-powered opportunity scanner for new trades with accurate pricing"""
        try:
            # Extract real-time market data if available
            real_time_data = market_data.get('real_time_market_data', {})
            
            prompt = f"""
            As a professional crypto trading analyst, analyze this comprehensive market data to identify high-probability trading opportunities:

            REAL-TIME MARKET DATA (includes current prices, OHLCV, volume, technical indicators):
            {json.dumps(real_time_data, indent=2)}

            NEWS & SENTIMENT DATA:
            {json.dumps(news_data, indent=2)}

            ADDITIONAL MARKET INTELLIGENCE:
            {json.dumps(market_data.get('opportunities', {}), indent=2)}

            **CRITICAL**: Use ONLY the real-time price data from REAL-TIME MARKET DATA section for all price calculations, entry/exit suggestions, and technical analysis.

            Provide comprehensive JSON analysis with:
            1. high_probability_setups: Top 3 trading setups with specific entry prices (use EXACT current prices from real-time data)
            2. entry_price_analysis: Exact entry prices based on current market data
            3. target_levels: Realistic profit targets based on technical levels and recent price action
            4. stop_loss_recommendations: Precise stop loss levels using current support/resistance
            5. risk_reward_ratios: Calculated risk/reward for each trade
            6. volume_confirmation: Volume analysis supporting each trade setup
            7. technical_signals: RSI, momentum, breakout patterns from the data
            8. news_catalysts: How recent news supports each trading opportunity
            9. timeline_expectations: Realistic timeframes for each trade
            10. position_sizing_suggestions: Recommended position sizes based on volatility

            **CRITICAL REQUIREMENTS**:
            - All prices must be based on the real-time market data provided
            - Include specific entry prices, not ranges  
            - Calculate realistic targets based on recent price action and volatility
            - Provide exact stop loss levels
            - NEWS DATES: All news data is from TODAY or last 24 hours - these are FRESH, current opportunities
            - SOCIAL DATA: LunarCrush data shows real-time social sentiment and trending coins
            - Justify each trade with technical and fundamental reasoning
            - Ignore any news older than 48 hours
            """

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional trading opportunity scout with expertise in technical analysis, fundamental analysis, and market timing for cryptocurrency markets."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            opportunities = json.loads(response.choices[0].message.content or "{}")
            opportunities['timestamp'] = datetime.now().isoformat()
            opportunities['ai_powered'] = True
            opportunities['analysis_type'] = 'opportunity_scan'
            opportunities['scan_id'] = f"scan_{datetime.now().strftime('%Y%m%d_%H%M')}"
            
            return opportunities

        except Exception as e:
            logger.error(f"Opportunity scanning error: {e}")
            return {
                'error': 'AI opportunity scanning temporarily unavailable',
                'manual_analysis_recommended': True,
                'timestamp': datetime.now().isoformat()
            }

    def scan_degen_opportunities(self, degen_data: Dict) -> Dict:
        """AI-powered degen/memes opportunity scanner for high-risk viral plays"""
        try:
            viral_plays = degen_data.get('viral_plays', {})
            trending_social = degen_data.get('trending_social', [])
            lunarcrush_data = degen_data.get('lunarcrush_data', {})
            
            viral_plays = degen_data.get('viral_plays', {})
            trending_social = degen_data.get('trending_social', [])
            dex_trending = degen_data.get('dex_trending', {})
            major_coins_excluded = degen_data.get('major_coins_excluded', [])
            
            prompt = f"""
            As a degenerate crypto trader expert in NEW LAUNCHES, meme coins, and viral plays, analyze this data for explosive opportunities.

            CRITICAL: IGNORE ALL MAJOR COINS LIKE BTC, ETH, SOL, ADA, MATIC, AVAX, DOT, LINK, UNI, ATOM. 
            Focus ONLY on new tokens, meme coins, micro caps, and viral plays under $100M market cap.

            VIRAL CONTENT & NEWS (New tokens only):
            {json.dumps(viral_plays, indent=2)}

            DEXSCREENER TRENDING (New/Small cap tokens with extracted symbols):
            {self._format_dex_tokens_for_ai(dex_trending)}

            SOCIAL TRENDING (Exclude major coins):
            {json.dumps(trending_social, indent=2)}

            EXCLUDED MAJOR COINS (DO NOT MENTION THESE):
            {json.dumps(major_coins_excluded, indent=2)}

            **STRICT DEGEN FOCUS**: 
            - NEW token launches (less than 30 days old)
            - Meme coins with viral potential 
            - Micro-cap gems under $10M market cap
            - Tokens with explosive social growth
            - DeFi protocol tokens gaining traction
            - Trending on CT (Crypto Twitter)

            Provide JSON analysis with:
            1. viral_opportunities: Top 3 NEW/SMALL tokens with viral potential (NO major coins)
            2. new_launches: Recently launched tokens with momentum
            3. meme_potential: Tokens with meme/viral characteristics
            4. micro_caps: Very small market cap gems
            5. risk_warning: "EXTREME RISK - New tokens can go to zero instantly"
            6. entry_strategy: "Micro positions only - max 0.5% portfolio per token"
            7. timeline: "Hours to days for viral plays"
            8. degen_score: Always 9-10 for new/micro tokens

            **CRITICAL REQUIREMENTS FOR TOKEN NAMES**:
            - NEVER use "Unknown" as a token name
            - Extract actual symbols from descriptions: "you pumpusto" becomes "YOU", "Ocean Beach guy" becomes "OCEAN", "Literally A Retarded Play" becomes "LARP"  
            - For viral_opportunities, provide actual token symbols extracted from descriptions
            - Look for patterns: uppercase words, meaningful terms, brand names in descriptions
            - Use token address first 6 chars as last resort: "DLJ57w" not "Unknown"
            - Focus on NEW launches under $10M market cap only
            - Provide actionable degen intelligence with proper token identification
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",  # the newest OpenAI model is "gpt-4o" which was released May 13, 2024. do not change this unless explicitly requested by the user
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.7  # Slightly higher temperature for creative degen insights
            )
            
            result = json.loads(response.choices[0].message.content)
            result['analysis_type'] = 'degen_opportunities'
            result['timestamp'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"AI degen analysis error: {e}")
            return {
                'error': 'Degen analysis temporarily unavailable',
                'viral_opportunities': ['Check trending Twitter for viral plays'],
                'risk_warning': 'EXTREME RISK: Only invest money you can afford to lose completely',
                'degen_score': 10,
                'manual_review_recommended': True,
                'timestamp': datetime.now().isoformat()
            }
    
    def _format_dex_tokens_for_ai(self, dex_data: Dict) -> str:
        """Format DexScreener tokens with extracted symbols for AI analysis"""
        try:
            formatted_tokens = []
            
            # Process both boosted and top_boosted tokens
            for token_type in ['latest_boosted', 'top_boosted']:
                if token_type in dex_data and dex_data[token_type]:
                    for token in dex_data[token_type][:5]:  # Limit to 5 per type
                        description = token.get('description', '')
                        token_address = token.get('tokenAddress', '')
                        
                        # Extract meaningful token symbol
                        symbol = self._extract_token_symbol(description, token_address)
                        
                        formatted_token = {
                            'symbol': symbol,
                            'description': description[:60],
                            'url': token.get('url', ''),
                            'boost_amount': token.get('amount', 0),
                            'chain': token.get('chainId', 'unknown')
                        }
                        formatted_tokens.append(formatted_token)
            
            return json.dumps(formatted_tokens, indent=2) if formatted_tokens else "No trending tokens available"
            
        except Exception as e:
            return f"Error formatting tokens: {str(e)}"
    
    def _extract_token_symbol(self, description: str, token_address: str) -> str:
        """Extract meaningful token symbol from description or address"""
        import re
        
        if not description and not token_address:
            return "NEW"
            
        description_text = description.upper()
        
        # Pattern matching for common cases
        if 'YOU' in description_text or 'PUMPUSTO' in description_text:
            return 'YOU'
        elif 'OCEAN' in description_text or 'BEACH' in description_text:
            return 'OCEAN'
        elif 'RETARDED' in description_text or 'LARP' in description_text:
            return 'LARP'
        elif 'BELIEVE' in description_text:
            return 'DO'
        
        # Find uppercase words (likely symbols)
        symbol_match = re.search(r'\b([A-Z]{2,8})\b', description_text)
        if symbol_match and symbol_match.group(1) not in ['THE', 'NEW', 'TOKEN', 'COIN', 'VIRAL']:
            return symbol_match.group(1)
        
        # Use token address prefix as fallback
        if token_address and len(token_address) > 6:
            return token_address[:6].upper()
        
        # Use first meaningful word
        words = description.split()
        if words:
            first_word = words[0].upper()[:6]
            return first_word if first_word else 'NEW'
        
        return 'NEW'

# Global instance for use in main_server.py
trading_ai = TradingIntelligence()
