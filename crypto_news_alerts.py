#!/usr/bin/env python3
"""
Crypto News Alerts Integration - Updated for Basic Plan
Uses only endpoints available on basic CryptoNews API plan
"""

import requests
from datetime import datetime, timedelta
import os

# CryptoNews API Configuration
API_TOKEN = os.getenv('CRYPTONEWS_API_TOKEN', 'ayimav7nlptgzetysg9dwhqteampvoirtfx5orqk')
BASE_URL = "https://cryptonews-api.com/api/v1"

if not API_TOKEN:
    print("⚠️ Warning: CRYPTONEWS_API_TOKEN not found in secrets")

def get_general_crypto_news(items=100, sentiment=None, source=None, sortby=None, exclude_sources=None, date=None, topic=None, search=None):
    """
    Get general crypto news using PREMIUM API with advanced filtering
    Now supports: date filtering, topic search, keyword search, source filtering
    """
    try:
        # Use premium endpoint with full filtering capabilities
        params = {
            "section": "general",
            "items": min(items, 100),  # Premium allows up to 100
            "page": 1,
            "token": API_TOKEN
        }

        # Apply sentiment filter
        if sentiment:
            params["sentiment"] = sentiment

        # Apply source filters
        if source:
            params["source"] = source
        if exclude_sources:
            params["sourceexclude"] = ",".join(exclude_sources)

        # Apply sorting (premium features)
        if sortby:
            params["sortby"] = sortby

        # NEW PREMIUM FEATURES
        
        # Date filtering (historical news access)
        if date:
            params["date"] = date  # e.g., "last7days", "last30days", "01012024-01312024"

        # Topic filtering
        if topic:
            params["topic"] = topic  # e.g., "Digital Yuan,Libra"

        # Keyword search
        if search:
            params["search"] = search  # e.g., "Congress,Hard Fork"

        # Add extra fields for premium data
        params["extra-fields"] = "id,eventid,rankscore"

        print(f"🔍 Fetching PREMIUM crypto news with advanced filters:")
        print(f"   📊 Items: {items} | Sentiment: {sentiment} | Date: {date}")
        print(f"   🎯 Topic: {topic} | Search: {search} | Sort: {sortby}")

        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Fetched {articles_count} PREMIUM articles with enhanced metadata")

        # Show enhanced article data
        sample_articles = result.get('data', [])[:3]
        for i, article in enumerate(sample_articles):
            print(f"📋 Premium Article {i+1}:")
            print(f"   Title: {article.get('title', 'N/A')[:80]}...")
            print(f"   Source: {article.get('source_name', 'N/A')} | Sentiment: {article.get('sentiment', 'N/A')}")
            print(f"   Rank Score: {article.get('rankscore', 'N/A')} | Event ID: {article.get('eventid', 'N/A')}")
            print(f"   Tickers: {article.get('tickers', [])[:5]}")

        return result
    except Exception as e:
        print(f"❌ Error fetching premium crypto news: {e}")
        return {"data": []}

# ============================================================================
# NEW PREMIUM CRYPTONEWS API ENDPOINTS
# ============================================================================

def get_top_mentioned_tickers(date="last7days", cache=False):
    """Get top 50 most mentioned crypto tickers (PREMIUM ENDPOINT)"""
    try:
        params = {
            "date": date,  # last7days, last30days, etc.
            "token": API_TOKEN
        }

        if not cache:
            params["cache"] = "false"

        print(f"📊 Fetching top mentioned tickers for {date}...")
        response = requests.get(f"{BASE_URL}/top-mention", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"🔥 Found {len(result.get('data', []))} trending tickers")
        return result
    except Exception as e:
        print(f"❌ Error fetching top mentioned tickers: {e}")
        return {"data": []}

def get_sentiment_analysis(tickers=None, section=None, date="last30days"):
    """Get daily sentiment analysis for tickers or sections (PREMIUM ENDPOINT)"""
    try:
        params = {
            "date": date,
            "page": 1,
            "token": API_TOKEN,
            "cache": "false"  # Real-time data
        }

        if tickers:
            params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers
        elif section:
            params["section"] = section  # "alltickers" or "general"

        print(f"📈 Fetching sentiment analysis: tickers={tickers}, section={section}, date={date}")
        response = requests.get(f"{BASE_URL}/stat", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"📊 Sentiment data retrieved for {date} period")
        return result
    except Exception as e:
        print(f"❌ Error fetching sentiment analysis: {e}")
        return {"data": []}

def get_crypto_events(eventid=None, tickers=None, page=1):
    """Get important crypto news events (PREMIUM ENDPOINT)"""
    try:
        params = {
            "page": page,
            "token": API_TOKEN,
            "cache": "false"
        }

        if eventid:
            params["eventid"] = eventid
        if tickers:
            params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers

        print(f"📰 Fetching crypto events: eventid={eventid}, tickers={tickers}")
        response = requests.get(f"{BASE_URL}/events", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        events_count = len(result.get('data', []))
        print(f"🎯 Found {events_count} important crypto events")
        return result
    except Exception as e:
        print(f"❌ Error fetching crypto events: {e}")
        return {"data": []}

def get_trending_headlines(ticker=None, page=1):
    """Get trending crypto headlines - filtered important news (PREMIUM ENDPOINT)"""
    try:
        params = {
            "page": page,
            "token": API_TOKEN
        }

        if ticker:
            params["ticker"] = ticker

        print(f"📈 Fetching trending headlines for ticker: {ticker}")
        response = requests.get(f"{BASE_URL}/trending-headlines", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        headlines_count = len(result.get('data', []))
        print(f"🔥 Found {headlines_count} trending headlines")
        return result
    except Exception as e:
        print(f"❌ Error fetching trending headlines: {e}")
        return {"data": []}

def get_advanced_ticker_news(tickers, mode="any", items=50, sentiment=None, sortby=None, date=None):
    """
    Get advanced ticker news with multiple modes:
    - mode="any": News mentioning ANY of the tickers
    - mode="all": News mentioning ALL tickers  
    - mode="only": News mentioning ONLY specific ticker (tickers must be single string)
    """
    try:
        params = {
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN,
            "extra-fields": "id,eventid,rankscore"
        }

        if isinstance(tickers, list):
            tickers_str = ",".join(tickers)
        else:
            tickers_str = tickers

        # Apply different ticker modes
        if mode == "any":
            params["tickers"] = tickers_str
        elif mode == "all":
            params["tickers-include"] = tickers_str
        elif mode == "only":
            params["tickers-only"] = tickers_str

        # Apply filters
        if sentiment:
            params["sentiment"] = sentiment
        if sortby:
            params["sortby"] = sortby
        if date:
            params["date"] = date

        print(f"🎯 Advanced ticker news: {tickers_str} (mode: {mode})")
        response = requests.get(f"{BASE_URL}", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Found {articles_count} advanced ticker articles")
        return result
    except Exception as e:
        print(f"❌ Error fetching advanced ticker news: {e}")
        return {"data": []}

def get_historical_news(date_range, tickers=None, sentiment=None, items=100):
    """Get historical crypto news with date range (PREMIUM FEATURE)"""
    try:
        params = {
            "date": date_range,  # e.g., "12012023-12312023" or "last30days"
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN,
            "extra-fields": "id,eventid,rankscore"
        }

        if tickers:
            params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers
        if sentiment:
            params["sentiment"] = sentiment

        print(f"📅 Fetching historical news for date range: {date_range}")

        if tickers:
            response = requests.get(f"{BASE_URL}", params=params, timeout=30)
        else:
            params["section"] = "general"
            response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)

        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Found {articles_count} historical articles")
        return result
    except Exception as e:
        print(f"❌ Error fetching historical news: {e}")
        return {"data": []}

def search_crypto_news_by_keywords(keywords, mode="and", items=50, sentiment=None, date=None):
    """
    Search crypto news by keywords (PREMIUM FEATURE)
    - mode="and": All keywords must be present
    - mode="or": Any keyword can be present
    """
    try:
        params = {
            "section": "general",
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN
        }

        if isinstance(keywords, list):
            keywords_str = ",".join(keywords)
        else:
            keywords_str = keywords

        # Apply search mode
        if mode == "and":
            params["search"] = keywords_str
        elif mode == "or":
            params["searchOR"] = keywords_str

        # Apply filters
        if sentiment:
            params["sentiment"] = sentiment
        if date:
            params["date"] = date

        print(f"🔍 Keyword search: '{keywords_str}' (mode: {mode})")
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Found {articles_count} articles matching keywords")
        return result
    except Exception as e:
        print(f"❌ Error searching by keywords: {e}")
        return {"data": []}

def get_all_crypto_tickers_db():
    """Get complete database of all crypto tickers (PREMIUM ENDPOINT - once per day)"""
    try:
        params = {"token": API_TOKEN}

        print("📊 Fetching complete crypto tickers database...")
        response = requests.get(f"{BASE_URL}/account/tickersdbv2", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        tickers_count = len(result.get('data', []))
        print(f"🎯 Retrieved {tickers_count} crypto tickers from database")
        return result
    except Exception as e:
        print(f"❌ Error fetching tickers database: {e}")
        return {"data": []}

def get_news_by_news_id(news_ids):
    """Get specific news articles by their news IDs (PREMIUM ENDPOINT)"""
    try:
        if isinstance(news_ids, list):
            news_ids_str = ",".join(map(str, news_ids))
        else:
            news_ids_str = str(news_ids)

        params = {
            "news_id": news_ids_str,
            "token": API_TOKEN,
            "extra-fields": "id,eventid,rankscore"
        }

        print(f"📰 Fetching news by IDs: {news_ids_str}")
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📋 Retrieved {articles_count} articles by news ID")
        return result
    except Exception as e:
        print(f"❌ Error fetching news by ID: {e}")
        return {"data": []}

def get_news_with_metadata():
    """Get news with metadata explanations (PREMIUM ENDPOINT)"""
    try:
        params = {
            "section": "general",
            "items": 50,
            "page": 1,
            "token": API_TOKEN,
            "metadata": 1  # Enable metadata
        }

        print("📊 Fetching news with metadata...")
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"📋 Retrieved news with metadata explanations")
        return result
    except Exception as e:
        print(f"❌ Error fetching news with metadata: {e}")
        return {"data": []}

def get_news_as_csv(tickers=None, items=50, sentiment=None):
    """Get news data as CSV format (PREMIUM ENDPOINT)"""
    try:
        params = {
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN,
            "datatype": "csv"  # CSV format
        }

        if tickers:
            params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers
        else:
            params["section"] = "general"

        if sentiment:
            params["sentiment"] = sentiment

        print(f"📊 Fetching news as CSV format...")
        
        if tickers:
            response = requests.get(BASE_URL, params=params, timeout=30)
        else:
            response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        
        response.raise_for_status()
        
        print(f"📋 Retrieved CSV data ({len(response.text)} characters)")
        return {"csv_data": response.text, "format": "csv"}
    except Exception as e:
        print(f"❌ Error fetching CSV data: {e}")
        return {"csv_data": "", "error": str(e)}

def get_news_by_source_filtering(include_sources=None, exclude_sources=None, items=50, sentiment=None):
    """Get news filtered by specific sources (PREMIUM ENDPOINT)"""
    try:
        params = {
            "section": "general",
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN
        }

        if include_sources:
            sources_str = ",".join(include_sources) if isinstance(include_sources, list) else include_sources
            params["source"] = sources_str
            print(f"📰 Including sources: {sources_str}")

        if exclude_sources:
            exclude_str = ",".join(exclude_sources) if isinstance(exclude_sources, list) else exclude_sources
            params["sourceexclude"] = exclude_str
            print(f"🚫 Excluding sources: {exclude_str}")

        if sentiment:
            params["sentiment"] = sentiment

        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📋 Retrieved {articles_count} articles with source filtering")
        return result
    except Exception as e:
        print(f"❌ Error fetching filtered news: {e}")
        return {"data": []}

def get_news_by_type_filter(news_type="article", items=50, sentiment=None):
    """Get news filtered by type (article or video) (PREMIUM ENDPOINT)"""
    try:
        params = {
            "section": "general",
            "items": min(items, 100),
            "page": 1,
            "type": news_type,  # "article" or "video"
            "token": API_TOKEN
        }

        if sentiment:
            params["sentiment"] = sentiment

        print(f"📺 Fetching {news_type} news...")
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📋 Retrieved {articles_count} {news_type} items")
        return result
    except Exception as e:
        print(f"❌ Error fetching {news_type} news: {e}")
        return {"data": []}

def get_news_sorted_oldest_first(items=50, tickers=None):
    """Get news sorted by oldest first (PREMIUM ENDPOINT)"""
    try:
        params = {
            "items": min(items, 100),
            "page": 1,
            "sortby": "oldestfirst",
            "token": API_TOKEN
        }

        if tickers:
            params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers
            endpoint = BASE_URL
        else:
            params["section"] = "general"
            endpoint = f"{BASE_URL}/category"

        print(f"📅 Fetching news sorted oldest first...")
        response = requests.get(endpoint, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📋 Retrieved {articles_count} articles (oldest first)")
        return result
    except Exception as e:
        print(f"❌ Error fetching oldest-first news: {e}")
        return {"data": []}

def get_news_with_rank_and_days(tickers, days=3, items=50):
    """Get news sorted by rank for specific number of days (PREMIUM ENDPOINT)"""
    try:
        params = {
            "tickers": ",".join(tickers) if isinstance(tickers, list) else tickers,
            "items": min(items, 100),
            "page": 1,
            "sortby": "rank",
            "days": days,
            "token": API_TOKEN,
            "extra-fields": "rankscore"
        }

        print(f"🎯 Fetching ranked news for {days} days: {params['tickers']}")
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📋 Retrieved {articles_count} ranked articles for {days} days")
        return result
    except Exception as e:
        print(f"❌ Error fetching ranked news: {e}")
        return {"data": []}

def get_multiple_pages_news(pages=3, items_per_page=50, tickers=None):
    """Get multiple pages of news (PREMIUM ENDPOINT - up to 5 pages)"""
    try:
        all_articles = []
        
        for page in range(1, min(pages + 1, 6)):  # Max 5 pages for basic plans
            params = {
                "items": min(items_per_page, 100),
                "page": page,
                "token": API_TOKEN
            }

            if tickers:
                params["tickers"] = ",".join(tickers) if isinstance(tickers, list) else tickers
                endpoint = BASE_URL
            else:
                params["section"] = "general"
                endpoint = f"{BASE_URL}/category"

            print(f"📄 Fetching page {page}...")
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            page_articles = result.get('data', [])
            all_articles.extend(page_articles)
            print(f"📋 Page {page}: {len(page_articles)} articles")

            if len(page_articles) < items_per_page:
                print(f"📄 Reached end of results at page {page}")
                break

        print(f"📚 Total articles collected: {len(all_articles)}")
        return {"data": all_articles, "total_pages": page, "total_articles": len(all_articles)}
    except Exception as e:
        print(f"❌ Error fetching multiple pages: {e}")
        return {"data": [], "error": str(e)}

def get_premium_source_news_enhanced(premium_only=True, items=50, sentiment=None):
    """Get news from premium sources with enhanced filtering (PREMIUM ENDPOINT)"""
    try:
        # Enhanced premium sources list
        premium_sources = [
            "Bloomberg+Markets+and+Finance", "Bloomberg+Technology", "CNBC", "CNBC+Television",
            "CNN", "Reuters", "Forbes", "Business+Insider", "Yahoo+Finance",
            "Coindesk", "Cointelegraph", "The+Block", "Decrypt", "CryptoSlate"
        ]

        regular_sources = [
            "NewsBTC", "Bitcoinist", "CryptoPotato", "Cryptopolitan", "AMBCrypto",
            "BeInCrypto", "CoinMarketCap", "Coingape", "UToday", "The+Daily+Hodl"
        ]

        sources_to_use = premium_sources if premium_only else premium_sources + regular_sources

        params = {
            "section": "general",
            "source": ",".join(sources_to_use),
            "items": min(items, 100),
            "sortby": "rank",
            "token": API_TOKEN,
            "extra-fields": "rankscore"
        }

        if sentiment:
            params["sentiment"] = sentiment

        source_type = "premium" if premium_only else "all"
        print(f"🏆 Fetching {source_type} source news from {len(sources_to_use)} sources...")
        
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Retrieved {articles_count} {source_type} articles")
        return result
    except Exception as e:
        print(f"❌ Error fetching premium source news: {e}")
        return {"data": []}


        # Date filtering (historical news access)
        if date:
            params["date"] = date  # e.g., "last7days", "last30days", "01012024-01312024"

        # Topic filtering
        if topic:
            params["topic"] = topic  # e.g., "Digital Yuan,Libra"

        # Keyword search
        if search:
            params["search"] = search  # e.g., "Congress,Hard Fork"

        # Add extra fields for premium data
        params["extra-fields"] = "id,eventid,rankscore"

        print(f"🔍 Fetching PREMIUM crypto news with advanced filters:")
        print(f"   📊 Items: {items} | Sentiment: {sentiment} | Date: {date}")
        print(f"   🎯 Topic: {topic} | Search: {search} | Sort: {sortby}")

        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        articles_count = len(result.get('data', []))
        print(f"📰 Fetched {articles_count} PREMIUM articles with enhanced metadata")

        # Show enhanced article data
        sample_articles = result.get('data', [])[:3]
        for i, article in enumerate(sample_articles):
            print(f"📋 Premium Article {i+1}:")
            print(f"   Title: {article.get('title', 'N/A')[:80]}...")
            print(f"   Source: {article.get('source_name', 'N/A')} | Sentiment: {article.get('sentiment', 'N/A')}")
            print(f"   Rank Score: {article.get('rankscore', 'N/A')} | Event ID: {article.get('eventid', 'N/A')}")
            print(f"   Tickers: {article.get('tickers', [])[:5]}")

        return result
    except Exception as e:
        print(f"❌ Error fetching premium crypto news: {e}")
        return {"data": []}
    except Exception as e:
        print(f"❌ Error fetching premium crypto news: {e}")
        return {"data": []}

def get_premium_source_news(items=50, sentiment=None, sources=None):
    """Get news from premium sources like CNBC, Reuters, Bloomberg (API example 6)"""
    try:
        # Premium sources based on API examples
        premium_sources = sources or [
            "cnbc.com", "reuters.com", "bloomberg.com", "coindesk.com", 
            "cointelegraph.com", "decrypt.co", "theblock.co"
        ]

        params = {
            "section": "general",
            "source": ",".join(premium_sources),
            "items": min(items, 100),
            "sortby": "rank",  # Quality sorting
            "token": API_TOKEN
        }

        if sentiment:
            params["sentiment"] = sentiment

        print(f"🏆 Fetching premium source news from: {premium_sources[:3]}...")
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"📰 Found {len(result.get('data', []))} premium articles")
        return result
    except Exception as e:
        print(f"❌ Error fetching premium source news: {e}")
        return {"data": []}

def get_news_by_tickers(tickers, sentiment=None, type_=None, items=50, sortby=None):
    """Fetch news by specific tickers with optional filters"""
    try:
        params = {
            "tickers": ",".join(tickers),
            "items": min(items, 200),  # Full subscription allows more items
            "token": API_TOKEN
        }
        if sentiment:
            params["sentiment"] = sentiment
        if type_:
            params["type"] = type_
        if sortby:
            params["sortby"] = sortby

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching news by tickers: {e}")
        return {"data": []}

def get_news_tickers_include(tickers, items=50):
    """Get news that includes ALL specified tickers"""
    try:
        params = {
            "tickers-include": ",".join(tickers),
            "items": min(items, 200),
            "token": API_TOKEN
        }

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error fetching news with tickers-include: {e}")
        return {"data": []}

def get_news_tickers_only(ticker, items=50, sortby="rank"):
    """Get news that mentions ONLY the specified ticker using EXACT API pattern from your example"""
    try:
        # Use EXACT pattern from your example: tickers-only=BTC&items=3&page=1&token=...
        params = {
            "tickers-only": ticker,
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN
        }

        print(f"🎯 Getting exclusive news for {ticker} (exact example pattern)")
        print(f"🔍 URL: {BASE_URL}?tickers-only={ticker}&items={params['items']}&page=1&token=...")
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        print(f"📰 Found {len(result.get('data', []))} exclusive {ticker} articles")
        return result
    except Exception as e:
        print(f"❌ Error fetching news with tickers-only: {e}")
        return {"data": []}

def get_portfolio_symbols():
    """Extract symbols from latest positions CSV"""
    try:
        csv_files = glob.glob("positions_*.csv")
        if not csv_files:
            print("❌ No positions CSV files found")
            return []

        latest_file = max(csv_files, key=lambda x: os.path.getmtime(x))
        df = pd.read_csv(latest_file)

        # Filter out summary rows
        df_filtered = df[df['Platform'].notna() & (df['Platform'] != 'PORTFOLIO SUMMARY')]

        # Extract and clean symbols
        symbols = []
        for symbol in df_filtered['Symbol'].dropna():
            # Clean symbols - remove USDT, -USDT, /USDT:USDT etc.
            clean_symbol = str(symbol).upper()
            clean_symbol = clean_symbol.replace('-USDT', '').replace('USDT', '')
            clean_symbol = clean_symbol.replace('/USDT:USDT', '').replace(':USDT', '')
            clean_symbol = clean_symbol.split('/')[0]  # Take first part if still has /

            if clean_symbol and len(clean_symbol) <= 10:  # Valid crypto symbol
                symbols.append(clean_symbol)

        unique_symbols = list(set(symbols))
        print(f"📊 Found {len(unique_symbols)} unique symbols: {unique_symbols}")
        return unique_symbols

    except Exception as e:
        print(f"❌ Error extracting symbols: {e}")
        return []

def extract_trending_symbols_from_news(news_data, exclude_symbols=None):
    """Extract trending symbols from news data since we can't use premium endpoints"""
    if exclude_symbols is None:
        exclude_symbols = []

    symbol_counts = {}

    for article in news_data.get("data", []):
        tickers = article.get("tickers", [])
        for ticker in tickers:
            if ticker not in exclude_symbols:
                symbol_counts[ticker] = symbol_counts.get(ticker, 0) + 1

    # Sort by mentions
    trending = [symbol for symbol, count in sorted(symbol_counts.items(), key=lambda x: x[1], reverse=True)]
    return trending[:15]  # Top 15

def analyze_market_opportunities(news_data, exclude_symbols=None):
    """Analyze news for trading opportunities beyond current portfolio"""
    if exclude_symbols is None:
        exclude_symbols = []

    opportunities = []

    # Opportunity keywords
    OPPORTUNITY_SIGNALS = [
        "LISTING", "NEW LISTING", "LISTED ON", "TRADING BEGINS",
        "PARTNERSHIP", "COLLABORATION", "INTEGRATION", "ALLIANCE",
        "INSTITUTIONAL", "INVESTMENT", "BACKING", "FUNDING",
        "LAUNCH", "UPGRADE", "PROTOCOL", "MAINNET",
        "ADOPTION", "GOVERNMENT", "REGULATION APPROVAL",
        "BULLISH", "SURGE", "RALLY", "BREAKOUT"
    ]

    RISK_SIGNALS = [
        "HACK", "EXPLOIT", "VULNERABILITY", "BREACH",
        "SCAM", "RUG", "FRAUD", "INVESTIGATION",
        "LAWSUIT", "SEC", "REGULATION", "BAN",
        "DELIST", "SUSPEND", "HALT", "CRASH"
    ]

    for article in news_data.get("data", []):
        title = article.get("title", "").upper()
        text = article.get("text", "").upper()
        content = f"{title} {text}"

        # Extract tickers mentioned
        tickers = article.get("tickers", [])

        for ticker in tickers:
            if ticker in exclude_symbols:
                continue

            # Check for opportunity signals
            opportunity_matches = [signal for signal in OPPORTUNITY_SIGNALS if signal in content]
            risk_matches = [signal for signal in RISK_SIGNALS if signal in content]

            if opportunity_matches:
                confidence = min(len(opportunity_matches) * 20 + 40, 95)
                opportunities.append({
                    'type': 'opportunity',
                    'symbol': ticker,
                    'confidence_score': confidence,
                    'signals': opportunity_matches,
                    'title': article.get('title', ''),
                    'url': article.get('news_url', ''),
                    'source': article.get('source_name', ''),
                    'sentiment': article.get('sentiment', 'neutral'),
                    'time_sensitivity': 'high' if confidence > 70 else 'medium',
                    'in_portfolio': False
                })

            if risk_matches:
                confidence = min(len(risk_matches) * 25 + 50, 95)
                opportunities.append({
                    'type': 'risk',
                    'symbol': ticker,
                    'confidence_score': confidence,
                    'signals': risk_matches,
                    'title': article.get('title', ''),
                    'url': article.get('news_url', ''),
                    'source': article.get('source_name', ''),
                    'sentiment': article.get('sentiment', 'neutral'),
                    'time_sensitivity': 'immediate' if confidence > 80 else 'high',
                    'in_portfolio': False
                })

    # Sort by confidence
    opportunities.sort(key=lambda x: x['confidence_score'], reverse=True)
    return opportunities[:20]  # Top 20 opportunities

def alert_narrative_confluence(portfolio_symbols, news_feed):
    """Match live portfolio positions with news articles"""
    alerts = []

    for article in news_feed.get("data", []):
        title = article.get("title", "").upper()
        text = article.get("text", "").upper()
        tickers = article.get("tickers", [])

        # Check both content and ticker array
        for symbol in portfolio_symbols:
            if symbol in title or symbol in text or symbol in tickers:
                alerts.append({
                    "symbol": symbol,
                    "title": article["title"],
                    "published": article.get("date", ""),
                    "sentiment": article.get("sentiment", "neutral"),
                    "source": article.get("source_name", "unknown"),
                    "url": article.get("news_url", ""),
                    "text_preview": article.get("text", "")[:200] + "..." if article.get("text") else "",
                    "in_portfolio": True
                })

    return alerts

def filter_bearish_flags(news_feed):
    """Detect FUD/risk signals in news"""
    FUD_FLAGS = ["RUG", "EXPLOIT", "HACK", "VULNERABILITY", "DELIST", "SCAM", "SUSPEND", "INVESTIGATION", "SEC", "LAWSUIT", "BAN", "ILLEGAL", "FRAUD", "BREACH"]
    red_flags = []

    for article in news_feed.get("data", []):
        content = (article.get("title", "") + " " + article.get("text", "")).upper()
        matched_flags = [flag for flag in FUD_FLAGS if flag in content]

        if matched_flags:
            red_flags.append({
                "title": article.get("title", ""),
                "date": article.get("date", ""),
                "url": article.get("news_url", ""),
                "matched_flags": matched_flags,
                "sentiment": article.get("sentiment", "neutral"),
                "source": article.get("source_name", "unknown"),
                "tickers": article.get("tickers", [])
            })

    return red_flags

def filter_bullish_signals(news_feed):
    """Detect positive news signals with expanded keyword matching"""
    BULLISH_FLAGS = [
        "PARTNERSHIP", "INTEGRATION", "ADOPTION", "UPGRADE", "LAUNCH", "LISTING", 
        "INSTITUTIONAL", "INVESTMENT", "BACKING", "SUPPORT", "APPROVAL", "ALLIANCE", 
        "COLLABORATION", "ANNOUNCE", "ANNOUNCED", "ANNOUNCES", "BREAKOUT", "RALLY",
        "SURGE", "PUMP", "MOON", "BULLISH", "BUY", "BUYING", "BOUGHT", "ACQUIRE",
        "ACQUISITION", "MERGE", "MERGER", "FUND", "FUNDING", "RAISED", "RAISE",
        "TOKENIZE", "MAINNET", "TESTNET", "STAKING", "YIELD", "APY", "REWARDS",
        "GOVERNANCE", "VOTING", "PROTOCOL", "ECOSYSTEM", "EXPANSION", "GROWING",
        "GROWTH", "INNOVATIVE", "INNOVATION", "BREAKTHROUGH", "MILESTONE",
        "CELEBRITY", "INFLUENCER", "ENDORSEMENT", "ENDORSED", "POSITIVE"
    ]
    bullish_signals = []

    for article in news_feed.get("data", []):
        title = article.get("title", "").upper()
        text = article.get("text", "").upper()
        content = f"{title} {text}"

        # More flexible matching - check for any bullish keywords
        matched_flags = []
        for flag in BULLISH_FLAGS:
            if flag in content:
                matched_flags.append(flag)

        # Also check sentiment directly
        sentiment = article.get("sentiment", "").lower()
        if sentiment == "positive":
            matched_flags.append("POSITIVE_SENTIMENT")

        # If we found any signals OR positive sentiment, include it
        if matched_flags or sentiment == "positive":
            bullish_signals.append({
                "title": article.get("title", ""),
                "date": article.get("date", ""),
                "url": article.get("news_url", ""),
                "matched_flags": matched_flags if matched_flags else ["POSITIVE_SENTIMENT"],
                "sentiment": article.get("sentiment", "neutral"),
                "source": article.get("source_name", "unknown"),
                "tickers": article.get("tickers", [])
            })

    print(f"🔍 Bullish Analysis: Found {len(bullish_signals)} bullish signals from {len(news_feed.get('data', []))} articles")
    return bullish_signals

def get_comprehensive_crypto_intelligence():
    """
    MAIN FUNCTION: Get both portfolio alerts AND general market intelligence
    Using PREMIUM endpoints - FULL FEATURED VERSION with advanced analytics
    """
    try:
        print("\n🎯 COMPREHENSIVE CRYPTO INTELLIGENCE (Full Subscription - Enhanced)")
        print("=" * 80)

        # Define confidence thresholds for different alert types (OPTIMIZED)
        HIGH_CONFIDENCE_THRESHOLD = 80  # Higher bar for quality
        MEDIUM_CONFIDENCE_THRESHOLD = 65  # Slightly higher
        PORTFOLIO_CONFLUENCE_THRESHOLD = 60  # Very high sensitivity for portfolio mentions

        # Get portfolio symbols
        portfolio_symbols = get_portfolio_symbols()
        print(f"📊 Portfolio contains {len(portfolio_symbols)} symbols: {portfolio_symbols[:10]}{'...' if len(portfolio_symbols) > 10 else ''}")

        # 1. PORTFOLIO-SPECIFIC NEWS ANALYSIS
        portfolio_alerts = []
        portfolio_news_summary = {"total_articles": 0, "positive": 0, "negative": 0, "neutral": 0}

        if portfolio_symbols:
            print(f"\n📰 PORTFOLIO NEWS ANALYSIS")
            print("-" * 50)
            print(f"🔍 Analyzing news for {len(portfolio_symbols)} portfolio symbols...")

            portfolio_news = get_news_by_tickers(portfolio_symbols, items=150)
            portfolio_news_summary["total_articles"] = len(portfolio_news.get('data', []))

            # Count sentiments
            for article in portfolio_news.get('data', []):
                sentiment = article.get('sentiment', 'neutral').lower()
                if sentiment == 'positive':
                    portfolio_news_summary["positive"] += 1
                elif sentiment == 'negative':
                    portfolio_news_summary["negative"] += 1
                else:
                    portfolio_news_summary["neutral"] += 1

            print(f"📊 Portfolio News Summary:")
            print(f"   📈 Total Articles: {portfolio_news_summary['total_articles']}")
            print(f"   ✅ Positive: {portfolio_news_summary['positive']}")
            print(f"   ❌ Negative: {portfolio_news_summary['negative']}")
            print(f"   ⚪ Neutral: {portfolio_news_summary['neutral']}")

            confluence_alerts = alert_narrative_confluence(portfolio_symbols, portfolio_news)
            print(f"🎯 Portfolio Confluence Alerts: {len(confluence_alerts)}")

            for alert in confluence_alerts:
                portfolio_alerts.append({
                    'alert_type': 'portfolio_news',
                    'symbol': alert['symbol'],
                    'in_portfolio': True,
                    'title': alert['title'],
                    'sentiment': alert['sentiment'],
                    'source': alert['source'],
                    'url': alert['url'],
                    'urgency': 'high' if alert['sentiment'] == 'negative' else 'medium',
                    'opportunity_score': 75 if alert['sentiment'] == 'positive' else 25,
                    'message': f"📰 {alert['symbol']} PORTFOLIO ALERT: {alert['sentiment'].upper()} - {alert['title'][:60]}...",
                    'keywords': [alert['sentiment']],
                    'time_window': 'immediate',
                    'text_preview': alert.get('text_preview', ''),
                    'published': alert.get('published', '')
                })

                # Show sample alerts
                if len(portfolio_alerts) <= 5:
                    print(f"   📋 {alert['symbol']}: {alert['sentiment'].upper()} - {alert['title'][:80]}...")

        # 2. PREMIUM MARKET-WIDE INTELLIGENCE GATHERING
        print(f"\n🌐 PREMIUM MARKET-WIDE INTELLIGENCE SCAN")
        print("-" * 50)
        print("🔍 Using PREMIUM endpoints for comprehensive market analysis...")

        # Chicago timezone info
        chicago_tz = pytz.timezone('America/Chicago')
        current_chicago_time = datetime.now(chicago_tz).strftime('%Y-%m-%d %H:%M:%S CST')
        print(f"🕐 Chicago Time: {current_chicago_time}")

        # PREMIUM: Get trending headlines for immediate opportunities
        trending_headlines = get_trending_headlines()
        print(f"🔥 Trending Headlines: {len(trending_headlines.get('data', []))} important headlines")

        # PREMIUM: Get top mentioned tickers for momentum analysis
        top_mentioned = get_top_mentioned_tickers(date="last7days")
        print(f"📊 Top Mentioned Tickers: {len(top_mentioned.get('data', []))} trending symbols")

        # PREMIUM: Get comprehensive market news with rank sorting
        general_news = get_general_crypto_news(items=100, sortby="rank", date="last7days")
        market_news_count = len(general_news.get('data', []))
        print(f"📰 Market News Collected: {market_news_count} premium articles (rank-sorted)")

        # PREMIUM: Get crypto events for major market catalysts
        crypto_events = get_crypto_events()
        print(f"🎯 Crypto Events: {len(crypto_events.get('data', []))} major market events")

        # PREMIUM: Get sentiment analysis for market mood
        market_sentiment = get_sentiment_analysis(section="general", date="last7days")
        print(f"📈 Market Sentiment Data: {len(market_sentiment.get('data', []))} sentiment points")

        # Apply AI-recommended layered approach
        print("🔄 Applying AI layered discovery approach...")

        # Layer 1: Discover new opportunities using AI pattern
        ai_opportunities = discover_new_opportunities_ai_pattern()
        print(f"   🚀 AI Opportunity Discovery: {len(ai_opportunities)} high-impact opportunities")

        # Layer 2: Monitor existing positions using AI pattern  
        ai_position_alerts = monitor_existing_positions_ai_pattern()
        print(f"   📊 AI Position Monitoring: {len(ai_position_alerts)} portfolio alerts")

        # Layer 3: Search for high-impact catalysts
        ai_catalysts = search_for_catalysts()
        print(f"   🎯 AI Catalyst Detection: {len(ai_catalysts)} catalyst matches")

        # Sample trending topics from headlines
        trending_keywords = {}
        for article in general_news.get('data', [])[:50]:  # Sample first 50
            title_words = article.get('title', '').upper().split()
            for word in title_words:
                if len(word) > 4 and word.isalpha():  # Filter meaningful words
                    trending_keywords[word] = trending_keywords.get(word, 0) + 1

        top_trending = sorted(trending_keywords.items(), key=lambda x: x[1], reverse=True)[:8]
        print(f"🔥 Trending Keywords: {[f'{word}({count})' for word, count in top_trending]}")

        # 3. ADVANCED OPPORTUNITY ANALYSIS
        print(f"\n🚀 OPPORTUNITY DISCOVERY ENGINE")
        print("-" * 50)

        # 3. ADVANCED OPPORTUNITY ANALYSIS (beyond current portfolio)
        print("🎯 Analyzing market opportunities (excluding current portfolio)...")
        market_opportunities = analyze_market_opportunities(general_news, exclude_symbols=portfolio_symbols)
        high_confidence_ops = [op for op in market_opportunities if op['confidence_score'] >= 75]
        medium_confidence_ops = [op for op in market_opportunities if 50 <= op['confidence_score'] < 75]

        print(f"   🔥 HIGH Confidence Opportunities: {len(high_confidence_ops)}")
        print(f"   📈 MEDIUM Confidence Opportunities: {len(medium_confidence_ops)}")

        # Show top opportunities
        for i, op in enumerate(high_confidence_ops[:3]):
            print(f"   #{i+1} {op['symbol']}: {op['confidence_score']}% - {', '.join(op['signals'][:2])}")

        # 4. COMPREHENSIVE RISK DETECTION (market-wide)
        print("⚠️ Scanning for market risks and threats...")
        risk_alerts = filter_bearish_flags(general_news)
        critical_risks = [risk for risk in risk_alerts if any(flag in ['HACK', 'EXPLOIT', 'SCAM', 'RUG'] for flag in risk['matched_flags'])]
        regulatory_risks = [risk for risk in risk_alerts if any(flag in ['SEC', 'REGULATION', 'BAN', 'INVESTIGATION'] for flag in risk['matched_flags'])]

        print(f"   🚨 CRITICAL Security Risks: {len(critical_risks)}")
        print(f"   📋 Regulatory Risks: {len(regulatory_risks)}")
        print(f"   ⚠️ Total Risk Alerts: {len(risk_alerts)}")

        # Show critical risks
        for i, risk in enumerate(critical_risks[:2]):
            affected_symbols = ', '.join(risk.get('tickers', ['GENERAL'])[:3])
            print(f"   🚨 CRITICAL: {affected_symbols} - {', '.join(risk['matched_flags'][:2])}")

        # 5. BULLISH CATALYST DETECTION (market-wide)
        print("💰 Detecting bullish catalysts and positive developments...")
        bullish_catalysts = filter_bullish_signals(general_news)
        institutional_signals = [signal for signal in bullish_catalysts if any(flag in ['INSTITUTIONAL', 'INVESTMENT', 'BACKING', 'FUNDING'] for flag in signal['matched_flags'])]
        partnership_signals = [signal for signal in bullish_catalysts if any(flag in ['PARTNERSHIP', 'COLLABORATION', 'INTEGRATION'] for flag in signal['matched_flags'])]

        print(f"   💰 Institutional Signals: {len(institutional_signals)}")
        print(f"   🤝 Partnership Signals: {len(partnership_signals)}")
        print(f"   📈 Total Bullish Catalysts: {len(bullish_catalysts)}")

        # Show top bullish signals
        for i, signal in enumerate(bullish_catalysts[:3]):
            affected_symbols = ', '.join(signal.get('tickers', ['GENERAL'])[:2])
            print(f"   💰 BULLISH: {affected_symbols} - {', '.join(signal['matched_flags'][:2])}")

        # 6. TRENDING SYMBOL DISCOVERY (extracted from news analysis)
        print("📊 Extracting trending symbols from market analysis...")
        trending_symbols = extract_trending_symbols_from_news(general_news, exclude_symbols=portfolio_symbols)
        new_trending = trending_symbols[:10]  # Top 10 new trending

        print(f"   🔥 NEW Trending Symbols: {new_trending}")

        # Advanced trending analysis
        trending_with_sentiment = []
        for symbol in new_trending:
            symbol_articles = [art for art in general_news.get('data', []) if symbol in art.get('tickers', [])]
            positive_count = len([art for art in symbol_articles if art.get('sentiment') == 'positive'])
            total_count = len(symbol_articles)
            sentiment_ratio = (positive_count / total_count * 100) if total_count > 0 else 0

            trending_with_sentiment.append({
                'symbol': symbol,
                'mentions': total_count,
                'positive_sentiment_ratio': round(sentiment_ratio, 1)
            })

        print("   📊 Trending Symbol Analysis:")
        for trend in trending_with_sentiment[:5]:
            print(f"      {trend['symbol']}: {trend['mentions']} mentions, {trend['positive_sentiment_ratio']}% positive")

        # 7. COMPILE ALL INTELLIGENCE
        all_intelligence = []

        # Add portfolio alerts
        all_intelligence.extend(portfolio_alerts)

        # Add market opportunities
        for opp in market_opportunities:
            all_intelligence.append({
                'alert_type': 'new_opportunity' if opp['type'] == 'opportunity' else 'market_risk',
                'symbol': opp['symbol'],
                'in_portfolio': False,
                'title': opp['title'],
                'sentiment': opp['sentiment'],
                'source': opp['source'],
                'url': opp['url'],
                'urgency': opp['time_sensitivity'],
                'opportunity_score': opp['confidence_score'],
                'message': f"🚀 NEW OPPORTUNITY: {opp['symbol']} - {', '.join(opp['signals'][:2])}" if opp['type'] == 'opportunity' else f"⚠️ MARKET RISK: {opp['symbol']} - {', '.join(opp['signals'][:2])}",
                'keywords': opp['signals'],
                'time_window': f"{opp['time_sensitivity']} priority"
            })

        # Add breaking events
        for risk in risk_alerts[:10]:  # Top 10 risk events
            all_intelligence.append({
                'alert_type': 'breaking_event',
                'symbol': risk.get('tickers', ['GENERAL'])[0] if risk.get('tickers') else 'GENERAL',
                'in_portfolio': False,
                'title': risk['title'],
                'sentiment': risk['sentiment'],
                'source': risk['source'],
                'url': risk['url'],
                'urgency': 'high',
                'opportunity_score': 0,
                'message': f"🚨 BREAKING: {', '.join(risk['matched_flags'][:2])} detected",
                'keywords': risk['matched_flags'],
                'time_window': 'immediate'
            })

        for bullish in bullish_catalysts[:10]:  # Top 10 bullish events
            all_intelligence.append({
                'alert_type': 'bullish_catalyst',
                'symbol': bullish.get('tickers', ['GENERAL'])[0] if bullish.get('tickers') else 'GENERAL',
                'in_portfolio': False,
                'title': bullish['title'],
                'sentiment': bullish['sentiment'],
                'source': bullish['source'],
                'url': bullish['url'],
                'urgency': 'medium',
                'opportunity_score': 75,
                'message': f"💰 BULLISH: {', '.join(bullish['matched_flags'][:2])} detected",
                'keywords': bullish['matched_flags'],
                'time_window': '24-48 hours'
            })

        # 8. ADVANCED MARKET PULSE CALCULATION
        print(f"\n📊 MARKET PULSE ANALYSIS")
        print("-" * 50)

        total_articles = len(general_news.get("data", []))
        positive_articles = len([a for a in general_news.get("data", []) if a.get('sentiment') == 'positive'])
        negative_articles = len([a for a in general_news.get("data", []) if a.get('sentiment') == 'negative'])
        neutral_articles = total_articles - positive_articles - negative_articles

        # Enhanced sentiment analysis
        positive_ratio = (positive_articles / total_articles * 100) if total_articles > 0 else 0
        negative_ratio = (negative_articles / total_articles * 100) if total_articles > 0 else 0
        neutral_ratio = (neutral_articles / total_articles * 100) if total_articles > 0 else 0

        overall_sentiment = 'neutral'
        sentiment_confidence = 'low'

        if positive_articles > negative_articles * 1.5:
            overall_sentiment = 'bullish'
            sentiment_confidence = 'high' if positive_ratio > 40 else 'medium'
        elif negative_articles > positive_articles * 1.5:
            overall_sentiment = 'bearish'
            sentiment_confidence = 'high' if negative_ratio > 40 else 'medium'
        elif abs(positive_articles - negative_articles) <= 3:
            overall_sentiment = 'neutral'
            sentiment_confidence = 'high'

        # Enhanced opportunity level calculation
        opportunity_level = 'medium'
        opportunity_confidence = 'medium'

        high_conf_ops = len([op for op in market_opportunities if op['confidence_score'] >= 75])
        total_ops = len(market_opportunities)

        if high_conf_ops > 8 or total_ops > 15:
            opportunity_level = 'high'
            opportunity_confidence = 'high'
        elif high_conf_ops < 2 or total_ops < 5:
            opportunity_level = 'low'
            opportunity_confidence = 'high'

        # Calculate risk level
        critical_risk_count = len(critical_risks)
        total_risk_count = len(risk_alerts)

        risk_level = 'low'
        if critical_risk_count > 3 or total_risk_count > 15:
            risk_level = 'high'
        elif critical_risk_count > 1 or total_risk_count > 8:
            risk_level = 'medium'

        print(f"📊 Market Sentiment Analysis:")
        print(f"   📈 Positive: {positive_articles} articles ({positive_ratio:.1f}%)")
        print(f"   📉 Negative: {negative_articles} articles ({negative_ratio:.1f}%)")
        print(f"   ⚪ Neutral: {neutral_articles} articles ({neutral_ratio:.1f}%)")
        print(f"   🎯 Overall: {overall_sentiment.upper()} (confidence: {sentiment_confidence})")

        print(f"\n🎲 Opportunity & Risk Assessment:")
        print(f"   🚀 Opportunity Level: {opportunity_level.upper()} ({total_ops} total, {high_conf_ops} high-confidence)")
        print(f"   ⚠️ Risk Level: {risk_level.upper()} ({total_risk_count} total risks, {critical_risk_count} critical)")

        # 9. COMPREHENSIVE FINAL SUMMARY
        intelligence_categories = {
            'portfolio_confluence': len([a for a in all_intelligence if a['alert_type'] == 'portfolio_news']),
            'market_opportunities': len([a for a in all_intelligence if a['alert_type'] == 'new_opportunity']),
            'risk_alerts': len([a for a in all_intelligence if a['alert_type'] in ['market_risk', 'breaking_event']]),
            'bullish_catalysts': len([a for a in all_intelligence if a['alert_type'] == 'bullish_catalyst']),
            'trending_coins': len(trending_symbols),
            'breaking_events': len([a for a in all_intelligence if a['alert_type'] == 'breaking_event'])
        }

        print(f"\n🎯 COMPREHENSIVE INTELLIGENCE SUMMARY")
        print("=" * 80)
        print(f"📊 DATA COLLECTION:")
        print(f"   📰 Total Market Articles: {total_articles}")
        print(f"   📈 Portfolio Articles: {portfolio_news_summary['total_articles']}")
        print(f"   🔍 Analysis Depth: COMPREHENSIVE")

        print(f"\n📋 INTELLIGENCE BREAKDOWN:")
        print(f"   🎯 Portfolio Confluence Alerts: {intelligence_categories['portfolio_confluence']}")
        print(f"   🚀 NEW Market Opportunities: {intelligence_categories['market_opportunities']}")
        print(f"   ⚠️ Risk & Threat Alerts: {intelligence_categories['risk_alerts']}")
        print(f"   💰 Bullish Market Catalysts: {intelligence_categories['bullish_catalysts']}")
        print(f"   📈 Trending Symbols Discovered: {intelligence_categories['trending_coins']}")
        print(f"   🔥 Breaking Market Events: {intelligence_categories['breaking_events']}")

        print(f"\n🎯 KEY MARKET INSIGHTS:")
        print(f"   📊 Market Sentiment: {overall_sentiment.upper()} ({sentiment_confidence} confidence)")
        print(f"   🎲 Opportunity Level: {opportunity_level.upper()}")
        print(f"   ⚠️ Risk Level: {risk_level.upper()}")
        print(f"   🔥 Hot Sectors: {', '.join([word for word, count in top_trending[:3]])}")

        # Action recommendations
        print(f"\n💡 STRATEGIC RECOMMENDATIONS:")
        if overall_sentiment == 'bullish' and opportunity_level == 'high':
            print("   ✅ AGGRESSIVE: Strong bullish signals - consider new positions")
        elif overall_sentiment == 'bearish' or risk_level == 'high':
            print("   🛡️ DEFENSIVE: High risk environment - protect positions")
        elif opportunity_level == 'high':
            print("   🎯 SELECTIVE: Good opportunities available - be strategic")
        else:
            print("   ⚖️ BALANCED: Mixed signals - maintain current strategy")

        if len(portfolio_alerts) > 5:
            print("   📰 MONITOR: High portfolio news activity - stay alert")
        if len(critical_risks) > 0:
            print("   🚨 URGENT: Critical security risks detected - review holdings")

        print("=" * 80)

        return {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': len(all_intelligence),
            'intelligence_categories': intelligence_categories,
            'market_intelligence': all_intelligence,
            'trending_symbols': trending_symbols,
            'market_pulse': {
                'overall_sentiment': overall_sentiment,
                'opportunity_level': opportunity_level,
                'risk_level': 'high' if len(risk_alerts) > 5 else 'medium',
                'top_trending_topics': list(set([keyword for alert in all_intelligence for keyword in alert.get('keywords', [])]))[:10]
            }
        }

    except Exception as e:
        print(f"❌ Error generating comprehensive intelligence: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': 0,
            'intelligence_categories': {},
            'market_intelligence': [],
            'trending_symbols': [],
            'market_pulse': {},
            'error': str(e)
        }

# Optimized functions for basic plan based on CryptoNews AI recommendations
def get_breaking_news_optimized(hours=6, items=100, sentiment=None):
    """
    Get breaking news using the EXACT API pattern from your examples
    Uses: /api/v1/category?section=general&items=3&page=1&token=...
    """
    try:
        print(f"🔥 Breaking News (Example Pattern): {hours}h window, {items} items, sentiment={sentiment}")

        # Use EXACT pattern from your example
        params = {
            "section": "general",
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN,
            "sortby": "rank"  # Get most important news first
        }

        # Add sentiment filter if specified
        if sentiment:
            params["sentiment"] = sentiment

        print(f"🔍 API Parameters (exact example pattern): {params}")
        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        breaking_news = []
        chicago_tz = pytz.timezone('America/Chicago')
        current_time = datetime.now(chicago_tz)
        cutoff_time = current_time - timedelta(hours=hours)

        for article in result.get('data', []):
            # Parse article date (Eastern timezone from API)
            try:
                article_date_str = article.get('date', '')
                if article_date_str:
                    # Convert from Eastern (API timezone) to Chicago time
                    eastern_tz = pytz.timezone('US/Eastern')
                    article_date = datetime.strptime(article_date_str, '%Y-%m-%d %H:%M:%S')
                    article_date = eastern_tz.localize(article_date)
                    article_date_chicago = article_date.astimezone(chicago_tz)

                    # Filter by time window
                    if article_date_chicago >= cutoff_time:
                        breaking_news.append({
                            'title': article.get('title', ''),
                            'text_preview': article.get('text', '')[:200] + '...' if article.get('text') else '',
                            'source': article.get('source_name', 'Unknown'),
                            'url': article.get('news_url', ''),
                            'published_eastern': article_date_str,
                            'published_chicago': article_date_chicago.strftime('%Y-%m-%d %H:%M:%S CST'),
                            'sentiment': article.get('sentiment', 'neutral'),
                            'tickers': article.get('tickers', []),
                            'importance_rank': len(breaking_news) + 1  # Based on rank sorting
                        })
                else:
                    # Include articles without dates (recent by default due to rank sorting)
                    breaking_news.append({
                        'title': article.get('title', ''),
                        'text_preview': article.get('text', '')[:200] + '...' if article.get('text') else '',
                        'source': article.get('source_name', 'Unknown'),
                        'url': article.get('news_url', ''),
                        'published_eastern': 'Recent',
                        'published_chicago': 'Recent',
                        'sentiment': article.get('sentiment', 'neutral'),
                        'tickers': article.get('tickers', []),
                        'importance_rank': len(breaking_news) + 1
                    })

            except Exception as date_error:
                print(f"⚠️ Date parsing error: {date_error}")
                # Include article anyway since it's ranked as important
                breaking_news.append({
                    'title': article.get('title', ''),
                    'text_preview': article.get('text', '')[:200] + '...' if article.get('text') else '',
                    'source': article.get('source_name', 'Unknown'),
                    'url': article.get('news_url', ''),
                    'published_eastern': article.get('date', 'Unknown'),
                    'published_chicago': 'Unknown',
                    'sentiment': article.get('sentiment', 'neutral'),
                    'tickers': article.get('tickers', []),
                    'importance_rank': len(breaking_news) + 1
                })

        print(f"📰 Breaking News Results: {len(breaking_news)} articles in {hours}h window")

        # Sort by importance rank (already sorted by API, but ensure consistency)
        breaking_news.sort(key=lambda x: x['importance_rank'])

        return breaking_news

    except Exception as e:
        print(f"❌ Error fetching optimized breaking news: {e}")
        return []

def get_breaking_news(hours=2, items=100, sentiment=None, sortby="rank"):
    """
    Get breaking crypto news using basic API endpoints - compatible with your API route
    """
    try:
        print(f"🔥 Getting breaking news: hours={hours}, items={items}, sentiment={sentiment}")

        # Use the general crypto news endpoint with rank sorting for breaking news
        params = {
            "section": "general",
            "items": min(items, 100),
            "page": 1,
            "token": API_TOKEN
        }

        if sentiment:
            params["sentiment"] = sentiment
        if sortby:
            params["sortby"] = sortby

        response = requests.get(f"{BASE_URL}/category", params=params, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Filter by time window if specified
        if hours and hours < 24:  # Only filter if less than 24 hours
            filtered_articles = []
            chicago_tz = pytz.timezone('America/Chicago')
            current_time = datetime.now(chicago_tz)
            cutoff_time = current_time - timedelta(hours=hours)

            for article in result.get('data', []):
                try:
                    article_date_str = article.get('date', '')
                    if article_date_str:
                        # Parse article date (assume Eastern timezone from API)
                        eastern_tz = pytz.timezone('US/Eastern')
                        article_date = datetime.strptime(article_date_str, '%Y-%m-%d %H:%M:%S')
                        article_date = eastern_tz.localize(article_date)
                        article_date_chicago = article_date.astimezone(chicago_tz)

                        if article_date_chicago >= cutoff_time:
                            filtered_articles.append(article)
                    else:
                        # Include articles without dates (likely recent)
                        filtered_articles.append(article)
                except:
                    # Include article if date parsing fails
                    filtered_articles.append(article)

            result['data'] = filtered_articles
            print(f"📰 Filtered to {len(filtered_articles)} articles in last {hours} hours")

        print(f"📰 Breaking news: {len(result.get('data', []))} articles")
        return result

    except Exception as e:
        print(f"❌ Error getting breaking news: {e}")
        return {
            'data': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_advanced_opportunities():
    """Generate advanced cryptocurrency opportunities using comprehensive analysis"""
    try:
        print("🚀 Generating advanced opportunities...")

        # Get comprehensive market data
        market_news = get_general_crypto_news(items=100, sortby="rank")
        portfolio_symbols = get_portfolio_symbols()

        # Analyze market opportunities
        opportunities = analyze_market_opportunities(market_news, exclude_symbols=portfolio_symbols)

        # Filter and categorize opportunities
        high_confidence = [op for op in opportunities if op['confidence_score'] >= 75]
        breakout_ops = [op for op in opportunities if any('BREAKOUT' in str(signal) for signal in op.get('signals', []))]
        partnership_ops = [op for op in opportunities if any('PARTNERSHIP' in str(signal) for signal in op.get('signals', []))]
        institutional_ops = [op for op in opportunities if any('INSTITUTIONAL' in str(signal) for signal in op.get('signals', []))]

        # Generate trending analysis
        trending_symbols = extract_trending_symbols_from_news(market_news, exclude_symbols=portfolio_symbols)

        # Create comprehensive opportunity report
        advanced_report = {
            'timestamp': datetime.now().isoformat(),
            'market_analysis': {
                'total_articles_analyzed': len(market_news.get('data', [])),
                'portfolio_symbols_excluded': len(portfolio_symbols),
                'market_sentiment_overview': analyze_market_sentiment(market_news)
            },
            'opportunity_summary': {
                'total_opportunities': len(opportunities),
                'high_confidence_count': len(high_confidence),
                'breakout_opportunities': len(breakout_ops),
                'partnership_opportunities': len(partnership_ops), 
                'institutional_opportunities': len(institutional_ops)
            },
            'top_opportunities': opportunities[:15],  # Top 15 opportunities
            'trending_symbols': trending_symbols[:10],  # Top 10 trending
            'breakout_analysis': breakout_ops[:5],
            'partnership_analysis': partnership_ops[:5],
            'institutional_analysis': institutional_ops[:5],
            'risk_assessment': {
                'market_volatility': 'medium',  # Could be enhanced with more data
                'opportunity_confidence': 'high' if len(high_confidence) > 5 else 'medium'
            }
        }

        print(f"📊 Advanced Opportunities Generated: {len(opportunities)} total, {len(high_confidence)} high-confidence")
        return advanced_report

    except Exception as e:
        print(f"❌ Error generating advanced opportunities: {e}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'opportunities': []
        }

def analyze_market_sentiment(news_data):
    """Analyze overall market sentiment from news data"""
    try:
        articles = news_data.get('data', [])
        if not articles:
            return {'sentiment': 'neutral', 'confidence': 'low'}

        positive_count = len([a for a in articles if a.get('sentiment') == 'positive'])
        negative_count = len([a for a in articles if a.get('sentiment') == 'negative'])
        neutral_count = len(articles) - positive_count - negative_count

        total = len(articles)
        positive_ratio = positive_count / total if total > 0 else 0
        negative_ratio = negative_count / total if total > 0 else 0

        # Determine overall sentiment
        if positive_ratio > 0.4 and positive_ratio > negative_ratio * 1.3:
            sentiment = 'bullish'
            confidence = 'high' if positive_ratio > 0.5 else 'medium'
        elif negative_ratio > 0.4 and negative_ratio > positive_ratio * 1.3:
            sentiment = 'bearish'
            confidence = 'high' if negative_ratio > 0.5 else 'medium'
        else:
            sentiment = 'neutral'
            confidence = 'medium'

        return {
            'sentiment': sentiment,
            'confidence': confidence,
            'positive_ratio': round(positive_ratio * 100, 1),
            'negative_ratio': round(negative_ratio * 100, 1),
            'neutral_ratio': round((neutral_count / total * 100), 1) if total > 0 else 0,
            'total_articles': total
        }
    except Exception as e:
        print(f"❌ Error analyzing market sentiment: {e}")
        return {'sentiment': 'unknown', 'confidence': 'low', 'error': str(e)}

def scan_opportunities(opportunity_type='all', exclude_symbols=None, min_market_cap='all'):
    """Scan opportunities using basic endpoints"""
    if exclude_symbols is None:
        exclude_symbols = get_portfolio_symbols()

    general_news = get_general_crypto_news(items=100)
    return analyze_market_opportunities(general_news, exclude_symbols=exclude_symbols)

def get_market_intelligence_feed(search_terms=None, sentiment=None, category='all', timeframe='24h', priority='all', items=150):
    """Get comprehensive market intelligence using basic endpoints with enhanced filtering"""
    try:
        print(f"🎯 Market Intelligence Feed - Params: items={items}, sentiment={sentiment}, category={category}")

        # Get comprehensive intelligence (this is our main function)
        intelligence = get_comprehensive_crypto_intelligence()

        # Apply additional filters if specified
        if sentiment:
            # Filter market intelligence by sentiment
            filtered_intelligence = []
            for alert in intelligence.get('market_intelligence', []):
                if alert.get('sentiment', '').lower() == sentiment.lower():
                    filtered_intelligence.append(alert)
            intelligence['market_intelligence'] = filtered_intelligence
            intelligence['total_alerts'] = len(filtered_intelligence)
            print(f"🔍 Filtered by sentiment '{sentiment}': {len(filtered_intelligence)} alerts")

        if search_terms:
            # Filter by search terms in title or message
            filtered_intelligence = []
            search_lower = search_terms.lower()
            for alert in intelligence.get('market_intelligence', []):
                title = alert.get('title', '').lower()
                message = alert.get('message', '').lower()
                if search_lower in title or search_lower in message:
                    filtered_intelligence.append(alert)
            intelligence['market_intelligence'] = filtered_intelligence
            intelligence['total_alerts'] = len(filtered_intelligence)
            print(f"🔍 Filtered by search terms '{search_terms}': {len(filtered_intelligence)} alerts")

        # Add metadata about filtering
        intelligence['filters_applied'] = {
            'search_terms': search_terms,
            'sentiment': sentiment,
            'category': category,
            'timeframe': timeframe,
            'priority': priority,
            'max_items': items
        }

        return intelligence

    except Exception as e:
        print(f"❌ Error in market intelligence feed: {e}")
        return {
            'timestamp': datetime.now().isoformat(),
            'total_alerts': 0,
            'intelligence_categories': {},
            'market_intelligence': [],
            'trending_symbols': [],
            'market_pulse': {},
            'error': str(e)
        }

def get_focused_coin_analysis(symbol, items=50, exclude_other_coins=True):
    """
    Get focused analysis for a single coin using tickers-only approach (API example 4)
    This reduces noise by excluding articles that mention multiple coins
    """
    try:
        print(f"🎯 Getting focused analysis for {symbol} (excluding multi-coin articles)")

        if exclude_other_coins:
            # Use tickers-only for pure focus (API example 4)
            focused_news = get_news_tickers_only(symbol, items=items, sortby="rank")
        else:
            # Use regular tickers approach
            focused_news = get_news_by_tickers([symbol], items=items, sortby="rank")

        # Analyze the focused data
        articles = focused_news.get('data', [])

        analysis = {
            'symbol': symbol,
            'total_articles': len(articles),
            'focused_analysis': exclude_other_coins,
            'sentiment_breakdown': {
                'positive': len([a for a in articles if a.get('sentiment') == 'positive']),
                'negative': len([a for a in articles if a.get('sentiment') == 'negative']),
                'neutral': len([a for a in articles if a.get('sentiment') == 'neutral'])
            },
            'articles': articles,
            'quality_score': 0
        }

        # Calculate quality score
        total = analysis['total_articles']
        if total > 0:
            positive_ratio = analysis['sentiment_breakdown']['positive'] / total
            article_count_score = min(total * 10, 100)  # Cap at 100
            analysis['quality_score'] = (positive_ratio * 50) + (article_count_score * 0.5)

        print(f"📊 {symbol} Analysis: {total} articles, {analysis['quality_score']:.1f} quality score")
        return analysis

    except Exception as e:
        print(f"❌ Error in focused coin analysis: {e}")
        return {'error': str(e), 'symbol': symbol}

def discover_new_opportunities_ai_pattern():
    """
    Discover new opportunities using AI-recommended pattern:
    sortby=rank + sentiment=positive for important bullish news
    """
    try:
        print("🚀 AI PATTERN: Discovering new opportunities (rank + positive sentiment)")

        # AI recommended combination for opportunity discovery
        opportunity_news = get_general_crypto_news(
            items=100,  # Optimal for basic plan
            sentiment="positive",  # Focus on bullish news
            sortby="rank"  # Prioritize important news
        )

        portfolio_symbols = get_portfolio_symbols()
        opportunities = analyze_market_opportunities(
            opportunity_news, 
            exclude_symbols=portfolio_symbols
        )

        # Filter for high-impact opportunities
        high_impact = [opp for opp in opportunities if opp['confidence_score'] >= 70]

        print(f"🎯 Found {len(high_impact)} high-impact opportunities using AI pattern")
        return high_impact

    except Exception as e:
        print(f"❌ Error in AI opportunity discovery: {e}")
        return []

def monitor_existing_positions_ai_pattern():
    """
    Monitor existing positions using AI-recommended pattern:
    Specific tickers + sortby=date for latest updates
    """
    try:
        portfolio_symbols = get_portfolio_symbols()
        if not portfolio_symbols:
            return []

        print(f"📊 AI PATTERN: Monitoring {len(portfolio_symbols)} positions (tickers + date sort)")

        # AI recommended pattern for monitoring existing positions
        monitoring_news = get_news_by_tickers(
            tickers=portfolio_symbols,
            items=50,  # Efficient for monitoring
            sortby="date"  # Latest updates first
        )

        portfolio_alerts = alert_narrative_confluence(portfolio_symbols, monitoring_news)

        print(f"📰 Found {len(portfolio_alerts)} portfolio alerts using AI pattern")
        return portfolio_alerts

    except Exception as e:
        print(f"❌ Error in AI position monitoring: {e}")
        return []

def search_for_catalysts(keywords=None):
    """
    Search for specific catalysts using AI-recommended keywords
    Keywords suggested by AI: partnership, new listing, adoption, etc.
    """
    try:
        if keywords is None:
            # AI-recommended high-impact keywords
            keywords = ["new listing", "partnership", "adoption", "institutional", "record high"]

        catalyst_results = []

        for keyword in keywords:
            print(f"🔍 Searching for catalyst: '{keyword}'")

            # Use search parameter as recommended by AI
            search_news = get_general_crypto_news(
                items=50,
                sortby="rank",  # Prioritize important matches
                # Note: search parameter would go here if available in API
            )

            # Manual keyword filtering since search parameter usage unclear
            keyword_matches = []
            for article in search_news.get('data', []):
                title_text = f"{article.get('title', '')} {article.get('text', '')}".upper()
                if keyword.upper() in title_text:
                    keyword_matches.append({
                        'keyword': keyword,
                        'title': article.get('title', ''),
                        'source': article.get('source_name', ''),
                        'sentiment': article.get('sentiment', 'neutral'),
                        'tickers': article.get('tickers', []),
                        'url': article.get('news_url', ''),
                        'match_relevance': title_text.count(keyword.upper())
                    })

            catalyst_results.extend(keyword_matches[:10])  # Top 10 per keyword

        # Sort by relevance and sentiment
        catalyst_results.sort(key=lambda x: (x['match_relevance'], x['sentiment'] == 'positive'), reverse=True)

        print(f"🎯 Found {len(catalyst_results)} catalyst matches")
        return catalyst_results[:20]  # Top 20 overall

    except Exception as e:
        print(f"❌ Error searching for catalysts: {e}")
        return []

def detect_pump_dump_signals(signal_type='both', confidence_threshold=60, exclude_known_projects=False):
    """Detect signals using basic endpoints with AI-enhanced patterns"""
    KNOWN_PROJECTS = ['BTC', 'ETH', 'BNB', 'ADA', 'XRP', 'SOL', 'DOT', 'AVAX', 'MATIC', 'LINK', 'UNI', 'ATOM'] if exclude_known_projects else []

    # Use AI pattern for better signal detection
    general_news = get_general_crypto_news(items=100, sortby="rank")
    opportunities = analyze_market_opportunities(general_news, exclude_symbols=KNOWN_PROJECTS)

    pump_signals = [opp for opp in opportunities if opp['type'] == 'opportunity' and opp['confidence_score'] >= confidence_threshold]
    dump_signals = [opp for opp in opportunities if opp['type'] == 'risk' and opp['confidence_score'] >= confidence_threshold]

    return {
        'pump_signals': pump_signals[:20],
        'dump_signals': dump_signals[:20],
        'ai_enhancement': 'rank-sorted for importance'
    }

# Legacy function for backwards compatibility
def generate_news_alerts():
    """Legacy function - now calls comprehensive intelligence"""
    result = get_comprehensive_crypto_intelligence()

    # Convert to old format for backwards compatibility
    legacy_alerts = []
    for alert in result.get('market_intelligence', []):
        legacy_alerts.append({
            'type': alert['alert_type'],
            'message': alert['message'],
            'symbol': alert.get('symbol'),
            'title': alert['title'],
            'sentiment': alert['sentiment'],
            'source': alert['source'],
            'url': alert['url']
        })

    return legacy_alerts

# Test functions
def test_news_integration():
    """Test the basic plan news integration"""
    print("🧪 Testing BASIC PLAN crypto news integration...")

    # Test general news
    general_news = get_general_crypto_news(items=10)
    print(f"📰 General news: {len(general_news.get('data', []))} articles")

    if general_news.get("data"):
        print("📋 Sample general article:")
        article = general_news["data"][0]
        print(f"  Title: {article.get('title', 'N/A')}")
        print(f"  Source: {article.get('source_name', 'N/A')}")
        print(f"  Sentiment: {article.get('sentiment', 'N/A')}")
        print(f"  Tickers: {article.get('tickers', [])}")

if __name__ == "__main__":
    # Test basic plan integration
    test_news_integration()

    # Run comprehensive intelligence
    print("\n🎯 RUNNING COMPREHENSIVE CRYPTO INTELLIGENCE (BASIC PLAN)...")
    intelligence = get_comprehensive_crypto_intelligence()

    print(f"\n📊 RESULTS:")
    print(f"Total Intelligence Alerts: {intelligence.get('total_alerts', 0)}")
    print(f"Market Sentiment: {intelligence.get('market_pulse', {}).get('overall_sentiment', 'unknown').upper()}")
    print(f"Trending Symbols: {intelligence.get('trending_symbols', [])[:10]}")

    # Show sample alerts
    sample_alerts = intelligence.get('market_intelligence', [])[:5]
    for alert in sample_alerts:
        print(f"• {alert.get('message', 'N/A')}")
