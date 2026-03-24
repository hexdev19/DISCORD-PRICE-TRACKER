from __future__ import annotations

from decimal import Decimal


_SPARK_BARS = "▁▂▃▄▅▆▇█"


def build_sparkline(prices: list[Decimal]) -> str:
	if not prices:
		return ""
	if len(prices) == 1:
		return _SPARK_BARS[0]

	minimum = min(prices)
	maximum = max(prices)
	span = maximum - minimum
	if span == 0:
		return _SPARK_BARS[0] * len(prices)

	last_index = len(_SPARK_BARS) - 1
	chars: list[str] = []
	for price in prices:
		ratio = (price - minimum) / span
		index = int(ratio * last_index)
		chars.append(_SPARK_BARS[index])
	return "".join(chars)
