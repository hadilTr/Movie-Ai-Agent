import streamlit as st
import requests
import json

# API Configuration
API_URL = "http://localhost:8000"

st.set_page_config(page_title="Movie AI Agent", page_icon="🎬", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #FF4B4B;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎬 Movie AI Agent")
st.markdown("Ask questions about movies using natural language!")

with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Status Check
    try:
        response = requests.get(f"{API_URL}/", timeout=2)
        if response.status_code == 200:
            st.success("✅ API Connected")
        else:
            st.error("❌ API Error")
    except:
        st.error("❌ API Not Running")
        st.info("Run: `python api.py`")
    
    st.markdown("---")
    
    # Show Graph Info
    if st.button("📊 Show Database Info"):
        try:
            response = requests.get(f"{API_URL}/graph-info")
            if response.status_code == 200:
                data = response.json()
                st.json(data)
            else:
                st.error("Failed to fetch graph info")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    st.markdown("---")
    st.markdown("### 📖 Example Queries")
    examples = [
        "Find movie titled Supernatural",
        "Who directed The Matrix?",
        "Find movies about supernatural themes",
        "Show me action movies from 2020",
        "Find movies with Tom Hanks"
    ]
    
    for example in examples:
        if st.button(example, key=example):
            st.session_state.query = example

# Initialize session state
if "query" not in st.session_state:
    st.session_state.query = ""
if "history" not in st.session_state:
    st.session_state.history = []

col1, col2 = st.columns([3, 1])

with col1:
    query = st.text_input(
        "Enter your query:",
        value=st.session_state.query,
        placeholder="e.g., Find movies about space exploration",
        key="query_input"
    )

with col2:
    st.markdown("<br>", unsafe_allow_html=True)  # Spacing
    submit = st.button("🔍 Search", type="primary", use_container_width=True)

if submit and query:
    st.session_state.query = query
    
    with st.spinner("🤖 AI Agent is thinking..."):
        try:
            response = requests.post(
                f"{API_URL}/ask",
                json={"query": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data["answer"]
                
                # Add to history
                st.session_state.history.append({
                    "query": query,
                    "answer": answer
                })
                
                st.markdown("---")
                st.subheader("💡 Answer")
                st.markdown(answer)
                
            else:
                st.error(f"❌ API Error: {response.status_code}")
                st.json(response.json())
                
        except requests.exceptions.Timeout:
            st.error("⏱️ Request timed out. The query is taking too long.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Cannot connect to API. Make sure it's running on port 8000.")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

if st.session_state.history:
    st.markdown("---")
    st.subheader("📜 Query History")
    
    for i, item in enumerate(reversed(st.session_state.history[-5:])):
        with st.expander(f"Query {len(st.session_state.history) - i}: {item['query'][:50]}..."):
            st.markdown(f"**Question:** {item['query']}")
            st.markdown(f"**Answer:** {item['answer']}")

if st.session_state.history:
    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.rerun()

st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        Powered by FastAPI + LangGraph + Groq + Neo4j
    </div>
    """,
    unsafe_allow_html=True
)