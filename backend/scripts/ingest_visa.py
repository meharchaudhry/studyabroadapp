"""
ingest_visa.py
==============
Ingests all visa-related markdown documents from data/visa_docs/ into ChromaDB.

Features:
  - Named collection "visa_policies" (consistent with rag.py)
  - Wipes the collection on each run so we always have a clean, up-to-date index
  - Larger chunks (600 chars, 200 overlap) for better semantic coherence
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


class GeminiEmbeddings:
    """REST-based Google embeddings — avoids gRPC DNS issues."""
    def __init__(self, api_key: str, model: str = "models/gemini-embedding-001"):
        from google import genai as _genai
        self._client = _genai.Client(api_key=api_key)
        self._model  = model

    def embed_documents(self, texts: list) -> list:
        results, batch_size = [], 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp  = self._client.models.embed_content(model=self._model, contents=batch)
            results.extend([list(e.values) for e in resp.embeddings])
            print(f"  Embedded {min(i+batch_size, len(texts))}/{len(texts)} chunks…", end="\r")
        print()
        return results

    def embed_query(self, text: str) -> list:
        resp = self._client.models.embed_content(model=self._model, contents=text)
        return list(resp.embeddings[0].values)

# ── Constants ─────────────────────────────────────────────────────────────────

COLLECTION_NAME = "visa_policies"

# Filename → canonical country name mapping
FILENAME_COUNTRY_MAP = {
    # Primary country guides
    "uk":                   "UK",
    "usa":                  "USA",
    "canada":               "Canada",
    # Legacy stub files
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
    "hong_kong":            "Hong Kong",
    "malaysia":             "Malaysia",
    # Detailed / FAQ supplements for existing countries
    "uk_student_visa_complete_guide":        "UK",
    "uk_graduate_route_guide":               "UK",
    "uk_atas_clearance":                     "UK",
    "uk_tb_test_guide":                      "UK",
    "ucas_application_guide":                "UK",
    "usa_f1_opt_cpt_guide":                  "USA",
    "usa_visa_interview_complete_guide":     "USA",
    "canada_study_permit_detailed":          "Canada",
    "canada_express_entry_study_pathway":    "Canada",
    "australia_485_visa_guide":              "Australia",
    "australia_study_pathway":               "Australia",
    "australia_cricos_guide":                "Australia",
    "germany_aps_certificate_guide":         "Germany",
    "german_aps_certificate_guide":          "Germany",
    "germany_blocked_account_guide":         "Germany",
    "germany_study_pathway_pr":              "Germany",
    "france_campus_france_guide":            "France",
    "south_korea_detailed_faq":              "South Korea",
    "norway_detailed_guide":                 "Norway",
    "italy_detailed_guide":                  "Italy",
    "portugal_detailed_guide":               "Portugal",
    "singapore_detailed_faq":               "Singapore",
    "uk_graduate_route_guide_faq":           "UK",
    # Raw scraped official pages (mixed-case stems, normalised in classify_doc)
    "australia_student500":                  "Australia",
    "finland_studentresidencepermit":        "Finland",
    "france_thedifferenttypesofvisas":       "France",
    "germany_studying":                      "Germany",
    "hongkong_studyhtml":                    "Hong Kong",
    "india_listofvisas":                     "General",
    "netherlands_studentresidencepermitforuniversityorhigherprofessionaleducation": "Netherlands",
    "singapore_apply":                       "Singapore",
    "spain_visadodeestudiosaspx":            "Spain",
    "switzerland_visumantragsformularhtml":  "Switzerland",
    "uk_studentvisa":                        "UK",
    "usa_studentvisahtml":                   "USA",
}

# Files whose topic spans multiple countries (classified as topic-guides)
TOPIC_GUIDES = {
    # Original guides
    "scholarships_guide",
    "post_study_work_visas",
    "sop_and_lor_guide",
    "bank_statements_financial_proof",
    "english_tests_guide",
    "visa_interview_us_tips",
    "health_insurance_guide",
    "police_clearance_guide",
    "job_portals_guide",
    # New topic guides (55 new documents)
    "cost_of_living_guide",
    "part_time_work_rights",
    "pre_departure_checklist",
    "post_arrival_guide",
    "document_attestation_apostille_guide",
    "document_attestation_guide",
    "wes_credential_evaluation",
    "wes_evaluation_guide",
    "financial_planning_guide",
    "banking_abroad_guide",
    "banking_india_before_leaving",
    "scholarship_database_guide",
    "scholarships_india_specific",
    "phd_application_guide",
    "phd_guide",
    "mba_application_guide",
    "mba_guide",
    "gre_gmat_guide",
    "visa_rejection_guide",
    "visa_rejection_appeal_guide",
    "dependent_visa_guide",
    "language_requirements_comprehensive",
    "language_tests_comprehensive",
    "travel_insurance_guide",
    "travel_insurance_study_guide",
    "global_health_insurance_guide",
    "accommodation_types_guide",
    "accommodation_application_timeline",
    "mental_health_wellbeing_guide",
    "mental_health_abroad_guide",
    "police_clearance_certificate_guide",
    "gap_year_reapplication_guide",
    "gap_year_guide",
    "india_to_abroad_comparison_guide",
    "transcript_gpa_conversion_guide",
    "transcript_evaluation",
    "research_proposal_guide",
    "internship_placement_guide",
    "internship_abroad_guide",
    "study_abroad_timeline_planning",
    "personal_statement_guide_detailed",
    "personal_statement_guide",
    "letter_of_recommendation_guide",
    "lor_writing_guide",
    "work_after_graduation_comparison",
    "post_study_work_visa_comparison",
    "ielts_preparation_guide",
    "community_resources_guide",
    "indian_community_abroad",
    "tax_guide_abroad",
    "transfer_guide",
    "campus_interview_prep",
    "study_permit_conditions",
    "europe_overview",
    "europe_student_hub_guide",
    "study_abroad_faq",
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
        chunk_size=600,
        chunk_overlap=200,
        separators=["\n## ", "\n### ", "\n#### ", "\n\n", "\n", " "],
    )
    chunks = splitter.split_documents(raw_docs)

    print(f"Chunking complete: {len(chunks)} chunks from {len(raw_docs)} documents")
    print(f"  avg chunk size: {sum(len(c.page_content) for c in chunks) // len(chunks)} chars\n")

    # Per-document chunk count
    from collections import Counter
    counts = Counter(c.metadata.get("source", "?") for c in chunks)
    for fname, n in sorted(counts.items()):
        print(f"  {fname}: {n} chunks")

    # ── Embed and store ───────────────────────────────────────────────────────
    # Load API key from backend/.env
    from dotenv import load_dotenv
    env_path = os.path.join(base_dir, ".env")
    load_dotenv(env_path)
    api_key = os.getenv("GOOGLE_API_KEY", "")
    if not api_key:
        print("❌ GOOGLE_API_KEY not set in backend/.env — aborting.")
        return

    print(f"\nInitialising embeddings (Google gemini-embedding-001 via REST)...")
    embeddings = GeminiEmbeddings(api_key=api_key)

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
