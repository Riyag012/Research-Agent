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

async def _run_concurrent_searches(outline: list, topic: str):
    """
    Manages the concurrent execution of comprehensive searches for all sections.
    """
    semaphore = asyncio.Semaphore(5)  # Limit concurrent sections being processed
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