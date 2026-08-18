#!/usr/bin/env python
"""Task 4 (SOLUTION) - Build a small RAG knowledge base.

Behavior (maps to MAIS-200 B3, FKC Q7/Q8): the from-scratch RAG order is
chunk -> embed (`mistral-embed`) -> retrieve by similarity -> ground the answer
in what you retrieved, and refuse when the fact is absent. Retrieval must rank by
DIRECTION (cosine similarity), not by document order, or you ground the answer on
the wrong passage. (The managed alternative is the Document Library / built-in
document tool, which handles chunk/embed/retrieve for you.)

Grounded SDK calls (mistralai==1.9.11, verified live):
  - client.embeddings.create(model="mistral-embed", inputs=[...]).data[i].embedding
  - client.chat.complete(model=..., messages=..., temperature=0)  (grounded answer)
Source: platform-docs-public public/studio-api/knowledge-rag/rag_quickstart.md +
        embeddings.md (pinned) + context7.
"""
import math
import os
import sys

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
MODEL = "mistral-small-latest"

# A tiny single corpus. The answer to the present-fact query is NOT the first
# chunk, so order-based "retrieval" gets it wrong; cosine similarity gets it right.
CORPUS = [
    "The office coffee machine is refilled every morning by the facilities team.",
    "The mistral-embed model produces embedding vectors with 1024 dimensions.",
    "Meeting rooms on the third floor can be booked through the internal portal.",
    "Parking permits are renewed annually in the building lobby.",
]
SIM_THRESHOLD = 0.75  # below this, we treat the fact as absent and refuse.


def embed(client, texts):
    resp = client.embeddings.create(model="mistral-embed", inputs=texts)
    return [d.embedding for d in resp.data]


def cosine(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def retrieve(query_vec, corpus_vecs):
    """Return (best_index, best_score), ranking by cosine similarity (direction)."""
    scores = [cosine(query_vec, v) for v in corpus_vecs]
    best = max(range(len(scores)), key=lambda i: scores[i])
    return best, scores[best]


def answer(client, question, passage):
    resp = client.chat.complete(
        model=MODEL,
        temperature=0,
        max_tokens=64,
        messages=[
            {"role": "system", "content": "Answer ONLY from the provided context. If it is not there, say you do not know."},
            {"role": "user", "content": f"Context: {passage}\n\nQuestion: {question}"},
        ],
    )
    return resp.choices[0].message.content


def ask(client, corpus_vecs, question):
    q_vec = embed(client, [question])[0]
    idx, score = retrieve(q_vec, corpus_vecs)
    if score < SIM_THRESHOLD:
        return None, score, "I do not have that information."
    return idx, score, answer(client, question, CORPUS[idx])


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    corpus_vecs = embed(client, CORPUS)

    # Present fact -> must retrieve chunk 1 and ground the answer on it.
    idx, score, resp = ask(client, corpus_vecs, "How many dimensions does mistral-embed produce?")
    print(f"PRESENT: idx={idx} score={score:.3f} answer={resp!r}")
    assert idx == 1, f"retrieved the wrong chunk (idx={idx}); ranking is not by similarity"
    assert "1024" in (resp or ""), f"grounded answer missing the retrieved fact: {resp!r}"

    # Absent fact -> similarity below threshold, so we refuse instead of inventing.
    idx2, score2, resp2 = ask(client, corpus_vecs, "What is the boiling point of helium in kelvin?")
    print(f"ABSENT: idx={idx2} score={score2:.3f} answer={resp2!r}")
    assert idx2 is None, f"should have refused (best score {score2:.3f} >= threshold)"

    print("TASK4 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK4 FAIL: {e}")
        sys.exit(1)
