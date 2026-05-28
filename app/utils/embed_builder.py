from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal
from typing import Any

from app.models.alert_event import AlertEvent
from app.models.product import Product
from app.models.server import Server
from app.models.watch import Watch
from app.utils.chart_builder import sparkline

COLOR_DROP = 0xE33D3D
COLOR_RESTOCK = 0x3B82F6
COLOR_THRESHOLD = 0x22C55E
COLOR_NEUTRAL = 0x6B7280
COLOR_ERROR = 0xE33D3D
COLOR_SUCCESS = 0x22C55E

_RULE_TITLE = {
    "drop": "Price drop",
    "threshold": "Threshold hit",
    "restock": "Back in stock",
}
_RULE_COLOR = {
    "drop": COLOR_DROP,
    "threshold": COLOR_THRESHOLD,
    "restock": COLOR_RESTOCK,
}


def alert_embed(event: AlertEvent, watch: Watch, product: Product) -> dict[str, Any]:
    rule = event.rule_type
    embed: dict[str, Any] = {
        "title": f"{_RULE_TITLE.get(rule, rule.title())}: {product.title or product.source_url}",
        "url": product.source_url,
        "description": _format_change(event),
        "color": _RULE_COLOR.get(rule, COLOR_NEUTRAL),
        "footer": {"text": f"id: {watch.short_id}"},
    }
    if product.image_url:
        embed["thumbnail"] = {"url": product.image_url}
    return embed


def watch_added(watch: Watch, product: Product) -> dict[str, Any]:
    scraped = product.last_scraped_at is not None
    fields: list[dict[str, Any]] = [
        {"name": "ID", "value": f"`{watch.short_id}`", "inline": True},
        {"name": "Alerts", "value": _format_rules(watch.alert_rules), "inline": True},
    ]
    if scraped:
        fields.append(
            {
                "name": "Price",
                "value": f"{_money(product.last_known_price)} {product.currency or ''}".strip(),
                "inline": True,
            }
        )
        fields.append(
            {
                "name": "Stock",
                "value": "in stock"
                if product.last_known_in_stock
                else ("out of stock" if product.last_known_in_stock is False else "unknown"),
                "inline": True,
            }
        )
    embed: dict[str, Any] = {
        "title": "Now tracking",
        "url": product.source_url,
        "description": product.title or product.source_url,
        "color": COLOR_SUCCESS,
        "fields": fields,
        "footer": {
            "text": "Use /watch refresh <id> to scrape on demand"
            if scraped
            else "Fetching product details…"
        },
    }
    if product.image_url:
        embed["thumbnail"] = {"url": product.image_url}
    return embed


def watch_list(
    rows: Iterable[tuple[Watch, Product]],
    *,
    page: int,
    pages: int,
    total: int,
    cap: int,
) -> dict[str, Any]:
    lines: list[str] = []
    for watch, product in rows:
        price = _money(product.last_known_price)
        stock = (
            "✅"
            if product.last_known_in_stock
            else ("❌" if product.last_known_in_stock is False else "❓")
        )
        title = (product.title or product.source_url)[:60]
        lines.append(f"`{watch.short_id}` · {price} {product.currency or ''} {stock} · {title}")
    return {
        "title": f"Tracked products ({total}/{cap})",
        "description": "\n".join(lines) or "_No active watches. Use `/track <url>` to add one._",
        "color": COLOR_NEUTRAL,
        "footer": {"text": f"page {page}/{pages}"},
    }


def watch_info(
    watch: Watch,
    product: Product,
    history: list[Decimal | None],
) -> dict[str, Any]:
    last_check = product.last_scraped_at.isoformat() if product.last_scraped_at else "never"
    embed: dict[str, Any] = {
        "title": product.title or product.source_url,
        "url": product.source_url,
        "color": COLOR_NEUTRAL,
        "fields": [
            {
                "name": "Price",
                "value": f"{_money(product.last_known_price)} {product.currency or ''}",
                "inline": True,
            },
            {
                "name": "Stock",
                "value": "in stock"
                if product.last_known_in_stock
                else ("out of stock" if product.last_known_in_stock is False else "unknown"),
                "inline": True,
            },
            {
                "name": "Last check",
                "value": last_check,
                "inline": True,
            },
            {"name": "Alerts", "value": _format_rules(watch.alert_rules), "inline": False},
            {"name": "History", "value": f"`{sparkline(history)}`", "inline": False},
        ],
        "footer": {"text": f"id: {watch.short_id}"},
    }
    if product.image_url:
        embed["thumbnail"] = {"url": product.image_url}
    return embed


def config_show(server: Server, watch_count: int, watch_cap: int) -> dict[str, Any]:
    return {
        "title": "Server configuration",
        "color": COLOR_NEUTRAL,
        "fields": [
            {"name": "Tracker role", "value": _mention("role", server.tracker_role_id)},
            {
                "name": "Alert channel",
                "value": _mention("channel", server.default_alert_channel_id),
            },
            {"name": "Mention role", "value": _mention("role", server.default_alert_role_id)},
            {"name": "Region", "value": server.region_default or "—"},
            {"name": "Usage", "value": f"{watch_count}/{watch_cap} watches"},
        ],
    }


def setup_hint() -> dict[str, Any]:
    return {
        "title": "Thanks for adding the price tracker!",
        "description": (
            "Quick setup (requires **Manage Server**):\n"
            "1. `/config role @role` — pick who can use the bot\n"
            "2. `/config channel #channel` — where alerts will appear\n"
            "3. `/help` to see everything"
        ),
        "color": COLOR_NEUTRAL,
    }


def error_embed(message: str) -> dict[str, Any]:
    return {"title": "Can't do that", "description": message, "color": COLOR_ERROR}


def info_embed(message: str) -> dict[str, Any]:
    return {"description": message, "color": COLOR_NEUTRAL}


def _format_change(event: AlertEvent) -> str:
    if event.rule_type == "restock":
        return "Item is back in stock."
    prev = _money(event.previous_price)
    new = _money(event.new_price)
    if event.rule_type == "drop":
        return f"~~{prev}~~ → **{new}**"
    return f"Now at **{new}** (was {prev})"


def _format_rules(rules: dict[str, Any] | None) -> str:
    if not rules:
        return "none"
    parts: list[str] = []
    for key in ("drop", "restock"):
        if rules.get(key):
            parts.append(key)
    threshold = rules.get("threshold")
    if threshold not in (None, False):
        parts.append(f"≤ {threshold}")
    return ", ".join(parts) or "none"


def _money(value: Any) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}" if isinstance(value, (int, float, Decimal)) else str(value)


def _mention(kind: str, value: int | None) -> str:
    if value is None:
        return "—"
    return f"<@&{value}>" if kind == "role" else f"<#{value}>"
