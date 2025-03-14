import streamlit as st
import openai
import json
from streamlit_agraph import agraph, Node, Edge, Config

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.title("Interactive Mindmapping Tool")

# User enters a topic
topic = st.text_input("Enter a topic for the mindmap:", placeholder="e.g., AI skills needed in the manufacturing industry")

if st.button("Generate Mindmap") and topic:
    with st.spinner("Generating mindmap..."):
        # Define a prompt instructing GPT‑4 to output a JSON with nodes and edges.
        prompt = (
            f"Generate a JSON structure for a mindmap on the topic: '{topic}'. "
            "The JSON should include a list of nodes where each node contains 'id', 'label', 'explanation', and optionally 'resources' (a list of URLs), "
            "and a list of edges where each edge contains 'source' and 'target'. "
            "Output only valid JSON."
        )
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You generate JSON for interactive mindmaps."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
            )
            mindmap_json = response['choices'][0]['message']['content']
            mindmap_data = json.loads(mindmap_json)
        except Exception as e:
            st.error(f"Error generating mindmap: {e}")
            mindmap_data = None

    if mindmap_data:
        st.subheader("Generated Mindmap Data")
        st.json(mindmap_data)

        # Create Node and Edge objects for streamlit-agraph.
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

        # Additional interactivity: select a node to view details.
        node_options = {node["label"]: node for node in mindmap_data.get("nodes", [])}
        selected_label = st.selectbox("Select a node to view details:", options=list(node_options.keys()))
        if selected_label:
            selected_node = node_options[selected_label]
            st.sidebar.header(selected_node["label"])
            st.sidebar.write(selected_node.get("explanation", "No explanation provided."))
            resources = selected_node.get("resources", [])
            if resources:
                st.sidebar.subheader("Resources")
                for res in resources:
                    st.sidebar.write(res)
