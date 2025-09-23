# news_search_tools.py

import os
import logging
import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

## THE FIX: Create a lock to serialize requests to the NewsAPI.
news_api_lock = asyncio.Lock()

async def search_news(query: str, max_results: int = 5) -> list:
    """Asynchronously searches for news articles using the NewsAPI."""
    if not NEWS_API_KEY:
        logging.warning("NEWS_API_KEY not found; skipping news search.")
        return []

    url = "https://newsapi.org/v2/everything"
    params = {'q': query, 'pageSize': max_results, 'apiKey': NEWS_API_KEY}
    
    ## THE FIX: Use the lock to prevent concurrent requests.
    async with news_api_lock:
        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                # A polite delay is still good practice
                await asyncio.sleep(1)
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                articles = data.get("articles", [])
                logging.info(f"NewsAPI search for '{query}' returned {len(articles)} articles.")
                return [{
                    "title": article.get("title"), 
                    "summary": article.get("description"),
                    "url": article.get("url"), # Added URL for completeness
                    "source": "NewsAPI"
                } for article in articles]
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error during NewsAPI search: {e.response.status_code}")
                return []
            except Exception as e:
                logging.error(f"An unexpected error occurred during NewsAPI search: {e}")
                return []