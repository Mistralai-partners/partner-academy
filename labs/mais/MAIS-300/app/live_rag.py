"""Task 3 live proof: single-corpus RAG (chunk -> embed -> retrieve -> cite).

Run: uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv \
       python live_rag.py
Grounded (rag_quickstart.md): chunk by characters; embed with
client.embeddings.create(model="mistral-embed", inputs=[...]) -> data[i].embedding;
retrieve nearest chunks; ground the answer in the retrieved context.
"""
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from mais.rag import chunk_text, top_k, build_grounded_prompt

load_dotenv("/Users/victor.rojo/source/course-automation/.env")

CORPUS = (
    "Mistral AI Studio is a platform for building agents. "
    "The mistral-embed model produces 1024-dimensional text embeddings. "
    "Batch jobs are submitted as JSONL where each line carries a custom_id. "
    "Conversations can be restarted from an earlier entry to branch a thread. "
    "The Moderation API returns per-category scores you threshold yourself."
)


def embed(client, texts):
    resp = client.embeddings.create(model="mistral-embed", inputs=texts)
    return [d.embedding for d in resp.data]


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    chunks = chunk_text(CORPUS, size=90, overlap=30)
    chunk_vecs = embed(client, chunks)
    question = "How many dimensions does mistral-embed produce?"
    q_vec = embed(client, [question])[0]
    idx = top_k(q_vec, chunk_vecs, k=2)
    retrieved = [chunks[i] for i in idx]
    print("retrieved chunks:", idx)
    for r in retrieved:
        print("  -", r.strip())
    prompt = build_grounded_prompt(question, retrieved)
    ans = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=40,
    )
    text = ans.choices[0].message.content
    print("grounded answer:", text)
    assert "1024" in "".join(retrieved), "retrieval missed the answer chunk"
    print("OK")


if __name__ == "__main__":
    main()
