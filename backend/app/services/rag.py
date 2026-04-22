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


# Model fallback chain — used only when quota is exhausted (429), NOT for transient 503s.
# gemini-2.5-flash-lite is the only confirmed fallback for this account.
_GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]


def _call_with_retry(fn, *args, max_retries=5, base_delay=2.0, **kwargs):
    """Call fn(*args, **kwargs) with exponential backoff on transient errors.

    Strategy:
      - 503 UNAVAILABLE (overload): retry same model, backoff 2→4→8→16→32s
      - 429 RESOURCE_EXHAUSTED (quota): switch to lighter fallback model once, then retry
      - Other errors: raise immediately
    """
    last_exc = None

    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            msg = str(e)
            is_503 = "503" in msg or "UNAVAILABLE" in msg
            is_429 = "429" in msg or "RESOURCE_EXHAUSTED" in msg

            if is_503 or is_429:
                last_exc = e
                delay = base_delay * (2 ** min(attempt, 4))   # cap at 32s
                # Only switch model on quota exhaustion (429), not overload (503)
                if is_429 and attempt == 1 and "model" in kwargs:
                    cur = kwargs["model"]
                    idx = _GEMINI_MODELS.index(cur) if cur in _GEMINI_MODELS else 0
                    if idx + 1 < len(_GEMINI_MODELS):
                        kwargs["model"] = _GEMINI_MODELS[idx + 1]
                        logger.warning("Quota exhausted — switching to fallback model %s", kwargs["model"])
                logger.warning("Gemini transient error (attempt %d/%d): %s — retrying in %.1fs",
                               attempt + 1, max_retries, msg[:100], delay)
                time.sleep(delay)
            else:
                raise
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

# Generic / multi-country query patterns → skip country filter
_GENERIC_QUERY_PATTERNS = re.compile(
    r"\b(any\s+(european|country|countries|schengen)|"
    r"all\s+(european|countries|schengen)|"
    r"european\s+(countr|visa|student|union|schengen)|"
    r"schengen|"
    r"multiple\s+countr|"
    r"which\s+countr|"
    r"compare\s+countr|"
    r"best\s+countr|"
    r"same\s+as|"
    r"vs\.?\s+\w|"
    r"differ(ent|ence|s)?\s+(between|from)|"
    r"general(ly)?|"
    r"in\s+general)\b",
    re.IGNORECASE,
)

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
    r"internship|graduate|grad|phd|masters|bachelor|application|sop|lor|transcript|"
    r"financial|bank\s+statement|blocked\s+account|health\s+insurance|document|"
    r"requirement|fee|cost|process|time|duration|course|college|degree|program|"
    r"post.?study\s+work|opt|sevis|f-1|f1|tier\s*4|pgwp|cricos|"
    r"housing|accommodation|flat|room|rent|apartment|hostel|dormitory|"
    r"job|career|work|employ|salary|internship|placement|graduate\s+job|"
    r"schengen|european|europe|aps|blocked\s+account|gic|biometrics|"
    r"savings|earning|sponsor|parent|fund|afford|budget|living\s+cost|"
    r"police\s+clearance|pcc|apostille|translation|notari|"
    r"statement\s+of\s+purpose|personal\s+statement|letter\s+of\s+recommend|"
    r"recommendation\s+letter|research\s+proposal|graduate\s+school|grad\s+school|"
    r"uk|usa|canada|australia|germany|france|netherlands|ireland|singapore|"
    r"japan|sweden|norway|denmark|finland|zealand|uae|portugal|italy|spain|"
    r"korea|switzerland|belgium|poland|india|indian)\b",
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
    """Cross-encoder disabled — NumPy 2.x incompatibility with sentence_transformers.
    We use Gemini reranker instead (see _gemini_rerank). Returns None always."""
    return None


def _gemini_rerank(
    query: str,
    candidates: List[Tuple[str, str, dict]],
    client,
    top_k: int = RERANK_TOP_K,
) -> List[Tuple[str, str, dict]]:
    """
    Use Gemini to score each candidate chunk's relevance to the query.
    Sends a single batch scoring prompt — much faster than one call per chunk.
    Falls back to RRF order on any failure.
    """
    if not candidates or client is None:
        return candidates[:top_k]

    try:
        from google.genai import types as _gt
        import json as _json
        n_cands = min(len(candidates), 15)   # cap at 15 to keep output tokens manageable
        # Build a compact scoring prompt — just indices + first 250 chars each
        snippets = "\n".join(
            f"[{i}] {text[:250].replace(chr(10), ' ')}"
            for i, (_, text, _) in enumerate(candidates[:n_cands])
        )
        prompt = (
            f"You are a relevance judge. For the student question below, score each passage "
            f"0-10 for relevance (10=directly answers the question). "
            f"Reply ONLY with a compact JSON array of {n_cands} integers on a SINGLE LINE. "
            f"Example for 3 passages: [8,5,2]\n"
            f"No markdown, no explanation, no newlines inside the array.\n\n"
            f"Question: {query}\n\nPassages:\n{snippets}\n\nScores:"
        )
        resp = _call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config=_gt.GenerateContentConfig(temperature=0.0, max_output_tokens=300),
        )
        raw = resp.text.strip()
        # Strip markdown code fences if Gemini wrapped the array
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```\s*$", "", raw)
        raw = raw.strip()

        # Try strict JSON parse first, then fall back to regex
        scores = None
        try:
            parsed = _json.loads(raw)
            if isinstance(parsed, list):
                scores = [float(x) for x in parsed]
        except Exception:
            pass

        if scores is None:
            # Regex: extract any [ ... ] block (handles multiline)
            m = re.search(r"\[[\d\s,\.]+\]", raw, re.DOTALL)
            if not m:
                # Last resort: grab all numbers from the line
                nums = re.findall(r"\b(\d+(?:\.\d+)?)\b", raw)
                if nums:
                    scores = [float(x) for x in nums]
                else:
                    raise ValueError(f"No numeric scores in response: {raw[:120]}")
            else:
                scores = [float(x) for x in re.findall(r"[\d\.]+", m.group())]

        # Pad with 0s if fewer scores than candidates
        while len(scores) < n_cands:
            scores.append(0.0)
        # Sort by score descending
        scored = sorted(
            zip(scores[:n_cands], candidates[:n_cands]),
            key=lambda x: x[0],
            reverse=True,
        )
        result = [c for _, c in scored[:top_k]]
        logger.debug("Gemini reranker: top score=%.1f, bottom=%.1f",
                     scores[0] if scores else 0, scores[-1] if scores else 0)
        return result
    except Exception as e:
        logger.warning("Gemini reranker failed (%s) — using RRF order", e)
        return candidates[:top_k]


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
    """Return the canonical country name if the query mentions exactly one country."""
    found = _detect_all_countries(text)
    if len(found) == 1:
        return found[0]
    return None  # 0 or multiple countries → caller handles


def _detect_all_countries(text: str) -> List[str]:
    """Return all unique canonical country names mentioned in the query."""
    lower = text.lower()
    seen: set = set()
    result: List[str] = []
    for alias in sorted(_COUNTRY_ALIASES, key=len, reverse=True):
        if re.search(r"\b" + re.escape(alias) + r"\b", lower):
            canonical = _COUNTRY_ALIASES[alias]
            if canonical not in seen:
                seen.add(canonical)
                result.append(canonical)
    return result


def _expand_query(query: str, client, country: Optional[str] = None) -> List[str]:
    """
    Generate 2 alternative phrasings of the query to improve recall.
    Returns [original, variant1, variant2]. Falls back to [original] on failure.
    """
    if client is None:
        return [query]
    try:
        from google.genai import types as _gt
        ctx = f" The student is asking about {country}." if country else ""
        prompt = (
            f"Rewrite this student question in 2 different ways to help retrieve relevant passages "
            f"from a visa/study-abroad knowledge base.{ctx}\n"
            f"Original: {query}\n"
            f"Reply with ONLY 2 lines, one rewriting per line. No numbering, no explanation."
        )
        resp = _call_with_retry(
            client.models.generate_content,
            model="gemini-2.5-flash",
            contents=prompt,
            config=_gt.GenerateContentConfig(temperature=0.0, max_output_tokens=100),
        )
        variants = [v.strip() for v in resp.text.strip().split("\n") if v.strip()][:2]
        return [query] + variants
    except Exception as e:
        logger.debug("Query expansion failed: %s", e)
        return [query]


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
            config=_gtypes.GenerateContentConfig(temperature=0.0, max_output_tokens=200),
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
    extra_queries: Optional[List[str]] = None,
) -> List[Tuple[str, str, dict]]:
    """
    4-leg retrieval merged with RRF:
      Leg 1 — Dense semantic (all docs, across all query variants)
      Leg 2 — BM25 keyword (union of all query variants)
      Leg 3 — Country-filtered dense (when country detected in query)
      Leg 4 — HyDE dense (pre-computed hypothetical doc embedding)
    Returns (id, text, metadata) tuples sorted by fused score.
    """
    vs = _get_vectorstore()
    if vs is None:
        return []

    # Leg 1 — Dense semantic (unfiltered) — run for each query variant, merge
    all_dense_docs: List = []
    all_dense_ids:  List[str] = []
    for q_variant in (extra_queries or [query]):
        try:
            docs = vs.similarity_search(q_variant, k=k)
            for d in docs:
                did = d.metadata.get("id", d.page_content[:40])
                if did not in {x.metadata.get("id", x.page_content[:40]) for x in all_dense_docs}:
                    all_dense_docs.append(d)
                    all_dense_ids.append(did)
        except Exception:
            pass
    dense_ids = all_dense_ids
    dense_map = {d.metadata.get("id", d.page_content[:40]): d for d in all_dense_docs}

    # Leg 2 — BM25 keyword (union of all query variants)
    bm25, corpus = _get_bm25()
    bm25_ids: List[str] = []
    bm25_map: Dict[str, Tuple[str, str, dict]] = {}
    if bm25 is not None and corpus:
        bm25_score_map: Dict[str, float] = {}
        for q_variant in (extra_queries or [query]):
            tokens = re.findall(r"\w+", q_variant.lower())
            scores = bm25.get_scores(tokens)
            for i, sc in enumerate(scores):
                cid = corpus[i][0]
                bm25_score_map[cid] = max(bm25_score_map.get(cid, 0.0), sc)
        top_items = sorted(bm25_score_map.items(), key=lambda x: x[1], reverse=True)[:k]
        bm25_ids  = [cid for cid, _ in top_items]
        bm25_map  = {corpus[i][0]: corpus[i] for i in range(len(corpus)) if corpus[i][0] in set(bm25_ids)}

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

    # Fill remainder from dense (fix: was referencing undefined `dense_docs`)
    for d in all_dense_docs:
        did = d.metadata.get("id", d.page_content[:40])
        if did not in seen and len(results) < k:
            results.append((did, d.page_content, d.metadata))
            seen.add(did)

    return results


def rerank(
    query: str,
    candidates: List[Tuple[str, str, dict]],
    top_k: int = RERANK_TOP_K,
    client=None,
) -> List[Tuple[str, str, dict]]:
    """Gemini-based reranking (replaces sentence-transformers CrossEncoder).
    Falls back to RRF order if Gemini is unavailable."""
    if not candidates:
        return []
    return _gemini_rerank(query, candidates, client=client, top_k=top_k)


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
You are StudyPathway's Study Abroad AI for Indian students. Primary focus: student visas. \
Secondary: jobs, housing, scholarships, financial proof, SOPs, and everything study-abroad.

**MANDATORY**: The retrieved context below contains the answer. You MUST extract and use it.

RULES (follow precisely):
1. COUNTRY: Answer only for the country asked. Never mix UK info into a Spain answer etc. \
   For "any European country" / "compare countries" → structured multi-country comparison.
2. LENGTH — match question complexity exactly:
   • Single-fact question (one fee, one date, yes/no) → 1–3 lines, no padding
   • Multi-part factual question → 4–8 bullet points with bold labels
   • Document checklist / process / timeline → full numbered/bulleted breakdown with India-specific specs
   • Comparison across countries → markdown table + brief notes per row
   • Financial requirements → exact figures + names of required documents
3. USE THE CONTEXT — If the retrieved context contains relevant information, you MUST answer \
   from it. NEVER say "I don't have information" or "I don't know" when the context has \
   relevant passages. Extract the specific facts, numbers, and steps from the context.
4. PRECISION — cite source filename inline: "According to germany.md…" or "(Source: germany.md)". \
   Do not pad with generic advice not in the context.
5. LINKS: include exact URLs from the context for jobs/housing/scholarship questions.
6. OUT-OF-SCOPE (only when context has zero relevant info): Respond exactly: \
   "This specific topic isn't covered in my knowledge base. Please check the official source: [URL]."
7. FORMAT: Use **bold** for key terms, bullet points for lists, numbered steps for processes, \
   markdown tables for comparisons. No fluff, no repetition.
8. DETERMINISTIC: State facts as facts. Avoid "might", "could", "possibly" unless the source \
   document itself is uncertain. Give the same consistent answer every time.

Target country: {country}

---RETRIEVED CONTEXT---
{context}
---END CONTEXT---
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
        """Direct REST call to Gemini with model fallback chain and retry."""
        from google.genai import types as _gt
        config = _gt.GenerateContentConfig(temperature=0.0, max_output_tokens=max_tokens)
        resp = _call_with_retry(
            self._client.models.generate_content,
            model=self._model,       # passed as kwarg so _call_with_retry can swap models
            contents=prompt,
            config=config,
        )
        return resp.text

    @staticmethod
    def _is_quota_error(e: Exception) -> bool:
        msg = str(e)
        return any(code in msg for code in ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "quota"))

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

        # Early guard — ensure vectorstore is loaded before doing any work
        if _get_vectorstore() is None:
            return {
                "answer": (
                    "The visa knowledge base hasn't been loaded yet. "
                    "Please run `python scripts/ingest_visa.py` in the backend directory "
                    "to index the documents, then restart the server."
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
        all_mentioned_countries = _detect_all_countries(query)
        detected_country = all_mentioned_countries[0] if len(all_mentioned_countries) == 1 else None
        ui_country = country if country not in ("the target country", "General", None) else None

        # Generic / multi-country / comparison queries → no country filter (retrieve broadly)
        is_generic = bool(_GENERIC_QUERY_PATTERNS.search(query))
        is_multi_country = len(all_mentioned_countries) > 1

        if is_generic or is_multi_country:
            effective_country = None   # don't narrow retrieval to one country
            prompt_country    = " vs ".join(all_mentioned_countries) if is_multi_country else "Multiple / General"
        else:
            # Query-mentioned country ALWAYS wins over UI dropdown selection
            effective_country = detected_country or ui_country
            prompt_country    = effective_country or country

        # ── Stage 1b: Query Expansion + HyDE (parallel best-effort) ─────────
        # Run both simultaneously — HyDE generates a hypothetical answer for richer retrieval
        # Query expansion generates 2 rephrased versions for better recall
        expanded_queries = _expand_query(query, self._client, effective_country)
        hyde_docs = _hyde_retrieve(query, self._client, k=10)

        # ── Stage 1c: Hybrid retrieval (dense + BM25 + country-filter + HyDE) ─
        try:
            candidates = hybrid_retrieve(
                query,
                k=HYBRID_FETCH_K,
                country_filter=effective_country,
                hyde_docs=hyde_docs,
                extra_queries=expanded_queries,
            )
            # For multi-country comparisons: guarantee docs from each country
            if is_multi_country and all_mentioned_countries:
                vs = _get_vectorstore()
                if vs is not None:
                    existing_ids = {cid for cid, _, _ in candidates}
                    extra: List[Tuple[str, str, dict]] = []
                    for cname in all_mentioned_countries:
                        try:
                            c_docs = vs.similarity_search(query, k=6, filter={"country": cname})
                            for d in c_docs:
                                did = d.metadata.get("id", d.page_content[:40])
                                if did not in existing_ids:
                                    extra.append((did, d.page_content, d.metadata))
                                    existing_ids.add(did)
                        except Exception:
                            pass
                    # Interleave extra country docs at front of candidates
                    candidates = extra + candidates
        except Exception as e:
            logger.error("Retrieval failed: %s", e, exc_info=True)
            if self._is_quota_error(e):
                return {
                    "answer": (
                        "Gemini API is rate-limited right now. "
                        "Please wait 30–60 seconds and ask your question again."
                    ),
                    "context": [],
                }
            return {
                "answer": (
                    f"I ran into an error while searching the knowledge base. "
                    f"Please try again. (Details: {type(e).__name__})"
                ),
                "context": [],
            }

        # ── Stage 2: Gemini reranker (replaces broken cross-encoder) ─────────
        top_chunks = rerank(query, candidates, top_k=RERANK_TOP_K, client=self._client)

        # ── Stage 2b: Hard country guarantee — ensure at least 3 country chunks ─
        if effective_country:
            existing_country_count = sum(
                1 for _, _, meta in top_chunks
                if meta.get("country") == effective_country
            )
            if existing_country_count < 3:
                vs = _get_vectorstore()
                if vs is not None:
                    try:
                        country_docs = vs.similarity_search(
                            query, k=5,
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
                            need = min(len(guaranteed), 3 - existing_country_count)
                            top_chunks = guaranteed[:need] + top_chunks[:RERANK_TOP_K - need]
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
            logger.error("Gemini generation failed: %s", e, exc_info=True)
            if self._is_quota_error(e):
                return {
                    "answer": (
                        "Gemini API quota reached. Please wait 30–60 seconds and ask again. "
                        "If this keeps happening, the free-tier daily limit may be exhausted — "
                        "check your API quota at aistudio.google.com."
                    ),
                    "context": [],
                }
            return {
                "answer": (
                    f"The AI model failed to generate a response. "
                    f"Please rephrase your question and try again. (Error: {type(e).__name__})"
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
    # For short follow-up queries ("how long?", "how much time?"), the query tokens
    # alone give poor signal — also score against the retrieved context to reward
    # answers that faithfully address the implicit topic.
    answer_relevancy_direct = _token_overlap(query, generated_answer)
    answer_relevancy_direct = min(1.0, answer_relevancy_direct * 8.0)  # normalise

    # Context-grounded relevancy: does the answer meaningfully use retrieved context?
    answer_relevancy_ctx = _token_overlap(combined_context[:2000], generated_answer) if combined_context else 0.0
    answer_relevancy_ctx = min(1.0, answer_relevancy_ctx * 6.0)

    # Short follow-up queries (≤6 words) rely more on context grounding
    query_word_count = len(query.split())
    if query_word_count <= 6:
        answer_relevancy = 0.4 * answer_relevancy_direct + 0.6 * answer_relevancy_ctx
    else:
        answer_relevancy = 0.7 * answer_relevancy_direct + 0.3 * answer_relevancy_ctx

    # Bonus for substantive answers
    answer_words = len(generated_answer.split())
    if answer_words > 50:
        answer_relevancy = min(1.0, answer_relevancy + 0.10)
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
