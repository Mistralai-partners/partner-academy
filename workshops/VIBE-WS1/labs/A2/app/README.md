# csv-report

`csv-report` is a small internal reporting utility. It exports a fixed sample
dataset from the command line. Today the `export` command supports one output
format: `csv`.

## Scenario

Product wants one new option: `--format json` on the `export` command. There is
an acceptance test already written for it (`tests/test_export.py::test_json_format`),
and it is failing because the feature does not exist yet. Your job is to make
that test pass by implementing only the new format, without changing anything
outside the export path.

## Layout

```
pyproject.toml            project metadata + pytest config (pythonpath = src)
src/csv_report/
  __init__.py
  cli.py                  argparse CLI with the `export` subcommand
  export.py               export logic: export_rows(rows, fmt)
  data.py                 the sample dataset the CLI reports on
tests/test_export.py      acceptance tests (csv passes, json fails today)
```

## Run it

Pure Python standard library plus pytest. No third-party runtime dependencies.

```bash
python -m pip install pytest        # once, if pytest is not already available
PYTHONPATH=src python -m csv_report.cli export --format csv
python -m pytest
```

`python -m pytest` reads `pythonpath = ["src"]` from `pyproject.toml`, so tests
find the package without an install. The CLI does not read that setting, so pass
`PYTHONPATH=src` when you run it directly (as shown above).

`python -m pytest` currently shows one passing test (`test_csv_format`) and one
failing test (`test_json_format`).
