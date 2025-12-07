from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import run_query
from tools.graph_query_tool import get_graph_schema_info

app = FastAPI(
    title="Movie AI Agent API",
    description="FastAPI backend for LangGraph Agent + Neo4j GraphRAG",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AskRequest(BaseModel):
    query: str

class AskResponse(BaseModel):
    answer: str

class GraphInfoResponse(BaseModel):
    node_labels: list
    relationship_types: list
    property_keys: list



@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "Movie AI Agent API is running", "version": "1.0.0"}


@app.post("/ask", response_model=AskResponse)
async def ask_endpoint(payload: AskRequest):
    """
    Takes a natural language question,
    sends it to the agent,
    and returns the final response.
    """
    try:
        
        answer = run_query(payload.query)
        
        return AskResponse(answer=answer)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graph-info", response_model=GraphInfoResponse)
async def graph_info():
    """
    Returns metadata about the Neo4j graph:
    - node labels
    - relationship types
    - properties
    """
    try:
        info = get_graph_schema_info()
        
        return GraphInfoResponse(
            node_labels=info["node_labels"],
            relationship_types=info["relationship_types"],
            property_keys=info["property_keys"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)