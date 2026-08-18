#!/usr/bin/env python
"""Task 4 (STARTER) - Reliable structured output with a strict JSON schema.

Your job: make `extract()` return output that a downstream service can parse
automatically and that always contains the required fields (sku, quantity,
unit_price) with the right types. Enforce a strict json_schema.

Grounded SDK call (mistralai==1.9.11):
  - client.chat.complete(model=..., messages=...,
        response_format={"type": "json_schema",
                         "json_schema": {"schema": <schema>, "name": ..., "strict": True}})
Source: platform-docs-public public/studio-api/conversations/structured-output.md.
"""
import json
import os
import sys

from dotenv import load_dotenv
from mistralai import Mistral

load_dotenv()
MODEL = "mistral-small-latest"

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
    # SYMPTOM: the output is prose that a downstream JSON parser cannot read. See tasks.md (Task 4).
    resp = client.chat.complete(
        model=MODEL,
        max_tokens=128,
        temperature=0,
        messages=[
            {"role": "system", "content": "Reply to the user in one short plain-English sentence."},
            {"role": "user", "content": text},
        ],
    )
    return resp.choices[0].message.content


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    raw = extract(client, ORDER)
    print(f"MODEL OUTPUT: {raw!r}")

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
