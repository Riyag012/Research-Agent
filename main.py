import streamlit as st
import logging
from graph import build_graph

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    The main function to run the Streamlit user interface.
    """
    st.set_page_config(page_title="Automated Research Report Generator", layout="wide")
    
    st.title("🤖 Automated Research Report Generator")
    st.write(
        "Enter a complex research topic below, and the multi-agent system will generate a comprehensive report for you."
    )

    # User input
    topic = st.text_input("Enter the research topic:", placeholder="e.g., The future of gene editing with CRISPR")

    if st.button("Generate Report"):
        if not topic:
            st.error("Please enter a research topic.")
            return

        try:
            with st.spinner("The agents are at work... This may take a few minutes."):
                
                # Build the graph
                app = build_graph()

                # Initial state for the graph
                initial_state = {"topic": topic, "error": None}

                st.write("---")
                st.write("### Agent Workflow Log:")

                final_state = None
                # Stream the events from the graph execution
                config = {"recursion_limit": 200}

                for event in app.stream(initial_state, config=config):
                    for key, value in event.items():
                        # The key is the name of the node that just ran
                        agent_name = key
                        
                        # The value is the dictionary returned by that node
                        agent_output = value
                        
                        st.write(f"**Agent:** `{agent_name}` has finished.")
                        
                        # Log the output for debugging/transparency
                        if "outline" in agent_output:
                            st.text("Generated Outline...")
                        if "search_results" in agent_output:
                            st.text("Completed Research...")
                        if "sections" in agent_output:
                             st.text("Finished Writing Sections...")
                        if "report" in agent_output:
                            st.text("Final Report Assembled.")

                        final_state = value

                st.success("Report generation complete!")
                st.write("---")
                
                # Display the final report
                if final_state and final_state.get("report"):
                    st.markdown(final_state["report"])
                else:
                    st.error("Something went wrong. The final report could not be generated.")
                    if final_state and final_state.get("error"):
                        st.error(f"Error details: {final_state['error']}")

        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            logging.error("An unexpected error occurred in the Streamlit app", exc_info=True)


if __name__ == "__main__":
    main()

