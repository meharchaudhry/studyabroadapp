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

import html
import os
import re
import time
import logging
from typing import Dict, List, Tuple, Optional

from langchain_chroma import Chroma

from app.core.config import settings

logger = logging.getLogger(__name__)


def _call_with_retry(fn, *args, max_retries=3, base_delay=2.0, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on 503/429 errors."""
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            # Retry on transient Gemini overload / rate-limit errors
            if any(code in msg for code in ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED")):
                last_exc = e
                delay = base_delay * (2 ** attempt)
                logger.warning("Gemini transient error (attempt %d/%d): %s — retrying in %.1fs",
                               attempt + 1, max_retries, msg[:120], delay)
                time.sleep(delay)
            else:
                raise  # non-transient — re-raise immediately
    raise last_exc


class GeminiEmbeddings:
    """
    Langchain-compatible embeddings using the google.genai REST SDK.
    Avoids the gRPC / numpy2 issues in langchain_google_genai and langchain_huggingface.
    """
    def __init__(self, api_key: str, model: str = "models/gemini-embedding-001"):
        from google import genai as _genai
        self._client = _genai.Client(api_key=api_key)
        self._model  = model

    def embed_documents(self, texts: list) -> list:
        """Embed a list of documents in batches of 50."""
        results = []
        batch_size = 50
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            resp  = _call_with_retry(
                self._client.models.embed_content, model=self._model, contents=batch
            )
            results.extend([list(e.values) for e in resp.embeddings])
        return results

    def embed_query(self, text: str) -> list:
        resp = _call_with_retry(
            self._client.models.embed_content, model=self._model, contents=text
        )
        return list(resp.embeddings[0].values)

# ── Configuration ─────────────────────────────────────────────────────────────
COLLECTION_NAME  = "visa_policies"   # must match ingest_visa.py
MAX_MEMORY_TURNS = 6
HYBRID_FETCH_K   = 30   # candidates fetched from each retriever before RRF
RERANK_TOP_K     = 8    # chunks passed to LLM after re-ranking
MAX_QUERY_LEN    = 500

# ── Country name → ChromaDB metadata value mapping ───────────────────────────
# Used for query-time country detection + metadata pre-filtering
_COUNTRY_ALIASES: dict[str, str] = {
    "usa": "USA", "us": "USA", "united states": "USA", "america": "USA",
    "uk": "UK", "united kingdom": "UK", "britain": "UK", "england": "UK",
    "canada": "Canada", "canadian": "Canada",
    "australia": "Australia", "australian": "Australia",
    "germany": "Germany", "german": "Germany", "deutschland": "Germany",
    "france": "France", "french": "France",
    "netherlands": "Netherlands", "dutch": "Netherlands", "holland": "Netherlands",
    "ireland": "Ireland", "irish": "Ireland",
    "singapore": "Singapore",
    "japan": "Japan", "japanese": "Japan",
    "sweden": "Sweden", "swedish": "Sweden",
    "norway": "Norway", "norwegian": "Norway",
    "denmark": "Denmark", "danish": "Denmark",
    "finland": "Finland", "finnish": "Finland",
    "new zealand": "New Zealand", "nz": "New Zealand",
    "uae": "UAE", "dubai": "UAE", "abu dhabi": "UAE", "united arab emirates": "UAE",
    "portugal": "Portugal", "portuguese": "Portugal",
    "italy": "Italy", "italian": "Italy",
    "spain": "Spain", "spanish": "Spain", "spai": "Spain",
    "south korea": "South Korea", "korea": "South Korea",
    "switzerland": "Switzerland", "swiss": "Switzerland",
    "belgium": "Belgium", "belgian": "Belgium",
    "poland": "Poland", "polish": "Poland",
}

# Injection / jailbreak patterns
_INJECTION_PATTERNS = re.compile(
    r"ignore\s+(previous|all|above|prior|these|system)|"
    r"act\s+as\s+(?!visa|study)|pretend\s+(you\s+are|to\s+be)|"
    r"(DAN|jailbreak|prompt\s+injection|bypass)|reveal\s+(your\s+)?(instructions?|prompt)",
    re.IGNORECASE,
)

_VISA_KEYWORDS = re.compile(
    r"\b(visa|student|study|university|tuition|ielts|toefl|gre|gmat|scholarship|"
    r"admission|permit|passport|embassy|consul|immigration|residence|work\s+permit|"
    r"internship|graduate|phd|masters|bachelor|application|sop|lor|transcript|"
    r"financial|bank\s+statement|blocked\s+account|health\s+insurance|document|"
    r"requirement|fee|cost|process|time|duration|course|college|degree|"
    r"post.?study\s+work|opt|sevis|f-1|f1|tier\s*4|pgwp|cricos|"
    r"uk|usa|canada|australia|germany|france|netherlands|ireland|singapore|"
    r"japan|sweden|norway|denmark|finland|zealand|uae|portugal|italy|spain|"
    r"korea|switzerland|belgium|poland)\b",
    re.IGNORECASE,
)

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
        api_key = settings.GOOGLE_API_KEY
        if not api_key:
            logger.error("GOOGLE_API_KEY not set — embeddings unavailable")
            return None
        _embeddings = GeminiEmbeddings(api_key=api_key)
    return _embeddings


def _get_vectorstore() -> Optional[Chroma]:
    global _vectorstore
    if _vectorstore is None:
        db = _db_dir()
        if not os.path.exists(db):
            logger.warning("ChromaDB not found at %s — run scripts/ingest_visa.py first", db)
            return None
        emb = _get_embeddings()
        if emb is None:
            logger.error("Embeddings unavailable — cannot load vectorstore")
            return None
        _vectorstore = Chroma(
            persist_directory=db,
            embedding_function=emb,
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


def cleanse_query(raw: str) -> tuple[str, bool]:
    """Strip HTML, control chars, and truncate. Returns (cleaned, was_truncated)."""
    text = html.unescape(raw)
    text = re.sub(r"<[^>]{0,200}>", "", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    text = re.sub(r"[ \t]{3,}", "  ", text).strip()
    truncated = len(text) > MAX_QUERY_LEN
    return text[:MAX_QUERY_LEN] + ("…" if truncated else ""), truncated


def is_visa_related(text: str) -> bool:
    return bool(_VISA_KEYWORDS.search(text))


def _detect_country(text: str) -> Optional[str]:
    """Return the canonical country name if the query mentions one."""
    lower = text.lower()
    # Longer aliases first to avoid partial matches (e.g. 'uk' inside 'ukraine')
    for alias in sorted(_COUNTRY_ALIASES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", lower):
            return _COUNTRY_ALIASES[alias]
    return None


def _reciprocal_rank_fusion(
    *ranked_lists: List[str],
    k: int = 60,
) -> List[str]:
    """Merge any number of ranked lists with Reciprocal Rank Fusion (RRF)."""
    scores: Dict[str, float] = {}
    for ranked in ranked_lists:
        for rank, doc_id in enumerate(ranked):
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return [doc_id for doc_id, _ in sorted(scores.items(), key=lambda x: x[1], reverse=True)]


def _hyde_retrieve(query: str, genai_client, k: int = 10) -> List[Tuple[str, str, dict]]:
    """
    Hypothetical Document Embedding (HyDE).
    Generate a short hypothetical answer → embed it → search ChromaDB.
    """
    vs = _get_vectorstore()
    if vs is None or genai_client is None:
        return []
    try:
        from google.genai import types as _gtypes
        hyde_prompt = (
            "You are a study abroad visa expert. Write a 2-3 sentence factual answer "
            "to this student question. Be specific with exact numbers, fees, and requirements.\n\n"
            f"Question: {query}"
        )
        resp    = genai_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=hyde_prompt,
            config=_gtypes.GenerateContentConfig(temperature=0.1, max_output_tokens=200),
        )
        hyp_doc = resp.text
        emb     = _get_embeddings()
        if emb is None:
            return []
        hyp_vec = emb.embed_query(hyp_doc)
        results = vs.similarity_search_by_vector(hyp_vec, k=k)
        return [
            (d.metadata.get("id", d.page_content[:40]), d.page_content, d.metadata)
            for d in results
        ]
    except Exception as e:
        logger.warning("HyDE retrieval failed: %s", e)
        return []


# ── Core Retrieval ────────────────────────────────────────────────────────────

def hybrid_retrieve(
    query: str,
    k: int = HYBRID_FETCH_K,
    country_filter: Optional[str] = None,
    hyde_docs: Optional[List[Tuple[str, str, dict]]] = None,
) -> List[Tuple[str, str, dict]]:
    """
    4-leg retrieval merged with RRF:
      Leg 1 — Dense semantic (all docs)
      Leg 2 — BM25 keyword
      Leg 3 — Country-filtered dense (when country detected in query)
      Leg 4 — HyDE dense (pre-computed hypothetical doc embedding)
    Returns (id, text, metadata) tuples sorted by fused score.
    """
    vs = _get_vectorstore()
    if vs is None:
        return []

    # Leg 1 — Dense semantic (unfiltered)
    dense_docs = vs.similarity_search(query, k=k)
    dense_ids  = [d.metadata.get("id", d.page_content[:40]) for d in dense_docs]
    dense_map  = {did: d for did, d in zip(dense_ids, dense_docs)}

    # Leg 2 — BM25 keyword
    bm25, corpus = _get_bm25()
    bm25_ids: List[str] = []
    bm25_map: Dict[str, Tuple[str, str, dict]] = {}
    if bm25 is not None and corpus:
        tokens   = re.findall(r"\w+", query.lower())
        scores   = bm25.get_scores(tokens)
        top_idx  = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        bm25_ids = [corpus[i][0] for i in top_idx]
        bm25_map = {corpus[i][0]: corpus[i] for i in top_idx}

    # Leg 3 — Country-filtered dense (strong signal when country is mentioned)
    country_ids: List[str] = []
    country_map: Dict[str, Tuple[str, str, dict]] = {}
    if country_filter:
        try:
            cf_docs = vs.similarity_search(query, k=k // 2, filter={"country": country_filter})
            for d in cf_docs:
                did = d.metadata.get("id", d.page_content[:40])
                country_ids.append(did)
                country_map[did] = (did, d.page_content, d.metadata)
        except Exception:
            pass

    # Leg 4 — HyDE results
    hyde_ids: List[str] = []
    hyde_map: Dict[str, Tuple[str, str, dict]] = {}
    if hyde_docs:
        for did, text, meta in hyde_docs:
            hyde_ids.append(did)
            hyde_map[did] = (did, text, meta)

    # RRF merge all legs (country + HyDE get double weight via duplication)
    fused_ids = _reciprocal_rank_fusion(
        dense_ids, bm25_ids, country_ids, country_ids, hyde_ids
    )

    # Reconstruct ordered results
    all_maps = [dense_map, bm25_map, country_map, hyde_map]
    results: List[Tuple[str, str, dict]] = []
    seen: set = set()
    for did in fused_ids:
        if did in seen:
            continue
        seen.add(did)
        for m in all_maps:
            if did in m:
                entry = m[did]
                if isinstance(entry, tuple):
                    results.append(entry)
                else:
                    results.append((did, entry.page_content, entry.metadata))
                break
        if len(results) >= k:
            break

    # Fill remainder from dense
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

CRITICAL RULES:
- Answer ONLY about the country the student asked about. If the student asks about Spain, answer about Spain only. Do NOT mix in information from other countries.
- Always cite the exact source document (e.g., "According to spain.md…").
- Be COMPREHENSIVE and DETAILED — include exact figures, fees in INR and local currency, processing times, work hour limits, specific thresholds, tips, common mistakes, and any warnings.
- Use bullet points and numbered steps. For document lists, include WHY each document is needed and any India-specific notes (apostille, translation requirements, etc.).
- Adapt response length to the question: simple factual questions → concise; "what documents do I need" or "explain the process" → full detailed breakdown.
- For documents questions: list EVERY document, include the exact specification (validity period, format, who issues it, India-specific requirements like apostille/notarisation/translation).
- For timeline questions: give exact week-by-week breakdown with all stages.
- If something is NOT in the context, say so clearly and recommend the official embassy website — do NOT invent information.
- Never fabricate visa policies, fees, or deadlines.

Target country: {country}

Retrieved context:
{context}
"""

    def __init__(self):
        api_key = settings.GOOGLE_API_KEY
        if not api_key or api_key == "your_gemini_api_key_here":
            logger.error("GOOGLE_API_KEY not set — Gemini LLM unavailable.")
            self._client = None
            return
        from google import genai as _genai
        self._client = _genai.Client(api_key=api_key)
        self._model  = "gemini-2.5-flash"

    def _generate(self, prompt: str, max_tokens: int = 2048) -> str:
        """Direct REST call to Gemini with retry on transient errors."""
        from google.genai import types as _gt
        config = _gt.GenerateContentConfig(temperature=0.1, max_output_tokens=max_tokens)
        resp = _call_with_retry(
            self._client.models.generate_content,
            model=self._model,
            contents=prompt,
            config=config,
        )
        return resp.text

    def invoke(self, input_dict: dict) -> dict:
        if self._client is None:
            return {
                "answer": (
                    "The AI answer generator is not available because the GOOGLE_API_KEY "
                    "environment variable has not been set. Please add your Gemini API key to "
                    "backend/.env and restart the server."
                ),
                "context": [],
            }

        raw_query  = input_dict["input"]
        country    = input_dict.get("country", "the target country")
        session_id = input_dict.get("session_id", "default")

        # ── Stage 0: Input cleansing + guard rails ────────────────────────────
        query, _ = cleanse_query(raw_query)

        if _INJECTION_PATTERNS.search(query):
            return {
                "answer": "I can only assist with study abroad and visa-related questions.",
                "context": [],
            }
        if len(query.strip()) > 10 and not is_visa_related(query):
            return {
                "answer": (
                    "I'm a study abroad visa assistant and can only help with questions "
                    "about student visas, university applications, scholarships, and related topics. "
                    "Please ask a question related to studying abroad."
                ),
                "context": [],
            }

        # ── Stage 1a: Detect country from query text ──────────────────────────
        detected_country = _detect_country(query)
        # Query-mentioned country ALWAYS wins — user may ask "Spain visa" while
        # the UI country selector still shows "UK". Fall back to the UI param.
        ui_country = country if country not in ("the target country", "General", None) else None
        effective_country = detected_country or ui_country
        # For the LLM prompt, show the true focus country
        prompt_country = effective_country or country

        # ── Stage 1b: HyDE — generate hypothetical answer for better retrieval ─
        # HyDE is best-effort; failure is already caught inside _hyde_retrieve
        hyde_docs = _hyde_retrieve(query, self._client, k=10)

        # ── Stage 1c: Hybrid retrieval (dense + BM25 + country-filter + HyDE) ─
        try:
            candidates = hybrid_retrieve(
                query,
                k=HYBRID_FETCH_K,
                country_filter=effective_country,
                hyde_docs=hyde_docs,
            )
        except Exception as e:
            logger.error("Retrieval failed: %s", e)
            return {
                "answer": (
                    "Gemini is experiencing high demand right now. "
                    "Please wait a moment and try your question again — it should work shortly."
                ),
                "context": [],
            }

        # ── Stage 2: Cross-encoder re-ranking ────────────────────────────────
        top_chunks = rerank(query, candidates, top_k=RERANK_TOP_K)

        # ── Stage 2b: Hard country guarantee (belt-and-suspenders) ────────────
        # If the effective country is known and fewer than 2 chunks come from
        # it, forcibly inject 1–2 country chunks so the LLM always has at
        # least some country-specific grounding.
        if effective_country:
            existing_country_count = sum(
                1 for _, _, meta in top_chunks
                if meta.get("country") == effective_country
            )
            if existing_country_count < 2:
                vs = _get_vectorstore()
                if vs is not None:
                    try:
                        country_docs = vs.similarity_search(
                            query, k=3,
                            filter={"country": effective_country},
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
                        pass

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
        system_block = self.SYSTEM_PROMPT.format(
            country=prompt_country, context=context_text
        )

        full_prompt = system_block + "\n\n"
        for prev_q, prev_a in history:
            full_prompt += f"Student: {prev_q}\nAssistant: {prev_a}\n\n"
        full_prompt += f"Student: {query}\nAssistant:"

        # Longer questions (documents/process/timeline) get more tokens
        is_detailed_q = any(w in query.lower() for w in
                            ["document", "process", "timeline", "step", "all", "complete",
                             "everything", "how to apply", "explain", "detail"])
        max_tok = 4096 if is_detailed_q else 2048

        try:
            answer = self._generate(full_prompt, max_tokens=max_tok)
        except Exception as e:
            logger.error("Gemini generation failed: %s", e)
            return {
                "answer": (
                    "Gemini is experiencing high demand right now. "
                    "Please wait a few seconds and ask your question again."
                ),
                "context": [],
            }

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
