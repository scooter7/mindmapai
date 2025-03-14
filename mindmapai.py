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

# Use a larger text area for topic input
topic = st.text_area(
    "Enter a topic for the mindmap:",
    placeholder="e.g., AI skills needed in the manufacturing industry",
    key="topic_input",
    height=100
)

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

    # Configure agraph display options.
    # 'linkDistance' is increased to provide ample space between nodes.
    config = Config(
        width=800,
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        linkDistance=200  # Adjust this value to increase or decrease spacing
    )

    st.subheader("Interactive Mindmap")
    agraph(nodes=nodes, edges=edges, config=config)

    # Additional interactivity: using the dropdown below to select a node and display its details in the sidebar.
    # (If you prefer node-click interactivity, additional event handling from streamlit-agraph may be required.)
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
