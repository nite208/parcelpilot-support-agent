import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.setup import setup_database
from rag.ingest import ingest_documents

if __name__ == "__main__":
    print("Setting up database...")
    setup_database()
    print("Ingesting documents...")
    ingest_documents()
    print("Setup complete.")