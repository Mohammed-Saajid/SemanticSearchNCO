from fastapi import FastAPI
from pydantic import BaseModel
import chromadb
import numpy as np
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
import pickle
import os
import sqlite3
from .utils import zscore_norm

# Load Prebuilt Indexes 
CHROMA_PATH = "db/chroma_db"
BM25_PATH = "db/bm25_index.pkl"
COLLECTION_NAME = "nco_roles"
SQLITE_DB_PATH = "db/roles.db"

# Initialize Chroma and sqlite
client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_or_create_collection(name=COLLECTION_NAME)
conn = sqlite3.Connection(SQLITE_DB_PATH, check_same_thread=False)

# Load BM25 index
if os.path.exists(BM25_PATH):
    with open(BM25_PATH, "rb") as f:
        bm25_index, bm25_ids = pickle.load(f)
else:
    raise FileNotFoundError("BM25 index not found. Please run preprocessing first.")

# Load embedding model
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# FastAPI App 
app = FastAPI(
    title="Hybrid Search API",
    description="Hybrid BM25 + Vector Semantic Search",
    version="1.0"
)

# Define request models
class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    bm25_weight: float = 0.4
    vector_weight: float = 0.6

class RoleDescriptionRequest(BaseModel):
    role_number: str


@app.post("/search")
def hybrid_search(req: SearchRequest):
    """
    Hybrid search combining BM25 and vector search.
    Ensures only one chunk per role_number is returned (the best-scoring one).
    
    Args:
        req (SearchRequest): The search request containing query and parameters.
    Returns:
        dict: The search results.
    """

    # Extract parameters
    query = req.query
    top_k = req.top_k
    bm25_weight = req.bm25_weight
    vector_weight = req.vector_weight

    # BM25 search
    tokenized_query = word_tokenize(query.lower())
    bm25_scores = bm25_index.get_scores(tokenized_query)

    # Vector search
    query_emb = model.encode(query).tolist()
    vector_results = collection.query(
        query_embeddings=[query_emb],
        n_results=len(bm25_ids)  # Retrieve all
    )

    # Initialize vector_scores aligned to bm25_ids
    vector_scores = np.zeros(len(bm25_ids))
    id_to_idx = {bm25_ids[i]: i for i in range(len(bm25_ids))}

    # Convert distances to similarity
    for i, doc_id in enumerate(vector_results["ids"][0]):
        if doc_id in id_to_idx:
            idx = id_to_idx[doc_id]
            sim = 1 - vector_results["distances"][0][i]  # cosine distance → similarity
            vector_scores[idx] = sim

    # Normalize scores
    bm25_scores = zscore_norm(np.array(bm25_scores))
    vector_scores = zscore_norm(np.array(vector_scores))

    # Combine scores 
    combined_scores = bm25_weight * bm25_scores + vector_weight * vector_scores

    # Track best chunk per role_number
    best_chunks = {}
    for idx, score in enumerate(combined_scores):
        doc_id = bm25_ids[idx]
        doc_data = collection.get(ids=[doc_id])
        role_number = doc_data["metadatas"][0]["role_number"]

        # If role not seen OR this chunk is better, replace
        if role_number not in best_chunks or score > best_chunks[role_number]["combined_score"]:
            best_chunks[role_number] = {
                "id": doc_id,
                "role_number": role_number,
                "chunk_index": doc_data["metadatas"][0]["chunk_index"],
                "chunk_text": doc_data["documents"][0],
                "bm25_score": float(bm25_scores[idx]),
                "vector_score": float(vector_scores[idx]),
                "combined_score": float(score)
            }

    # Sort by combined score and take top_k
    results = sorted(best_chunks.values(), key=lambda x: -x["combined_score"])[:top_k]

    return {"query": query, "results": results}




@app.get('/getroledescription')
def get_role_description(req: RoleDescriptionRequest):
    """
    Get the role description for a specific role number.
    Args:
        req (RoleDescriptionRequest): The role description request containing the role number.
    Returns:
        dict: The role description.
    """

    # Extract the Role Number
    role_number = req.role_number
    # Query the database
    cur = conn.cursor()
    cur.execute("SELECT description FROM roles WHERE role_number=?", (role_number,))
    description = cur.fetchone()

    return {"description": description}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
