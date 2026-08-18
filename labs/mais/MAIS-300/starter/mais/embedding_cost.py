"""Embedding storage trade-off: output_dimension x output_dtype -> bytes/vector.

Grounded (mistralai==1.9.11): client.embeddings.create(model="mistral-embed",
output_dimension=<int>, output_dtype=<"float"|"int8"|"uint8"|"binary"|"ubinary">).

Bytes per component:
  float            -> 4 bytes
  int8 / uint8     -> 1 byte
  binary / ubinary -> 1 BIT, packed 8 components per byte

TASK 5 (Analyze/debug): the storage estimate is wrong for two dtypes, so the
build-vs-quantize decision is being made on bad numbers. Fix them.
"""
# BUG 1 (Task 5): symptom — float storage is overstated. Compare this table to the
# per-component sizes stated in the docstring above; one entry is off by 2x.
_BYTES = {"float": 8, "int8": 1, "uint8": 1}


def bytes_per_vector(dim: int, dtype: str = "float") -> int:
    if dim <= 0:
        raise ValueError("dim must be > 0")
    if dtype in _BYTES:
        return dim * _BYTES[dtype]
    if dtype in ("binary", "ubinary"):
        # BUG 2 (Task 5): symptom — binary storage is overstated by 8x. Re-read how
        # many components pack into a single byte for a binary dtype (docstring),
        # then check what this line actually returns.
        return dim
    raise ValueError(f"unknown dtype {dtype!r}")


def storage_ratio(dim_a: int, dtype_a: str, dim_b: int, dtype_b: str) -> float:
    return bytes_per_vector(dim_a, dtype_a) / bytes_per_vector(dim_b, dtype_b)
