# graph.py

import logging
import time # Import the time module for our delay
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

# Import agent runners
from agents.planner import get_planner_agent, run_planner_agent
from agents.searcher import run_searcher_agent
from agents.writer import get_writer_agent
from agents.editor import get_editor_agent, run_editor_agent
from agents.critiquer import get_critiquer_agent, Critique

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Define the state for our graph ---
class GraphState(TypedDict):
    topic: str
    outline: List[str]
    search_results: List[Dict]
    sections: List[str]
    completed_sections: List[str]
    report: str
    error: str
    critique: Critique
    revision_number: int
    current_section_index: int

# --- Agent Nodes ---

def planner_node(state: GraphState):
    logging.info("Executing Planner Node")
    topic = state.get("topic")
    planner_agent = get_planner_agent()
    outline = run_planner_agent(planner_agent, topic)
    return {
        "outline": outline,
        "current_section_index": 0,
        "completed_sections": []
    }

def search_node(state: GraphState):
    logging.info("Executing Search Node")
    topic = state.get("topic")
    outline = state.get("outline")
    search_results = run_searcher_agent(outline, topic)
    return {"search_results": search_results}

def write_node(state: GraphState):
    search_results = state.get("search_results")
    outline = state.get("outline")
    critique = state.get("critique")
    current_section_index = state.get("current_section_index")
    revision_number = state.get("revision_number", 0)

    current_section_topic = outline[current_section_index]
    logging.info(f"Writing section: '{current_section_topic}' (Revision #{revision_number})")

    writer_agent = get_writer_agent()
    section_context = "\n\n---\n\n".join([
        f"**Source:** {res.get('url', 'N/A')}\n**Content:** {res.get('summary', 'N/A')}"
        for res in search_results if res.get('section') == current_section_topic
    ])
    
    section_content_result = writer_agent.invoke({
        "section_topic": current_section_topic,
        "context": section_context,
        "critique": critique.critique if critique and hasattr(critique, 'critique') else "N/A"
    })
    
    return {
        "sections": [section_content_result], # Storing as a single item list
        "revision_number": revision_number + 1
    }

def critique_node(state: GraphState):
    logging.info("Executing Critique Node")
    search_results = state.get("search_results")
    outline = state.get("outline")
    current_section_index = state.get("current_section_index")
    written_section = state.get("sections")[0]

    current_section_topic = outline[current_section_index]
    section_context = "\n\n---\n\n".join([
        f"**Source:** {res.get('url', 'N/A')}\n**Content:** {res.get('summary', 'N/A')}"
        for res in search_results if res.get('section') == current_section_topic
    ])

    critiquer_agent = get_critiquer_agent()
    critique_result = critiquer_agent.invoke({
        "context": section_context,
        "section": written_section,
        "topic": current_section_topic 
    })
    logging.info(f"Critique received: Score {critique_result.score}, Feedback: '{critique_result.critique}'")
    return {"critique": critique_result}

def save_section_and_continue_node(state: GraphState):
    logging.info("Saving approved section.")
    approved_section = state.get("sections")[0]
    completed_sections = state.get("completed_sections")
    current_section_index = state.get("current_section_index")

    completed_sections.append(approved_section)
    
    # THE FIX: Add a polite delay to avoid hitting Gemini API rate limits
    logging.info("Pausing for 3 seconds before starting next section...")
    time.sleep(3)

    return {
        "completed_sections": completed_sections,
        "current_section_index": current_section_index + 1,
        "critique": None,
        "revision_number": 0,
    }

def editor_node(state: GraphState):
    logging.info("Executing Editor Node")
    topic = state.get("topic")
    completed_sections = state.get("completed_sections")
    editor_agent = get_editor_agent()
    report = run_editor_agent(editor_agent, topic, completed_sections)
    return {"report": report}

# --- Conditional Edge Functions ---

def route_to_write_or_edit(state: GraphState):
    outline = state.get("outline")
    current_section_index = state.get("current_section_index")
    if current_section_index >= len(outline):
        logging.info("All sections have been written and approved. Proceeding to editor.")
        return "editor"
    else:
        logging.info(f"Proceeding to write section {current_section_index + 1}/{len(outline)}.")
        return "writer"

def route_to_rewrite_or_save(state: GraphState):
    critique = state.get("critique")
    revision_number = state.get("revision_number", 0)
    if critique.score >= 8 or revision_number > 2:
        logging.info("Critique passed or max revisions reached. Saving section.")
        return "save_and_continue"
    else:
        logging.info("Critique failed. Looping back to writer for revision.")
        return "writer" # Corrected from "rewrite" to "writer" to loop back to the write_node

# --- Graph Builder ---

def build_graph():
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("searcher", search_node)
    workflow.add_node("writer", write_node)
    workflow.add_node("critiquer", critique_node)
    workflow.add_node("save_section_and_continue", save_section_and_continue_node)
    workflow.add_node("editor", editor_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "searcher")
    
    workflow.add_conditional_edges(
        "searcher",
        route_to_write_or_edit,
        {"writer": "writer", "editor": "editor"}
    )
    
    workflow.add_edge("writer", "critiquer")
    
    workflow.add_conditional_edges(
        "critiquer",
        route_to_rewrite_or_save,
        {"writer": "writer", "save_and_continue": "save_section_and_continue"}
    )

    workflow.add_conditional_edges(
        "save_section_and_continue",
        route_to_write_or_edit,
        {"writer": "writer", "editor": "editor"}
    )

    workflow.add_edge("editor", END)

    app = workflow.compile()
    logging.info("LangGraph workflow compiled successfully.")
    return app

