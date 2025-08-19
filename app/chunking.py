import json
import chromadb
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import pickle


def fixed_token_chunk(text, max_tokens=250, overlap=50):
    """
    Split text into fixed-length overlapping chunks.
    Each chunk will have up to `max_tokens` tokens,
    and consecutive chunks overlap by `overlap` tokens.

    Args:
        text (str): The input text to chunk.
        max_tokens (int): The maximum number of tokens per chunk.
        overlap (int): The number of overlapping tokens between chunks.
    Returns:
        list: A list of text chunks.
    """
    words = word_tokenize(text)
    chunks = []
    start = 0
    while start < len(words):
        end = start + max_tokens
        chunk_words = words[start:end]
        chunks.append(" ".join(chunk_words))
        if end >= len(words):
            break
        start = end - overlap  # slide back for overlap
    return chunks


def store_chunks_in_chroma_and_bm25(json_file, collection_name="role_descriptions",
                                    max_tokens=250, overlap=50):
    """
    Store text chunks in ChromaDB and BM25 index.
    Args:
        json_file (str): The path to the JSON file.
        collection_name (str): The name of the ChromaDB collection.
        max_tokens (int): The maximum number of tokens per chunk.
        overlap (int): The number of overlapping tokens between chunks.
    Returns:
        tuple: A tuple containing the ChromaDB collection, BM25 index, BM25 IDs, and the model.
    """

    # Load JSON data
    with open(json_file, "r", encoding="utf-8") as f:
        roles_data = json.load(f)

    # Initialize model
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

    # ChromaDB client
    client = chromadb.PersistentClient(path="db/chroma_db")
    collection = client.get_or_create_collection(name=collection_name)

    bm25_corpus = []
    bm25_ids = []

    for role_number, description in roles_data.items():
        chunks = fixed_token_chunk(description, max_tokens=max_tokens, overlap=overlap)
        for idx, chunk in enumerate(chunks):
            emb = model.encode(chunk).tolist()
            doc_id = f"{role_number}_chunk{idx}"

            # Store in Chroma
            collection.add(
                ids=[doc_id],
                documents=[chunk],
                embeddings=[emb],
                metadatas=[{"role_number": role_number, "chunk_index": idx}]
            )

            # Prepare for BM25
            bm25_corpus.append(word_tokenize(chunk.lower()))
            bm25_ids.append(doc_id)

    # Build BM25 index
    bm25_index = BM25Okapi(bm25_corpus)
    with open("db/bm25_index.pkl", "wb") as f:
        pickle.dump((bm25_index, bm25_ids), f)

    print(f"Stored {len(bm25_corpus)} chunks in Chroma and BM25.")
    return collection, bm25_index, bm25_ids, model


if __name__ =="__main__":
    collection, bm25_index, bm25_ids, model = store_chunks_in_chroma_and_bm25( "dump/roles.json", collection_name="nco_roles" )
   