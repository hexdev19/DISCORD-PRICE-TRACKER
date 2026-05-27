from __future__ import annotations

import uuid
from decimal import Decimal
from types import SimpleNamespace

from app.utils import embed_builder


def _watch(**kw):
    base = dict(
        short_id="ABCD1234",
        alert_rules={"drop": True, "restock": True, "threshold": "75.00"},
    )
    base.update(kw)
    return SimpleNamespace(**base)


def _product(**kw):
    base = dict(
        id=uuid.uuid4(),
        title="Demo Widget",
        source_url="https://example.com/p/1",
        image_url=None,
        currency="USD",
        last_known_price=Decimal("99.95"),
        last_known_in_stock=True,
        last_scraped_at=None,
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_watch_added_includes_short_id_and_rules() -> None:
    embed = embed_builder.watch_added(_watch(), _product())
    assert embed["color"] == embed_builder.COLOR_SUCCESS
    fields = {f["name"]: f["value"] for f in embed["fields"]}
    assert "`ABCD1234`" in fields["ID"]
    assert "drop" in fields["Alerts"]
    assert "≤ 75.00" in fields["Alerts"]


def test_watch_list_empty_state() -> None:
    embed = embed_builder.watch_list([], page=1, pages=1, total=0, cap=25)
    assert "No active watches" in embed["description"]
    assert embed["footer"]["text"] == "page 1/1"


def test_watch_list_renders_rows() -> None:
    embed = embed_builder.watch_list(
        [(_watch(), _product())], page=1, pages=1, total=1, cap=25
    )
    assert "`ABCD1234`" in embed["description"]
    assert "99.95" in embed["description"]


def test_watch_info_includes_sparkline_field() -> None:
    embed = embed_builder.watch_info(
        _watch(), _product(), [Decimal("100"), Decimal("90"), Decimal("80")]
    )
    field_names = [f["name"] for f in embed["fields"]]
    assert "History" in field_names
    assert "Price" in field_names


def test_config_show_uses_dashes_for_unset() -> None:
    server = SimpleNamespace(
        tracker_role_id=None,
        default_alert_channel_id=None,
        default_alert_role_id=None,
        region_default=None,
        plan="free",
    )
    embed = embed_builder.config_show(server, watch_count=0, watch_cap=25)
    values = {f["name"]: f["value"] for f in embed["fields"]}
    assert values["Tracker role"] == "—"
    assert values["Usage"] == "0/25 watches"


def test_setup_hint_is_safe_for_dm() -> None:
    embed = embed_builder.setup_hint()
    assert "/config role" in embed["description"]
