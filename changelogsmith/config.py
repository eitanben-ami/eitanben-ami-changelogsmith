from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


DEFAULT_CONFIG_FILE = "changelogsmith.toml"
DEFAULT_SECTION_MAP: dict[str, str] = {
    "feat": "Features",
    "fix": "Bug Fixes",
    "docs": "Documentation",
    "refactor": "Refactoring",
    "perf": "Performance",
    "test": "Tests",
    "build": "Build",
    "ci": "CI",
    "chore": "Chores",
    "revert": "Reverts",
}
CONVENTIONAL_COMMIT_RE = re.compile(
    r"^(?P<type>[a-z]+)(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<description>.+)$"
)


@dataclass(frozen=True)
class CommitMessage:
    hash: str
    author: str
    date: str
    subject: str
    body: str
    type: str = "other"
    scope: str | None = None
    breaking: bool = False
    description: str = ""
    level: int = 0
    parent_text: str | None = None

    @classmethod
    def from_raw(cls, in_title: str, in_body: str, *, hash: str, author: str, date: str) -> CommitMessage:
        subject = (in_title or "").strip()
        body = (in_body or "").strip()
        match = CONVENTIONAL_COMMIT_RE.match(subject)
        type_ = "other"
        scope = None
        breaking = False
        description = subject

        if match:
            type_ = match.group("type")
            scope = match.group("scope")
            breaking = bool(match.group("breaking"))
            description = match.group("description").strip()

            if type_ == "revert":
                revert_match = re.search(r"This reverts commit ([0-9a-f]{7,40})", body, re.IGNORECASE)
                if revert_match:
                    return cls(
                        hash=hash,
                        author=author,
                        date=date,
                        subject=subject,
                        body=body,
                        type=type_,
                        scope=scope,
                        breaking=breaking,
                        description=description,
                        level=0,
                        parent_text=revert_match.group(1),
                    )
        return cls(
            hash=hash,
            author=author,
            date=date,
            subject=subject,
            body=body,
            type=type_,
            scope=scope,
            breaking=breaking,
            description=description,
            level=0,
        )

    def should_include(self, config: ChangelogConfig) -> bool:
        if config.types and self.type not in config.types:
            return False
        if self.type in config.exclude_types:
            return False
        return True


class Entry:
    def __init__(self, section: str, message: CommitMessage) -> None:
        self.section = section
        self.message = message
        self.children: list[Entry] = []


@dataclass(frozen=True)
class ChangelogConfig:
    sections: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_SECTION_MAP))
    types: list[str] = field(default_factory=list)
    exclude_types: list[str] = field(default_factory=list)
    include_refs: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> ChangelogConfig:
        sections = dict(DEFAULT_SECTION_MAP)
        sections.update(data.get("sections", {}))
        return cls(
            sections=sections,
            types=data.get("types", []),
            exclude_types=data.get("exclude_types", []),
            include_refs=data.get("include_refs", True),
        )

    def section_for(self, commit: CommitMessage) -> str | None:
        if commit.type in self.exclude_types:
            return None
        if self.types and commit.type not in self.types:
            return None
        return self.sections.get(commit.type)


def find_config(lookup: str | None) -> tuple[Path, dict]:
    path = Path(lookup) if lookup else Path.cwd() / DEFAULT_CONFIG_FILE
    root = path if path.is_file() else _search_up(path)

    data: dict = {}
    if root and root.suffix == ".toml":
        try:
            import tomllib
        except ModuleNotFoundError:  # pragma: no cover
            import tomli as tomllib
        data = tomllib.loads(root.read_text(encoding="utf-8"))
    elif root and root.suffix == ".json":
        import json

        data = json.loads(root.read_text(encoding="utf-8"))
    return (root or Path.cwd()), data


def _search_up(start: Path) -> Path | None:
    candidates = [start if start.is_file() else start.parent, *start.parents]
    for directory in candidates:
        candidate = directory / DEFAULT_CONFIG_FILE
        if candidate.exists():
            return candidate
    return None


def iter_commits(since: str) -> Iterator[str]:
    delimiter = "\0"
    format_line = f"%h{delimiter}%an{delimiter}%ad{delimiter}%s{delimiter}%b{delimiter}"
    command = ["git", "log", f"{since}..", f"--format={format_line}"]
    try:
        stream = _run_command(command)
    except RuntimeError as exc:
        raise RuntimeError(f"Failed to run git log: {exc}") from exc

    for chunk in stream.split(delimiter):
        lines = chunk.splitlines()
        if len(lines) < 3:
            continue
        hash_, lines = lines[0], lines[1:]
        author, date = lines[0], lines[1]
        subject = lines[2] if len(lines) > 2 else ""
        body = "\n".join(lines[3:]) if len(lines) > 3 else ""
        yield delimiter.join([hash_, author, date, subject, body]) + delimiter


def _run_command(command: list[str]) -> str:
    from subprocess import run, PIPE

    result = run(command, check=True, stdout=PIPE, stderr=PIPE, text=True)
    return result.stdout


def build_section_tree(messages: list[CommitMessage], config: ChangelogConfig) -> list[Entry]:
    roots: list[Entry] = []
    for message in messages:
        section = config.section_for(message)
        if section is None:
            continue
        entry = Entry(section, message)
        roots.append(entry)
    return roots


def should_include(commit: CommitMessage, config: ChangelogConfig) -> bool:
    return commit.should_include(config)


def load_config(path: str) -> ChangelogConfig:
    _, data = find_config(path)
    return ChangelogConfig.from_dict(data)


def format_entry(entry: Entry, config: ChangelogConfig, indent: int = 0) -> list[str]:
    lines: list[str] = []
    prefix = "  " * indent
    ref = f" ({entry.message.hash})" if config.include_refs else ""
    lines.append(f"{prefix}- {entry.message.description}{ref}")
    return lines


def render_tree(entries: list[Entry], config: ChangelogConfig) -> str:
    output_parts: list[str] = []
    seen: set[str] = set()
    section_order = {name: i for i, name in enumerate(config.sections.values())}
    ordered_roots = sorted(
        entries,
        key=lambda entry: section_order.get(entry.section, len(section_order)),
    )

    for entry in ordered_roots:
        if entry.section not in seen:
            output_parts.append(f"## {entry.section}\n")
            seen.add(entry.section)
        output_parts.extend(format_entry(entry, config, indent=1))
    return "\n".join(output_parts)
