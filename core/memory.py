import chromadb
import uuid
from sentence_transformers import SentenceTransformer
import os

class AgentMemory:
    def __init__(self, db_path="./agent_memory_db"):
        print("Initializing Neural Memory...")
        # 1. Load the Embedding Model (The Translator)
        # 'all-MiniLM-L6-v2' is a standard, fast model for text similarity
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # 2. Connect to Database (Creates folder if missing)
        self.client = chromadb.PersistentClient(path=db_path)
        
        # 3. Get or Create the Collection
        self.collection = self.client.get_or_create_collection(
            name="project_knowledge"
        )

    def save_memory(self, content: str, source: str = "user"):
        """
        Saves a text snippet (code, plan, or fact) to the database.
        """
        # Convert text to vector
        vector = self.model.encode(content).tolist()
        
        # Generate unique ID
        mem_id = str(uuid.uuid4())
        
        # Store in DB
        self.collection.add(
            documents=[content],
            embeddings=[vector],
            metadatas=[{"source": source}],
            ids=[mem_id]
        )
        # print(f"      (Memory Saved: {mem_id})") # Debug

    def search_memory(self, query: str, limit: int = 2):
        """
        Finds the most relevant past memories for a query.
        """
        query_vector = self.model.encode(query).tolist()
        
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=limit
        )
        
        # Return clean list of strings
        if results and results['documents']:
            return results['documents'][0]
        return []

# Singleton Instance (So we don't load the model twice)
memory = AgentMemory()