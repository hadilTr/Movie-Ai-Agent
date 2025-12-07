# 🎬 Movie AI Agent

<div align="center">

**A Neo4j-powered Agentic AI system using LangGraph, LLM tool-use, and hybrid GraphRAG retrieval**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.0+-green.svg)](https://neo4j.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Groq](https://img.shields.io/badge/Groq-LLM-purple.svg)](https://groq.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[Features](#-features) • [Demo](#-demo) • [Setup](#-setup-instructions) • [Usage](#-usage) • [Architecture](#-architecture) • [Contributing](#-contributing)

</div>

---

## ✨ Features

This project demonstrates how to build an **intelligent movie assistant** capable of:

- 🧠 **Understanding** natural language questions about movies
- 🎯 **Deciding** autonomously whether to use Cypher queries or vector search
- 🔍 **Retrieving** information from a Neo4j knowledge graph
- 💬 **Returning** structured, accurate, and context-aware answers
- 🔄 **ReAct Pattern** reasoning loop for complex queries
- 🛠️ **Tool Transparency** showing which tools were used

### Tech Stack

Built with cutting-edge technologies:

| Component | Technology |
|-----------|------------|
| **Graph Database** | Neo4j (with vector search) |
| **Agent Framework** | LangGraph (ReAct pattern) |
| **LLM** | Groq (Llama 3.3 70B) |
| **Embeddings** | HuggingFace E5-base-v2 |
| **Backend** | FastAPI |
| **Frontend** | Streamlit |
| **Retrieval** | Hybrid GraphRAG (Cypher + Vector) |

---

## 🚀 Setup Instructions

### Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **Neo4j** database (Desktop, Aura, or Docker)
- **Groq API key** (free at [console.groq.com](https://console.groq.com/))

### Step-by-Step Setup

#### 1️⃣ Clone the Repository

```bash
git clone https://github.com/hadilTr/Movie-Ai-Agent.git
cd Movie-Ai-Agent
```

#### 2️⃣ Create & Activate Virtual Environment

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

#### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root:

```env
# Groq API Key (get yours at console.groq.com)
groq_api_key=gsk_your_key_here

# Neo4j Connection
uri_neo4j=bolt://localhost:7687
user=neo4j
password=your_password_here
```

> 💡 **Tip:** Copy `.env.example` and fill in your credentials

#### 5️⃣ Start Neo4j Database

Choose your preferred method:

**Option A: Neo4j Desktop**
- Download from [neo4j.com/download](https://neo4j.com/download/)
- Create a new database
- Start the database

**Option B: Neo4j Aura (Cloud)**
- Sign up at [console.neo4j.io](https://console.neo4j.io/)
- Create a free instance
- Use provided credentials

**Option C: Docker**
```bash
docker run --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password123 \
  -d neo4j:latest
```

Verify Neo4j is running: [http://localhost:7474](http://localhost:7474)


#### 7️⃣ Run the Backend Server

```bash
python api.py
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

#### 8️⃣ Launch Streamlit UI (Optional)

In a **new terminal**:

```bash
streamlit run frontend/app.py
```

**Access the app:** [http://localhost:8501](http://localhost:8501)

#### 9️⃣ Run Evaluator (Optional)

Test the agent's performance with predefined scenarios:

```bash
python evaluate.py
```

---

## 💻 Usage

### Web Interface

1. Open [http://localhost:8501](http://localhost:8501)
2. Enter your query (e.g., "Find movies about space exploration")
3. Click **Search**
4. View the answer and which tools were used

### REST API

**Health Check:**
```bash
curl http://localhost:8000/
```

**Ask a Question:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "Find movies directed by Christopher Nolan"}'
```

**Get Database Schema:**
```bash
curl http://localhost:8000/graph-info
```

**Interactive Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Python Integration

```python
from main import run_query_with_tools

# Run a query
answer, tools_used = run_query_with_tools("Find sci-fi movies about AI")

print(f"Answer: {answer}")
print(f"Tools used: {[tool['tool_name'] for tool in tools_used]}")
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐
│   Streamlit UI  │  User Interface
│   (Frontend)    │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────────────────────┐
│         FastAPI Backend         │
│          REST API Layer         │
└───┬─────────────────────────┬───┘
    │                         │
    │ POST /ask               │ GET /graph-info
    │ (User Query)            │ (Schema Info)
    │                         │
    ▼                         ▼
┌─────────────────┐      ┌──────────────┐
│   LangGraph     │      │    Neo4j     │◄─── Direct Access
│   ReAct Agent   │      │  Graph DB    │
└────────┬────────┘      │              │
         │               └──────────────┘
    ┌────┴────────────────┐
    ▼                     ▼
┌──────────┐      ┌──────────────┐
│   Groq   │      │    Neo4j     │◄─── Agent Access
│   LLM    │      │  Graph DB +  │
│          │      │ Vector Index │
└──────────┘      └──────────────┘
```

### ReAct Agent Flow

```
User Query
↓
ReAct Agent (LLM) — Think
↓
Tool Selection — Decide: Cypher or Vector Search?
↓
Act — Call chosen tool
↓
Observe — Get tool result
↺ (loops Think → Decide → Act → Observe as needed)
↓
Final Answer — Format and respond in natural language
```

### Dual Retrieval Strategy

| Query Type | Tool | Example |
|------------|------|---------|
| **Exact Match** | `query` (Cypher) | "Find movie 'Inception'" |
| **Actor/Director** | `query` (Cypher) | "Movies with Tom Hanks" |
| **Thematic** | `vector_search` | "Space exploration movies" |
| **Conceptual** | `vector_search` | "Films about AI ethics" |

---

## 📂 Project Structure

```
Movie-AI-Agent/
│
├── 📁 __pycache__/
├── 📁 .venv/
│
├── 📁 backend/
│   └── api.py
│
├── 📁 data/
│   ├── movies.csv
│   ├── persons.csv
│   └── roles.csv
│
├── 📁 frontend/
│   └── app.py
│
├── 📁 tools/
│   ├── __pycache__/
│   ├── __init__.py
│   ├── graph_query_tool.py
│   └── search_tool.py
│
├── .env
├── .gitignore
├── generate_embeddings.py
├── main.py
├── react_agent_graph.png
├── README.md
├── requirements.txt
└── system_evaluation.py
---

## 🔧 Configuration

### Customize LLM Settings

Edit `main.py`:

```python
llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # Change model
    temperature=0,                     # 0 = deterministic, 1 = creative
    api_key=os.getenv("groq_api_key")
)
```

### Adjust System Prompt

Modify the agent's behavior in `main.py`:

```python
system_prompt = """You are a movie database assistant..."""
```

### Change Vector Search Parameters

In `tools/search_tool.py`:

```python
def vector_search(text_query: str, top_k: int = 5):  # Adjust top_k
```

---

## 🧪 Evaluation

Run the evaluation suite to test agent performance:

```bash
python evaluate.py
```

**Metrics tracked:**
- Tool selection accuracy
- Query correctness
- Response time

---

## 🐛 Troubleshooting

<details>
<summary><b>Cannot connect to Neo4j</b></summary>

**Solutions:**
- Verify Neo4j is running: [http://localhost:7474](http://localhost:7474)
- Check credentials in `.env` match your Neo4j password
- Test connection:
  ```python
  from neo4j import GraphDatabase
  driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))
  driver.verify_connectivity()
  ```
</details>

<details>
<summary><b>Groq API errors</b></summary>

**Solutions:**
- Verify API key in `.env` is correct
- Check your quota at [console.groq.com](https://console.groq.com/)
- Ensure key starts with `gsk_`
</details>

<details>
<summary><b>Module not found errors</b></summary>

**Solutions:**
```bash
# Activate virtual environment
source .venv/bin/activate  # Mac/Linux
.venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```
</details>

<details>
<summary><b>Port already in use</b></summary>

**Solutions:**
```bash
# Change API port
python api.py --port 8001

# Change Streamlit port
streamlit run frontend/app.py --server.port 8502
```
</details>

---

## 🙏 Acknowledgments

Built with open-source technologies:

- [**LangGraph**](https://github.com/langchain-ai/langgraph) - Agent framework with ReAct pattern
- [**Groq**](https://groq.com/) - Lightning-fast LLM inference
- [**Neo4j**](https://neo4j.com/) - Graph database with vector search
- [**Streamlit**](https://streamlit.io/) - Beautiful web interfaces
- [**FastAPI**](https://fastapi.tiangolo.com/) - Modern REST API framework
- [**HuggingFace**](https://huggingface.co/) - Transformer models and embeddings

---

## 📧 Contact

**Hadil** - [@hadilTr](https://github.com/hadilTr)

**Project Link:** [https://github.com/hadilTr/Movie-Ai-Agent](https://github.com/hadilTr/Movie-Ai-Agent)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

</div>
