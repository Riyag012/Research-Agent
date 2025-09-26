from graph import build_graph

def main():
    """
    Builds the graph and saves a visual representation to a file.
    """
    # Build the graph from your existing configuration
    app = build_graph()

    # Generate and save the image
    # The .get_graph() method returns a drawable object, and .draw_mermaid_png()
    # renders it to a file.
    try:
        image_data = app.get_graph().draw_mermaid_png()
        with open("research_agent_graph.png", "wb") as f:
            f.write(image_data)
        print("Successfully generated the graph visualization!")
        print("Please check the 'research_agent_graph.png' file.")
    except Exception as e:
        print(f"An error occurred while generating the graph image: {e}")
        print("Please ensure you have the required dependencies for visualization (e.g., 'playwright').")
        print("You can try installing it with: playwright install")


if __name__ == "__main__":
    main()
