#!/usr/bin/env python
"""Task 4 (SOLUTION) - Reliable structured output with a strict JSON schema.

Expert point (maps to FKC Q7 / B5): when a downstream service parses your
model's JSON automatically and must never break on a missing field, enforce a
strict json_schema (additionalProperties=false, all fields required, strict=true).
Free-form prose or bare JSON mode do not guarantee the shape; a strict schema does.

Grounded SDK call (mistralai==1.9.11, verified live):
  - client.chat.complete(model=..., messages=...,
        response_format={"type": "json_schema",
                         "json_schema": {"schema": <schema>, "name": ..., "strict": True}})
Source: platform-docs-public public/studio-api/conversations/structured-output.md
        + structured-output/custom.md + context7 (JSONSchema.strict).
"""
import json
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "mistral-small-latest"

# Downstream contract: these keys must always be present with these types.
SCHEMA = {
    "type": "object",
    "title": "LineItem",
    "properties": {
        "sku": {"type": "string", "title": "Sku"},
        "quantity": {"type": "integer", "title": "Quantity"},
        "unit_price": {"type": "number", "title": "UnitPrice"},
    },
    "required": ["sku", "quantity", "unit_price"],
    "additionalProperties": False,
}
REQUIRED_TYPES = {"sku": str, "quantity": int, "unit_price": (int, float)}
ORDER = "Please log 4 units of part number QX-77 at 12.50 dollars each."


def extract(client, text):
    """Strict schema guarantees a parseable object with all required keys."""
    resp = client.chat.complete(
        model=MODEL,
        max_tokens=128,
        temperature=0,
        messages=[
            {"role": "system", "content": "Extract the order line item."},
            {"role": "user", "content": text},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"schema": SCHEMA, "name": "line_item", "strict": True},
        },
    )
    return resp.choices[0].message.content


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    raw = extract(client, ORDER)
    print(f"MODEL OUTPUT: {raw!r}")

    # Acceptance contract: parses as JSON, every required key present, right types.
    obj = json.loads(raw)
    for key, typ in REQUIRED_TYPES.items():
        assert key in obj, f"missing required field: {key}"
        assert isinstance(obj[key], typ), f"field {key} has wrong type: {type(obj[key])}"
    print(f"PARSED OK: {obj}")
    print("TASK4 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK4 FAIL: {e}")
        sys.exit(1)
