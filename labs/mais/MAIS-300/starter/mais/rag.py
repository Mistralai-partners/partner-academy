"""Single-corpus RAG helpers: chunk -> embed -> cosine retrieve -> grounded prompt.

Grounded on rag_quickstart.md (platform-docs-public @ a3e0f0c7) and mistralai==1.9.11:
  - Chunk the corpus by characters (size, plus an overlap to preserve context).
  - Embed with client.embeddings.create(model="mistral-embed", inputs=[...])
    and read vectors from response.data[i].embedding.
  - Retrieve the most similar chunks (cosine similarity).

TASK 3 (Analyze/debug): retrieval is returning the wrong chunks. Two bugs:
one in chunking, one in the similarity math. Trace them from the tests and fix.
"""
import math
from typing import List, Sequence


def chunk_text(text: str, size: int, overlap: int = 0) -> List[str]:
    if size <= 0:
        raise ValueError("size must be > 0")
    # BUG 1 (Task 3): symptom — a fact that straddles a chunk boundary is split
    # and never retrieved intact. This function takes an `overlap` argument;
    # trace whether the step size below actually uses it.
    return [text[i:i + size] for i in range(0, len(text), size)]


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    # BUG 2 (Task 3): symptom — a long, high-magnitude chunk out-ranks a
    # semantically closer short one. Ask what property a *direction* comparison
    # must have that this expression does not.
    return sum(x * y for x, y in zip(a, b))


def top_k(query_vec: Sequence[float], matrix: Sequence[Sequence[float]], k: int) -> List[int]:
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
