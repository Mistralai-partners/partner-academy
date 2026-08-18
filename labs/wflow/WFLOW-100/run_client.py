"""Trigger the hello-world workflow from the client side.

Requires a running worker (start it with the scaffold's `make start-worker`) and
MISTRAL_API_KEY in your environment.
"""
import os

from mistralai.client import Mistral

client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])

execution = client.workflows.execute_workflow(
    workflow_identifier="hello-world",
    input={"name": "World"},
)
print(execution.model_dump_json(indent=2))
