import os
import chromadb
from google import genai
from google.genai import types
from chromadb import Documents, EmbeddingFunction, Embeddings
import time

# 1. Modular Client Setup
# We pass the key directly from the GUI to keep the app flexible.
def get_gemini_client(api_key):
    # Your verified SSL bypass for the network
    http_options = types.HttpOptions(client_args={'verify': False})
    return genai.Client(api_key=api_key, http_options=http_options)

# 2. Flexible Embedding Function
# Uses the active client to convert text chunks into numerical vectors.
class GeminiEmbeddingFunction(EmbeddingFunction):
    def __init__(self, client):
        self.client = client
        
    def __call__(self, input: Documents) -> Embeddings:
        # Get the response from Gemini Embedding model
        response = self.client.models.embed_content(
            model="gemini-embedding-001", 
            contents=input,
            config={'task_type': 'retrieval_document'}
        )
        
        # Extract the numerical values from the response
        raw_embeddings = [item.values for item in response.embeddings]
        
        # Mandatory pause to respect Gemini Free Tier rate limits
        time.sleep(3) 
        
        return raw_embeddings

# 3. Dynamic ChromaDB Connection
# No more hardcoded defaults. The GUI/Loader must tell it which collection to use.
def get_chroma_collection(client, db_path, collection_name):
    # Initialize the embedding function with the user's client
    gemini_ef = GeminiEmbeddingFunction(client)
    
    # Connect to the persistent database on your drive
    chroma_client = chromadb.PersistentClient(path=db_path)
    
    # Get the collection or create it if it doesn't exist
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=gemini_ef
    )
    
    return collection, chroma_client