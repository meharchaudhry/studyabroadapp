"""
ingest_visa.py
==============
Ingests all visa-related markdown documents from data/visa_docs/ into ChromaDB.

Features:
  - Named collection "visa_policies" (consistent with rag.py)
  - Wipes the collection on each run so we always have a clean, up-to-date index
  - Larger chunks (800 chars, 150 overlap) for better semantic coherence
  - Rich metadata: source filename, country, topic_type (country-guide | topic-guide)
  - Prints chunk counts per document for verification
"""

import os
import re
import glob
import shutil
import sys

# Allow running from repo root or from scripts/ directory
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

# ── Constants ─────────────────────────────────────────────────────────────────

COLLECTION_NAME = "visa_policies"

# Filename → canonical country name mapping
FILENAME_COUNTRY_MAP = {
    # Full comprehensive guides (new)
    "uk":                   "UK",
    "usa":                  "USA",
    "canada":               "Canada",
    # Legacy stub files (now superseded — still map them)
    "ukvi_student_visa":    "UK",
    "uscis_f1_visa":        "USA",
    "ircc_study_permit":    "Canada",
    "australia":            "Australia",
    "germany":              "Germany",
    "france":               "France",
    "netherlands":          "Netherlands",
    "ireland":              "Ireland",
    "singapore":            "Singapore",
    "japan":                "Japan",
    "sweden":               "Sweden",
    "norway":               "Norway",
    "denmark":              "Denmark",
    "finland":              "Finland",
    "new_zealand":          "New Zealand",
    "uae":                  "UAE",
    "portugal":             "Portugal",
    "italy":                "Italy",
    "spain":                "Spain",
    "south_korea":          "South Korea",
    "switzerland":          "Switzerland",
    "belgium":              "Belgium",
    "poland":               "Poland",
    "czech_republic":       "Czech Republic",
}

# Files whose topic spans multiple countries (classified as topic-guides)
TOPIC_GUIDES = {
    "scholarships_guide",
    "post_study_work_visas",
    "sop_and_lor_guide",
    "bank_statements_financial_proof",
    "english_tests_guide",
    "visa_interview_us_tips",
    "health_insurance_guide",
    "police_clearance_guide",
}


def classify_doc(stem: str) -> tuple[str, str]:
    """
    Returns (country, topic_type) for a document filename stem.
    topic_type is 'country-guide' or 'topic-guide'.
    """
    key = stem.lower().replace("-", "_")
    if key in TOPIC_GUIDES:
        return "General", "topic-guide"
    country = FILENAME_COUNTRY_MAP.get(key, "General")
    return country, "country-guide"


def load_documents(docs_dir: str) -> list[Document]:
    docs = []
    md_files = sorted(glob.glob(os.path.join(docs_dir, "*.md")))
    if not md_files:
        print("⚠️  No .md files found in", docs_dir)
        return docs

    for filepath in md_files:
        stem = os.path.splitext(os.path.basename(filepath))[0]
        country, topic_type = classify_doc(stem)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        docs.append(Document(
            page_content=content,
            metadata={
                "source":     os.path.basename(filepath),
                "country":    country,
                "topic_type": topic_type,
                "stem":       stem,
            }
        ))
        print(f"  Loaded: {os.path.basename(filepath)}  [{country} / {topic_type}]  ({len(content):,} chars)")

    return docs


def save_chunks_to_json(chunks: list[Document], output_path: str):
    """Saves the list of Document chunks to a JSON file for verification."""
    import json
    chunk_data = []
    for chunk in chunks:
        chunk_data.append({
            "content": chunk.page_content,
            "metadata": chunk.metadata,
        })
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunk_data, f, indent=2, ensure_ascii=False)
    print(f"  ✅ Saved {len(chunks)} chunks for verification to: {output_path}")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    docs_dir = os.path.join(base_dir, "data", "visa_docs")
    db_dir   = os.path.join(base_dir, "data", "chroma_db")

    print(f"\n{'='*60}")
    print("StudyPathway — Visa Document Ingestion")
    print(f"{'='*60}")
    print(f"Source:     {docs_dir}")
    print(f"ChromaDB:   {db_dir}")
    print(f"Collection: {COLLECTION_NAME}")
    print()

    # ── Load documents ────────────────────────────────────────────────────────
    print("Loading documents...")
    raw_docs = load_documents(docs_dir)
    if not raw_docs:
        print("No documents found. Aborting.")
        return

    print(f"\nTotal: {len(raw_docs)} documents loaded.\n")

    # ── Chunk documents ───────────────────────────────────────────────────────
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(raw_docs)

    # Save chunks to a local file for verification
    output_path = os.path.join(base_dir, "data", "visa_ingest_preview.json")
    save_chunks_to_json(chunks, output_path)

    print(f"\nChunking complete: {len(chunks)} chunks from {len(raw_docs)} documents")
    print(f"  avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars\n")

    # Per-document chunk count
    from collections import Counter
    counts = Counter(c.metadata.get("source", "?") for c in chunks)
    for fname, n in sorted(counts.items()):
        print(f"  {fname}: {n} chunks")

    # ── Embed and store ───────────────────────────────────────────────────────
    print(f"\nInitialising embeddings (all-MiniLM-L6-v2)...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print(f"Wiping existing collection '{COLLECTION_NAME}' (if any) and re-ingesting...")

    # Delete and recreate the collection for a clean build
    try:
        import chromadb
        client = chromadb.PersistentClient(path=db_dir)
        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"  Deleted existing collection '{COLLECTION_NAME}'")
        except Exception:
            pass  # Collection didn't exist — that's fine
    except Exception as e:
        print(f"  ChromaDB client init warning: {e} — proceeding with Langchain interface")

    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=db_dir,
        collection_name=COLLECTION_NAME,
    )

    # Verify
    total_stored = vectorstore._collection.count()
    print(f"\n✅ Ingestion complete!")
    print(f"   {total_stored} chunks stored in collection '{COLLECTION_NAME}'")
    print(f"   ChromaDB location: {db_dir}")
    print()

    # Quick retrieval test
    print("Quick retrieval test — 'UK student visa financial requirements':")
    results = vectorstore.similarity_search("UK student visa financial requirements", k=3)
    for i, r in enumerate(results):
        print(f"  [{i+1}] {r.metadata.get('source')} ({r.metadata.get('country')}) — {r.page_content[:100]}...")

    print("\nQuick retrieval test — 'IELTS score requirements for Canada':")
    results2 = vectorstore.similarity_search("IELTS score requirements for Canada", k=3)
    for i, r in enumerate(results2):
        print(f"  [{i+1}] {r.metadata.get('source')} ({r.metadata.get('country')}) — {r.page_content[:100]}...")

    print("\n✅ Ingest and retrieval verification done.\n")


if __name__ == "__main__":
    main()
