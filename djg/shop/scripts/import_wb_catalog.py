from __future__ import annotations

import argparse
import decimal
import re
import zipfile
from pathlib import Path
from typing import Iterator
from xml.etree import ElementTree as ET

import django

NS = {"a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_NS = {"r": "http://schemas.openxmlformats.org/package/2006/relationships"}

# Fixed columns in catalog_full.xlsx
COL_LINK = "A"
COL_ARTICLE = "B"
COL_TITLE = "C"
COL_PRICE = "D"
COL_DESCRIPTION = "E"
COL_IMAGES = "F"


def _setup_django() -> None:
    import os
    import sys

    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "shop.settings")
    django.setup()


def _col_to_idx(col: str) -> int:
    value = 0
    for ch in col:
        value = value * 26 + (ord(ch) - ord("A") + 1)
    return value - 1


def _cell_ref_to_idx(ref: str) -> int:
    m = re.match(r"([A-Z]+)\d+", ref)
    return _col_to_idx(m.group(1)) if m else -1


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        text_node = cell.find("a:is/a:t", NS)
        return (text_node.text or "").strip() if text_node is not None else ""

    value_node = cell.find("a:v", NS)
    if value_node is None:
        return ""
    raw = (value_node.text or "").strip()
    if cell_type == "s" and raw.isdigit():
        idx = int(raw)
        if 0 <= idx < len(shared_strings):
            return shared_strings[idx]
        return ""
    return raw


def _read_xlsx_rows(path: Path) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(path) as zf:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for item in root.findall("a:si", NS):
                shared_strings.append("".join((node.text or "") for node in item.findall(".//a:t", NS)))

        wb_root = ET.fromstring(zf.read("xl/workbook.xml"))
        rel_root = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rel_map = {node.attrib["Id"]: node.attrib["Target"] for node in rel_root.findall("r:Relationship", REL_NS)}
        first_sheet = wb_root.find("a:sheets/a:sheet", NS)
        if first_sheet is None:
            return

        rel_id = first_sheet.attrib.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id", "")
        target = rel_map.get(rel_id, "").lstrip("/")
        if not target:
            return

        sheet_root = ET.fromstring(zf.read(target))
        first_row = True
        for row in sheet_root.findall(".//a:sheetData/a:row", NS):
            if first_row:
                first_row = False
                continue

            values: dict[int, str] = {}
            for cell in row.findall("a:c", NS):
                idx = _cell_ref_to_idx(cell.attrib.get("r", ""))
                if idx >= 0:
                    values[idx] = _cell_value(cell, shared_strings)

            yield {
                "link": values.get(_col_to_idx(COL_LINK), "").strip(),
                "article": values.get(_col_to_idx(COL_ARTICLE), "").strip(),
                "title": values.get(_col_to_idx(COL_TITLE), "").strip(),
                "price": values.get(_col_to_idx(COL_PRICE), "").strip(),
                "description": values.get(_col_to_idx(COL_DESCRIPTION), "").strip(),
                "images": values.get(_col_to_idx(COL_IMAGES), "").strip(),
            }


def _parse_price(raw: str) -> decimal.Decimal:
    return decimal.Decimal(raw.replace(" ", "").replace(",", "."))


def _pick_subcategory(title: str) -> str:
    text = title.lower()
    mapping = [
        ("palt", "Coats"),
        ("palto", "Coats"),
        ("пальто", "Coats"),
        ("куртк", "Jackets"),
        ("пухов", "Down Jackets"),
        ("плать", "Dresses"),
        ("юбк", "Skirts"),
        ("брюк", "Trousers"),
        ("джинс", "Jeans"),
        ("кофт", "Sweaters"),
        ("толстов", "Hoodies"),
        ("костюм", "Suits"),
        ("кроссов", "Shoes"),
        ("ботин", "Shoes"),
        ("сапог", "Shoes"),
    ]
    for needle, category in mapping:
        if needle in text:
            return category
    return "Misc"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    _setup_django()
    from botconfig.models import Category, Product, ProductImage, Subcategory

    source = Path(args.file)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")

    root_category, _ = Category.objects.get_or_create(title="Wildberries", defaults={"is_active": True})
    subcategory_cache: dict[str, Subcategory] = {}

    imported = 0
    skipped = 0

    for row in _read_xlsx_rows(source):
        if imported >= args.limit:
            break

        title = row["title"]
        price_raw = row["price"]
        description = row["description"]
        images_raw = row["images"]

        if not title or not price_raw:
            skipped += 1
            continue

        try:
            price = _parse_price(price_raw)
        except decimal.InvalidOperation:
            skipped += 1
            continue

        sub_title = _pick_subcategory(title)
        subcategory = subcategory_cache.get(sub_title)
        if subcategory is None:
            subcategory, _ = Subcategory.objects.get_or_create(
                category=root_category,
                title=sub_title,
                defaults={"is_active": True},
            )
            subcategory_cache[sub_title] = subcategory

        product, _ = Product.objects.update_or_create(
            category=root_category,
            subcategory=subcategory,
            title=title[:255],
            defaults={
                "description": description,
                "price": price,
                "is_active": True,
            },
        )

        image_urls = [item.strip() for item in images_raw.split(",") if item.strip()][:10]
        ProductImage.objects.filter(product=product).delete()
        ProductImage.objects.bulk_create(
            [ProductImage(product=product, image_url=url, position=idx) for idx, url in enumerate(image_urls)]
        )
        imported += 1

    print(f"Imported: {imported}")
    print(f"Skipped: {skipped}")


if __name__ == "__main__":
    main()
