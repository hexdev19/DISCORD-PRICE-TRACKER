from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from decimal import Decimal
from typing import Any

import discord


GREEN = 0x57F287
RED = 0xED4245
BLUE = 0x5865F2
YELLOW = 0xFEE75C
GREY = 0x99AAB5


def _to_money(value: Any, currency: str | None = None) -> str:
	if value is None:
		return "N/A"
	if isinstance(value, Decimal):
		amount = f"{value:.2f}"
	else:
		amount = str(value)
	if currency:
		return f"{amount} {currency}"
	return amount


def _to_percent(value: Any) -> str:
	if value is None:
		return "N/A"
	if isinstance(value, Decimal):
		return f"{value:.2f}%"
	return f"{value}%"


def _field(embed: discord.Embed, name: str, value: str, inline: bool = True) -> None:
	embed.add_field(name=name, value=value if value else "N/A", inline=inline)


def tracking_embed(listing: Any, product: Any) -> discord.Embed:
	store_name = getattr(getattr(listing, "store", None), "name", "Store")
	product_name = getattr(product, "canonical_name", "Product")
	embed = discord.Embed(title=f"{store_name} - {product_name}", color=BLUE)

	price = _to_money(getattr(listing, "current_price", None), getattr(listing, "currency", None))
	stock = "✅ In stock" if bool(getattr(listing, "in_stock", False)) else "❌ Out of stock"

	_field(embed, "Price", price)
	_field(embed, "Availability", stock)

	thumb = getattr(listing, "image_url", None) or getattr(product, "image_url", None)
	if thumb:
		embed.set_thumbnail(url=str(thumb))

	embed.set_footer(text="Tracking started")
	return embed


def comparison_embed(listings: list[Any], product: Any | None = None) -> discord.Embed:
	if product is None and listings:
		product = getattr(listings[0], "product", None)
	product_name = getattr(product, "canonical_name", "Product")

	embed = discord.Embed(title=f"🛒 {product_name}", color=BLUE)
	sorted_rows = sorted(listings, key=lambda row: getattr(row, "current_price", Decimal("0")))[:20]

	for index, listing in enumerate(sorted_rows):
		store_name = getattr(getattr(listing, "store", None), "name", "Store")
		price = _to_money(getattr(listing, "current_price", None), getattr(listing, "currency", None))
		stock = "✅" if bool(getattr(listing, "in_stock", False)) else "❌"
		prefix = "🏆 " if index == 0 else ""
		_field(embed, f"{prefix}{store_name}", f"{price} {stock}", inline=False)

	embed.set_footer(text="Sorted by price ↑")
	return embed


def searching_embed(query: str, location: str | None) -> discord.Embed:
	where = location if location else "Global"
	embed = discord.Embed(
		title="🔍 Searching...",
		description=f"Query: {query}\nLocation: {where}",
		color=GREY,
	)
	return embed


def history_listing_embed(data: dict[str, Any], page: int) -> discord.Embed:
	listing = data.get("listing")
	listing_title = getattr(listing, "title", "Listing")
	stats = data.get("stats", {})

	embed = discord.Embed(title=f"📈 {listing_title}", color=BLUE)
	_field(embed, "Current", _to_money(getattr(listing, "current_price", None), getattr(listing, "currency", None)))
	_field(embed, "Min", _to_money(stats.get("min"), getattr(listing, "currency", None)))
	_field(embed, "Max", _to_money(stats.get("max"), getattr(listing, "currency", None)))
	_field(embed, "Avg", _to_money(stats.get("avg"), getattr(listing, "currency", None)))

	sparkline = data.get("sparkline", "")
	_field(embed, "Trend", f"```{sparkline}```", inline=False)

	rows: Iterable[Any] = data.get("rows", [])
	change_lines: list[str] = []
	for row in rows:
		timestamp = getattr(row, "recorded_at", None)
		if isinstance(timestamp, datetime):
			label = timestamp.strftime("%Y-%m-%d")
		else:
			label = "Unknown time"
		line = f"{label} | {getattr(row, 'change_type', 'no_change')} | {_to_money(getattr(row, 'price', None), getattr(row, 'currency', None))}"
		change_lines.append(line)

	if change_lines:
		_field(embed, "Changes", "\n".join(change_lines), inline=False)

	embed.set_footer(text=f"Page {page}")
	return embed


def history_product_embed(data: dict[str, Any], product: Any) -> discord.Embed:
	product_name = getattr(product, "canonical_name", "Product")
	embed = discord.Embed(title=f"📊 {product_name}", color=BLUE)

	best_ever = data.get("best_price_ever")
	_field(embed, "Best price ever", _to_money(best_ever), inline=False)

	for store_data in data.get("stores", []):
		store_name = str(store_data.get("store_id", "Store"))
		currency = store_data.get("currency")
		min_price = _to_money(store_data.get("min"), currency)
		max_price = _to_money(store_data.get("max"), currency)
		avg_price = _to_money(store_data.get("avg"), currency)
		_field(embed, store_name, f"Min: {min_price}\nMax: {max_price}\nAvg: {avg_price}", inline=False)

	return embed


def alert_embed(listing: Any, product: Any, change_type: str) -> discord.Embed:
	color_map = {
		"price_drop": GREEN,
		"price_rise": RED,
		"restock": GREEN,
		"out_of_stock": YELLOW,
	}
	embed = discord.Embed(title="🔔 Price Alert", color=color_map.get(change_type, GREY))

	store_name = getattr(getattr(listing, "store", None), "name", "Store")
	current_price = getattr(listing, "current_price", None)
	currency = getattr(listing, "currency", None)
	old_price = getattr(listing, "previous_price", None)
	delta_pct = getattr(listing, "delta_pct", None)

	_field(embed, "Store", store_name)
	_field(embed, "Price", f"{_to_money(old_price, currency)} → {_to_money(current_price, currency)}", inline=False)
	_field(embed, "Delta", _to_percent(delta_pct))

	thumb = getattr(listing, "image_url", None) or getattr(product, "image_url", None)
	if thumb:
		embed.set_thumbnail(url=str(thumb))

	embed.set_footer(text="/untrack to stop")
	return embed


def success_embed(message: str) -> discord.Embed:
	return discord.Embed(description=message, color=GREEN)


def error_embed(message: str) -> discord.Embed:
	return discord.Embed(description=message, color=RED)


def info_embed(message: str) -> discord.Embed:
	return discord.Embed(description=message, color=BLUE)

