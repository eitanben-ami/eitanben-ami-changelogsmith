from changelogsmith.config import ChangelogConfig, CommitMessage, build_section_tree, load_config, render_tree
from changelogsmith.parser import iter_commits, should_include


from datetime import datetime, timezone
from typing import Sequence



def collect_entries(since: str, config_path: str) -> tuple[ChangelogConfig, list[CommitMessage]]:
    config = load_config(config_path)
    entries: list[CommitMessage] = []
    for raw in iter_commits(since=since):
        commit = CommitMessage.from_raw(
            in_title=raw.subject,
            in_body=raw.body,
            hash=raw.hash,
            author=raw.author,
            date=raw.date,
        )
        if should_include(commit, config):
            entries.append(commit)
    return config, entries


def write_changelog(
    entries: Sequence[CommitMessage],
    config: ChangelogConfig,
    version_tag: str,
    date: str,
) -> str:
    date_text = datetime.now(timezone.utc).date().isoformat()
    tag_text = version_tag or date_text

    body_parts = [
        "# Changelog",
        "",
        "All notable changes to this project will be documented in this file.",
        "",
        f"## [{tag_text}] - {date_text}",
        "",
        render_tree(build_section_tree(list(entries), config), config),
        "",
    ]
    return "\n".join(body_parts)
