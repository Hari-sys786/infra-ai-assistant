import os
from pathlib import Path
import pdfplumber
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import chromadb

from rag_bot.config import VENDOR_DOCUMENTS, DATA_ROOT

# 1. Set up ChromaDB client & collection (persistent DB)
CHROMA_DB_DIR = Path(__file__).parent.parent.parent.parent / "data" / "chroma_db"
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = chroma_client.get_or_create_collection("infra_docs")

# 2. Set up embedding model (local)
EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"
embedder = SentenceTransformer(EMBED_MODEL_NAME)

def extract_pdf_text(pdf_path: Path):
    """Extract text from each page of the PDF as a list of strings."""
    texts = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text and text.strip():
                texts.append({
                    "page_num": page_num,
                    "text": text.strip()
                })
    return texts

def chunk_text(text, chunk_size=200, overlap=30):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def ingest_pdfs_to_chromadb():
    for vendor, docs in VENDOR_DOCUMENTS.items():
        vendor_dir = DATA_ROOT / vendor
        print(f"\n--- Ingesting PDFs for {vendor} ---")
        for doc in docs:
            if not doc['name'].lower().endswith('.pdf'):
                continue  # skip non-PDFs here
            pdf_path = vendor_dir / doc["name"]
            if not pdf_path.exists():
                print(f"[WARN] File not found: {pdf_path}")
                continue
            print(f"[INFO] Processing: {pdf_path.name}")

            # 1. Extract text per page
            pages = extract_pdf_text(pdf_path)
            for page in tqdm(pages, desc=f"Pages of {pdf_path.name}"):
                page_text = page["text"]
                page_num = page["page_num"]
                # 2. Chunk page text
                chunks = chunk_text(page_text)
                for idx, chunk in enumerate(chunks):
                    # 3. Embed chunk
                    embedding = embedder.encode(chunk)
                    # 4. Store in ChromaDB with metadata
                    metadata = {
                        "vendor": vendor,
                        "document": doc["name"],
                        "page": page_num,
                        "chunk": idx,
                        "source_path": str(pdf_path)
                    }
                    collection.add(
                        documents=[chunk],
                        embeddings=[embedding.tolist()],
                        metadatas=[metadata],
                        ids=[f"{vendor}_{doc['name']}_p{page_num}_c{idx}"]
                    )
            print(f"[DONE] Ingested {pdf_path.name}")

    print("Total in collection:", collection.count())
    print("Chroma DB dir:", CHROMA_DB_DIR.resolve())

if __name__ == "__main__":
    ingest_pdfs_to_chromadb()
