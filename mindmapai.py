import streamlit as st
import openai
import json
from streamlit_agraph import agraph, Node, Edge, Config

# Set the page layout to wide for more horizontal space
st.set_page_config(layout="wide")

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.title("Interactive Mindmapping Tool")

# -------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------
if "mindmap_data" not in st.session_state:
    st.session_state["mindmap_data"] = None
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""

# -------------------------------------------------------------------
# Example Topic Button
# -------------------------------------------------------------------
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Load Example Topic"):
        st.session_state["topic_input"] = (
            "AI and machine learning skills needed for manufacturing. "
            "Provide a comprehensive mindmap that covers training programs, "
            "community colleges in Iowa, and online courses. Include links to community colleges in Iowa offering AI training, "
            "online resources, and industry certifications that support learning and development."
        )
with col2:
    st.markdown(
        "Click **Load Example Topic** to auto-fill the text field with an example. "
        "You can modify the text if needed before generating the mindmap."
    )

# -------------------------------------------------------------------
# Topic Input Field
# -------------------------------------------------------------------
topic = st.text_area(
    "Enter a topic for the mindmap:",
    placeholder="e.g., AI skills needed in the manufacturing industry",
    value=st.session_state["topic_input"],
    key="topic_input",
    height=100
)

# -------------------------------------------------------------------
# Generate Mindmap Button and GPT-4 API Call
# -------------------------------------------------------------------
if st.button("Generate Mindmap"):
    if topic.strip():
        with st.spinner("Generating mindmap..."):
            prompt = (
                f"Generate a JSON structure for a comprehensive mindmap on the topic: '{topic}'. "
                "The JSON should include a list of nodes where each node contains 'id', 'label', 'explanation', "
                "and optionally 'resources' (a list of URLs), and a list of edges where each edge contains 'source' and 'target'. "
                "Output only valid JSON without any additional text or markdown formatting."
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You generate JSON for interactive mindmaps."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=5000,
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
                
                # Extract only the JSON part by taking the substring from the first '{' to the last '}'
                start_index = mindmap_json.find("{")
                end_index = mindmap_json.rfind("}")
                if start_index == -1 or end_index == -1:
                    raise ValueError("Could not find valid JSON boundaries in the response.")
                mindmap_json = mindmap_json[start_index:end_index + 1]
                
                if not mindmap_json:
                    raise ValueError("Received empty JSON after extraction from GPT-4 response.")
                
                mindmap_data = json.loads(mindmap_json)
                st.session_state["mindmap_data"] = mindmap_data
            except Exception as e:
                st.error(f"Error generating mindmap: {e}")
    else:
        st.error("Please enter a topic.")

# -------------------------------------------------------------------
# Display Interactive Mindmap
# -------------------------------------------------------------------
if st.session_state["mindmap_data"]:
    mindmap_data = st.session_state["mindmap_data"]

    # Prepare nodes and edges for visualization
    nodes = [Node(id=node["id"], label=node["label"], size=20)
             for node in mindmap_data.get("nodes", [])]
    edges = [Edge(source=edge["source"], target=edge["target"])
             for edge in mindmap_data.get("edges", [])]

    config = Config(
        width=1200,           # Increased canvas width
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        linkDistance=200      # More space between nodes
    )

    st.subheader("Interactive Mindmap")
    agraph(nodes=nodes, edges=edges, config=config)

    # Node Detail Display via dropdown
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
