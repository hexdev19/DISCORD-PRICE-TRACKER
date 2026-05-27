from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace

from app.utils.embed_builder import alert_embed


def _event(rule: str, *, prev: Decimal | None = Decimal("100"), new: Decimal | None = Decimal("80")) -> SimpleNamespace:
    return SimpleNamespace(
        rule_type=rule,
        previous_price=prev,
        new_price=new,
    )


def _watch() -> SimpleNamespace:
    return SimpleNamespace(short_id="ABCD1234")


def _product() -> SimpleNamespace:
    return SimpleNamespace(
        title="Demo Widget",
        source_url="https://example.com/p/1",
        image_url="https://example.com/img.png",
        id=uuid.uuid4(),
    )


def test_drop_uses_red_strike_format() -> None:
    embed = alert_embed(_event("drop"), _watch(), _product())
    assert embed["color"] == 0xE33D3D
    assert embed["title"].startswith("Price drop")
    assert "~~100.00~~" in embed["description"]
    assert "**80.00**" in embed["description"]
    assert embed["footer"]["text"] == "id: ABCD1234"


def test_threshold_uses_green() -> None:
    embed = alert_embed(_event("threshold"), _watch(), _product())
    assert embed["color"] == 0x22C55E
    assert "Threshold hit" in embed["title"]


def test_restock_uses_blue_and_omits_price_change() -> None:
    embed = alert_embed(_event("restock", prev=None, new=None), _watch(), _product())
    assert embed["color"] == 0x3B82F6
    assert embed["description"] == "Item is back in stock."


def test_missing_image_omits_thumbnail() -> None:
    product = _product()
    product.image_url = None
    embed = alert_embed(_event("drop"), _watch(), product)
    assert "thumbnail" not in embed
