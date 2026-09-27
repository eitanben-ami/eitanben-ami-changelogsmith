from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    base = "HEAD~1"
    root = Path(__file__).resolve().parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from changelogsmith.writer import collect_entries, write_changelog

    config_path = str(root / "changelogsmith.toml")
    output = root / "CHANGELOG.md"

    config, entries = collect_entries(base, config_path)
    rendered = write_changelog(entries, config, "", "")

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")

    print(rendered)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
