# TICKET PAY-482: Add idempotency keys to the refund endpoint

**Priority:** High
**Reporter:** Payments platform lead

## Background

You have just been added to `payments-service`, a repository you have never
seen. A support incident showed that a client retried a refund request after a
network timeout and the customer was refunded twice. Today the refund path has
no idempotency key, so a retried request is processed as a brand new refund. The
test `test_duplicate_request_creates_two_refunds_today` documents this behavior.

## Ask

Add support for an idempotency key on the refund endpoint so that a retried
request with the same key returns the original refund instead of creating a
second one.

## What leadership wants FIRST

Before touching any file, produce a written change-plan they can review. The
plan must name the exact files and functions you would change, the store lookup
you would add, your assumptions, and the acceptance test you would add. Do not
edit code yet. The plan is the deliverable for this ticket.

## Acceptance for the eventual change (for context only, do not build it now)

- A refund request may carry an `idempotency_key`.
- The first request with a given key creates and stores the refund.
- A repeated request with the same key returns the same refund, and no second
  refund is recorded.
