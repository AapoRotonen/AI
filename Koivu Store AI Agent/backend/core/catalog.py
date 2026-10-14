"""Shared public product catalogue used by the storefront and backend."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
import re


def _catalog_file() -> Path:
    module_dir = Path(__file__).resolve().parent
    candidates = (
        module_dir.parent / "frontend" / "catalog.json",
        module_dir.parents[1] / "frontend" / "catalog.json",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    checked = ", ".join(str(path) for path in candidates)
    raise FileNotFoundError(f"Shared product catalogue not found; checked: {checked}")


@lru_cache(maxsize=1)
def get_catalog() -> tuple[dict, ...]:
    """Load and validate the JSON catalogue once per process."""
    raw = json.loads(_catalog_file().read_text(encoding="utf-8"))
    if not isinstance(raw, list) or not raw:
        raise ValueError("Product catalogue must be a non-empty JSON array")
    products: list[dict] = []
    seen_ids: set[str] = set()
    seen_skus: set[str] = set()
    allowed_categories = {"neuleet", "vaatteet", "asusteet", "laukut", "kengät"}
    for product in raw:
        if not isinstance(product, dict):
            raise ValueError("Each product must be a JSON object")
        product_id = product.get("id")
        sku = product.get("sku")
        price = product.get("price_cents")
        if not isinstance(product_id, str) or not product_id or product_id in seen_ids:
            raise ValueError("Product IDs must be unique non-empty strings")
        if not isinstance(sku, str) or not re.fullmatch(r"[A-Z]{3}-\d{3}", sku) or sku in seen_skus:
            raise ValueError("Product SKUs must be unique non-empty strings")
        if isinstance(price, bool) or not isinstance(price, int) or price <= 0:
            raise ValueError(f"Product {product_id} has an invalid price")
        if product.get("category") not in allowed_categories:
            raise ValueError(f"Product {product_id} has an unknown category")
        if not all(isinstance(product.get(field), str) and product[field].strip() for field in (
            "name", "material", "description", "image", "alt"
        )):
            raise ValueError(f"Product {product_id} is missing required public text")
        if not isinstance(product.get("colors"), list) or not product["colors"]:
            raise ValueError(f"Product {product_id} is missing variants")
        sizes = product.get("sizes")
        if not isinstance(sizes, list) or not sizes or any(not isinstance(size, str) or not size for size in sizes):
            raise ValueError(f"Product {product_id} has invalid sizes")
        if len(sizes) != len(set(sizes)):
            raise ValueError(f"Product {product_id} has duplicate sizes")
        color_names: set[str] = set()
        for color in product["colors"]:
            if not isinstance(color, dict) or not isinstance(color.get("name"), str) or not color["name"]:
                raise ValueError(f"Product {product_id} has an invalid color variant")
            name = color["name"]
            stock = color.get("stock")
            if name in color_names or not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(color.get("hex", ""))):
                raise ValueError(f"Product {product_id} has an invalid color definition")
            if not isinstance(stock, list) or any(value not in sizes for value in stock):
                raise ValueError(f"Product {product_id} has an invalid demo-availability list")
            color_names.add(name)
        seen_ids.add(product_id)
        seen_skus.add(sku)
        products.append(product)
    return tuple(products)


def get_catalog_by_id() -> dict[str, dict]:
    """Return product data keyed by its stable public ID."""
    return {product["id"]: product for product in get_catalog()}


def catalog_document(product: dict) -> str:
    """Build a factual, deterministic retrieval document from public catalogue data."""
    colors = ", ".join(
        f"{color['name']} ({', '.join(color['stock']) if color['stock'] else 'ei saatavilla demossa'})"
        for color in product["colors"]
    )
    return "\n".join((
        f"TUOTE {product['sku']}: {product['name']}",
        f"Tuotekoodi: {product['sku']}",
        f"Kategoria: {product['category']}",
        f"Hinta: {product['price_cents'] / 100:.2f} euroa (demohinta)",
        f"Materiaali: {product['material']}",
        f"Kuvaus: {product['description']}",
        f"Hoito-ohje: {product.get('care', 'Tarkista tuotteen pesuohje.')}",
        f"Koot: {', '.join(product['sizes'])}",
        f"Värit ja demossa saatavilla olevat koot: {colors}",
        "Saatavuustiedot ovat portfolio-demon esimerkkitietoja, eivät reaaliaikaista varastoa.",
    ))
