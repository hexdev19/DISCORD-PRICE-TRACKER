from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
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
COLOR_IN_STOCK = 0x22C55E
COLOR_OUT_OF_STOCK = 0xE33D3D

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
        {"name": "🆔 ID", "value": f"`{watch.short_id}`", "inline": True},
    ]
    if scraped:
        fields.append({"name": "💵 Price", "value": _price(product), "inline": True})
        fields.append(
            {
                "name": "📦 Stock",
                "value": f"{_stock_emoji(product.last_known_in_stock)} "
                f"{_stock_text(product.last_known_in_stock)}",
                "inline": True,
            }
        )
    fields.append({"name": "🔔 Alerts", "value": _format_rules(watch.alert_rules), "inline": False})
    embed: dict[str, Any] = {
        "author": {"name": "✅ Now tracking"},
        "title": product.title or product.source_url,
        "url": product.source_url,
        "color": COLOR_SUCCESS,
        "fields": fields,
        "footer": {
            "text": f"id: {watch.short_id} · /watch refresh to update"
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
        title = (product.title or product.source_url)[:64]
        paused = " · ⏸️ paused" if watch.paused_at is not None else ""
        lines.append(
            f"{_stock_emoji(product.last_known_in_stock)} `{watch.short_id}` · "
            f"{_price(product)}{paused}\n┗ [{title}]({product.source_url})"
        )
    return {
        "title": f"📋 Tracked products · {total}/{cap}",
        "description": "\n\n".join(lines)
        or "_No active watches yet._\nUse `/track <url>` to start tracking a product.",
        "color": COLOR_NEUTRAL,
        "footer": {"text": f"page {page}/{pages} · /info <id> for details"},
    }


def watch_info(
    watch: Watch,
    product: Product,
    history: list[Decimal | None],
) -> dict[str, Any]:
    real = [v for v in history if v is not None]
    cur = product.currency or ""
    if real:
        history_value = (
            f"`{sparkline(history)}`\n"
            f"low **{_money(min(real))}** · high **{_money(max(real))}** {cur}".strip()
        )
    else:
        history_value = "_no price history yet_"

    embed: dict[str, Any] = {
        "author": {"name": product.domain},
        "title": product.title or product.source_url,
        "url": product.source_url,
        "color": _stock_color(product.last_known_in_stock),
        "fields": [
            {
                "name": "💵 Price",
                "value": f"{_price(product)} {_trend(history)}".strip(),
                "inline": True,
            },
            {
                "name": "📦 Stock",
                "value": f"{_stock_emoji(product.last_known_in_stock)} "
                f"{_stock_text(product.last_known_in_stock)}",
                "inline": True,
            },
            {
                "name": "🕒 Last check",
                "value": _relative_time(product.last_scraped_at),
                "inline": True,
            },
            {"name": "🔔 Alerts", "value": _format_rules(watch.alert_rules), "inline": False},
            {"name": "📈 History", "value": history_value, "inline": False},
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


def _price(product: Product) -> str:
    amount = _money(product.last_known_price)
    if amount == "—":
        return "—"
    return f"**{amount}** {product.currency or ''}".strip()


def _stock_emoji(in_stock: bool | None) -> str:
    return "🟢" if in_stock else ("🔴" if in_stock is False else "⚪")


def _stock_text(in_stock: bool | None) -> str:
    return "In stock" if in_stock else ("Out of stock" if in_stock is False else "Unknown")


def _stock_color(in_stock: bool | None) -> int:
    return (
        COLOR_IN_STOCK if in_stock else (COLOR_OUT_OF_STOCK if in_stock is False else COLOR_NEUTRAL)
    )


def _relative_time(value: datetime | None) -> str:
    if value is None:
        return "never"
    return f"<t:{int(value.timestamp())}:R>"


def _trend(history: list[Decimal | None]) -> str:
    real = [v for v in history if v is not None]
    if len(real) < 2 or real[-1] == real[-2]:
        return ""
    return "📉" if real[-1] < real[-2] else "📈"


def _mention(kind: str, value: int | None) -> str:
    if value is None:
        return "—"
    return f"<@&{value}>" if kind == "role" else f"<#{value}>"
