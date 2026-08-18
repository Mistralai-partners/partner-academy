#!/usr/bin/env python
"""Task 2 (STARTER) - Grounded RAG answer with an honest refusal (the live demo).

The demo you run in front of a customer worried about hallucination: the same
model answers a question it CAN support from their documents, and refuses -
instead of inventing - a question it cannot. This is the honesty story a
technical seller must be able to show, not just assert (course B4: RAG grounding
vs a model answering from parametric memory).

Your job: make `answer()` ground its reply in the retrieved corpus and say
NOT_IN_SOURCES when the corpus does not contain the answer. The starter ignores
the retrieved context and lets the model answer from memory, so it fabricates a
warranty period that is nowhere in the sources.

Grounded SDK calls (mistralai==1.9.11):
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
    # SYMPTOM: the model answers from its own memory, and for a question the corpus
    # does not cover (warranty) it invents a plausible-sounding value. See tasks.md (Task 2).
    resp = client.chat.complete(
        model=CHAT_MODEL,
        max_tokens=80,
        temperature=0,
        messages=[{"role": "user", "content": query}],
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
