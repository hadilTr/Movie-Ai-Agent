# tools/graph_query_tool.py
from neo4j import GraphDatabase
from dotenv import load_dotenv
from langchain_core.tools import tool
import os
import json

load_dotenv()

@tool
def query(cypher_query: str) -> str:
   
    if not cypher_query:
        return json.dumps({"error": "No Cypher query provided."})

    try:
        uri = os.getenv("uri_neo4j")
        user = os.getenv("user")
        password = os.getenv("password")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session() as session:
            result = session.run(cypher_query)
            data = [record.data() for record in result]
        
        driver.close()
        
        if not data:
            return "No results found for this query."
        
        return json.dumps(data, indent=2)

    except Exception as e:
        return json.dumps({"error": str(e)})


def get_graph_schema_info():
    """Retrieve metadata about the Neo4j graph: node labels, relationship types, property keys"""
    uri = os.getenv("uri_neo4j")
    user = os.getenv("user")
    password = os.getenv("password")
    driver = GraphDatabase.driver(uri, auth=(user, password))
    
    with driver.session() as session:
        node_labels = session.run("CALL db.labels()").values()
        relationship_types = session.run("CALL db.relationshipTypes()").values()
        property_keys = session.run("CALL db.propertyKeys()").values()
    
    driver.close()
    
    return {
        "node_labels": [label[0] for label in node_labels],
        "relationship_types": [rel_type[0] for rel_type in relationship_types],
        "property_keys": [prop_key[0] for prop_key in property_keys],
    }


# Example usage
if __name__ == "__main__":
    cypher = "MATCH (m:movie) WHERE m.title = 'Supernatural' RETURN m LIMIT 5"
    result = query.invoke({"cypher_query": cypher})
    print("Query Result:", result)