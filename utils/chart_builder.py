from __future__ import annotations

from decimal import Decimal


_SPARK_BARS = "▁▂▃▄▅▆▇█"
_MAX_POINTS = 14


def _sample_evenly(prices: list[Decimal], max_points: int) -> list[Decimal]:
	if len(prices) <= max_points:
		return prices

	step = (len(prices) - 1) / (max_points - 1)
	indices = [round(index * step) for index in range(max_points)]
	return [prices[index] for index in indices]


def build_sparkline(prices: list[Decimal]) -> str:
	if len(prices) <= 1:
		return ""

	values = _sample_evenly(prices, _MAX_POINTS)

	minimum = min(values)
	maximum = max(values)
	span = maximum - minimum
	if span == 0:
		return _SPARK_BARS[0] * len(values)

	last_index = len(_SPARK_BARS) - 1
	chars: list[str] = []
	for price in values:
		ratio = (price - minimum) / span
		index = int(round(ratio * last_index))
		chars.append(_SPARK_BARS[index])
	return "".join(chars)
