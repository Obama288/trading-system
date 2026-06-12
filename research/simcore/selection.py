from __future__ import annotations

from decimal import Decimal
from typing import Sequence

from research.simcore.models import TradeSim


def select_non_overlapping(sims: Sequence[TradeSim], *, target_r: Decimal) -> list[TradeSim]:
    """Return the non-overlapping subset for headline metrics (constitution §3.8).

    Per symbol, sorted by entry_index: keep a sim only if its entry_index is
    strictly greater than the exit_index (for target_r) of the last kept sim
    for that symbol.  The full sequence remains available as diagnostics.
    """
    by_symbol: dict[str, list[TradeSim]] = {}
    for sim in sims:
        by_symbol.setdefault(sim.spec.symbol, []).append(sim)

    result: list[TradeSim] = []
    for symbol_sims in by_symbol.values():
        sorted_sims = sorted(symbol_sims, key=lambda s: s.entry_index)
        last_exit: int | None = None
        for sim in sorted_sims:
            if target_r not in sim.targets:
                continue
            if last_exit is None or sim.entry_index > last_exit:
                result.append(sim)
                last_exit = sim.targets[target_r].exit_index

    return result
