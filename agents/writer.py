# writer.py

import logging
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

def get_writer_agent():
    """Initializes and returns the Writer Agent."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)
    
    prompt_template = """
You are an expert technical writer. Your task is to write a detailed, well-structured, and informative report section on a specific topic using the provided context.

**Topic:**
"{section_topic}"

**Previous Critique (if any):**
{critique}

**Search Results (Context):**
{context}

**Instructions:**
1.  **Synthesize Information:** Read and synthesize the provided "Search Results" to understand the key facts, findings, and figures.
2.  **Check for Relevance:** Before writing, ensure the provided context is relevant to the section topic. If the context is about a completely different subject (e.g., Elasticsearch when the topic is Quantum Computing), you MUST ignore it and treat the information as insufficient.
3.  **Address Critique:** If a "Previous Critique" is provided and is not "N/A", you MUST address its feedback in your new version.
4.  **Ground Your Writing:** Base your writing *only* on the information given in the search results. Do not add any information from outside the provided context.
5.  **Format Correctly:** The output should be a single block of Markdown text. Do not include a title or heading.
6.  **Handle Insufficient Information:** If the search results are empty or irrelevant, you MUST output the single phrase: "*Generated using LLM due to insufficient search results.*" followed by a brief, general summary of the topic in italics based on your own knowledge.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    writer_agent = prompt | llm | StrOutputParser()
    logging.info("Writer Agent initialized successfully.")
    return writer_agent

