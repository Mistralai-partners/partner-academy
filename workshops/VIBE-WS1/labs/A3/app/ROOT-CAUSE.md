# Incident report: `test_reorder_threshold` regression

**Component:** `inventory-cli` / `src/inventory_cli/reorder.py`
**Symptom:** `test_reorder_threshold` fails; the rest of the suite passes.
**Severity:** Medium. Items sitting exactly at their reorder point were never
flagged for reorder, so they could silently run down to zero.

## What the test told us

```
assert needs_reorder(5, 5) is True
E       assert False is True
E        +  where False = needs_reorder(5, 5)
```

The boundary case (stock level equal to the threshold) returned `False` when
the business rule requires `True`. The other cases (clearly below, clearly
above) still behaved correctly, which is why only one test went red.

## Root cause

The business rule is: **the threshold is the reorder trigger point.** An item
must be reordered once its stock *reaches* the threshold or drops below it. That
makes the threshold comparison inclusive.

During the refactor, the comparison in `needs_reorder` was written as a strict
"below" check instead of a "reached or below" check. As a result the exact
boundary (stock == threshold) fell on the wrong side of the comparison: the
function reported "no reorder needed" for an item that had, in fact, hit its
trigger point. This is a classic off-by-one at the boundary. The two other tests
never exercised the boundary, so they masked the defect.

## The fix

The change lands in the **source**, in `needs_reorder`:

```python
# before (starter):  strict comparison misses the boundary
return stock_level < threshold

# after (solution):  inclusive comparison, threshold is the trigger point
return stock_level <= threshold
```

`reorder_quantity` needed no change: it already delegates the decision to
`needs_reorder`, so correcting the boundary there fixes the quantity path too.

## Why the fix does NOT belong in the test

`test_reorder_threshold` encodes the requirement itself: "an item at its
threshold must be reordered." Weakening that assertion, deleting the test, or
wrapping the call in a `try/except` would make the suite green while leaving the
real defect in place. The test is the specification. The source has to satisfy
it.

## Verification

- `python -m pytest tests/test_reorder.py::test_reorder_threshold` -> green
- `python -m pytest` -> full suite passes
- `git diff --name-only` -> only `src/inventory_cli/reorder.py` changed; no files
  under `tests/` were touched
