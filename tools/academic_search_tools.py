# academic_search_tools.py

import asyncio
import logging
import httpx
from dotenv import load_dotenv
import os

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
SEMANTIC_SCHOLAR_API_KEY = os.environ.get("SEMANTIC_SCHOLAR_API_KEY")
semantic_scholar_lock = asyncio.Lock()

async def search_arxiv(query: str, max_results: int = 3) -> list:
    """Asynchronously searches arXiv for a given query."""
    # ArXiv is not very sensitive, a small delay is fine.
    await asyncio.sleep(4)
    try:
        from langchain_community.tools import ArxivQueryRun
        arxiv_tool = ArxivQueryRun(load_max_docs=max_results)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, arxiv_tool.run, query)
        
        if "Published" not in results:
             return [{"title": "No relevant articles found on arXiv", "summary": results, "url": "", "source": "arXiv"}]
        
        entries = results.split('Published: ')
        formatted_results = []
        for entry in entries[1:]:
            parts = entry.split('\nTitle: ')
            if len(parts) < 2: continue
            
            url_part = parts[0].strip()
            title_part = parts[1].split('\nAuthors: ')[0].strip()
            summary_part = entry.split('\nSummary: ')[1].strip() if '\nSummary: ' in entry else 'No summary available.'
            
            formatted_results.append({
                "title": title_part,
                "summary": summary_part,
                "url": url_part,
                "source": "arXiv"
            })
        logging.info(f"ArXiv search for '{query}' returned {len(formatted_results)} results.")
        return formatted_results
    except Exception as e:
        logging.error(f"An error occurred during ArXiv search for '{query}': {e}")
        return []


# async def search_semantic_scholar(query: str, max_results: int = 3) -> list:
#     """Asynchronously searches Semantic Scholar for a given query."""
#     base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
#     params = {"query": query, "limit": max_results, "fields": "title,abstract,authors,year,url"}
    
#     async with semantic_scholar_lock:
#         async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
#             try:
#                 # THE FINAL FIX: Increase the delay within the lock to be extra polite.
#                 await asyncio.sleep(4) 
#                 response = await client.get(base_url, params=params)
#                 response.raise_for_status()
#                 data = response.json()
#                 results = data.get('data', [])
#                 logging.info(f"Semantic Scholar search for '{query}' returned {len(results)} results.")
#                 return [{
#                     "title": item.get('title'), 
#                     "summary": item.get('abstract'),
#                     "url": item.get('url'),
#                     "source": "Semantic Scholar"
#                 } for item in results]
#             except httpx.HTTPStatusError as e:
#                 logging.error(f"HTTP error during Semantic Scholar search: {e.response.status_code}")
#                 return []
#             except Exception as e:
#                 logging.error(f"An error occurred during Semantic Scholar search for '{query}': {e}")
#                 return []

async def search_semantic_scholar(query: str, max_results: int = 3) -> list:
    """Asynchronously searches Semantic Scholar for a given query using an API key."""
    # 1. Check if the API key exists
    if not SEMANTIC_SCHOLAR_API_KEY:
        logging.warning("SEMANTIC_SCHOLAR_API_KEY not found; skipping Semantic Scholar search.")
        return []

    base_url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {"query": query, "limit": max_results, "fields": "title,abstract,authors,year,url"}
    
    # 2. Create the headers dictionary with your API key
    headers = {"x-api-key": SEMANTIC_SCHOLAR_API_KEY}

    # The lock is still a good practice to be polite to the API
    async with semantic_scholar_lock:
        async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
            try:
                # You can reduce the sleep time now that you have a key
                await asyncio.sleep(2) 
                
                # 3. Pass the headers into the request
                response = await client.get(base_url, params=params, headers=headers)
                
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