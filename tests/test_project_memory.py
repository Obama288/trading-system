from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT = ROOT / "docs" / "CURRENT_STATE.md"
RESEARCH = ROOT / "research" / "signal_observation" / "RESEARCH_STATE.md"
MEMORY = ROOT / "docs" / "MEMORY_POLICY.md"
RUNBOOK = ROOT / "docs" / "OPERATOR_RUNBOOK.md"
WORKFLOW = ROOT / ".github" / "workflows" / "research-ci.yml"
PORTFOLIO = ROOT / "research" / "signal_observation" / "HYPOTHESIS_PORTFOLIO_2026_07.md"

CANONICAL_DOCS = (
    ROOT / "README.md",
    ROOT / "docs" / "README.md",
    ROOT / "docs" / "BOUNDARIES.md",
    ROOT / "docs" / "CURRENT_STATE.md",
    ROOT / "docs" / "HOW_WE_WORK.md",
    ROOT / "docs" / "MEMORY_POLICY.md",
    ROOT / "research" / "signal_observation" / "RESEARCH_STATE.md",
    PORTFOLIO,
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _git_lines(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [line for line in result.stdout.splitlines() if line]


def test_canonical_memory_files_exist_and_declare_status():
    for path in CANONICAL_DOCS:
        assert path.is_file(), f"missing canonical memory file: {path.relative_to(ROOT)}"
        first_ten_lines = _read(path).splitlines()[:10]
        assert any(line.startswith("Status: ") for line in first_ten_lines), (
            f"missing lifecycle status near top of {path.relative_to(ROOT)}"
        )


def test_compact_state_files_stay_compact():
    assert len(_read(CURRENT).splitlines()) <= 150
    assert len(_read(RESEARCH).splitlines()) <= 180
    assert len(_read(ROOT / "docs" / "HOW_WE_WORK.md").splitlines()) <= 220


def test_economic_objective_and_owner_constraints_are_aligned():
    current = _read(CURRENT)
    research = _read(RESEARCH)
    memory = _read(MEMORY)

    for text in (current, research, memory):
        normalized = re.sub(r"\s+", " ", text)
        assert "net trading profit" in normalized

    assert "No new project spending" in current
    assert "No new project spending" in memory
    assert "No paid API key" in research
    assert "Live trading: NO-GO" in current


def test_research_gate_is_consistent_across_state_files():
    current = _read(CURRENT)
    research = _read(RESEARCH)

    assert "Research lane: no active family." in current
    assert "Active family: none." in research
    assert "Setup I / Price-Flow Divergence Reversion" in current
    assert "Setup I / Price-Flow Divergence Reversion" in research


def test_hypothesis_shortlist_and_testnet_evidence_boundary_are_consistent():
    current = _read(CURRENT)
    research = _read(RESEARCH)
    portfolio = _read(PORTFOLIO)

    for text in (current, research, portfolio):
        normalized = re.sub(r"\s+", " ", text)
        assert "Cross-Venue Perpetual Funding Dispersion" in normalized
        assert "Beta-Neutral Cross-Sectional Residual Reversion" in normalized

    assert "Testnet/demo results are implementation evidence, not evidence of edge." in portfolio
    assert "Active family: none." in research


def test_agent_startup_files_are_identical_and_snapshot_free():
    agents = _read(ROOT / "AGENTS.md")
    claude = _read(ROOT / "CLAUDE.md")

    assert agents == claude
    assert "contains no dated project snapshot" in agents
    assert "9 services healthy" not in agents
    assert "Alembic head:" not in agents
    assert "passed, " not in agents


def test_documented_alembic_head_matches_migration_graph():
    migration_files = sorted((ROOT / "infra" / "migrations" / "versions").glob("[0-9]*.py"))
    revisions: set[str] = set()
    down_revisions: set[str] = set()

    for path in migration_files:
        text = _read(path)
        revision = re.search(r'^revision\s*=\s*"([^"]+)"', text, re.MULTILINE)
        down_revision = re.search(r'^down_revision\s*=\s*"([^"]+)"', text, re.MULTILINE)
        assert revision, f"missing revision in {path.name}"
        revisions.add(revision.group(1))
        if down_revision:
            down_revisions.add(down_revision.group(1))

    heads = revisions - down_revisions
    assert heads == {"0009_create_paper_account_authority"}

    for path in (CURRENT, RUNBOOK):
        text = _read(path)
        assert "0009_create_paper_account_authority" in text
        assert "0008_unique_tc_signal_id" not in text


def test_root_readme_matches_packaging_metadata():
    pyproject = _read(ROOT / "pyproject.toml")
    assert 'readme = "README.md"' in pyproject
    assert (ROOT / "README.md").is_file()


def test_uppercase_archive_tree_is_removed_or_pending_deletion():
    uppercase_tracked = {
        path for path in _git_lines("ls-files", "docs/ARCHIVE") if path.startswith("docs/ARCHIVE/")
    }
    pending_deletions = set(_git_lines("diff", "--name-only", "--diff-filter=D"))
    assert uppercase_tracked <= pending_deletions


def test_local_only_test_and_agent_settings_are_not_tracked():
    tracked = set(_git_lines("ls-files"))
    gitignore = _read(ROOT / ".gitignore")

    assert ".claude/settings.local.json" in gitignore
    assert ".claude/settings.local.json" not in tracked
    assert "conftest.py" not in tracked
    assert "editor or agent local settings" in _read(MEMORY)


def test_ci_installs_project_and_runs_full_suite():
    workflow = _read(WORKFLOW)

    assert 'pip install -e ".[dev,research]"' in workflow
    assert "python -m pytest tests/test_project_memory.py -q" in workflow
    assert "python -m pytest -q" in workflow


def test_entry_point_markdown_links_resolve():
    for path in (ROOT / "README.md", ROOT / "docs" / "README.md"):
        for href in re.findall(r"\[[^\]]+\]\(([^)]+)\)", _read(path)):
            if href.startswith(("http://", "https://", "#")):
                continue
            target = (path.parent / href).resolve()
            assert target.exists(), f"broken link in {path.relative_to(ROOT)}: {href}"
