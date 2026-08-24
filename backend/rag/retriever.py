import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_PERSIST_DIR


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_collection(name="parcelpilot_docs", embedding_function=ef)


def retrieve(query, account_id=None, n_results=6):
    collection = get_collection()
    
    results = collection.query(
        query_texts=[query],
        n_results=n_results + 4,
        include=["documents", "metadatas", "distances"]
    )
    
    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    
    processed = []
    for doc, meta, dist in zip(docs, metas, distances):
        is_deprecated = meta.get("is_deprecated", "False") == "True"
        authority = int(meta.get("authority", 50))
        source = meta.get("source", "")
        
        if is_deprecated:
            continue
        
        if account_id and "Enterprise_Agreement" in source:
            account_hint = "ACCT-001" if "Northstar" in source else "ACCT-002"
            if account_hint != account_id:
                continue
        
        relevance = (1 - dist) * 100
        final_score = (relevance * 0.5) + (authority * 0.5)
        
        processed.append({
            "content": doc,
            "source": source,
            "page": meta.get("page", 1),
            "authority": authority,
            "relevance": round(relevance, 2),
            "final_score": round(final_score, 2)
        })
    
    processed.sort(key=lambda x: x["final_score"], reverse=True)
    return processed[:n_results]