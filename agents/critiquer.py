# critiquer.py

import logging
from typing import TypedDict
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.pydantic_v1 import BaseModel, Field

# Define the output structure for the Critiquer Agent
class Critique(BaseModel):
    """
    Represents a critique of a written report section.
    It assesses whether the section is well-supported by the provided context and relevant to the topic.
    """
    score: int = Field(
        description="A score from 1-10 evaluating how well the section is grounded in the provided context and relevant to the topic. 1 is poor, 10 is excellent.",
        ge=1,
        le=10,
    )
    critique: str = Field(
        description="A detailed, constructive critique. Explain why you gave the score. Point out specific claims that are unsupported or sections that are off-topic."
    )

def get_critiquer_agent():
    """Initializes and returns the Critiquer Agent."""
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.0)
    
    structured_llm = llm.with_structured_output(Critique)

    prompt_template = """
You are an expert academic editor and fact-checker. Your task is to critique a written report section based *only* on the provided search results (context).

**Overall Section Topic:**
"{topic}"

**Written Section to Critique:**
{section}

**Search Results (Context):**
{context}

**Instructions:**
1.  **Check for Fallback:** First, check if the "Written Section" contains the exact phrase "*Generated using LLM due to insufficient search results.*". 
    -   If it does, the writer has intentionally used its fallback. In this case, you MUST give it a score of 8 and a simple critique like "Writer fallback detected due to insufficient context. Passing."
2.  **Primary Goal: Grounding.** If no fallback is detected, your main job is to determine if all claims in the "Written Section" are fully supported by the "Search Results."
3.  **Secondary Goal: Relevance.** You must also check if the information used from the context is relevant to the "Overall Section Topic." If the section discusses something completely unrelated (e.g., database technology when the topic is quantum physics), the score must be low (e.g., 3-4).
4.  **Scoring (if no fallback):** Assign a score from 1 to 10.
    -   A score of 8-10 means the section is well-supported and relevant.
    -   A score below 8 means there are significant issues with unsupported claims or irrelevant information.
5.  **Provide Detailed Feedback:** In your critique, you MUST list every specific claim that is not supported by the context or is off-topic. Be precise.
"""
    prompt = ChatPromptTemplate.from_template(prompt_template)
    critiquer_agent = prompt | structured_llm
    logging.info("Critiquer Agent initialized successfully.")
    return critiquer_agent

