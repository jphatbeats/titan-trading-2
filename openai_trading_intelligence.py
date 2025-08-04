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
        """AI-powered opportunity scanner for new trades"""
        try:
            prompt = f"""
            As an opportunity scout, identify trading opportunities:

            Market Data:
            {json.dumps(market_data, indent=2)}

            Recent News:
            {json.dumps(news_data, indent=2)}

            Identify JSON opportunities with:
            1. high_probability_setups: Best trading setups right now
            2. breakout_candidates: Assets near key breakout levels
            3. value_opportunities: Oversold quality assets
            4. momentum_plays: Assets with strong momentum
            5. news_driven_trades: Opportunities from recent news
            6. risk_reward_analysis: Risk/reward ratio for each opportunity
            7. entry_strategies: Specific entry methods for each
            8. timeline: Expected timeframe for each opportunity
            9. stop_loss_levels: Risk management for each trade

            Rank opportunities by probability of success.
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

# Global instance for use in main_server.py
trading_ai = TradingIntelligence()