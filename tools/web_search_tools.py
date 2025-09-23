# web_search_tools.py (Your code is correct)

import os
import logging
from langchain_tavily import TavilySearch
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
if not TAVILY_API_KEY:
    logging.warning("TAVILY_API_KEY not found in environment variables. Web search will be disabled.")

async def search_tavily(query: str, max_results: int = 7) -> list:
    """
    Asynchronously performs a web search using the Tavily API and robustly formats the results.
    """
    if not TAVILY_API_KEY:
        return []
    
    try:
        tavily_tool = TavilySearch(max_results=max_results, tavily_api_key=TAVILY_API_KEY)
        results = await tavily_tool.ainvoke({"query": query})
        logging.info(f"Tavily search for '{query}' returned {len(results)} results.")
        
        formatted_results = []
        if isinstance(results, list):
            for res in results:
                if isinstance(res, dict):
                    formatted_results.append({
                        "title": res.get("title", "No Title Available"),
                        "summary": res.get("content", "No content available."),
                        "url": res.get("url", ""),
                        "source": "Tavily Web Search"
                    })
                elif isinstance(res, str):
                    formatted_results.append({
                        "title": "Web Search Result",
                        "summary": res,
                        "url": "",
                        "source": "Tavily Web Search"
                    })
        
        return formatted_results
        
    except Exception as e:
        logging.error(f"An unexpected error occurred during Tavily search for '{query}': {e}")
        return []