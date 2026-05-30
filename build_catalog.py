# -*- coding: utf-8 -*-
"""
Build the deployable catalog from per-dish YAML sources.

Inputs:
  dishes/manual/*.yaml      -- hand-authored dishes (source of truth)
  dishes/generated/*.yaml   -- emitted by generate_khmer_menu.py

Outputs (all under build/, committed so GitHub Pages serves them directly):
  build/index.json          -- slim catalog used by the page for grid + search
  build/dishes/<slug>.json  -- full per-dish detail, fetched lazily on click
  build/khmer_menu.json     -- bulk dataset (meta + recipes[]) for downstream consumers

Run after editing any YAML or running the generator:
  python build_catalog.py
"""

import json
import os
import sys
import datetime
import shutil
import yaml

MANUAL_DIR = os.path.join("dishes", "manual")
GENERATED_DIR = os.path.join("dishes", "generated")
BUILD_DIR = "build"
INDEX_PATH = os.path.join(BUILD_DIR, "index.json")
DISHES_OUT = os.path.join(BUILD_DIR, "dishes")
BULK_PATH = os.path.join(BUILD_DIR, "khmer_menu.json")

# Fields kept in the lightweight index (drives grid display, search, filters,
# dish-of-the-day). Everything else lives in the per-dish detail file and is
# only fetched when a user opens a recipe.
INDEX_FIELDS = [
    "id", "slug", "name",
    "category", "subcategory",
    "image", "imageFamily",
    "tags", "dietary",
    "spiceLevel", "difficulty",
    "time", "kroeung",
]

REQUIRED_FIELDS = ["id", "slug", "name", "category", "ingredients", "instructions"]


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level must be a mapping")
    return data


def validate(recipe, source_path):
    for f in REQUIRED_FIELDS:
        if f not in recipe:
            raise ValueError(f"{source_path}: missing required field '{f}'")
    if not isinstance(recipe["ingredients"], list) or not recipe["ingredients"]:
        raise ValueError(f"{source_path}: ingredients must be a non-empty list")
    if not isinstance(recipe["instructions"], list) or not recipe["instructions"]:
        raise ValueError(f"{source_path}: instructions must be a non-empty list")
    name = recipe.get("name") or {}
    if "en" not in name:
        raise ValueError(f"{source_path}: name.en is required")


def collect_recipes():
    """Return a list of recipes; manual wins on slug collision (with a warning)."""
    by_slug = {}
    sources = {}  # slug -> "manual" / "generated"

    def ingest(folder, kind):
        if not os.path.isdir(folder):
            return
        for fname in sorted(os.listdir(folder)):
            if not fname.endswith(".yaml"):
                continue
            path = os.path.join(folder, fname)
            r = load_yaml(path)
            validate(r, path)
            slug = r["slug"]
            if slug in by_slug and sources[slug] == "manual":
                # manual wins
                if kind == "generated":
                    continue
            by_slug[slug] = r
            sources[slug] = kind

    ingest(MANUAL_DIR, "manual")
    ingest(GENERATED_DIR, "generated")
    # log collisions
    collisions = []
    if os.path.isdir(MANUAL_DIR) and os.path.isdir(GENERATED_DIR):
        manual_slugs = {f[:-5] for f in os.listdir(MANUAL_DIR) if f.endswith(".yaml")}
        gen_slugs = {f[:-5] for f in os.listdir(GENERATED_DIR) if f.endswith(".yaml")}
        collisions = sorted(manual_slugs & gen_slugs)
    if collisions:
        print("note: manual overrides for slug(s):", ", ".join(collisions[:5]),
              "(+%d more)" % (len(collisions) - 5) if len(collisions) > 5 else "")
    return list(by_slug.values()), sources


def slim_for_index(r):
    out = {}
    for f in INDEX_FIELDS:
        if f in r:
            out[f] = r[f]
    return out


def main():
    # clean rebuild for deterministic output
    if os.path.isdir(BUILD_DIR):
        shutil.rmtree(BUILD_DIR)
    os.makedirs(DISHES_OUT, exist_ok=True)

    recipes, sources = collect_recipes()
    # signature dishes first, then alphabetical by English name
    recipes.sort(key=lambda r: (
        0 if "signature" in (r.get("tags") or []) else 1,
        r["name"].get("en", ""),
    ))

    # write per-dish detail
    for r in recipes:
        with open(os.path.join(DISHES_OUT, r["slug"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False)

    # write slim index
    index = {
        "schemaVersion": "1.0",
        "count": len(recipes),
        "categories": sorted({r["category"] for r in recipes}),
        "generatedAt": datetime.date.today().isoformat(),
        "recipes": [slim_for_index(r) for r in recipes],
    }
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False)

    # write bulk dataset (back-compat for downstream consumers)
    bulk = {
        "meta": {
            "schemaVersion": "1.0",
            "title": "Khmer Chief — Cambodian Recipe Catalog",
            "cuisine": "Khmer",
            "language": {"primary": "en", "names": ["km", "romanized", "en"]},
            "count": len(recipes),
            "categories": index["categories"],
            "generatedAt": index["generatedAt"],
            "license": "CC-BY-4.0 (recipes are traditional / generated for demonstration)",
        },
        "recipes": recipes,
    }
    with open(BULK_PATH, "w", encoding="utf-8") as f:
        json.dump(bulk, f, ensure_ascii=False)

    # report
    manual = sum(1 for s in sources.values() if s == "manual")
    generated = sum(1 for s in sources.values() if s == "generated")
    print(f"Built {len(recipes)} dishes ({manual} manual + {generated} generated)")
    print(f"  -> {INDEX_PATH}   ({os.path.getsize(INDEX_PATH)/1024:.1f} KB)")
    print(f"  -> {DISHES_OUT}/*.json  ({len(recipes)} files)")
    print(f"  -> {BULK_PATH}      ({os.path.getsize(BULK_PATH)/1024:.1f} KB)")


if __name__ == "__main__":
    sys.exit(main())
