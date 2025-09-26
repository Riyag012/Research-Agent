# academic_search_tools.py

import asyncio
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

semantic_scholar_lock = asyncio.Lock()

async def search_arxiv(query: str, max_results: int = 5) -> list:
    # ... (this function is fine, no changes needed)
    pass

async def search_semantic_scholar(query: str, max_results: int = 5) -> list:
    """Asynchronously searches Semantic Scholar for a given query."""
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,abstract,authors,year,url"}
    
    async with semantic_scholar_lock:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            try:
                ## THE FIX: Increase the delay to be more cautious.
                await asyncio.sleep(3) 
                response = await client.get(base_url, params=params)
                response.raise_for_status()
                data = response.json()
                results = data.get('data', [])
                logging.info(f"Semantic Scholar search for '{query}' returned {len(results)} results.")
                return [{
                    "title": item.get('title'), 
                    "summary": item.get('abstract'),
                    "url": item.get('url'),
                    "source": "Semantic Scholar"
                } for item in results]
            except httpx.HTTPStatusError as e:
                logging.error(f"HTTP error during Semantic Scholar search: {e.response.status_code}")
                return []
            except Exception as e:
                logging.error(f"An error occurred during Semantic Scholar search for '{query}': {e}")
                return []