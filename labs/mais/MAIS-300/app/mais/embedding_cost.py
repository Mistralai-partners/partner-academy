"""Embedding storage trade-off: output_dimension x output_dtype -> bytes/vector.

Grounded (mistralai==2.9.4): client.embeddings.create(model="mistral-embed",
output_dimension=<int>, output_dtype=<"float"|"int8"|"uint8"|"binary"|"ubinary">).
Reducing the dimension and/or quantizing the dtype trades a little accuracy for a
large storage/scan saving at corpus scale.

Bytes per component:
  float            -> 4 bytes
  int8 / uint8     -> 1 byte
  binary / ubinary -> 1 BIT, packed 8 components per byte

The Analyze skill: quantify the storage delta before choosing a posture. binary at
the same dimension is 32x smaller than float; that is the reason to consider it.
"""
_BYTES = {"float": 4, "int8": 1, "uint8": 1}


def bytes_per_vector(dim: int, dtype: str = "float") -> int:
    if dim <= 0:
        raise ValueError("dim must be > 0")
    if dtype in _BYTES:
        return dim * _BYTES[dtype]
    if dtype in ("binary", "ubinary"):
        return (dim + 7) // 8  # 1 bit per component, packed into whole bytes
    raise ValueError(f"unknown dtype {dtype!r}")


def storage_ratio(dim_a: int, dtype_a: str, dim_b: int, dtype_b: str) -> float:
    """How many times larger option A is than option B."""
    return bytes_per_vector(dim_a, dtype_a) / bytes_per_vector(dim_b, dtype_b)
