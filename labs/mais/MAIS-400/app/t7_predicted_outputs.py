#!/usr/bin/env python
"""Task 7 (SOLUTION) - Predicted outputs for low-latency edits.

Behavior (maps to MAIS-400 L2): supply a prediction of what the output will
look like so the API can skip regenerating unchanged tokens. Saves latency
and cost when editing code or making small changes to long text.

Grounded SDK calls (mistralai==2.9.4, verified live 2026-09-01):
  - client.chat.complete(
        model="codestral-latest",
        messages=[...],
        prediction={"type": "content", "content": <predicted_output>})
    -> .choices[0].message.content (edited code)
Source: context7 /mistralai/client-python docs/sdks/chat/README.md.
"""
import os
import sys

from dotenv import load_dotenv
from mistralai.client import Mistral

load_dotenv()
MODEL = "codestral-latest"

ORIGINAL_CODE = '''\
def greet(name):
    return f"Hello, {name}!"


def farewell(name):
    return f"Goodbye, {name}!"
'''


def edit_with_prediction(client, code, instruction):
    """Edit code using predicted output to reduce latency."""
    resp = client.chat.complete(
        model=MODEL,
        messages=[
            {"role": "user", "content": f"Edit this code: {instruction}\n\n```python\n{code}\n```\n\nReturn only the edited code, no explanation."},
        ],
        prediction={"type": "content", "content": code},
    )
    return resp.choices[0].message.content


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

    result = edit_with_prediction(
        client, ORIGINAL_CODE,
        "Add type hints to both functions (name: str -> str).",
    )
    print(f"edited code:\n{result}")

    assert "str" in result, "predicted edit did not add type hints"
    assert "greet" in result, "predicted edit lost the greet function"
    print("TASK7 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK7 FAIL: {e}")
        sys.exit(1)
