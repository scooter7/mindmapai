import streamlit as st
import openai
import json
from streamlit_cytoscape import st_cytoscape

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

        # Transform nodes and edges into Cytoscape elements.
        cytoscape_elements = []

        # Process nodes: wrap each node in a 'data' dictionary.
        for node in mindmap_data.get("nodes", []):
            cytoscape_elements.append({
                "data": {
                    "id": node["id"],
                    "label": node["label"],
                    "explanation": node.get("explanation", ""),
                    "resources": node.get("resources", [])
                }
            })

        # Process edges.
        for edge in mindmap_data.get("edges", []):
            cytoscape_elements.append({
                "data": {
                    "source": edge["source"],
                    "target": edge["target"]
                }
            })

        st.subheader("Interactive Mindmap")
        # Render the mindmap using streamlit-cytoscape.
        cyto_response = st_cytoscape(
            elements=cytoscape_elements,
            layout={"name": "breadthfirst"},
            style={"width": "100%", "height": "600px"},
        )

        # When a node is clicked, st_cytoscape returns event data.
        if cyto_response:
            selected_node = cyto_response.get("selectedNode")
            if selected_node:
                # Locate the node details from the original mindmap_data.
                node_details = next((node for node in mindmap_data.get("nodes", []) if node["id"] == selected_node), None)
                if node_details:
                    st.sidebar.header(node_details["label"])
                    st.sidebar.write(node_details.get("explanation", "No explanation provided."))
                    resources = node_details.get("resources", [])
                    if resources:
                        st.sidebar.subheader("Resources")
                        for res in resources:
                            st.sidebar.write(res)
