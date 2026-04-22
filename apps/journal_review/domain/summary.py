from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class JournalSummary:
    advisory_note: str
    summary_text: str
    key_patterns: list[str] = field(default_factory=list)
    recurring_risks: list[str] = field(default_factory=list)
    suggested_focus: list[str] = field(default_factory=list)
    event_count: int = 0
    window_start: str = ""
    window_end: str = ""

    def to_dict(self) -> dict:
        return {
            "advisory_note": self.advisory_note,
            "summary_text": self.summary_text,
            "key_patterns": self.key_patterns,
            "recurring_risks": self.recurring_risks,
            "suggested_focus": self.suggested_focus,
            "event_count": self.event_count,
            "window_start": self.window_start,
            "window_end": self.window_end,
        }
