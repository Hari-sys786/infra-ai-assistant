import os
from pathlib import Path
from bs4 import BeautifulSoup
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
import chromadb

from rag_bot.config import VENDOR_DOCUMENTS, DATA_ROOT

CHROMA_DB_DIR = Path(__file__).parent.parent.parent.parent / "data" / "chroma_db"
CHROMA_DB_DIR.mkdir(parents=True, exist_ok=True)  # Ensure directory exists

chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
collection = chroma_client.get_or_create_collection("infra_docs")

EMBED_MODEL_NAME = "BAAI/bge-base-en-v1.5"
embedder = SentenceTransformer(EMBED_MODEL_NAME)

def extract_html_text(html_path: Path):
    with open(html_path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")
        for tag in soup(["script", "style", "header", "footer", "nav"]):
            tag.decompose()
        text = ' '.join(soup.stripped_strings)
    return text

def chunk_text(text, chunk_size=200, overlap=30):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+chunk_size]
        chunks.append(" ".join(chunk))
        i += chunk_size - overlap
    return chunks


def ingest_htmls_to_chromadb():
    for vendor, docs in VENDOR_DOCUMENTS.items():
        vendor_dir = DATA_ROOT / vendor
        print(f"\n--- Ingesting HTMLs for {vendor} ---")
        for doc in docs:
            if not doc['name'].lower().endswith('.html'):
                continue
            html_path = vendor_dir / doc["name"]
            if not html_path.exists():
                print(f"[WARN] File not found: {html_path}")
                continue
            print(f"[INFO] Processing: {html_path.name}")

            all_text = extract_html_text(html_path)
            chunks = chunk_text(all_text)
            for idx, chunk in enumerate(chunks):
                embedding = embedder.encode(chunk)
                metadata = {
                    "vendor": vendor,
                    "document": doc["name"],
                    "chunk": idx,
                    "source_path": str(html_path)
                }
                collection.add(
                    documents=[chunk],
                    embeddings=[embedding.tolist()],
                    metadatas=[metadata],
                    ids=[f"{vendor}_{doc['name']}_c{idx}"]
                )
            print(f"[DONE] Ingested {html_path.name}")

    print("Total in collection:", collection.count())
    print("Chroma DB dir:", CHROMA_DB_DIR.resolve())

if __name__ == "__main__":
    ingest_htmls_to_chromadb()
