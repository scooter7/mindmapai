import streamlit as st
import openai
import json
from streamlit_agraph import agraph, Node, Edge, Config

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.title("Interactive Mindmapping Tool")

# Initialize session state for mindmap data if not already set
if "mindmap_data" not in st.session_state:
    st.session_state["mindmap_data"] = None

# Topic input
topic = st.text_input(
    "Enter a topic for the mindmap:",
    placeholder="e.g., AI skills needed in the manufacturing industry",
    key="topic_input"
)

# Generate button
if st.button("Generate Mindmap"):
    if topic:
        with st.spinner("Generating mindmap..."):
            prompt = (
                f"Generate a JSON structure for a mindmap on the topic: '{topic}'. "
                "The JSON should include a list of nodes where each node contains 'id', 'label', 'explanation', "
                "and optionally 'resources' (a list of URLs), and a list of edges where each edge contains 'source' and 'target'. "
                "Output only valid JSON."
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
                # Use dot-notation to extract the generated JSON
                mindmap_json = response.choices[0].message.content
                mindmap_data = json.loads(mindmap_json)
                st.session_state["mindmap_data"] = mindmap_data
            except Exception as e:
                st.error(f"Error generating mindmap: {e}")
    else:
        st.error("Please enter a topic.")

# If mindmap data exists in session state, display the interactive mindmap
if st.session_state["mindmap_data"]:
    mindmap_data = st.session_state["mindmap_data"]

    # Prepare nodes and edges for streamlit-agraph
    nodes = []
    for node in mindmap_data.get("nodes", []):
        nodes.append(Node(id=node["id"], label=node["label"], size=20))
        
    edges = []
    for edge in mindmap_data.get("edges", []):
        edges.append(Edge(source=edge["source"], target=edge["target"]))

    # Configure agraph display options
    config = Config(
        width=800,
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
    )

    st.subheader("Interactive Mindmap")
    agraph(nodes=nodes, edges=edges, config=config)

    # Additional interactivity: select a node to view its details.
    node_options = {node["label"]: node for node in mindmap_data.get("nodes", [])}
    selected_label = st.selectbox(
        "Select a node to view details:",
        options=list(node_options.keys()),
        key="node_select"
    )
    if selected_label:
        selected_node = node_options[selected_label]
        st.sidebar.header(selected_node["label"])
        st.sidebar.write(selected_node.get("explanation", "No explanation provided."))
        resources = selected_node.get("resources", [])
        if resources:
            st.sidebar.subheader("Resources")
            for res in resources:
                st.sidebar.write(res)
