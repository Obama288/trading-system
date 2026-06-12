from __future__ import annotations

from decimal import Decimal

from research.simcore.models import TargetSim

# Standard cost scenarios (per side, taker + slippage, in bps of entry notional).
# Moderate is the gate scenario per constitution §3.6.
SCENARIOS: dict[str, Decimal] = {
    "optimistic": Decimal("5"),
    "moderate": Decimal("8"),
    "conservative": Decimal("15"),
}


def cost_in_r(*, entry_price: Decimal, initial_r: Decimal, bps_per_side: Decimal) -> Decimal:
    """Convert per-side bps cost to R units for a single trade (constitution §3.6).

    Charges entry + exit (2 sides). Tight stops produce large cost_r by design —
    this replaces the old flat-R scenarios that understated costs for tight setups.

    All arguments must be Decimal; floats are rejected with TypeError.
    """
    for name, val in (("entry_price", entry_price), ("initial_r", initial_r), ("bps_per_side", bps_per_side)):
        if not isinstance(val, Decimal):
            raise TypeError(f"{name} must be Decimal, got {type(val).__name__}")
    return (Decimal(2) * bps_per_side / Decimal(10000)) * entry_price / initial_r


def final_r_net(target_sim: TargetSim, cost_r: Decimal) -> Decimal:
    """Post-cost R for a resolved target (constitution §3.6).

    Net values are computed by reporting code, not stored in TargetSim
    (one gross truth, N cost views).
    """
    return target_sim.final_r_gross - cost_r
