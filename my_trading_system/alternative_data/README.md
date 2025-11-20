# Alternative Data

This directory contains infrastructure for collecting and processing alternative data sources (news, social media, sentiment, etc.).

## Structure

```
alternative_data/
├── scrapers/       # Data collection from various sources
├── processors/     # Data processing (sentiment, NLP, etc.)
├── providers/      # Real-time data providers for strategies
├── storage/        # Database and storage layer
└── utils/          # Utilities (rate limiting, etc.)
```

## Workflow

```
1. Scrape Data (scrapers/)
   └─> Collect from news sites, Twitter, Reddit, etc.

2. Process Data (processors/)
   └─> Sentiment analysis, entity extraction, cleaning

3. Store Data (storage/)
   └─> Save to database or files (data/alternative/)

4. Serve to Strategies (providers/)
   └─> Real-time feeds to trading strategies

5. Research (notebooks/alternative_data/)
   └─> Analyze impact on prices
```

## Components

### Scrapers (`scrapers/`)

Collect data from external sources.

**Common sources:**
- News websites (CoinDesk, CoinTelegraph, Bloomberg)
- News APIs (NewsAPI, GDELT)
- Twitter/X
- Reddit
- Telegram channels
- Discord servers

**Pattern:**
```python
# alternative_data/scrapers/news_scrapers.py
class BaseNewsScraper:
    def __init__(self, rate_limit_seconds=1.0):
        self.rate_limit = rate_limit_seconds

    def scrape(self) -> List[Dict]:
        # Return list of articles
        pass

class CoinDeskScraper(BaseNewsScraper):
    def scrape(self) -> List[Dict]:
        # Scrape CoinDesk
        return articles
```

### Processors (`processors/`)

Transform raw data into usable features.

**Common processors:**
- `sentiment_analyzer.py` - Sentiment analysis (positive/negative/neutral)
- `entity_extractor.py` - Extract tickers, companies, topics
- `text_cleaner.py` - Clean and normalize text
- `event_classifier.py` - Classify event types
- `deduplicator.py` - Remove duplicate news

**Pattern:**
```python
# alternative_data/processors/sentiment_analyzer.py
class SentimentAnalyzer:
    def __init__(self, model_name="ProsusAI/finbert"):
        self.model = pipeline("sentiment-analysis", model=model_name)

    def analyze_text(self, text: str) -> Dict:
        result = self.model(text)[0]
        return {
            'sentiment': result['label'],
            'confidence': result['score'],
            'sentiment_score': self._to_score(result)
        }

    def analyze_batch(self, texts: List[str]) -> pd.DataFrame:
        # Batch processing
        pass
```

### Providers (`providers/`)

Serve real-time data to trading strategies.

**Pattern:**
```python
# alternative_data/providers/news_feed.py
class NewsFeedProvider:
    def __init__(self, scrapers, processors):
        self.scrapers = scrapers
        self.processors = processors

    def start_feed(self, callback):
        # Continuously scrape and process
        # Call callback with new data
        pass
```

### Storage (`storage/`)

Persist alternative data.

**Pattern:**
```python
# alternative_data/storage/news_database.py
class NewsDatabase:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)

    def save_articles(self, articles_df):
        articles_df.to_sql('articles', self.conn, if_exists='append')

    def load_articles(self, symbol, start_date, end_date):
        query = "SELECT * FROM articles WHERE symbol = ? AND timestamp BETWEEN ? AND ?"
        return pd.read_sql(query, self.conn, params=[symbol, start_date, end_date])
```

## Data Storage

Alternative data is stored in `data/alternative/`:

```
data/alternative/
├── news/
│   ├── raw/                  # Raw scraped articles
│   │   ├── 2024-11/
│   │   │   ├── news_20241119.parquet
│   │   │   └── news_20241120.parquet
│   │   └── 2024-12/
│   └── processed/            # With sentiment scores
│       ├── btc_news_sentiment.parquet
│       └── eth_news_sentiment.parquet
├── twitter/
│   ├── raw/
│   └── processed/
└── reddit/
    ├── raw/
    └── processed/
```

## Common Data Sources

### News

**Free APIs:**
- NewsAPI (500 requests/day free)
- GDELT Project (free, global news)
- CryptoPanic API (crypto-specific)

**Scraping:**
- CoinDesk, CoinTelegraph, Decrypt (crypto news)
- Reuters, Bloomberg (general finance)

**Pattern:**
```python
# Scrape every 15 minutes
python scripts/alternative_data/scrape_news_continuous.py
```

### Social Media

**Twitter/X:**
- Twitter API v2 (requires API key)
- Track specific accounts, hashtags

**Reddit:**
- Reddit API (PRAW library)
- Monitor r/cryptocurrency, r/bitcoin

**Pattern:**
```python
# Stream real-time data
python scripts/alternative_data/stream_twitter.py
```

### Sentiment Analysis

**Models:**
- FinBERT (finance-specific)
- Twitter-RoBERTa (social media)
- VADER (rule-based, fast)

**Aggregation:**
```python
# Aggregate sentiment over time windows
sentiment_hourly = aggregate_sentiment(news_df, window='1H')
```

## Automation Scripts

Located in `scripts/alternative_data/`:

### One-Time Scrape
```bash
# Scrape historical data
python scripts/alternative_data/scrape_news_batch.py --start 2024-01-01 --end 2024-11-19
```

### Continuous Scraping
```bash
# Run as background service
python scripts/alternative_data/scrape_news_continuous.py &

# Check it's running
ps aux | grep scrape_news
```

### Processing
```bash
# Batch process raw data
python scripts/alternative_data/process_news_batch.py
```

## Using in Strategies

### Custom Data Type
```python
# Define custom data for news
from nautilus_trader.core.data import Data

class NewsSentimentData(Data):
    def __init__(self, symbol, sentiment_score, article_count, ts_event, ts_init):
        super().__init__(ts_event=ts_event, ts_init=ts_init)
        self.symbol = symbol
        self.sentiment_score = sentiment_score
        self.article_count = article_count
```

### In Strategy
```python
# strategies/alternative_data/news_sentiment.py
class NewsSentimentStrategy(Strategy):
    def on_data(self, data: Data):
        if isinstance(data, NewsSentimentData):
            if data.sentiment_score > 0.5:
                # Bullish signal
                pass
```

## Best Practices

### 1. Rate Limiting
```python
# Always respect rate limits
class RateLimitedScraper:
    def __init__(self, requests_per_second=1):
        self.min_interval = 1.0 / requests_per_second
        self.last_request = 0

    def wait_if_needed(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
```

### 2. Error Handling
```python
# Handle API failures gracefully
try:
    articles = scraper.scrape()
except requests.exceptions.RequestException as e:
    logger.error(f"Scraping failed: {e}")
    # Continue with cached data or skip
```

### 3. Deduplication
```python
# Remove duplicate articles
def deduplicate(articles_df):
    return articles_df.drop_duplicates(subset=['url', 'title'])
```

### 4. API Key Management
```python
# Never commit API keys!
# Use configs/alternative_data/scrapers/api_keys.yaml (gitignored)
import yaml

with open('configs/alternative_data/scrapers/api_keys.yaml') as f:
    keys = yaml.safe_load(f)

api_key = keys['newsapi_key']
```

### 5. Data Quality
```python
# Validate scraped data
def validate_article(article):
    required_fields = ['title', 'url', 'timestamp']
    return all(field in article for field in required_fields)
```

## Research Workflow

### 1. Explore Data
```python
# notebooks/alternative_data/01_explore_news.ipynb
news_df = load_news_data('BTC', '2024-01-01', '2024-11-19')
print(news_df.head())
news_df['title'].value_counts()
```

### 2. Analyze Sentiment
```python
# notebooks/alternative_data/02_sentiment_analysis.ipynb
analyzer = SentimentAnalyzer()
news_df = analyzer.analyze_news_df(news_df)
```

### 3. Study Impact
```python
# notebooks/alternative_data/04_news_impact_study.ipynb
# Correlate sentiment with price movements
merged = merge_news_and_prices(news_df, price_df)
correlation = merged['sentiment'].corr(merged['returns_1h'])
```

### 4. Build Strategy
```python
# notebooks/strategies/news_sentiment_strategy.ipynb
# Test strategy using news signals
```

## Adding New Data Sources

To add blockchain data, fundamental data, etc.:

```bash
# 1. Create new module
mkdir -p blockchain_data/{collectors,processors,providers,storage}

# 2. Follow same pattern as alternative_data/
# - collectors/ for data collection
# - processors/ for data processing
# - providers/ for real-time feeds
# - storage/ for persistence

# 3. Add to data/
mkdir -p data/blockchain/{raw,processed}

# 4. Add scripts
mkdir -p scripts/blockchain_data
```

## Resources

- [NewsAPI Documentation](https://newsapi.org/docs)
- [Twitter API Documentation](https://developer.twitter.com/en/docs)
- [FinBERT Model](https://huggingface.co/ProsusAI/finbert)
- [GDELT Project](https://www.gdeltproject.org/)
- Main README: [../README.md](../README.md)
