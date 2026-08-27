# inventory-cli

A small stock-reorder helper. Given an item's current stock level and its reorder
threshold, it answers two questions:

1. Does this item need to be reordered right now?
2. If so, how many units should we order to get back to the target level?

## The scenario (VIBE-WS1 lab A3)

`inventory-cli` shipped a regression: `test_reorder_threshold` started failing
after a refactor. Nobody has found why. Your job is to get the suite green again,
correctly, not by deleting the test.

The failing test encodes a real business requirement. The fix belongs in the
source, not in the test.

## Layout

```
src/inventory_cli/
  __init__.py
  inventory.py    # Item data model
  reorder.py      # needs_reorder() and reorder_quantity() logic
  cli.py          # argparse command-line interface
tests/
  test_reorder.py # includes the failing test_reorder_threshold
```

## Run it

The test suite runs with no install step: `pyproject.toml` sets
`pythonpath = ["src"]`, so pytest finds the package on its own.

```bash
python -m pytest                     # run the whole suite
```

To exercise the CLI, put `src` on the import path (either an editable install or
`PYTHONPATH`):

```bash
python -m pip install -e ".[dev]"                 # editable install, then:
python -m inventory_cli.cli --help

# or, without installing:
PYTHONPATH=src python -m inventory_cli.cli reorder --stock 5 --threshold 5 --target 20
```
