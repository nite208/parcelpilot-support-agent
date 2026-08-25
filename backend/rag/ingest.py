import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pypdf import PdfReader
import chromadb
from config import CHROMA_PERSIST_DIR, DATA_DIR, DOCUMENT_AUTHORITY, DEPRECATED_DOCS


def extract_text_from_pdf(filepath):
    reader = PdfReader(filepath)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text and text.strip():
            pages.append({"page": i + 1, "text": text.strip()})
    return pages


def chunk_text(text, chunk_size=600, overlap=100):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        if end == len(words):
            break
        start += chunk_size - overlap
    return chunks


def ingest_documents():
    client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    collection = client.get_or_create_collection(
        name="parcelpilot_docs",
        metadata={"hnsw:space": "cosine"}
    )

    existing = collection.get()
    if existing["ids"]:
        print(f"Collection already has {len(existing['ids'])} chunks. Skipping ingest.")
        return

    pdf_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".pdf")]

    total_chunks = 0
    for filename in pdf_files:
        filepath = os.path.join(DATA_DIR, filename)
        authority = DOCUMENT_AUTHORITY.get(filename, 50)
        is_deprecated = filename in DEPRECATED_DOCS

        pages = extract_text_from_pdf(filepath)

        for page_data in pages:
            chunks = chunk_text(page_data["text"])

            for i, chunk in enumerate(chunks):
                chunk_id = f"{filename}_p{page_data['page']}_c{i}"

                collection.add(
                    ids=[chunk_id],
                    documents=[chunk],
                    metadatas=[{
                        "source": filename,
                        "page": page_data["page"],
                        "authority": authority,
                        "is_deprecated": str(is_deprecated),
                        "chunk_index": i
                    }]
                )
                total_chunks += 1

        print(f"Ingested {filename} — authority={authority}, deprecated={is_deprecated}")

    print(f"Ingest complete. Total chunks: {total_chunks}")


if __name__ == "__main__":
    ingest_documents()