import os
from dotenv import load_dotenv
from transformers import AutoModel, AutoTokenizer
from neo4j import GraphDatabase
import torch

load_dotenv()

class Neo4jEmbedder:
    def __init__(self):
        # Neo4j connection
        self.uri = os.getenv("uri_neo4j")
        self.user = os.getenv("user")
        self.password = os.getenv("password")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

        # Transformer model for embeddings
        self.model = AutoModel.from_pretrained("intfloat/e5-base-v2")
        self.tokenizer = AutoTokenizer.from_pretrained("intfloat/e5-base-v2")

        # Neo4j property and vector index names
        self.embedding_property = "plot_embedding"
        self.vector_index_name = "movies_plot_index"

    def embed(self, text: str):
        """Generate embedding using transformer and mean pooling"""
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        last_hidden = outputs.last_hidden_state
        mask = inputs['attention_mask'].unsqueeze(-1)
        summed = (last_hidden * mask).sum(1)
        counted = mask.sum(1)
        embedding = (summed / counted).squeeze(0).tolist()
        return embedding

    def store_embeddings(self):
        """Compute embeddings for all movies and store in Neo4j"""
        with self.driver.session() as session:
            movies = session.run("MATCH (m:movie) RETURN m.title AS title, m.plot AS plot")
            for record in movies:
                title = record["title"]
                plot = record["plot"]
                embedding_vector = self.embed(plot)
                session.run(
                    f"MATCH (m:movie {{title: $title}}) SET m.{self.embedding_property} = $embedding",
                    {"title": title, "embedding": embedding_vector}
                )
                print(f"Stored embedding for '{title}'")

    def close(self):
        self.driver.close()


if __name__ == "__main__":
    embedder = Neo4jEmbedder()
    embedder.store_embeddings()
    embedder.close()
    print("All embeddings stored successfully.")
