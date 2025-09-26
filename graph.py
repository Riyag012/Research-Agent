# graph.py

import logging
import time
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

# Import agent runners
from agents.planner import get_planner_agent, run_planner_agent
from agents.searcher import run_searcher_agent
from agents.writer import get_writer_agent, run_writer_agent
from agents.editor import get_editor_agent, run_editor_agent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Define the state for our graph
class GraphState(TypedDict):
    topic: str
    outline: List[str]
    search_results: List[Dict]
    sections: List[str]
    report: str
    error: str

# --- Agent Nodes ---

def planner_node(state: GraphState):
    logging.info("Executing Planner Node")
    topic = state.get("topic")
    planner_agent = get_planner_agent()
    outline = run_planner_agent(planner_agent, topic)
    return {"outline": outline}

def search_node(state: GraphState):
    logging.info("Executing Search Node")
    topic = state.get("topic")
    outline = state.get("outline")
    search_results = run_searcher_agent(outline, topic)
    return {"search_results": search_results}

def write_node(state: GraphState):
    logging.info("Executing Write Node")
    search_results = state.get("search_results")
    outline = state.get("outline")  # <-- FIX: Get the original outline
    writer_agent = get_writer_agent()
    # <-- FIX: Pass the outline to the writer to ensure all sections are processed
    sections = run_writer_agent(writer_agent, outline, search_results)
    return {"sections": sections}

def editor_node(state: GraphState):
    logging.info("Executing Editor Node")
    
    logging.info("Pausing for 30 seconds before starting editor to respect API rate limits.")
    time.sleep(30)
    
    topic = state.get("topic")
    sections = state.get("sections")
    editor_agent = get_editor_agent()
    report = run_editor_agent(editor_agent, topic, sections)
    return {"report": report}

# --- Graph Builder ---

def build_graph():
    """Builds and compiles the LangGraph workflow."""
    workflow = StateGraph(GraphState)

    workflow.add_node("planner", planner_node)
    workflow.add_node("searcher", search_node)
    workflow.add_node("writer", write_node)
    workflow.add_node("editor", editor_node)

    workflow.set_entry_point("planner")
    workflow.add_edge("planner", "searcher")
    workflow.add_edge("searcher", "writer")
    workflow.add_edge("writer", "editor")
    workflow.add_edge("editor", END)

    app = workflow.compile()
    logging.info("LangGraph workflow compiled successfully.")
    return app
