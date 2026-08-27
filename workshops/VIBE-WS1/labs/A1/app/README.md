# payments-service

A tiny payments API used for training. It has no web framework and no external
dependencies. A request is a plain Python dict, and the "database" is a set of
in-memory dictionaries that reset when the process exits. This keeps the whole
service readable in a few minutes.

## What it does

- Stores captured payments.
- Accepts refund requests against a captured payment.
- Enforces three rules on a refund: the payment must exist, the amount must be
  positive, and the total refunded amount must not exceed the captured amount.

## Layout

```
src/payments_service/
  __init__.py   public exports
  api.py        request handlers and a tiny router (handle_refund, route)
  refunds.py    refund domain logic (process_refund, RefundError)
  store.py      in-memory Payment and Refund store (PaymentStore)
tests/
  test_refunds.py   passing tests for current behavior
```

## The request shape

There is no HTTP server. A request is a dict:

```python
{"method": "POST", "path": "/refunds", "body": {"payment_id": "pay_123", "amount_cents": 1500}}
```

`route(store, request)` dispatches to `handle_refund`, which returns a response
dict with a `status` code and a `body`.

## Run the tests

```bash
python -m pytest
```

All tests pass as shipped. See `TICKET.md` for the change you are being asked to
plan.
