# writer.py

import asyncio
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from .utils import clean_section_title

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_writer_agent():
    """Initializes and returns the Writer Agent."""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
        prompt_template = """
You are an expert technical writer and research assistant. Your task is to write a detailed, well-structured, and informative report section on a specific topic using the provided context.

**Instructions:**
1.  **Synthesize Information:** Read and synthesize the provided "Search Results" to understand the key facts, findings, and figures.
2.  **Write the Section:** Write a comprehensive report section for the topic: **"{section_topic}"**.
3.  **Ground Your Writing:** Base your writing *only* on the information given in the search results. Do not add any information from outside the provided context.
4.  **Format Correctly:** The output should be a single block of Markdown text. Do not include a title or heading for the section; just write the body content.
5.  **Handle Insufficient Information:** If the search results are empty or insufficient to write a meaningful section, you MUST output the single phrase: "Insufficient information to write this section."

**Search Results:**
{context}
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        writer_agent = prompt | llm
        logging.info("Writer Agent initialized successfully.")
        return writer_agent
    except Exception as e:
        logging.error(f"Error initializing Writer Agent: {e}")
        return None

async def write_section(writer_agent, section_topic: str, search_results: list, semaphore: asyncio.Semaphore):
    """
    Asynchronously writes a single section of the report.
    """
    async with semaphore:
        ## THE FIX: Add a delay to respect the 15 requests/minute limit of the Gemini free tier.
        ## This prevents 429 errors and long retry waits. (60 seconds / 15 RPM = 4 seconds/request)
        await asyncio.sleep(4)

        cleaned_topic = clean_section_title(section_topic)
        logging.info(f"Starting to write section: '{cleaned_topic}'")
        
        section_context = [
            res for res in search_results 
            if res and res.get('section') == section_topic
        ]

        if not section_context:
            logging.warning(f"No context available for section: '{cleaned_topic}'. Skipping.")
            return f"### {cleaned_topic}\n\nInsufficient information to write this section."

        context_str = "\n\n---\n\n".join([
            f"**Source Title:** {res.get('title', 'N/A')}\n"
            f"**Content:** {res.get('summary') or res.get('content', 'N/A')}"
            for res in section_context
        ])

        try:
            response = await writer_agent.ainvoke({"section_topic": cleaned_topic, "context": context_str})
            section_content = response.content
            
            final_section = f"### {cleaned_topic}\n\n{section_content}"
            logging.info(f"Finished writing section: '{cleaned_topic}'")
            return final_section
        except Exception as e:
            logging.error(f"An error occurred while writing section '{cleaned_topic}': {e}")
            return f"### {cleaned_topic}\n\nError: Could not generate content for this section due to an API error: {e}"

async def _run_concurrent_writes(writer_agent, search_results: list):
    """
    Manages the concurrent execution of writing all sections.
    """
    semaphore = asyncio.Semaphore(2) # Keep semaphore low as a backup control
    
    unique_sections = sorted(list(set(res['section'] for res in search_results if res and res.get('section'))))
    
    tasks = [
        write_section(writer_agent, section, search_results, semaphore)
        for section in unique_sections
    ]
    
    written_sections = await asyncio.gather(*tasks, return_exceptions=True)
    return written_sections

def run_writer_agent(writer_agent, search_results: list) -> list:
    """
    Entry point for running the writer agent.
    """
    logging.info("Writer Agent starting to write all sections.")
    
    if not isinstance(search_results, list) or not search_results:
        logging.error("Writer agent received invalid or empty search results.")
        return ["Error: No search results were provided to the writer."]
    
    try:
        sections_content = asyncio.run(_run_concurrent_writes(writer_agent, search_results))
        return sections_content
    except Exception as e:
        logging.error(f"An unexpected error occurred in the writer agent: {e}")
        return [f"An unexpected error occurred during the writing phase: {e}"]