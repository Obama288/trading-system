"""Permanent architecture guards replacing one-time audit greps.

Fail messages cite the governing document so the reader knows what rule broke
and where to look, not just that something matched.
"""
from __future__ import annotations

import re
from pathlib import Path

RESEARCH_ROOT = Path(__file__).parent.parent.parent / "research"


def test_session_labels_derive_from_decision_time():
    """Token 'session_label(' must only appear in simcore/timeutil.py and sessions.py.

    Constitution §3.1: session labels must derive from decision_time (bar close),
    not from bar open time. The only places that may call or define session_label()
    are the canonical implementation and the legacy-alias shim.
    """
    allowed = {
        RESEARCH_ROOT / "simcore" / "timeutil.py",
        RESEARCH_ROOT / "signal_observation" / "sessions.py",
    }
    violations: list[str] = []
    for path in sorted(RESEARCH_ROOT.rglob("*.py")):
        if "session_label(" in path.read_text(encoding="utf-8"):
            if path not in allowed:
                violations.append(str(path.relative_to(RESEARCH_ROOT.parent)))
    assert not violations, (
        "Constitution §3.1 violation — 'session_label(' found outside allowed modules.\n"
        "All session labels must derive from decision_time (bar close), not open time.\n"
        "Offending files:\n" + "\n".join(f"  {v}" for v in violations)
    )


def test_single_outcome_simulator():
    """Outside research/simcore/, no module may define resolve_outcome or *simulate*trade*.

    SIMCORE_SPEC.md §1: one simulator, one exit-logic implementation.
    Allowlist: research/signal_observation/outcomes.py is permitted ONLY while it
    imports from research.simcore.simulator (adapter pattern). If that import is
    ever removed, this test fails immediately.
    """
    pattern = re.compile(r"def\s+(resolve_outcome|\w*simulate\w*trade\w*)")
    simcore_dir = RESEARCH_ROOT / "simcore"
    outcomes_path = RESEARCH_ROOT / "signal_observation" / "outcomes.py"

    violations: list[str] = []
    for path in sorted(RESEARCH_ROOT.rglob("*.py")):
        if path.is_relative_to(simcore_dir):
            continue
        text = path.read_text(encoding="utf-8")
        if not pattern.search(text):
            continue
        if path == outcomes_path:
            assert "research.simcore.simulator" in text, (
                "outcomes.py is allowlisted but no longer imports research.simcore.simulator — "
                "SIMCORE_SPEC.md §1 contract broken (adapter must delegate to simcore)"
            )
            continue
        matches = pattern.findall(text)
        violations.append(
            f"  {path.relative_to(RESEARCH_ROOT.parent)}: defines {matches}"
        )
    assert not violations, (
        "SIMCORE_SPEC.md §1 violation — trade-exit logic found outside research/simcore/.\n"
        "All outcome resolution must go through research.simcore.simulator.\n"
        + "\n".join(violations)
    )
