"""Task 5 live proof: embedding storage trade-off (output_dimension + output_dtype).

Run: uv run --no-project --with 'mistralai==2.9.4' --with python-dotenv \
       python live_embedding_cost.py
Grounded: client.embeddings.create(model="codestral-embed", output_dimension=...,
output_dtype=...) returns shorter / quantized vectors. (Note: mistral-embed does
NOT accept output_dimension; codestral-embed does — this is exactly the text-vs-code
embedding trade-off the course teaches.) We measure the real returned length and
compare it to bytes_per_vector's estimate.
"""
import os

from dotenv import load_dotenv
from mistralai.client import Mistral

from mais.embedding_cost import bytes_per_vector, storage_ratio

load_dotenv("/Users/victor.rojo/source/course-automation/.env")

TEXT = "Advanced RAG at scale trades a little accuracy for a lot of storage."


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    full = client.embeddings.create(model="codestral-embed", inputs=[TEXT])
    full_dim = len(full.data[0].embedding)
    print(f"full float vector: dim={full_dim} -> {bytes_per_vector(full_dim, 'float')} bytes")

    reduced = client.embeddings.create(
        model="codestral-embed", inputs=[TEXT], output_dimension=256, output_dtype="int8"
    )
    red_dim = len(reduced.data[0].embedding)
    print(f"reduced int8 vector: dim={red_dim} -> {bytes_per_vector(red_dim, 'int8')} bytes")

    ratio = storage_ratio(full_dim, "float", red_dim, "int8")
    print(f"full-float is {ratio:.0f}x larger than reduced-int8")
    print(f"binary at {full_dim} dims would be {bytes_per_vector(full_dim, 'binary')} bytes "
          f"({storage_ratio(full_dim, 'float', full_dim, 'binary'):.0f}x smaller than float)")
    assert red_dim == 256, "output_dimension did not take effect"
    print("OK")


if __name__ == "__main__":
    main()
