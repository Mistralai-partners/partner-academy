"""Single-corpus RAG helpers: chunk -> embed -> cosine retrieve -> grounded prompt.

Grounded on rag_quickstart.md (platform-docs-public @ a3e0f0c7) and mistralai==2.9.4:
  - Chunk the corpus by characters (size, plus an overlap to preserve context).
  - Embed with client.embeddings.create(model="mistral-embed", inputs=[...])
    and read vectors from response.data[i].embedding.
  - Retrieve the most similar chunks. The quickstart uses FAISS IndexFlatL2; here
    we implement cosine similarity explicitly so the ranking math is inspectable.

The Analyze skill: retrieval quality depends on (a) chunk overlap so a fact that
straddles a boundary is not lost, and (b) using COSINE (normalized) similarity so
a long chunk does not out-rank a semantically closer short one on raw dot product.
"""
import math
from typing import List, Sequence


def chunk_text(text: str, size: int, overlap: int = 0) -> List[str]:
    """Split text into character windows of `size` that overlap by `overlap`."""
    if size <= 0:
        raise ValueError("size must be > 0")
    step = size - overlap
    if step <= 0:
        raise ValueError("overlap must be smaller than size")
    return [text[i:i + size] for i in range(0, len(text), step)]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)


def top_k(query_vec: Sequence[float], matrix: Sequence[Sequence[float]], k: int) -> List[int]:
    """Return indices of the k chunks most similar to query_vec, best first."""
    scored = [(_cosine(query_vec, row), i) for i, row in enumerate(matrix)]
    scored.sort(key=lambda t: t[0], reverse=True)
    return [i for _, i in scored[:k]]


def build_grounded_prompt(question: str, retrieved_chunks: Sequence[str]) -> str:
    context = "\n---\n".join(retrieved_chunks)
    return (
        "Context information is below.\n"
        "---------------------\n"
        f"{context}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, answer the query.\n"
        f"Query: {question}\n"
        "Answer:"
    )
