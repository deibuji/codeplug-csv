# repeater-csv

## Commands

- `task test` — run the test suite
- `task run` — generate CSV files in `output/`
- `task run -- --locator IO91` — pass extra CLI args
- `task` — run tests then generate output (default)

## Setup

The venv must exist before running tasks:

```sh
uv venv && uv pip install -e ".[dev]"
```
