"""Validate public catalog records and build a dependency-free static site."""

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)
PHOTO = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,90}\.(?:jpe?g|png|webp)", re.IGNORECASE | re.ASCII)
PRICE = re.compile(r"[0-9]{1,4}(?:\.[0-9]{1,2})?", re.ASCII)
CATEGORIES = {"Tees", "Hoodies", "Sets", "Denim", "Outerwear", "Accessories", "Other"}


def catalog_path(root):
    return root / "catalog" / "products.json"


def photo_path(root, filename):
    if not PHOTO.fullmatch(filename):
        raise ValueError("Enter just the filename of a JPEG, PNG, or WebP in the media folder.")
    path = root / "media" / filename
    if path.is_symlink() or not path.is_file():
        raise ValueError("That photo was not found in the media folder.")
    with path.open("rb") as image:
        signature = image.read(12)
    suffix = path.suffix.lower()
    valid = (
        (suffix in {".jpg", ".jpeg"} and signature.startswith(b"\xff\xd8\xff"))
        or (suffix == ".png" and signature.startswith(b"\x89PNG\r\n\x1a\n"))
        or (suffix == ".webp" and signature.startswith(b"RIFF") and signature[8:12] == b"WEBP")
    )
    if not valid or path.stat().st_size > 5 * 1024 * 1024:
        raise ValueError("Use a valid JPEG, PNG, or WebP up to 5 MB.")
    return path


def validated(product, root):
    if not isinstance(product, dict):
        raise ValueError("Invalid product record.")
    slug, name, category, cents, description, image = (
        product.get(field) for field in ("id", "name", "category", "price_cents", "description", "image")
    )
    if not isinstance(slug, str) or len(slug) > 60 or not ID.fullmatch(slug):
        raise ValueError("Use a product ID of up to 60 lowercase letters, numbers, and single hyphens.")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        raise ValueError("Enter a product name of up to 100 characters.")
    if not isinstance(category, str) or category not in CATEGORIES:
        raise ValueError("Choose a listed category.")
    if type(cents) is not int or not 0 <= cents <= 999999:
        raise ValueError("Enter a USD price between 0.00 and 9,999.99.")
    if not isinstance(description, str) or len(description) > 1500:
        raise ValueError("Keep the description within 1,500 characters.")
    if not isinstance(image, str):
        raise ValueError("Invalid image path.")
    if image:
        if not image.startswith("media/"):
            raise ValueError("Product photos must be inside the media folder.")
        photo_path(root, image.removeprefix("media/"))
    return dict(id=slug, name=name.strip(), category=category, price_cents=cents,
                description=description, image=image)


def read_catalog(root):
    records = json.loads(catalog_path(root).read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("The catalog must be a list.")
    products = [validated(item, root) for item in records]
    if len({item["id"] for item in products}) != len(products):
        raise ValueError("Product IDs must be unique.")
    return products


def update_catalog(root, inputs):
    products = read_catalog(root)
    operation = inputs.get("operation")
    if operation == "check":
        return products
    slug = inputs.get("product_id", "").strip()
    if len(slug) > 60 or not ID.fullmatch(slug):
        raise ValueError("Use a product ID of up to 60 lowercase letters, numbers, and single hyphens.")
    ids = {product["id"] for product in products}
    if operation == "remove":
        if slug not in ids:
            raise ValueError("No product matches that ID.")
        products = [item for item in products if item["id"] != slug]
    elif operation == "add_or_update":
        price = inputs.get("price", "").strip()
        if not PRICE.fullmatch(price):
            raise ValueError("Enter a USD price such as 45.00, without a dollar sign.")
        whole, _, decimal = price.partition(".")
        filename = inputs.get("photo", "").strip()
        product = validated(dict(
            id=slug, name=inputs.get("name", ""), category=inputs.get("category", "Other"),
            price_cents=int(whole) * 100 + int(decimal.ljust(2, "0")),
            description=inputs.get("description", "").strip(), image=f"media/{filename}" if filename else "",
        ), root)
        products = [product if item["id"] == slug else item for item in products] if slug in ids else [product, *products]
    else:
        raise ValueError("Unknown catalog operation.")
    catalog_path(root).write_text(json.dumps(products, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return products


def build(root, destination):
    products = read_catalog(root)
    destination = destination.resolve()
    if destination != (root / "_site").resolve() or (root / "_site").is_symlink():
        raise ValueError("Build output must be the project's _site directory.")
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(root / "public", destination)
    (destination / "catalog.json").write_text(json.dumps(products, ensure_ascii=False) + "\n", encoding="utf-8")
    for item in products:
        if item["image"]:
            filename = item["image"].removeprefix("media/")
            target = destination / "media" / filename
            target.parent.mkdir(exist_ok=True)
            shutil.copyfile(photo_path(root, filename), target)
    return products


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "update"])
    parser.add_argument("--event", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "update":
            if args.event is None:
                raise ValueError("A GitHub workflow event is required.")
            update_catalog(ROOT, json.loads(args.event.read_text(encoding="utf-8"))["inputs"])
        build(ROOT, ROOT / "_site")
    except (ValueError, TypeError, KeyError, OSError) as exc:
        parser.exit(1, f"Catalog error: {exc}\n")


if __name__ == "__main__":
    main()
