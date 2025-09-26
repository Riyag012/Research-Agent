import os
import logging
from typing import List
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_vertexai import ChatVertexAI
from google.oauth2 import service_account
from langchain_google_genai import ChatGoogleGenerativeAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

def get_editor_agent():
    """Initializes and returns the Editor Agent's LLM chain."""
    try:
        # credentials_path = "D:/Projects/Research Agent/credentials.json"
        # credentials = service_account.Credentials.from_service_account_file(credentials_path)
        # llm = ChatVertexAI(
        #     model_name="gemini-1.5-flash",
        #     project="research-agent-473309",
        #     credentials=credentials,
        #     temperature=0.0
        # )
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            # project="research-agent-473309",
            # credentials=credentials,
            temperature=0.0
        )
        editor_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert editor for technical research reports.
                    Your task is to take a collection of individually written report sections and a topic,
                    and format them into a single, cohesive, and polished report.

                    Follow these instructions:
                    1.  **Assemble the Report:** Combine all the provided sections into one document.
                    2.  **Add a Title:** Create a suitable title for the report based on the original topic.
                    3.  **Create a Table of Contents:** Generate a markdown-formatted table of contents.
                    4.  **Proofread and Polish:** Review the entire document for grammatical errors, awkward phrasing, and inconsistencies.
                    5.  **Improve Transitions:** Ensure smooth transitions between sections to improve the overall flow.
                    6.  **Final Formatting:** The final output must be a single, well-formatted Markdown document.
                    7.  **IMPORTANT - Preserve Notices:** If any section begins with an italicized notice like '*Generated using LLM due to insufficient search results.*', you MUST preserve this notice and its italics exactly as it is at the end of its section in the final report. Do not edit or remove it. Only italicize this warning '*Generated using LLM due to insufficient search results.*' keeping rest of the section content normal.
                    """
                ),
                ("user",
                 "**Original Topic:**\n{topic}\n\n"
                 "**Report Sections (in order):**\n{report_sections}\n\n"
                 "Please assemble, edit, and format the final report now."
                 ),
            ]
        )
        editor_agent = editor_prompt | llm
        logging.info("Editor Agent initialized successfully.")
        return editor_agent
    except Exception as e:
        logging.error(f"Error initializing Editor Agent: {e}")
        raise

def run_editor_agent(agent, topic: str, sections: List[str]) -> str:
    """
    Runs the Editor Agent to assemble and polish the final report.
    
    Args:
        agent: The editor agent chain.
        topic (str): The original research topic.
        sections (List[str]): The list of written report sections.
        
    Returns:
        str: The final, formatted report in Markdown.
    """
    logging.info("Editor Agent is starting to assemble the final report.")
    
    # Simple assembly first
    collated_sections = "\n\n---\n\n".join(sections)
    
    try:
        response = agent.invoke({
            "topic": topic,
            "report_sections": collated_sections
        })
        logging.info("Editor Agent finished.")
        return response.content
    except Exception as e:
        logging.error(f"Error running Editor Agent: {e}")
        return "Error: Could not produce the final report."

