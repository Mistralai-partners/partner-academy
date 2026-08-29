#!/usr/bin/env python
"""Task 2 (SOLUTION) - Grounded RAG answer with an honest refusal (the live demo).

Demo point (maps to B4): a build-your-own RAG pipeline is embed -> retrieve ->
ground. Retrieval alone is not grounding; you must also constrain generation to
the retrieved context. Done right, the model answers supported questions from the
customer's own documents AND refuses unsupported ones instead of hallucinating -
which is the trust moment that wins a skeptical technical buyer. (When the buyer
wants this managed rather than hand-built, that is Libraries; see tasks.md.)

Grounded SDK calls (mistralai==1.9.11, verified live):
  - client.embeddings.create(model="mistral-embed", inputs=[...])
  - client.chat.complete(model=..., messages=[...])
Source: platform-docs-public public/studio-api/knowledge-rag/rag_quickstart.md
        (build-your-own RAG) + knowledge-rag/embeddings.md.
"""
import math
import os
import sys

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
CHAT_MODEL = "mistral-small-latest"
EMBED_MODEL = "mistral-embed"

CORPUS = [
    "The Meridian X1 drone has a maximum flight time of 38 minutes on a single charge.",
    "The Meridian X1 supports a top speed of 72 kilometers per hour.",
    "Meridian X1 firmware updates are delivered over the air every quarter.",
    "The Meridian X1 operating temperature range is -10 to 40 degrees Celsius.",
    "The Meridian X1 camera captures 4K video at 60 frames per second.",
]


def _embed(client, texts):
    return [d.embedding for d in client.embeddings.create(model=EMBED_MODEL, inputs=texts).data]


def _cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb)


def retrieve(client, corpus_vecs, query, k=2):
    qv = _embed(client, [query])[0]
    scored = sorted(((_cosine(qv, v), i) for i, v in enumerate(corpus_vecs)), reverse=True)
    return [CORPUS[i] for _, i in scored[:k]]


def answer(client, corpus_vecs, query):
    """Ground the reply: pass the retrieved context and forbid outside knowledge."""
    context = "\n".join(f"- {c}" for c in retrieve(client, corpus_vecs, query))
    system = (
        "Answer ONLY using the provided context. If the answer is not in the "
        "context, reply with exactly NOT_IN_SOURCES and nothing else."
    )
    resp = client.chat.complete(
        model=CHAT_MODEL,
        max_tokens=80,
        temperature=0,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"},
        ],
    )
    return resp.choices[0].message.content.strip()


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    corpus_vecs = _embed(client, CORPUS)

    grounded_q = "How long can the Meridian X1 fly on one charge?"
    unknown_q = "What is the warranty period for the Meridian X1?"

    a1 = answer(client, corpus_vecs, grounded_q)
    a2 = answer(client, corpus_vecs, unknown_q)
    print(f"GROUNDED  Q: {grounded_q}\n           A: {a1!r}")
    print(f"UNKNOWN   Q: {unknown_q}\n           A: {a2!r}")

    # Acceptance: the supported question is answered from the corpus (contains
    # the fact), and the unsupported question is honestly refused.
    assert "38" in a1, "grounded answer did not surface the supported fact (38 minutes)"
    assert a2.strip().upper().startswith("NOT_IN_SOURCES"), (
        "unsupported question was NOT refused - the model answered from memory"
    )
    print("TASK2 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK2 FAIL: {e}")
        sys.exit(1)
