# changelogsmith

[![Python](https://img.shields.io/badge/python-%3E%3D3.10-blue)](https://github.com/eitanben-ami/changelogsmith)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automatically generate `CHANGELOG.md` from git history using conventional commits. Extract the signal without writer's block.

Source: https://github.com/eitanben-ami/changelogsmith

## About

`changelogsmith` ships a small CLI that reads recent commit messages, parses them, and produces a scoped changelog section. By combining structured git metadata with human-friendly formatting, it isolates the what-changed view during local development.

## Features

- Conventional commit-aware parsing
- Configurable section mapping via `changelogsmith.toml`
- Optional commit hash refs
- Fully typed implementation
- Scoped commit message extraction, not everything since inception

## Installation

### From source

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
```

### Via pip after publish

```bash
pip install changelogsmith
```

## Usage

```bash
changelogsmith generate
```

## Configuration

Optional `changelogsmith.toml` keys:
- `sections`
- `types`
- `exclude_types`
- `include_refs`

## Project structure

```text
  .github/workflows/tests.yml
  .gitignore
  LICENSE
  README.md
  changelogsmith.toml
  changelogsmith/__main__.py
  changelogsmith/cli.py
  changelogsmith/config.py
  changelogsmith/parser.py
  changelogsmith/writer.py
  docs/TODO.md
  pyproject.toml
  tests/test_parser.py
```


## Topics

python, changelog, conventional-commits, cli, developer-tools, automation, git
