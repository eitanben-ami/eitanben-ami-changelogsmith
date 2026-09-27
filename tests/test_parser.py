
from changelogsmith.parser import (
    DEFAULT_SECTION_MAP,
    CONVENTIONAL_COMMIT_RE,
    ChangelogConfig,
    CommitMessage,
    Entry,
    build_section_tree,
    format_entry,
    render_tree,
    should_include,
)


def test_default_section_map_contains_common_conventions() -> None:
    assert "feat" in DEFAULT_SECTION_MAP
    assert "fix" in DEFAULT_SECTION_MAP
    assert DEFAULT_SECTION_MAP["feat"] == "Features"


def test_commit_message_parses_conventional_commit() -> None:
    match = CONVENTIONAL_COMMIT_RE.match("feat(cli): add generate command")
    assert match is not None
    assert match.group("type") == "feat"
    assert match.group("scope") == "cli"
    assert match.group("description") == "add generate command"


def test_commit_message_identifies_breaking_change() -> None:
    match = CONVENTIONAL_COMMIT_RE.match("feat!: remove legacy endpoint")
    assert match is not None
    assert bool(match.group("breaking")) is True


def test_commit_message_falls_back_to_other() -> None:
    match = CONVENTIONAL_COMMIT_RE.match("Person changed a line")
    assert match is None


def test_should_include_respects_filter() -> None:
    config = ChangelogConfig(types=["feat", "fix"])
    commit = CommitMessage(
        hash="abc123",
        author="Person",
        date="2026-07-16",
        subject="chore: update README",
        body="",
        type="chore",
    )
    assert should_include(commit, config) is False


def test_should_include_excludes_type() -> None:
    config = ChangelogConfig(exclude_types=["chore"])
    commit = CommitMessage(
        hash="abc123",
        author="Person",
        date="2026-07-16",
        subject="chore: update README",
        body="",
        type="chore",
    )
    assert should_include(commit, config) is False


def test_build_section_tree_orders_by_config() -> None:
    config = ChangelogConfig(
        sections={"feat": "Features", "fix": "Bug Fixes", "chore": "Chores"},
    )
    commits = [
        CommitMessage(
            hash="1",
            author="Person",
            date="2026-07-16",
            subject="chore: lint",
            body="",
            type="chore",
            description="lint",
        ),
        CommitMessage(
            hash="2",
            author="Person",
            date="2026-07-16",
            subject="feat: add command",
            body="",
            type="feat",
            description="add command",
        ),
        CommitMessage(
            hash="3",
            author="Person",
            date="2026-07-16",
            subject="fix: edge case",
            body="",
            type="fix",
            description="edge case",
        ),
    ]
    tree = build_section_tree(commits, config)
    rendered = render_tree(tree, config)
    assert rendered.index("Features") < rendered.index("Bug Fixes")
    assert rendered.index("Bug Fixes") < rendered.index("Chores")


def test_format_entry_includes_refs_by_default() -> None:
    commit = CommitMessage(
        hash="deadbeef",
        author="Person",
        date="2026-07-16",
        subject="feat: demo",
        body="",
        type="feat",
        description="demo",
    )
    entry = Entry("Features", commit)
    lines = format_entry(entry, ChangelogConfig(), indent=1)
    assert lines == ["  - demo (deadbeef)"]


def test_format_entry_skips_refs_when_configured() -> None:
    commit = CommitMessage(
        hash="deadbeef",
        author="Person",
        date="2026-07-16",
        subject="feat: demo",
        body="",
        type="feat",
        description="demo",
    )
    entry = Entry("Features", commit)
    config = ChangelogConfig(include_refs=False)
    lines = format_entry(entry, config, indent=0)
    assert lines == ["- demo"]
