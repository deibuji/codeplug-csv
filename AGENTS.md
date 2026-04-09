# AGENTS.md

This document outlines the rules, conventions, and commands for any agent operating within the `codeplug-csv` repository.

## 1. Workflow Commands

Agents must use the following commands defined in `Taskfile.yml` and the CLI for all major operations:

- **`task test`**: Run the entire test suite to ensure full code coverage.
- **`task run`**: Generate all required CSV output files in the `output/` directory.
- **`task`**: Run tests first, then generate output (default behavior).
- **`task run -- --locator <locator>`**: Pass extra CLI arguments to the task runner.
- **`codeplug-csv -o output/<file>`**: Generate specific data files, e.g., `codeplug-csv -o output/Channel.CSV`.

For specific, localized tasks, agents should utilize the `read`, `grep`, and `edit` tools when interacting with files, and the `bash` tool for system operations. When performing complex, multi-step tasks, use the `task` tool or prompt for specific steps.

## 2. Code Style Guidelines

The codebase adheres to **Python** conventions (PEP 8). Agents must strictly follow these guidelines:

### Formatting and Naming
- **PEP 8 Compliance**: All code must adhere to PEP 8 standards regarding line length, spacing, and naming conventions.
- **Naming**: Variables, functions, and module names must be descriptive and follow snake_case (e.g., `calculate_total` instead of `calculateTotal`).
- **Module Structure**: Keep related logic grouped logically within modules (e.g., `src/codeplug_csv/extract.py`, `src/codeplug_csv/transform.py`).

### Imports and Dependencies
- **Absolute Imports**: Use absolute imports for all module references (e.g., `from src.codeplug_csv import extract`).
- **Minimal Imports**: Only import necessary modules to maintain readability and efficiency.
- **Dependencies**: Only use libraries explicitly listed in `pyproject.toml` or the standard Python library unless explicitly added by the task.

### Error Handling
- **Exceptions**: Use Python's standard exception hierarchy appropriately for error signaling.
- **Logging**: Use the `logging` module for recording important operational steps and errors, especially during data extraction and transformation. Do not rely solely on printing to stdout for error reporting.
- **File Operations**: Wrap file reading/writing operations with robust `try...except` blocks to handle `FileNotFoundError` or permission errors.

### Type Hinting (If Applicable)
- **Type Hints**: For complex functions or module interfaces where type safety is beneficial, use Python type hints to specify expected input and output types.

## 3. Agent Protocol
- **Verification First**: Before writing code, agents must analyze existing files, run tests (`task test`), and use the `read` tool to understand the existing state.
- **State Management**: For complex tasks, use the `todowrite` tool to structure the plan, ensuring sequential, traceable steps.
- **Commit Strategy**: Changes should be small, atomic, and explicitly requested for commit, following the standard git protocol carefully.
- **Data Integrity**: Agents must confirm data lineage and structure (e.g., CSV headers and data types) when generating output files. All generated CSVs must strictly adhere to the structure expected by the Anytone CPS software.
