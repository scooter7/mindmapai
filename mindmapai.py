import streamlit as st
import openai
import json
import requests  # New import for URL validation
from streamlit_agraph import agraph, Node, Edge, Config

# Set the page layout to wide for more horizontal space
st.set_page_config(layout="wide")

# Set your OpenAI API key from Streamlit secrets
openai.api_key = st.secrets["openai"]["api_key"]

st.title("Interactive Mindmapping Tool")

# =============================================================================
# Session State Initialization
# =============================================================================
if "mindmap_data" not in st.session_state:
    st.session_state["mindmap_data"] = None
if "topic_input" not in st.session_state:
    st.session_state["topic_input"] = ""
if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # to store conversation messages

# =============================================================================
# Helper Function: Validate URLs
# =============================================================================
def is_valid_url(url):
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

# =============================================================================
# Example Topic Button (to auto-fill the topic text area)
# =============================================================================
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("Load Example Topic"):
        st.session_state["topic_input"] = (
            "AI and machine learning skills needed for manufacturing. "
            "Provide a comprehensive mindmap that covers training programs, "
            "community colleges in Iowa, online courses, and industry certifications. "
            "Ensure that any resource links are valid and reference relevant news stories or online articles discussing the topic."
        )
with col2:
    st.markdown(
        "Click **Load Example Topic** to auto-fill the text field with an example. "
        "You can modify the text if needed before generating the mindmap."
    )

# =============================================================================
# Topic Input Field
# =============================================================================
topic = st.text_area(
    "Enter a topic for the mindmap:",
    placeholder="e.g., AI skills needed in the manufacturing industry",
    value=st.session_state["topic_input"],
    key="topic_input",
    height=100
)

# =============================================================================
# Generate Mindmap Button and GPT‑4 API Call
# =============================================================================
if st.button("Generate Mindmap"):
    if topic.strip():
        with st.spinner("Generating mindmap..."):
            prompt = (
                f"Generate a JSON structure for a comprehensive mindmap on the topic: '{topic}'. "
                "The JSON should include a list of nodes where each node contains 'id', 'label', and 'explanation', "
                "and optionally 'resources' which is a list of valid URLs from reputable sources that reference "
                "online educational organizations (like Coursera or EdX), educational institutions, or relevant news stories and online articles discussing the topic. Do not use generic placeholder URLs. "
                "Also, include a list of edges where each edge contains 'source' and 'target'. "
                "Output only valid JSON without any additional text or markdown formatting."
            )
            try:
                response = openai.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "You generate JSON for comprehensive interactive mindmaps with valid resource links."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=7000,
                )
                # Extract and clean up the GPT‑4 output
                mindmap_json = response.choices[0].message.content.strip()
                
                # Remove markdown formatting if present
                if mindmap_json.startswith("```"):
                    lines = mindmap_json.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].strip().startswith("```"):
                        lines = lines[:-1]
                    mindmap_json = "\n".join(lines).strip()

                # Extract the JSON substring between the first '{' and last '}'
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

# =============================================================================
# Display Interactive Mindmap
# =============================================================================
if st.session_state["mindmap_data"]:
    mindmap_data = st.session_state["mindmap_data"]

    # Prepare nodes and edges for streamlit-agraph visualization
    nodes = [Node(id=node["id"], label=node["label"], size=20)
             for node in mindmap_data.get("nodes", [])]
    edges = [Edge(source=edge["source"], target=edge["target"])
             for edge in mindmap_data.get("edges", [])]

    # Configure the agraph display with increased canvas width and node spacing.
    config = Config(
        width=1200,  # Increased canvas width for more horizontal space
        height=500,
        directed=True,
        physics=True,
        nodeHighlightBehavior=True,
        highlightColor="#F7A7A6",
        linkDistance=200  # More space between nodes
    )

    st.subheader("Interactive Mindmap")
    agraph(nodes=nodes, edges=edges, config=config)

    # Optional: Node Details via a dropdown
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

        # Ensure 'resources' is always a list and properly formatted
        resources = selected_node.get("resources", [])
        if not isinstance(resources, list):  # Ensure it's a list
            resources = [resources] if isinstance(resources, str) else []

        if resources:
            st.sidebar.subheader("Resources")
            for res in resources:
                if isinstance(res, str) and is_valid_url(res):  # Ensure valid URL before displaying
                    st.sidebar.write(f"[{res}]({res})")  # Display clickable links

# =============================================================================
# Discussion Chat Section
# =============================================================================
st.markdown("## Discussion Chat")
st.markdown("Use the chat below to discuss the topic or any specific resources.")

# Chat input field
chat_input = st.text_input("Your message:", key="chat_input")

if st.button("Send", key="send_chat"):
    if chat_input.strip():
        # Append the user's message to chat history
        st.session_state.chat_history.append({"role": "user", "message": chat_input})

        # Build conversation context with an initial system prompt
        conversation = [{"role": "system", "content": "You are an expert assisting with a discussion on the provided mindmap topic and resources."}]

        # Convert chat history items to the required format (with key 'content')
        for entry in st.session_state.chat_history:
            conversation.append({"role": entry["role"], "content": entry["message"]})

        try:
            chat_response = openai.chat.completions.create(
                model="gpt-4o",
                messages=conversation,
                temperature=0.7,
                max_tokens=7000,
            )
            bot_message = chat_response.choices[0].message.content.strip()
            st.session_state.chat_history.append({"role": "assistant", "message": bot_message})
        except Exception as e:
            st.error(f"Error generating chat response: {e}")
    else:
        st.error("Please enter a message before sending.")

# Display chat history
st.markdown("### Chat History")
for entry in st.session_state.chat_history:
    if entry["role"] == "user":
        st.markdown(f"**User:** {entry['message']}")
    else:
        st.markdown(f"**Assistant:** {entry['message']}")
