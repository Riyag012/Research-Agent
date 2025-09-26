# writer.py

import asyncio
import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from .utils import clean_section_title
from langchain_google_genai import ChatGoogleGenerativeAI
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_writer_agent():
    """Initializes and returns the Writer Agent."""
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.0
        )
        # <-- FIX: The instruction to handle insufficient info is removed from this prompt
        # because it's now handled by a separate fallback logic.
        prompt_template = """
You are an expert technical writer and research assistant. Your task is to write a detailed, well-structured, and informative report section on a specific topic using the provided context.

**Instructions:**
1.  **Synthesize Information:** Read and synthesize the provided "Search Results" to understand the key facts, findings, and figures.
2.  **Write the Section:** Write a comprehensive report section for the topic: **"{section_topic}"**.
3.  **Ground Your Writing:** Base your writing *only* on the information given in the search results. Do not add any information from outside the provided context.
4.  **Format Correctly:** The output should be a single block of Markdown text. Do not include a title or heading for the section; just write the body content.

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
    Asynchronously writes a single section of the report. If search results are empty or
    insufficient, it uses a fallback mechanism to generate a general summary.
    """
    async with semaphore:
        # Increased sleep time to avoid hitting API rate limits.
        # 15 requests/minute = 1 request every 4 seconds. 5 seconds is a safe buffer.
        await asyncio.sleep(5)

        cleaned_topic = clean_section_title(section_topic)
        logging.info(f"Starting to write section: '{cleaned_topic}'")
        
        section_context = [
            res for res in search_results 
            if res and res.get('section') == section_topic
        ]

        context_str = "\n\n---\n\n".join([
            f"**Source Title:** {res.get('title', 'N/A')}\n"
            f"**Content:** {res.get('summary') or res.get('content', 'N/A')}"
            for res in section_context
        ])
        
        is_sufficient = len(context_str) > 250 and len(section_context) > 0

        try:
            if is_sufficient:
                logging.info(f"Sufficient context found for '{cleaned_topic}'. Writing from search results.")
                response = await writer_agent.ainvoke({"section_topic": cleaned_topic, "context": context_str})
                section_content = response.content
            else:
                logging.warning(f"Insufficient context for '{cleaned_topic}'. Using LLM fallback.")
                
                fallback_llm = writer_agent.steps[-1]
                fallback_prompt_template = """
You are an expert technical writer. The search for the section topic "{section_topic}" yielded insufficient information.
To ensure the report is complete, please write a brief, general, and high-level summary of this topic based on your own knowledge.
IMPORTANT: The entire summary MUST be formatted in italics and must begin with the phrase '*Generated using LLM due to insufficient search results.*'

**Example Output:**
*Generated using LLM due to insufficient search results.*
*This is a brief, italicized summary of the topic based on general knowledge...*
"""
                fallback_prompt = ChatPromptTemplate.from_template(fallback_prompt_template)
                fallback_chain = fallback_prompt | fallback_llm
                
                response = await fallback_chain.ainvoke({"section_topic": cleaned_topic})
                section_content = response.content
            
            final_section = f"### {cleaned_topic}\n\n{section_content}"
            logging.info(f"Finished writing section: '{cleaned_topic}'")
            return final_section
            
        except Exception as e:
            logging.error(f"An error occurred while writing section '{cleaned_topic}': {e}")
            return f"### {cleaned_topic}\n\nError: Could not generate content for this section due to an API error: {e}"

async def _run_concurrent_writes(writer_agent, outline: list, search_results: list):
    """
    Manages the concurrent execution of writing all sections.
    """
    semaphore = asyncio.Semaphore(3)
    
    tasks = [
        write_section(writer_agent, section, search_results, semaphore)
        for section in outline
    ]
    
    written_sections = await asyncio.gather(*tasks, return_exceptions=True)
    return written_sections

def run_writer_agent(writer_agent, outline: list, search_results: list) -> list:
    """
    Entry point for running the writer agent.
    """
    logging.info("Writer Agent starting to write all sections.")
    
    if not isinstance(outline, list) or not outline:
        logging.error("Writer agent received an invalid or empty outline.")
        return ["Error: No outline was provided to the writer."]
    
    try:
        sections_content = asyncio.run(_run_concurrent_writes(writer_agent, outline, search_results))
        return sections_content
    except Exception as e:
        logging.error(f"An unexpected error occurred in the writer agent: {e}")
        return [f"An unexpected error occurred during the writing phase: {e}"]

