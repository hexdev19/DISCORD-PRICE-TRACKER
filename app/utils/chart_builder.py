from __future__ import annotations

from decimal import Decimal

_BLOCKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[Decimal | float | int | None]) -> str:
    real = [float(v) for v in values if v is not None]
    if not real:
        return "—"
    lo, hi = min(real), max(real)
    if hi == lo:
        return _BLOCKS[len(_BLOCKS) // 2] * len(values)
    out: list[str] = []
    for v in values:
        if v is None:
            out.append(" ")
            continue
        idx = int((float(v) - lo) / (hi - lo) * (len(_BLOCKS) - 1))
        out.append(_BLOCKS[idx])
    return "".join(out)
