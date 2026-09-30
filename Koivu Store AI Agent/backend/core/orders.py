"""Least-privilege order lookup used by the agent workflow."""

from __future__ import annotations

import re

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from core.database import Database


DEMO_STORE_CATALOG: dict[str, dict] = {
    "merino": {"name": "Merinovillapaita Klassik", "unit_price_cents": 8900, "variants": {
        "Forest": ("XS", "S", "M", "L", "XL", "XXL"), "Navy": ("XS", "S", "M", "L", "XL", "XXL"),
        "Charcoal": ("XS", "S", "M", "L", "XL", "XXL"), "Ivory": ("XS", "S", "M", "L", "XL", "XXL"),
    }},
    "pellava": {"name": "Pellavahousut Rento", "unit_price_cents": 12000, "variants": {
        "Beige": ("XS", "S", "M", "L", "XL"), "White": ("XS", "S", "M", "L", "XL"), "Sage": ("XS", "S", "M"), "Camel": (),
    }},
    "vyö": {"name": "Nahkavyö Slim", "unit_price_cents": 4500, "variants": {
        "Cognac": ("75 cm", "80 cm", "85 cm", "90 cm", "95 cm", "100 cm"),
        "Black": ("75 cm", "80 cm", "85 cm", "90 cm", "95 cm", "100 cm"),
        "Tan": ("75 cm", "90 cm", "95 cm", "100 cm"),
    }},
    "kasmir": {"name": "Kasmirhuivi Luxe", "unit_price_cents": 16000, "variants": {
        "Forest": ("Yksi koko",), "Camel": ("Yksi koko",), "Dusty Rose": ("Yksi koko",), "Midnight": ("Yksi koko",),
    }},
    "denim": {"name": "Denim-takki Vintage", "unit_price_cents": 18500, "variants": {
        "Washed Blue": ("XS", "S", "M", "L", "XL", "XXL"), "Dark Indigo": ("S", "M", "L"), "Ecru": (),
    }},
    "silkki": {"name": "Silkkipaita Elegance", "unit_price_cents": 13500, "variants": {
        "Ivory": ("XS", "S", "M", "L", "XL"), "Blush": ("XS", "S", "M"), "Champagne": (), "Black": ("XS", "S", "M", "L", "XL"),
    }},
}


def price_demo_order_items(items: list[dict]) -> tuple[list[dict], int]:
    """Validate cart variants and derive names/prices from the server-side demo catalogue."""
    if not items or len(items) > 24:
        raise ValueError("Tilauksessa pitää olla 1–24 tuoteriviä.")
    priced_items: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    total_cents = 0
    for item in items:
        product_id = item.get("product_id")
        color = item.get("color")
        size = item.get("size")
        quantity = item.get("quantity")
        product = DEMO_STORE_CATALOG.get(product_id) if isinstance(product_id, str) else None
        if product is None or not isinstance(color, str) or not isinstance(size, str):
            raise ValueError("Ostoskorissa on tuntematon tuote tai tuotevalinta.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or not 1 <= quantity <= 20:
            raise ValueError("Tuotemäärän pitää olla 1–20.")
        if size not in product["variants"].get(color, ()):
            raise ValueError("Valitsemasi väri ja koko eivät ole saatavilla.")
        key = (product_id, color, size)
        if key in seen:
            raise ValueError("Poista ostoskorista saman tuotteen päällekkäiset rivit.")
        seen.add(key)
        unit_price_cents = product["unit_price_cents"]
        priced_items.append({
            "product_id": product_id, "name": product["name"], "color": color, "size": size,
            "quantity": quantity, "unit_price_cents": unit_price_cents,
        })
        total_cents += unit_price_cents * quantity
    return priced_items, total_cents


class OrderStatusInput(BaseModel):
    order_id: str | None = Field(
        default=None,
        max_length=32,
        pattern=r"^(?:ORD-[A-Fa-f0-9]{8}|[0-9]{1,32})$",
    )


class OrderStatusOutput(BaseModel):
    order_id: str
    status: str
    tracking_code: str | None


class OrderStatusService:
    def __init__(self, database: Database):
        self.database = database

    def get_status(self, user_id: str, order_id: str | None = None) -> OrderStatusOutput | None:
        request = OrderStatusInput(order_id=order_id)
        if request.order_id is None:
            order = self.database.get_latest_owned_order(user_id)
        else:
            order = self.database.get_owned_order(request.order_id, user_id)
        if order is None:
            # Missing and other customers' orders are intentionally indistinguishable.
            return None
        return OrderStatusOutput(
            order_id=order["id"],
            status=order["status"],
            tracking_code=order["tracking_code"],
        )

    def as_agent_tool(self, user_id: str) -> StructuredTool:
        """Bind identity in backend code; the tool schema only accepts an order id."""

        def lookup(order_id: str | None = None) -> dict | None:
            result = self.get_status(user_id=user_id, order_id=order_id)
            return result.model_dump() if result else None

        return StructuredTool.from_function(
            func=lookup,
            name="get_order_status",
            description=(
                "Return the status of an order owned by the authenticated customer. "
                "If order_id is omitted, return that customer's latest order. "
                "A missing or unowned order returns no result. Never use this for another customer."
            ),
            args_schema=OrderStatusInput,
        )


_ORDER_REFERENCE = re.compile(r"\bORD-[A-Fa-f0-9]{8}\b|\b\d{1,32}\b", re.IGNORECASE)


def extract_order_reference(text: str) -> str | None:
    matches = _ORDER_REFERENCE.findall(text)
    if len(matches) != 1:
        return None
    return matches[0].upper() if matches[0].upper().startswith("ORD-") else matches[0]
