# Reference change-plan: idempotency keys for the refund endpoint (PAY-482)

This is a plan only. No code is edited here. It names the exact files,
functions, and the test to add. The learner's own plan is checked against this
set of targets, not against wording.

## Goal

A retried refund request that carries the same `idempotency_key` must return the
original refund instead of creating a second one.

## Assumptions

- The idempotency key is client supplied and scoped per payment. The pair
  (payment_id, idempotency_key) identifies a unique refund attempt.
- Keys live only in memory, alongside the existing store, since this service has
  no real database. Persistence is out of scope for this ticket.
- Only the refund path needs a key today. Other endpoints are unchanged.
- A request without a key keeps today's behavior (no idempotency guarantee), so
  the change is backward compatible.

## Target files and functions to change

1. `src/payments_service/store.py`: `PaymentStore`
   - Add an in-memory index mapping an idempotency key to a stored refund id,
     for example `self._refunds_by_key: dict[str, str] = {}`.
   - Add `get_refund_by_idempotency_key(key)` that returns the stored `Refund`
     or `None`.
   - Update `add_refund` (or add `add_refund_with_key`) so a refund recorded
     with a key is indexed by that key.

2. `src/payments_service/refunds.py`: `process_refund`
   - Extend the signature to accept an optional `idempotency_key` argument.
   - On entry, if a key is present and `get_refund_by_idempotency_key` returns a
     refund, return that existing refund without recording a new one. Otherwise
     record the refund and index it by key. Keep the existing validation rules
     (unknown payment, non-positive amount, over-refund) unchanged.

3. `src/payments_service/api.py`: `handle_refund`
   - Read `idempotency_key` from `request["body"]` (optional) and pass it
     through to `process_refund`.
   - Keep the existing 400 validation for missing `payment_id` / `amount_cents`.
     A repeated request with a known key should return the same refund body and
     a success status.

## Test to add

Add to `tests/test_refunds.py` a new test named
`test_duplicate_refund_is_idempotent`:

- Send a refund request with an `idempotency_key`, then send the same request
  with the same key.
- Assert both responses return the same `refund_id`.
- Assert `store.total_refunded_cents(...)` equals a single refund amount, proving
  no second refund was recorded.

Keep the existing `test_duplicate_request_creates_two_refunds_today` as the
documented behavior for requests that send no key.

## Out of scope

- Persistent storage of keys, key expiry, and cross-payment key uniqueness.
- Any change to the payment capture path or the router `route`.

## Verification for the eventual change (not this lab)

- New and existing tests in `tests/test_refunds.py` pass under `python -m pytest`.
