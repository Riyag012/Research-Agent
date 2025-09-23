# planner.py

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_planner_agent():
    """Initializes and returns the Planner Agent."""
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.0)
        
        ## THE FIX: Modify the instructions to request a smaller outline.
        ## This ensures the total number of sections is less than the daily API limit of 50.
        prompt_template = """
You are an expert research assistant. Your task is to create a concise, structured outline for a technical report on the given topic.

**Topic:**
{topic}

**Instructions:**
1.  Generate a hierarchical outline with 3-4 main sections.
2.  Each main section should have 2-3 subsections.
3.  Use Markdown for formatting (e.g., use '*' for bullet points).
4.  Output ONLY the Markdown outline. Do not include any introductory text, concluding text, or any other conversational language.

**Example Output:**
* **I. Introduction**
* A. Background on Topic
* B. Problem Statement
* **II. Main Section Two**
* A. Sub-point A
* B. Sub-point B
"""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        planner_agent = prompt | llm
        logging.info("Planner Agent initialized successfully.")
        return planner_agent
    except Exception as e:
        logging.error(f"Error initializing Planner Agent: {e}")
        return None

def run_planner_agent(planner_agent, topic: str) -> list:
    """Runs the planner agent to generate a research report outline."""
    logging.info(f"Running Planner Agent for topic: {topic}")
    try:
        response = planner_agent.invoke({"topic": topic})
        
        outline = [line.strip() for line in response.content.split('\n') if line.strip()]

        if not outline or len(outline) > 50:
            logging.error(f"Planner agent generated an invalid or excessively long outline (sections: {len(outline)}).")
            return ["Error: Planner failed to generate a valid outline."]
            
        logging.info("Planner Agent finished successfully.")
        return outline
    except Exception as e:
        logging.error(f"An error occurred in the planner agent: {e}")
        return [f"Error in planner: {e}"]