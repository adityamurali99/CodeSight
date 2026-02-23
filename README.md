# AI Code Reviewer

A static analysis tool for Pull Requests that maps cross-file dependencies and surfaces architectural risks before they merge.

---

## Features

**Deterministic Code Graph** — Parses Python source with the `ast` module to extract function calls, definitions, and class inheritance. The graph gives the AI precise, structured context rather than raw text.

**Impact Analysis** — Tracks incoming edges on modified nodes to identify what else in the codebase depends on changed code. Callers and subclasses are surfaced explicitly so side effects don't go unnoticed.

**Reviewer-Auditor Pipeline** — A two-agent loop where a second model audits the first's suggestions against Pylint/Radon output and a syntax sandbox. Suggestions that don't pass are revised before surfacing.

---

## Modules

| Module | Responsibility |
| :--- | :--- |
| `graph_builder.py` | Parses source files and extracts function calls and definitions via AST |
| `graph_manager.py` | Maintains the dependency graph and handles traversal queries |
| `github_client.py` | Fetches PR diffs and changed files; posts review comments back to GitHub |
| `reviewer.py` | Orchestrates the analysis pipeline and injects graph context into prompts |
| `sandbox.py` | Validates AI-generated code suggestions for syntax correctness before use |
