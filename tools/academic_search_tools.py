# academic_search_tools.py

import asyncio
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

## THE FIX: Create a lock specifically for the Semantic Scholar API.
semantic_scholar_lock = asyncio.Lock()

async def search_arxiv(query: str, max_results: int = 3) -> list:
    """Asynchronously searches arXiv for a given query."""
    base_url = "https://export.arxiv.org/api/query"
    params = {"search_query": query, "start": 0, "max_results": max_results, "sortBy": "relevance"}
    
    async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
        try:
            await asyncio.sleep(0.5)
            response = await client.get(base_url, params=params)
            response.raise_for_status()
            
            # (Your parsing logic here)
            logging.info(f"arXiv search for '{query}' successful.")
            return [{
                "title": f"Placeholder ArXiv result for {query}", 
                "summary": f"Content for {query} would be parsed from XML.", 
                "url": "#",
                "source": "arXiv"
            }]
        except httpx.HTTPStatusError as e:
            logging.error(f"HTTP error during ArXiv search for '{query}': {e.response.status_code}")
            return []
        except Exception as e:
            logging.error(f"An error occurred during ArXiv search for '{query}': {e}")
            return []

async def search_semantic_scholar(query: str, max_results: int = 3) -> list:
    """Asynchronously searches Semantic Scholar for a given query."""
    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,abstract,authors,year,url"}
    
    ## THE FIX: Use the lock to ensure only one request to this API runs at a time.
    async with semantic_scholar_lock:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            try:
                # A small sleep is still polite.
                await asyncio.sleep(1) 
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