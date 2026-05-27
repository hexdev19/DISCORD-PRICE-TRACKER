"""Discord embed payloads.

Phase 4 ships the minimal ``alert_embed`` payload the alert dispatcher
posts to ``/channels/{id}/messages``. Phase 5 extends this with colors,
icons, and richer formatting from ``bot-commands.md`` §Reply UX.
"""

from __future__ import annotations

from typing import Any

from app.models.alert_event import AlertEvent
from app.models.product import Product
from app.models.watch import Watch

_RULE_TITLE = {
    "drop": "Price drop",
    "threshold": "Threshold hit",
    "restock": "Back in stock",
}
_RULE_COLOR = {
    "drop": 0xE33D3D,
    "threshold": 0x22C55E,
    "restock": 0x3B82F6,
}


def alert_embed(
    event: AlertEvent,
    watch: Watch,
    product: Product,
) -> dict[str, Any]:
    rule = event.rule_type
    title = _RULE_TITLE.get(rule, rule.title())
    description = _format_change(event)
    embed: dict[str, Any] = {
        "title": f"{title}: {product.title or product.source_url}",
        "url": product.source_url,
        "description": description,
        "color": _RULE_COLOR.get(rule, 0x6B7280),
        "footer": {"text": f"id: {watch.short_id}"},
    }
    if product.image_url:
        embed["thumbnail"] = {"url": product.image_url}
    return embed


def _format_change(event: AlertEvent) -> str:
    if event.rule_type == "restock":
        return "Item is back in stock."
    prev = _money(event.previous_price)
    new = _money(event.new_price)
    if event.rule_type == "drop":
        return f"~~{prev}~~ → **{new}**"
    return f"Now at **{new}** (was {prev})"


def _money(value: Any) -> str:
    return f"{value:.2f}" if value is not None else "—"
