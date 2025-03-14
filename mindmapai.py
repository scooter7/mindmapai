import streamlit as st
import openai
import json
from streamlit_agraph import agraph, Node, Edge, Config

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.title("Interactive Mindmapping Tool")

# Use session state to store the generated mindmap
if "mindmap_data" not in st.session_state:
    st.session_state["mindmap_data"] = None

# Topic input
topic = st.text_input(
    "Enter a topic for the mindmap:",
    placeholder="e.g., AI skills needed in the manufacturing industry",
    key="topic_input"
)

# Generate mindmap when button is clicked
if st.button("Generate Mindmap"):
    if topic:
        with st.spinner("Generating mindmap..."):
            prompt = (
                f"Generate a JSON structure for a mindmap on the topic: '{topic}'. "
                "The JSON should include a list of nodes where each node contains 'id', 'label', 'explanation', "
                "and optionally 'resources' (a list of URLs), and a list of edges where each edge contains 'source' and 'target'. "
                "Output only valid JSON without any additional text or markdown formatting."
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You generate JSON for interactive mindmaps."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                )
                # Extract and clean up the GPT‑4 output
                mindmap_json = response.choices[0].message.content.strip()
                # Remove markdown code block formatting if present
                if mindmap_json.startswith("```"):
                    lines = mindmap_json.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    mindmap_json = "\n".join(lines).strip()
                if not mindmap_json:
                    raise ValueError("Received empty response from GPT-4.")
                mindmap_data = json.loads(mindmap_json)
                st.session_state["mindmap_data"] = mindmap_data
            except Exception as e:
                st.error(f"Error generating mindmap: {e}")
    else:
        st.error("Please enter a topic.")

# If a mindmap is stored in session state, display the interactive graph.
if st.session_state["mindmap_data"]:
    mindmap_data = st.session_state["mindmap_data"]

    # Prepare nodes and edges for streamlit-agraph
    nodes = []
    for node in mindmap_data.get("nodes", []):
        nodes.append(Node(id=node["id"], label=node["label"], size=20))
        
    edges = []
    for edge in mindmap_data.get("edges", []):
        edges.append(Edge(source=edge["source"], target=edge["target"]))

    # Configure the agraph display options
    config = Config(
        width=800,
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
    )

    st.subheader("Interactive Mindmap")
    # agraph returns event data when the user interacts with the graph.
    agraph_response = agraph(nodes=nodes, edges=edges, config=config)

    # When a node is clicked, display its details in the sidebar.
    if agraph_response:
        # Check if a node has been selected (event key may vary based on the version)
        if "event" in agraph_response and agraph_response["event"] == "node_selected":
            selected_node_id = agraph_response.get("id")
            selected_node = next(
                (node for node in mindmap_data.get("nodes", []) if node["id"] == selected_node_id),
                None,
            )
            if selected_node:
                st.sidebar.header(selected_node["label"])
                st.sidebar.write(selected_node.get("explanation", "No explanation provided."))
                resources = selected_node.get("resources", [])
                if resources:
                    st.sidebar.subheader("Resources")
                    for res in resources:
                        st.sidebar.write(res)
