"""
Semantic skill matching using FAISS.

Exact string matching (used in agents/matching_agent.py) misses skills that
are phrased differently but mean the same thing — e.g. "ML" vs "Machine
Learning", "React.js" vs "React", "NLP" vs "Natural Language Processing".

This module builds a small in-memory FAISS index over a candidate's resume
skills and queries it with each job-description skill to find near-matches
that exact matching would otherwise report as "missing."

Design note: this uses the same FAISS + HuggingFaceEmbeddings pattern already
used in rag/vector_store.py for document-level RAG, applied here at the
skill-phrase level. Skill lists are small (typically under 30 items), so a
fresh in-memory FAISS index per match call is cheap — no persistence needed.

Calibration note (measured on sentence-transformers/all-MiniLM-L6-v2 via
scripts/calibrate.py):
    React.js <-> React                          distance = 0.234
    NLP <-> Natural Language Processing          distance = 0.796
    ML <-> Machine Learning                      distance = 1.255
    Docker <-> Photoshop (unrelated, baseline)   distance = 1.463

0.85 was chosen as the default threshold: it catches true synonyms like the
React and NLP pairs while staying well clear of the unrelated-pair distance.
It deliberately does NOT catch "ML" <-> "Machine Learning" — bare two-letter
acronyms carry too little semantic signal for this embedding model in
isolation, and their distance (1.255) sits too close to genuinely unrelated
pairs (1.463) to raise the threshold that high without introducing false
positives. _COMMON_ACRONYMS below expands a short list of known offenders
before embedding as a targeted fix for that specific gap.
"""

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings

_embeddings = None

# Bare acronyms embed poorly in isolation (see calibration note above).
# Expand the common ones before embedding rather than relying on the
# embedding model to bridge the gap on its own.
_COMMON_ACRONYMS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "cv": "computer vision",
    "dl": "deep learning",
    "llm": "large language model",
    "api": "application programming interface",
    "db": "database",
    "ci/cd": "continuous integration continuous deployment",
    "oop": "object oriented programming",
}


def _expand(skill: str) -> str:
    """Expand known acronyms; otherwise return the skill unchanged."""
    expansion = _COMMON_ACRONYMS.get(skill.strip().lower())
    return expansion if expansion else skill


def _get_embedder():
    """Lazily load the embedding model once and reuse it across calls."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def find_semantic_matches(
    resume_skills: list[str],
    jd_skills: list[str],
    distance_threshold: float = 0.85,
):
    """
    For each jd_skill, find the closest resume_skill by embedding distance.

    Returns a dict: { jd_skill: {"matched_to": resume_skill, "distance": float} }
    for every jd_skill whose nearest resume_skill is within distance_threshold.

    NOTE on distance_threshold: LangChain's FAISS wrapper returns L2
    (Euclidean) distance by default — LOWER means more similar. This is not
    a 0-1 cosine similarity score. See the calibration note in the module
    docstring for how 0.85 was chosen and its known limitation with bare
    acronyms.
    """
    if not resume_skills or not jd_skills:
        return {}

    embedder = _get_embedder()

    expanded_resume_skills = [_expand(s) for s in resume_skills]
    index = FAISS.from_texts(expanded_resume_skills, embedder)

    # Map expanded text back to the original resume skill for reporting.
    expanded_to_original = dict(zip(expanded_resume_skills, resume_skills))

    matches = {}
    for skill in jd_skills:
        query = _expand(skill)
        results = index.similarity_search_with_score(query, k=1)
        if not results:
            continue

        doc, distance = results[0]
        if distance <= distance_threshold:
            matches[skill] = {
                "matched_to": expanded_to_original.get(doc.page_content, doc.page_content),
                "distance": round(float(distance), 4),
            }

    return matches


def calibrate_threshold(pairs: list[tuple[str, str]]):
    """
    Utility to help you pick distance_threshold before relying on it.

    Pass known synonym pairs, e.g.:
        [("ML", "Machine Learning"), ("React.js", "React"), ("NLP", "Natural Language Processing")]

    Prints the distance for each pair so you can see what a "true match"
    distance looks like, then compare against distances for clearly
    unrelated skill pairs (e.g. "Docker" vs "Photoshop") to find a cutoff
    that separates the two groups.

    Run this once on your machine before trusting the default threshold above.
    """
    embedder = _get_embedder()
    for a, b in pairs:
        index = FAISS.from_texts([a], embedder)
        results = index.similarity_search_with_score(b, k=1)
        distance = results[0][1] if results else None
        print(f"{a!r} <-> {b!r}: distance = {distance}")