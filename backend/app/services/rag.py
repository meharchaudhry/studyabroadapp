"""
Visa RAG Pipeline
=================
Three-stage retrieval pipeline:
  1. Hybrid search — ChromaDB dense search + BM25 keyword search,
     merged with Reciprocal Rank Fusion (RRF).
  2. Cross-encoder re-ranking — ms-marco-MiniLM-L-6-v2 re-scores the
     top candidates by reading the (query, chunk) pair together.
  3. LLM answer generation — Gemini 1.5 Flash, grounded in the
     re-ranked context with conversation memory.

Collection: "visa_policies" (must match ingest_visa.py COLLECTION_NAME)
"""

import os
import re
import logging
from typing import Dict, List, Tuple, Optional

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
COLLECTION_NAME  = "visa_policies"   # must match ingest_visa.py
MAX_MEMORY_TURNS = 6
HYBRID_FETCH_K   = 20   # candidates fetched from each retriever before RRF
RERANK_TOP_K     = 6    # chunks passed to LLM after re-ranking

# ── Module-level lazy caches ──────────────────────────────────────────────────
_vectorstore: Optional[Chroma]  = None
_bm25_index                     = None
_bm25_corpus: Optional[List[Tuple[str, str, dict]]] = None
_cross_encoder                  = None
_embeddings                     = None

# Conversation memory: session_id → [(question, answer), ...]
_memory_store: Dict[str, List[Tuple[str, str]]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _db_dir() -> str:
    # rag.py lives at: backend/app/services/rag.py
    # We need:         backend/data/chroma_db
    # So go up 3 levels from this file.
    services_dir = os.path.dirname(os.path.abspath(__file__))   # backend/app/services
    app_dir      = os.path.dirname(services_dir)                 # backend/app
    backend_dir  = os.path.dirname(app_dir)                      # backend
    return os.path.join(backend_dir, "data", "chroma_db")


def _get_embeddings():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    return _embeddings


def _get_vectorstore() -> Optional[Chroma]:
    global _vectorstore
    if _vectorstore is None:
        db = _db_dir()
        if not os.path.exists(db):
            logger.warning("ChromaDB not found at %s — run scripts/ingest_visa.py first", db)
            return None
        _vectorstore = Chroma(
            persist_directory=db,
            embedding_function=_get_embeddings(),
            collection_name=COLLECTION_NAME,
        )
        try:
            n = _vectorstore._collection.count()
            logger.info("ChromaDB loaded: %d chunks in collection '%s'", n, COLLECTION_NAME)
        except Exception:
            pass
    return _vectorstore


def _get_bm25():
    """Build BM25 index lazily from ChromaDB corpus."""
    global _bm25_index, _bm25_corpus
    if _bm25_index is not None:
        return _bm25_index, _bm25_corpus

    vs = _get_vectorstore()
    if vs is None:
        return None, None

    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed — BM25 leg of hybrid search disabled.")
        return None, None

    collection = vs._collection
    # ChromaDB ≥1.0: "ids" is always returned; only supplementary fields go in include
    result = collection.get(include=["documents", "metadatas"])
    ids   = result.get("ids", [])
    texts = result.get("documents", [])
    metas = result.get("metadatas", [])

    if not ids:
        logger.warning("ChromaDB collection is empty — did you run ingest_visa.py?")
        return None, None

    tokenized    = [re.findall(r"\w+", t.lower()) for t in texts]
    _bm25_corpus = list(zip(ids, texts, metas))
    _bm25_index  = BM25Okapi(tokenized)
    logger.info("BM25 index built: %d documents", len(ids))
    return _bm25_index, _bm25_corpus


def _get_cross_encoder():
    global _cross_encoder
    if _cross_encoder is None:
        try:
            from sentence_transformers import CrossEncoder
            _cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info("CrossEncoder loaded successfully.")
        except Exception as e:
            logger.warning("CrossEncoder load failed: %s — will use dense-only ranking.", e)
    return _cross_encoder


def _reciprocal_rank_fusion(
    dense_ids: List[str],
    bm25_ids: List[str],
    k: int = 60,
) -> List[str]:
    """Merge two ranked lists with Reciprocal Rank Fusion (RRF)."""
    scores: Dict[str, float] = {}
    for rank, doc_id in enumerate(dense_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    for rank, doc_id in enumerate(bm25_ids):
        scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return [doc_id for doc_id, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


# ── Core Retrieval ────────────────────────────────────────────────────────────

def hybrid_retrieve(query: str, k: int = HYBRID_FETCH_K) -> List[Tuple[str, str, dict]]:
    """
    BM25 + dense search merged with RRF.
    Returns (id, text, metadata) tuples sorted by fused score.
    """
    vs = _get_vectorstore()
    if vs is None:
        return []

    # 1. Dense semantic search
    dense_docs = vs.similarity_search(query, k=k)
    dense_ids  = [d.metadata.get("id", d.page_content[:40]) for d in dense_docs]
    dense_map  = {did: d for did, d in zip(dense_ids, dense_docs)}

    # 2. BM25 keyword search
    bm25, corpus = _get_bm25()
    bm25_ids: List[str] = []
    bm25_map: Dict[str, Tuple[str, str, dict]] = {}
    if bm25 is not None and corpus:
        tokens   = re.findall(r"\w+", query.lower())
        scores   = bm25.get_scores(tokens)
        top_idx  = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        bm25_ids = [corpus[i][0] for i in top_idx]
        bm25_map = {corpus[i][0]: corpus[i] for i in top_idx}

    # 3. Reciprocal Rank Fusion
    fused_ids = _reciprocal_rank_fusion(dense_ids, bm25_ids)

    # 4. Reconstruct ordered results
    results: List[Tuple[str, str, dict]] = []
    seen: set = set()
    for did in fused_ids:
        if did in seen:
            continue
        seen.add(did)
        if did in dense_map:
            d = dense_map[did]
            results.append((did, d.page_content, d.metadata))
        elif did in bm25_map:
            results.append(bm25_map[did])
        if len(results) >= k:
            break

    # Fill remainder from dense if RRF list is short
    for did, d in zip(dense_ids, dense_docs):
        if did not in seen and len(results) < k:
            results.append((did, d.page_content, d.metadata))
            seen.add(did)

    return results


def rerank(
    query: str,
    candidates: List[Tuple[str, str, dict]],
    top_k: int = RERANK_TOP_K,
) -> List[Tuple[str, str, dict]]:
    """Cross-encoder re-ranking. Falls back to dense order if unavailable."""
    ce = _get_cross_encoder()
    if ce is None or not candidates:
        return candidates[:top_k]

    pairs  = [(query, text) for _, text, _ in candidates]
    scores = ce.predict(pairs)
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)
    return [item for _, item in ranked[:top_k]]


# ── Memory ────────────────────────────────────────────────────────────────────

def _get_memory(session_id: str) -> List[Tuple[str, str]]:
    return _memory_store.setdefault(session_id, [])


def _add_to_memory(session_id: str, question: str, answer: str) -> None:
    mem = _get_memory(session_id)
    mem.append((question, answer))
    _memory_store[session_id] = mem[-MAX_MEMORY_TURNS:]


def clear_session_memory(session_id: str) -> None:
    _memory_store.pop(session_id, None)


# ── Main Public Interface ─────────────────────────────────────────────────────

class VisaAssistantChain:
    """
    Full RAG chain:  hybrid retrieve → cross-encoder rerank → Gemini LLM
    with per-session conversation memory.
    """

    SYSTEM_PROMPT = """\
You are an expert Study Abroad Visa Assistant specialising in helping Indian students navigate international visa processes.

Use ONLY the context below — which contains official visa policy documents, scholarship guides, financial documentation requirements, and related resources — to answer the student's question.

Guidelines:
- Always cite the source document name when referencing specific information (e.g., "According to australia.md…").
- Be specific and concrete: quote exact figures (fees, processing times, financial thresholds, work-hour limits).
- If the country is specified, focus your answer on that country's visa rules.
- If you reference a topic that spans multiple countries (e.g., IELTS requirements, bank statements), answer comprehensively.
- If the answer is genuinely not present in the context below, say: "I don't have specific information on this in my knowledge base. I recommend checking the official embassy website for {country}."
- Never fabricate visa policies, fees, or deadlines.
- Format your response clearly — use bullet points or numbered steps where appropriate.

Target country context: {country}

Retrieved context:
{context}
"""

    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("GOOGLE_API_KEY not set — Gemini LLM unavailable. Set GOOGLE_API_KEY in backend/.env")
            self.llm = None
            return
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.15,
            google_api_key=api_key,
        )

    def invoke(self, input_dict: dict) -> dict:
        if self.llm is None:
            return {
                "answer": (
                    "The AI answer generator is not available because the GOOGLE_API_KEY "
                    "environment variable has not been set. Please add your Gemini API key to "
                    "backend/.env and restart the server."
                ),
                "context": [],
            }

        query      = input_dict["input"]
        country    = input_dict.get("country", "the target country")
        session_id = input_dict.get("session_id", "default")

        # ── Stage 1: Hybrid retrieval ─────────────────────────────────────────
        candidates = hybrid_retrieve(query, k=HYBRID_FETCH_K)

        # ── Stage 2: Cross-encoder re-ranking ────────────────────────────────
        top_chunks = rerank(query, candidates, top_k=RERANK_TOP_K)

        # ── Stage 2b: Country-specific guarantee ──────────────────────────────
        # When a specific country is named AND the top chunks are missing that
        # country's docs, inject up to 2 country-specific chunks from a
        # filtered search. Skip the boost when ≥2 chunks from the target
        # country are already present (they ranked high naturally).
        if country and country not in ("the target country", "General"):
            existing_country_count = sum(
                1 for _, _, meta in top_chunks
                if meta.get("country") == country
            )
            if existing_country_count < 2:
                vs = _get_vectorstore()
                if vs is not None:
                    try:
                        country_docs = vs.similarity_search(
                            query, k=3,
                            filter={"country": country},
                        )
                        existing_texts = {t[:100] for _, t, _ in top_chunks}
                        guaranteed: List[Tuple[str, str, dict]] = []
                        for d in country_docs:
                            if d.page_content[:100] not in existing_texts:
                                doc_id = d.metadata.get("id", d.page_content[:40])
                                guaranteed.append((doc_id, d.page_content, d.metadata))
                                existing_texts.add(d.page_content[:100])
                        if guaranteed:
                            n = min(len(guaranteed), 2 - existing_country_count)
                            top_chunks = guaranteed[:n] + top_chunks[:RERANK_TOP_K - n]
                    except Exception:
                        pass  # filter unsupported — skip silently

        if not top_chunks:
            answer = (
                "I'm unable to retrieve relevant documents right now. "
                "Please ensure the visa knowledge base has been ingested "
                "(run scripts/ingest_visa.py) and try again."
            )
            return {"answer": answer, "context": []}

        context_text = "\n\n---\n\n".join(
            f"[Source: {meta.get('source', 'unknown')} | Country: {meta.get('country', '?')}]\n{text}"
            for _, text, meta in top_chunks
        )

        # ── Stage 3: Build prompt with conversation history ───────────────────
        history = _get_memory(session_id)
        messages = [("system", self.SYSTEM_PROMPT.format(country=country, context=context_text))]

        for prev_q, prev_a in history:
            messages.append(("human", prev_q))
            messages.append(("ai", prev_a))

        messages.append(("human", query))

        prompt   = ChatPromptTemplate.from_messages(messages)
        chain    = prompt | self.llm
        response = chain.invoke({})
        answer   = response.content

        # ── Stage 4: Persist memory ───────────────────────────────────────────
        _add_to_memory(session_id, query, answer)

        docs_for_api = [
            type("Doc", (), {"page_content": text, "metadata": meta})()
            for _, text, meta in top_chunks
        ]

        return {"answer": answer, "context": docs_for_api}


# Singleton
_chain_instance: Optional[VisaAssistantChain] = None


def get_visa_assistant_chain() -> VisaAssistantChain:
    global _chain_instance
    if _chain_instance is None:
        _chain_instance = VisaAssistantChain()
    return _chain_instance


# ── Evaluation ────────────────────────────────────────────────────────────────

def _token_overlap(text_a: str, text_b: str) -> float:
    """Jaccard token overlap between two strings (fast faithfulness proxy)."""
    if not text_a or not text_b:
        return 0.0
    a = set(re.findall(r"\w+", text_a.lower()))
    b = set(re.findall(r"\w+", text_b.lower()))
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def evaluate_rag_response(
    query: str,
    retrieved_docs: list,
    generated_answer: str,
    relevant_sources: Optional[List[str]] = None,
) -> dict:
    """
    Compute retrieval and generation quality metrics.

    Retrieval metrics (require `relevant_sources` ground-truth list):
      Hit Rate @k  — did at least one relevant source appear in top-k?
      MRR @k       — Mean Reciprocal Rank of first relevant source
      MAP @k       — Mean Average Precision across relevant sources
      NDCG @k      — Normalised Discounted Cumulative Gain (binary relevance)

    Generation metrics (proxy, no ground-truth needed):
      Faithfulness       — token overlap between answer and retrieved context
      Answer Relevancy   — answer length + absence of "I don't know" patterns
      Contextual Precision — fraction of retrieved docs from a relevant source
    """
    import math

    n = len(retrieved_docs)
    doc_sources = [getattr(d, "metadata", {}).get("source", "") for d in retrieved_docs]
    k = n  # evaluate at k = number of retrieved docs

    # ── Retrieval metrics (only when ground-truth is provided) ────────────────
    hit_rate = mrr = map_k = ndcg = None

    if relevant_sources and n > 0:
        rel_set = set(relevant_sources)

        # Binary relevance vector for retrieved docs (1 = relevant, 0 = not)
        rel_vector = [1 if s in rel_set else 0 for s in doc_sources]

        # Hit Rate @k — 1 if any relevant doc retrieved
        hit_rate = float(any(rel_vector))

        # MRR @k — 1 / rank of first hit
        mrr = 0.0
        for rank, rel in enumerate(rel_vector, start=1):
            if rel:
                mrr = 1.0 / rank
                break

        # MAP @k — average precision at each recall point
        hits = 0
        precision_sum = 0.0
        n_relevant = sum(rel_vector)
        for rank, rel in enumerate(rel_vector, start=1):
            if rel:
                hits += 1
                precision_sum += hits / rank
        map_k = (precision_sum / n_relevant) if n_relevant > 0 else 0.0

        # NDCG @k — discounted cumulative gain / ideal DCG
        dcg = sum(rel / math.log2(rank + 1) for rank, rel in enumerate(rel_vector, start=1))
        ideal_rels = sorted(rel_vector, reverse=True)
        idcg = sum(r / math.log2(rank + 1) for rank, r in enumerate(ideal_rels, start=1) if r)
        ndcg = dcg / idcg if idcg > 0 else 0.0

    # ── Generation metrics (proxy, no ground-truth) ───────────────────────────

    # Faithfulness: Jaccard overlap between answer tokens and retrieved context tokens
    combined_context = " ".join(
        getattr(d, "page_content", "") for d in retrieved_docs
    )
    faithfulness = _token_overlap(generated_answer, combined_context) if combined_context else 0.0
    # Normalise: token overlap of 0.1+ is already excellent for long-form text
    faithfulness = min(1.0, faithfulness * 6.0)

    # Penalise graceful refusals when docs were retrieved (LLM ignoring context)
    refusal_phrases = [
        "i don't have specific information",
        "i don't know",
        "i cannot answer",
        "not in my knowledge base",
    ]
    is_refusal = any(p in generated_answer.lower() for p in refusal_phrases)
    if is_refusal and n > 0:
        faithfulness = min(faithfulness, 0.30)

    # Answer Relevancy: keyword overlap between query and answer
    answer_relevancy = _token_overlap(query, generated_answer)
    answer_relevancy = min(1.0, answer_relevancy * 8.0)  # normalise
    # Bonus for substantive answers
    answer_words = len(generated_answer.split())
    if answer_words > 50:
        answer_relevancy = min(1.0, answer_relevancy + 0.15)
    if is_refusal:
        answer_relevancy = max(answer_relevancy - 0.30, 0.10)

    # Contextual Precision: fraction of retrieved docs that share a source with any other
    # (proxy: diverse sources → lower precision; repeated sources → higher precision)
    if n > 0 and relevant_sources:
        rel_set = set(relevant_sources)
        cp_hits = sum(1 for s in doc_sources if s in rel_set)
        contextual_precision = cp_hits / n
    elif n > 0:
        # Without ground-truth: use source diversity as inverse proxy
        unique_sources = len(set(doc_sources))
        contextual_precision = max(0.40, 1.0 - (unique_sources - 1) * 0.08)
    else:
        contextual_precision = 0.0

    result = {
        "contextual_precision": round(contextual_precision, 3),
        "faithfulness":         round(faithfulness, 3),
        "answer_relevancy":     round(answer_relevancy, 3),
        "chunks_retrieved":     n,
        "search_method":        "hybrid_bm25_dense_crossencoder_rrf_country_boost",
    }

    # Add retrieval IR metrics when ground-truth was provided
    if relevant_sources is not None:
        k_str = f"@{k}"
        result[f"hit_rate{k_str}"]  = round(hit_rate, 3)   if hit_rate  is not None else None
        result[f"mrr{k_str}"]       = round(mrr, 3)        if mrr       is not None else None
        result[f"map{k_str}"]       = round(map_k, 3)      if map_k     is not None else None
        result[f"ndcg{k_str}"]      = round(ndcg, 3)       if ndcg      is not None else None

    return result
