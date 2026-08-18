#!/usr/bin/env python
"""Task 1 (STARTER) - Batch cost optimization + custom_id reconciliation.

Your job: make `reconcile()` account for EVERY custom_id across BOTH the output
file and the error file, and surface any request that did not return 200 - even
though the job's top-level status is SUCCESS.

Grounded SDK calls (mistralai==1.9.11):
  - client.files.upload(file=File(...), purpose="batch")
  - client.batch.jobs.create(input_files=[...], model=..., endpoint="/v1/chat/completions")
  - client.batch.jobs.get(job_id=...) -> .status/.output_file/.error_file/...
  - client.files.download(file_id=...).read()
Source: platform-docs-public public/studio-api/batch-processing.md.
"""
import io
import json
import os
import sys
import time

from dotenv import load_dotenv
from mistralai import Mistral
from mistralai.models import File

load_dotenv()
MODEL = "ministral-3b-latest"


def build_input_rows():
    return [
        {"custom_id": "inv-0", "body": {"max_tokens": 8, "messages": [{"role": "user", "content": "Say the word alpha."}]}},
        {"custom_id": "inv-1", "body": {"max_tokens": 8, "messages": [{"role": "user", "content": "Say the word bravo."}]}},
        {"custom_id": "inv-2", "body": {"max_tokens": 8, "messages": [{"role": "user", "content": "Say the word charlie."}]}},
        {"custom_id": "inv-3", "body": {"max_tokens": 8, "messages": [{"role": "user", "content": "Hi"}], "tool_choice": "required"}},
    ]


def submit(client, rows):
    buf = io.BytesIO("\n".join(json.dumps(r) for r in rows).encode())
    up = client.files.upload(file=File(file_name="batch_input.jsonl", content=buf.getvalue()), purpose="batch")
    job = client.batch.jobs.create(input_files=[up.id], model=MODEL, endpoint="/v1/chat/completions")
    t0 = time.time()
    while job.status in ("QUEUED", "RUNNING"):
        time.sleep(5)
        job = client.batch.jobs.get(job_id=job.id)
        if time.time() - t0 > 280:
            break
    return job


def parse_jsonl(client, file_id):
    if not file_id:
        return []
    data = client.files.download(file_id=file_id).read().decode()
    return [json.loads(ln) for ln in data.strip().splitlines() if ln.strip()]


def reconcile(client, job, input_ids):
    # BUG: this trusts the job-level SUCCESS status and only reads the output
    # file. It never opens the error file, so a request that failed at inference
    # is silently dropped and reported as if everything succeeded.
    # TODO: reconcile every custom_id across BOTH output_file AND error_file,
    #       and check each output row's response.status_code.
    succeeded = set()
    for row in parse_jsonl(client, job.output_file):
        succeeded.add(row.get("custom_id"))
    return {
        "complete": job.status == "SUCCESS",
        "total": len(input_ids),
        "succeeded": len(succeeded),
        "failed": [],
        "missing": [],
    }


def main():
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    rows = build_input_rows()
    input_ids = [r["custom_id"] for r in rows]
    job = submit(client, rows)
    print(f"job status={job.status} total={job.total_requests} "
          f"succeeded={job.succeeded_requests} failed={job.failed_requests}")

    r = reconcile(client, job, input_ids)
    print(f"RECONCILE complete={r['complete']} total={r['total']} "
          f"succeeded={r['succeeded']} failed={len(r['failed'])} missing={len(r['missing'])}")
    print(f"  failed_ids={r['failed']} missing_ids={r['missing']}")

    assert r["complete"], f"unaccounted custom_ids: {r['missing']}"
    assert len(r["failed"]) >= 1, "reconciliation failed to surface the errored request"
    assert r["succeeded"] < r["total"], "expected at least one failed request"
    print("TASK1 PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f"TASK1 FAIL: {e}")
        sys.exit(1)
