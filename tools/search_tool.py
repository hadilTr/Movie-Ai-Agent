# tools/search_tool.py
from neo4j import GraphDatabase
from dotenv import load_dotenv
from transformers import AutoModel, AutoTokenizer
from langchain_core.tools import tool
import os
import torch
import json

load_dotenv()

class SearchTool:
    def __init__(self):
        self.uri = os.getenv("uri_neo4j")
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

        self.model = AutoModel.from_pretrained("intfloat/e5-base-v2")  
        self.tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-base-v2")
        self.embedding_property = "plot_embedding"
        self.vector_index_name = "movies_plot_index"

    def embed(self, text: str):
        """
        Creates an embedding vector from text using Hugging Face transformer.
        Returns a plain Python list.
        """
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        last_hidden = outputs.last_hidden_state
        mask = inputs['attention_mask'].unsqueeze(-1)
        summed = (last_hidden * mask).sum(1)
        counted = mask.sum(1)
        embedding = (summed / counted).squeeze(0).tolist()
        return embedding
    
    def close(self):
        self.driver.close()


@tool
def vector_search(text_query: str, top_k: int = 5) -> str:
    """
    Perform a semantic vector search on movie plots in Neo4j.
    
    Args:
        text_query: The search query describing themes, plot, or concepts
        top_k: Number of results to return (default: 5)
        
    Returns:
        Matching movies as a JSON-formatted string with title, year, and similarity score
    """
    try:
        # Initialize search tool
        search_tool = SearchTool()
        embedding_vector = search_tool.embed(text_query)

        cypher = f"""
        CALL db.index.vector.queryNodes('{search_tool.vector_index_name}', $top_k, $embedding)
        YIELD node, score
        RETURN node.title AS title, node.year AS year, node.plot AS plot, score
        ORDER BY score DESC
        """

        with search_tool.driver.session() as session:
            result = session.run(cypher, {
                "top_k": top_k,
                "embedding": embedding_vector
            })
            data = [record.data() for record in result]
        
        search_tool.close()
        
        # Return message if no results
        if not data:
            return "No matching movies found for this search."
        
        # Convert to JSON string
        return json.dumps(data, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


# Example usage
if __name__ == "__main__":
    result = vector_search.invoke({
        "text_query": "supernatural horror movies",
        "top_k": 3
    })
    print("Search Result:", result)