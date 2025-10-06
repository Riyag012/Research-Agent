# searcher.py

import asyncio
import logging
from .utils import clean_section_title
from tools.web_search_tools import search_tavily
from tools.academic_search_tools import search_arxiv, search_semantic_scholar
from tools.news_search_tools import search_news

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def search_section(section: str, topic: str, semaphore: asyncio.Semaphore):
    """
    Asynchronously searches for information on a single section of the report
    using web, academic, and news sources.
    """
    async with semaphore:
        cleaned_section = clean_section_title(section)
        query = f"{topic}: {cleaned_section}"
        
        logging.info(f"Starting comprehensive search for section: '{section}'")
        
        # Define all search tasks for the current section
        # It contains four awaitable coroutine objects. 
        search_tasks = [
            search_tavily(query, max_results=5),
            search_arxiv(query, max_results=3),
            search_semantic_scholar(query, max_results=3),
            search_news(query, max_results=3)
        ]
        
        try:
            # Run all searches concurrently for this section
            results_from_all_sources = await asyncio.gather(*search_tasks, return_exceptions=True)
            
            # Flatten the list of lists and tag each result with its section
            final_section_results = []
            for source_results in results_from_all_sources:
                if isinstance(source_results, list):
                    for item in source_results:
                        if isinstance(item, dict):
                            item['section'] = section  # Tag with the original section title
                            final_section_results.append(item)
                elif isinstance(source_results, Exception):
                    logging.error(f"A search task failed for section '{section}': {source_results}")
            
            logging.info(f"Found {len(final_section_results)} total results for section '{section}'")
            return final_section_results
            
        except Exception as e:
            logging.error(f"An unexpected error occurred during search for section '{section}': {e}")
            return []

# he single underscore _ at the beginning of _run_concurrent_searches is a convention in Python to signal that this function is
# intended for internal use only within the searcher.py file.
async def _run_concurrent_searches(outline: list, topic: str):
    """
    Manages the concurrent execution of comprehensive searches for all sections.
    """
    semaphore = asyncio.Semaphore(3)  # Limit concurrent sections being processed
    tasks = [search_section(section, topic, semaphore) for section in outline]
    
    # This will be a list of lists of results
    all_results_list = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Flatten the final list of lists into a single list of results
    final_results = []
    for item in all_results_list:
        if isinstance(item, list):
            final_results.extend(item)
        elif isinstance(item, Exception):
            logging.error(f"A top-level section search task failed: {item}")
            
    return final_results

def run_searcher_agent(outline: list, topic: str) -> list:
    """
    Entry point for running the searcher agent.
    """
    if not outline or not isinstance(outline, list):
        logging.error("Searcher agent received an invalid or empty outline.")
        return []

    logging.info(f"Searcher Agent starting research for {len(outline)} sections.")
    try:
        search_results = asyncio.run(_run_concurrent_searches(outline, topic))
        if not search_results:
             logging.warning("The search agent returned no results across all sources.")
        else:
             logging.info(f"Searcher agent finished with a total of {len(search_results)} results.")
        return search_results
    except Exception as e:
        logging.error(f"A critical error occurred in the searcher agent: {e}")
        return []


'''
Here is a brief explanation of the role and purpose of each of the three functions in `searcher.py`.

### 1. `search_section()`

* **Role:** The "Worker"
* **Purpose:** This function does the actual searching for **one single section** of the report. It takes a section topic
    (e.g., "*A. Wave-Particle Duality*"), runs all the different searches (Tavily, arXiv, News, etc.) concurrently for that topic,
    gathers the results, and tags each result with the original section name. This tagging is crucial so the writer agent knows
    which information belongs to which section.

### 2. `_run_concurrent_searches()`

* **Role:** The "Manager" or "Coordinator"
* **Purpose:** This function manages the entire search operation. It takes the full `outline` (the list of all sections from the planner) 
    and creates a `search_section` task for **every single section in that outline**. It then runs all of these tasks at the same time to 
    make the research process as fast as possible. Its final contribution is to collect the results from all the individual section searches
    and flatten them into one big list.

### 3. `run_searcher_agent()`

* **Role:** The "Public Entry Point"
* **Purpose:** This is the main function that the `graph.py` file calls to start the entire search process. It acts as a clean interface,
    hiding the complexity of the asynchronous code. Its job is to kick off the "Manager" (`_run_concurrent_searches`), wait for it to finish,
    perform some final logging, and then return the complete, flattened list of all search results back to the graph so the next agent
    (the writer) can use it.
'''