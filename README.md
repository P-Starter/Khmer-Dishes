# 🍳 Khmer Dishes — Cambodian Recipe Catalog

An open, structured catalog of **1,059+ Cambodian (Khmer) dishes** — each with a
trilingual name (Khmer / romanized / English), structured ingredients, and
step-by-step *how-to-cook* instructions — plus a lightweight, searchable webview
that runs anywhere as a static site.

> **Live site:** https://p-starter.github.io/Khmer-Dishes/ *(once GitHub Pages is enabled)*

The goal is to grow into the most complete, machine-readable reference of Khmer
home cooking — and to recommend a **daily Khmer dish** to anyone learning to cook it.

---

## ✨ Features

- **1,059 dishes** across 14 categories (stir-fry, soup, curry, grilled, fried, braised, steamed, salad, noodles, rice, dip, dessert, drink, snack).
- **Trilingual names** — Khmer script, romanization, and English.
- **Real cooking steps** — grouped ingredients + numbered instructions with chef's tips.
- **Searchable webview** — typo-tolerant fuzzy search, filters (category / protein / diet / spice), and a deterministic **dish of the day**.
- **Open data** — one clean JSON file validated by a published [JSON Schema](#-data--schema).
- **Zero backend** — pure static files; deploys free on GitHub Pages.

---

## 🚀 Quick start

**View the site locally** — no build step, no server required:

```bash
# Option A: just double-click index.html  (data loads from khmer_data.js)

# Option B: serve it (better for testing)
python -m http.server 8000
# then open http://localhost:8000
```

---

## 📦 Repository structure

| File | Purpose |
|------|---------|
| `index.html` | Self-contained webview (search, filters, dish-of-the-day, recipe detail). |
| `khmer_menu.json` | **The dataset** — `{ meta, recipes[] }`, 1,059 dishes. |
| `khmer_menu.schema.json` | JSON Schema (draft-07) — the data contract. |
| `khmer_data.js` | The dataset wrapped as `window.KHMER_MENU` so the page works offline by double-click. |
| `generate_khmer_menu.py` | Generator — the **source of truth** for the catalog. |
| `fetch_images.py` | Optional: fetch one stock photo per dish-family (Pexels / Unsplash). |

---

## 🧾 Data & schema

The catalog is a single JSON document validated against
[`khmer_menu.schema.json`](./khmer_menu.schema.json). Use it as a dataset or a
read-only API — point your app straight at `khmer_menu.json`.

```jsonc
{
  "meta": {
    "schemaVersion": "1.0",
    "cuisine": "Khmer",
    "count": 1059,
    "categories": ["stir-fry", "soup", "curry", "..."],
    "language": { "primary": "en", "names": ["km", "romanized", "en"] }
  },
  "recipes": [ /* … */ ]
}
```

### Recipe object

```jsonc
{
  "id": "khm-0001",                       // stable unique id
  "slug": "fish-amok",                    // URL-safe slug
  "name": { "km": "អាម៉ុកត្រី", "romanized": "Amok Trey", "en": "Fish Amok" },
  "category": "curry",
  "subcategory": "amok",
  "cuisine": "Khmer",
  "description": "Cambodia's national dish — a silky steamed coconut fish curry…",
  "image": "images/dishes/fish-amok.jpg", // relative path; falls back to placeholder
  "imageFamily": "fish-amok",             // protein variants share one image (~164 families)
  "tags": ["signature", "fish", "steamed", "coconut"],
  "dietary": ["pescatarian", "gluten-free"],
  "spiceLevel": 1,                        // 0–5
  "difficulty": "medium",                 // easy | medium | hard
  "servings": 4,
  "time": { "prepMinutes": 40, "cookMinutes": 25, "totalMinutes": 65 },
  "kroeung": ["lemongrass", "galangal", "turmeric", "…"],   // the Khmer flavour base
  "equipment": ["steamer", "banana leaf cups", "mortar and pestle"],
  "ingredients": [
    { "group": "main", "item": "snakehead fish fillet", "quantity": 500, "unit": "g", "notes": "sliced" }
  ],
  "instructions": [
    { "step": 1, "text": "Pound the kroeung to a smooth paste.", "tip": "Smoothness is everything in amok." }
  ]
}
```

### Field reference

| Field | Type | Notes |
|-------|------|-------|
| `id` | string | `khm-NNNN`, unique & stable. |
| `slug` | string | URL-safe, unique. |
| `name` | object | `{ km, romanized, en }` — `en` required. |
| `category` / `subcategory` | string | Menu category + Khmer technique family (`cha`, `samlor`, `amok`, `kho`, …). |
| `description` | string | One-paragraph intro. |
| `image` / `imageFamily` | string | Relative image path + the shared image group key. |
| `tags` / `dietary` | string[] | `dietary` ∈ `vegetarian, vegan, pescatarian, gluten-free, dairy-free, halal`. |
| `spiceLevel` | int 0–5 | 0 = none, 5 = very hot. |
| `difficulty` | enum | `easy` \| `medium` \| `hard`. |
| `servings` | int | — |
| `time` | object | `prepMinutes`, `cookMinutes`, `totalMinutes`. |
| `kroeung` / `equipment` | string[] | Aromatic paste components + tools. |
| `ingredients[]` | object[] | `{ group, item, quantity?, unit?, notes? }`. |
| `instructions[]` | object[] | `{ step, text, tip? }`. |

**Validate the data** (optional):

```bash
pip install jsonschema
python -c "import json,jsonschema; d=json.load(open('khmer_menu.json',encoding='utf-8')); \
s=json.load(open('khmer_menu.schema.json',encoding='utf-8')); jsonschema.validate(d,s); print('valid')"
```

---

## 🔁 Regenerating the catalog

`khmer_menu.json` and `khmer_data.js` are **build artifacts** — the source of
truth is `generate_khmer_menu.py`. It composes dishes from authentic Khmer
building blocks (`cooking method × aromatic/vegetable style × protein`) plus
hand-written iconic dishes. Output is deterministic.

```bash
python generate_khmer_menu.py     # rewrites khmer_menu.json + khmer_data.js
```

---

## 🖼️ Dish images (optional)

To reduce 1,059 dishes to ~164 images, protein variants of a base dish share one
photo (via `imageFamily`). `fetch_images.py` downloads one stock photo per family.

```bash
# free API key: https://www.pexels.com/api/  or  https://unsplash.com/developers
python fetch_images.py --dry-run                       # preview families + queries
python fetch_images.py --source pexels --key YOUR_KEY  # download (resumable)
```

Images land in `images/dishes/`, with attribution written to
`images/dishes/attribution.json` and `credits.html`. Dishes without a good match
keep the page's emoji placeholder.

---

## 🤝 Contributing — submit more dishes

**We want this catalog to grow well beyond 1,000 dishes.** Authentic Khmer
recipes — regional specialties, family recipes, festival dishes, street food —
are all welcome.

Because the JSON is generated, **don't edit `khmer_menu.json` directly** (it gets
overwritten). Instead, add to `generate_khmer_menu.py`:

- **A one-off named dish** → add a record to the `iconic()` function (hand-written, full recipe).
- **A new family of variations** → add an entry to the matching style list, e.g. `CHA_STYLES`, `SAMLOR_STYLES`, `CURRY_STYLES`, `VEG_PAIRS`, `PROTEINS`, the dessert/drink/snack lists, etc. It will be combined across proteins automatically.

Then run `python generate_khmer_menu.py` and commit the updated artifacts.

**Checklist for a good submission**

- [ ] Trilingual name (Khmer script + romanization + English).
- [ ] Correct `category` and a sensible `subcategory`/technique.
- [ ] Authentic `kroeung` / aromatics where relevant.
- [ ] Real, ordered `instructions` a home cook can follow.
- [ ] `ingredients` with quantities and helpful `notes`.
- [ ] `dietary`, `spiceLevel`, and `difficulty` set honestly.
- [ ] Data still validates against the schema.

Open a Pull Request with a short note on the dish and its region/source. 🇰🇭

---

## 🌐 Deploy (GitHub Pages)

1. **Settings → Pages → Build and deployment → Source:** *Deploy from a branch*.
2. **Branch:** `main` · **Folder:** `/ (root)` → **Save**.
3. The repo must be **public** for free Pages (private needs GitHub Pro).
4. Pages auto-rebuilds on every push to `main`. A `.nojekyll` file ships the assets as-is.

---

## 📄 License & credits

- **Recipe data:** CC-BY-4.0 (recipes are traditional; this catalog is compiled/generated for educational use) — see the `meta.license` field.
- **Dish photos:** courtesy of their photographers via **Pexels / Unsplash**, credited in `credits.html`.

Built with ❤️ for Khmer home cooks.
