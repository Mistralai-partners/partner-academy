#!/usr/bin/env python
"""Task 3 (SOLUTION) - Advanced embeddings: retrieval + measured quality.

Expert point (maps to FKC Q6 / B4): you cannot eyeball retrieval quality. You
rank candidates with the RIGHT similarity signal (cosine over the embedding
vectors) and you MEASURE the ordering with recall@k and MRR. A silent
similarity/ordering bug tanks both metrics even though the code "runs".
The grounded expert re-rank move is to reorder first-stage candidates by
embedding cosine similarity - not to reach for an ungrounded dedicated re-ranker.

Grounded SDK call (mistralai==2.9.4, verified live):
  - client.embeddings.create(model="mistral-embed", inputs=[...])
      -> response.data[i].embedding (1024-dim), response.data[i].index
Source: platform-docs-public public/studio-api/knowledge-rag/embeddings.md + context7.
"""
import math
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
EMB = "mistral-embed"

DOCS = [
    ("d0", "How to reset your account password from the login page."),
    ("d1", "Our refund policy allows returns within 30 days of purchase."),
    ("d2", "The warehouse ships orders every business day before 5pm."),
    ("d3", "To change your password, open Settings then Security."),
    ("d4", "Enterprise customers get a dedicated account manager."),
    ("d5", "Track a shipment using the tracking number in your email."),
]
QUERIES = [
    ("q0", "I forgot my password, how do I get back in?", {"d0", "d3"}),
    ("q1", "Can I return an item and get my money back?", {"d1"}),
    ("q2", "When will my package be shipped?", {"d2", "d5"}),
]
K = 3


def embed_all(client, texts):
    resp = client.embeddings.create(model=EMB, inputs=texts)
    ordered = sorted(resp.data, key=lambda d: d.index)
    return [d.embedding for d in ordered]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def similarity(a, b):
    """Cosine similarity - the correct signal for ranking mistral-embed vectors."""
    na, nb = math.sqrt(_dot(a, a)), math.sqrt(_dot(b, b))
    return _dot(a, b) / (na * nb)


def retrieve(query_vec, doc_vecs, k):
    """Return the k most similar doc ids, most-similar first (descending)."""
    scored = [(DOCS[i][0], similarity(query_vec, dv)) for i, dv in enumerate(doc_vecs)]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, _ in scored[:k]]


def evaluate(doc_vecs, query_vecs):
    rr_total, recall_total = 0.0, 0.0
    for i, (_, _, relevant) in enumerate(QUERIES):
        ranked = retrieve(query_vecs[i], doc_vecs, len(DOCS))
        for pos, doc_id in enumerate(ranked, start=1):
            if doc_id in relevant:
                rr_total += 1.0 / pos
                break
        topk = set(ranked[:K])
        recall_total += len(topk & relevant) / len(relevant)
    n = len(QUERIES)
    return rr_total / n, recall_total / n


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    texts = [d[1] for d in DOCS] + [q[1] for q in QUERIES]
    vecs = embed_all(client, texts)
    doc_vecs, query_vecs = vecs[: len(DOCS)], vecs[len(DOCS):]

    mrr, recall = evaluate(doc_vecs, query_vecs)
    print(f"RETRIEVAL mrr={mrr:.3f} recall@{K}={recall:.3f}")

    # Acceptance contract: correctly ranked retrieval scores near-perfect here.
    assert recall >= 0.99, f"recall@{K} too low: {recall:.3f}"
    assert mrr >= 0.80, f"MRR too low: {mrr:.3f}"
    print("TASK3 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK3 FAIL: {e}")
        sys.exit(1)
