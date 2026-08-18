"""Trigger the hello-world workflow with the Python SDK.

Requires a running worker (see README) and MISTRAL_API_KEY in your environment.
"""
import mistralai.workflows as workflows

result = workflows.execute_workflow(
    workflow_identifier="hello-world",
    input={"name": "World"},
)
print("Result:", result)
