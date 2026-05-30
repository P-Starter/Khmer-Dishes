# -*- coding: utf-8 -*-
"""
Khmer Chief — menu catalog generator.

Produces `khmer_menu.json`: a website-ready catalog of 1000+ Cambodian (Khmer)
dishes, each with structured ingredients and step-by-step cooking instructions.

Strategy (how a real Khmer kitchen scales a menu):
  1. Iconic signature dishes are written by hand.
  2. The rest is generated from authentic building blocks:
        cooking method  (Cha, Samlor, Kari/Amok, Aing, Chien, Nhoam, noodles...)
      × aromatic / kroeung style  (lemongrass, ginger, Kampot pepper, kapi...)
      × vegetable pairing  (morning glory, yardlong bean, bitter melon...)
      × protein  (chicken, pork, beef, fish, shrimp, squid, tofu, egg...)
     Each combination is a dish Cambodians actually cook.
  3. Desserts (bong-aem), drinks (teuk krolok) and street snacks (num) round it out.

Run:  python generate_khmer_menu.py
"""

import json
import hashlib
import datetime
import re

OUT_FILE = "khmer_menu.json"
SCHEMA_FILE = "khmer_menu.schema.json"
TARGET = 1000

# --------------------------------------------------------------------------- #
# deterministic pseudo-randomness (stable output across runs)
# --------------------------------------------------------------------------- #
def _h(key: str) -> int:
    return int(hashlib.md5(key.encode("utf-8")).hexdigest(), 16)

def pick(key, options):
    return options[_h(key) % len(options)]

def rng(key, lo, hi):
    return lo + (_h(key) % (hi - lo + 1))

def slugify(s: str) -> str:
    out = []
    for ch in s.lower():
        if ch.isalnum():
            out.append(ch)
        elif ch in " -_/":
            out.append("-")
    slug = "".join(out)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")

def ing(item, qty=None, unit=None, group="main", notes=""):
    d = {"group": group, "item": item}
    if qty is not None:
        d["quantity"] = qty
    if unit is not None:
        d["unit"] = unit
    if notes:
        d["notes"] = notes
    return d

# --------------------------------------------------------------------------- #
# proteins
# --------------------------------------------------------------------------- #
PROTEINS = [
    dict(key="chicken",   km="សាច់មាន់", rom="Sach Moan",   en="Chicken",
         group="meat", prep="cut into bite-sized pieces", cook="until cooked through and no longer pink", min=12),
    dict(key="pork",      km="សាច់ជ្រូក", rom="Sach Chrouk", en="Pork",
         group="meat", prep="cut into thin slices", cook="until cooked through", min=12),
    dict(key="beef",      km="សាច់គោ",   rom="Sach Ko",     en="Beef",
         group="meat", prep="sliced thin against the grain", cook="until just browned but still tender", min=8),
    dict(key="duck",      km="សាច់ទា",   rom="Sach Tia",    en="Duck",
         group="meat", prep="chopped into pieces", cook="until tender", min=25),
    dict(key="frog",      km="កង្កែប",   rom="Kong Kep",    en="Frog",
         group="meat", prep="cleaned and jointed", cook="until tender", min=15),
    dict(key="fish",      km="ត្រី",     rom="Trey",        en="Fish",
         group="seafood", prep="cut into thick fillet slices", cook="until the flesh turns opaque and flakes", min=10),
    dict(key="shrimp",    km="បង្គា",    rom="Bangkea",     en="Shrimp",
         group="seafood", prep="peeled and deveined", cook="until they curl and turn pink", min=5),
    dict(key="squid",     km="មឹក",      rom="Meuk",        en="Squid",
         group="seafood", prep="cleaned and scored into rings", cook="until just opaque (do not overcook)", min=4),
    dict(key="crab",      km="ក្ដាម",    rom="Kdam",        en="Crab",
         group="seafood", prep="cleaned and quartered", cook="until the shells turn bright orange", min=12),
    dict(key="clam",      km="ងាវ",      rom="Ngiev",       en="Clams",
         group="seafood", prep="scrubbed", cook="until the shells open", min=6),
    dict(key="tofu",      km="តៅហ៊ូ",     rom="Taohu",       en="Tofu",
         group="veg", prep="cubed and lightly fried until golden", cook="until heated through", min=6),
    dict(key="egg",       km="ពងមាន់",   rom="Pong Moan",   en="Egg",
         group="veg", prep="lightly beaten", cook="until softly set", min=4),
    dict(key="mushroom",  km="ផ្សិត",    rom="Phset",       en="Mushroom",
         group="veg", prep="torn or sliced", cook="until softened and glossy", min=6),
    dict(key="vegetable", km="បន្លែ",     rom="Bonlae",      en="Mixed Vegetables",
         group="veg", prep="cut into bite-sized pieces", cook="until tender-crisp", min=7),
]
P = {p["key"]: p for p in PROTEINS}
MEAT     = [P[k] for k in ("chicken", "pork", "beef", "duck", "frog")]
SEAFOOD  = [P[k] for k in ("fish", "shrimp", "squid", "crab", "clam")]
VEG      = [P[k] for k in ("tofu", "egg", "mushroom", "vegetable")]
MEAT_SEA = MEAT + SEAFOOD
ALL_PROT = MEAT + SEAFOOD + VEG

# --------------------------------------------------------------------------- #
# common ingredient blocks
# --------------------------------------------------------------------------- #
KROEUNG_YELLOW = [
    ing("lemongrass", 3, "stalks", "kroeung", "tender part, finely sliced"),
    ing("galangal", 1, "thumb", "kroeung", "peeled and sliced"),
    ing("fresh turmeric", 1, "tsp", "kroeung", "or 1 thumb fresh"),
    ing("kaffir lime leaves", 4, "leaves", "kroeung", "de-stemmed"),
    ing("garlic", 4, "cloves", "kroeung"),
    ing("shallots", 3, "whole", "kroeung"),
    ing("dried red chili", 2, "whole", "kroeung", "soaked, optional for heat"),
]
KROEUNG_RED = KROEUNG_YELLOW + [ing("dried red chili", 6, "whole", "kroeung", "soaked, for colour & heat")]

SEASON_BASE = [
    ing("fish sauce (teuk trey)", 2, "tbsp", "seasoning"),
    ing("palm sugar", 1, "tsp", "seasoning"),
    ing("vegetable oil", 2, "tbsp", "seasoning"),
]
COCONUT = [
    ing("coconut milk", 400, "ml", "main"),
    ing("coconut cream", 4, "tbsp", "garnish", "for topping"),
]
RICE_SIDE = ing("steamed jasmine rice", 4, "servings", "serving", "to serve")

def steamed_rice_step(n):
    return {"step": n, "text": "Serve hot with steamed jasmine rice."}

# --------------------------------------------------------------------------- #
# CHA — stir-fries by aromatic / kroeung style
# --------------------------------------------------------------------------- #
CHA_STYLES = [
    dict(key="kreung", rom="Kreung", km="គ្រឿង", en="Lemongrass Kroeung",
         desc="Stir-fried in fragrant yellow lemongrass kroeung — the soul of Khmer cooking.",
         arom="Pound or blend the kroeung — lemongrass, galangal, turmeric, kaffir lime leaf, garlic and shallot — into a fragrant yellow paste.",
         arom_ing=KROEUNG_YELLOW,
         add="Toss in yardlong beans and sweet pepper and stir-fry until tender-crisp.",
         add_ing=[ing("yardlong beans", 100, "g", "veg", "cut in 4 cm lengths"),
                  ing("sweet pepper", 1, "whole", "veg", "sliced")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning")],
         garnish="holy basil and sliced fresh chili", spice=2),
    dict(key="khnhei", rom="Khnhei", km="ខ្ញី", en="Ginger",
         desc="A clean, warming ginger stir-fry — light on aromatics, big on freshness.",
         arom="Smash the garlic and shred a generous thumb of young ginger.",
         arom_ing=[ing("young ginger", 1, "thumb", "kroeung", "julienned"),
                   ing("garlic", 3, "cloves", "kroeung", "smashed")],
         add="Add sliced onion, spring onion and wood-ear mushroom; stir-fry briefly.",
         add_ing=[ing("onion", 1, "half", "veg", "sliced"),
                  ing("spring onion", 2, "stalks", "veg", "cut in 4 cm lengths"),
                  ing("wood-ear mushroom", 20, "g", "veg", "soaked, sliced")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning"),
                 ing("light soy sauce", 1, "tbsp", "seasoning")],
         garnish="ground white pepper and spring onion", spice=1),
    dict(key="marech", rom="Marech Khiew", km="ម្រេចខៀវ", en="Fresh Green Kampot Pepper",
         desc="Stir-fried with whole strands of fresh green Kampot peppercorns — citrusy, aromatic, pleasantly numbing.",
         arom="Smash the garlic and rinse the fresh green peppercorn strands.",
         arom_ing=[ing("fresh green Kampot peppercorns", 3, "tbsp", "kroeung", "on the stalk if possible"),
                   ing("garlic", 4, "cloves", "kroeung", "smashed")],
         add="Add sliced chili and a handful of holy basil.",
         add_ing=[ing("fresh red chili", 2, "whole", "veg", "sliced"),
                  ing("holy basil", 1, "handful", "veg")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning"),
                 ing("light soy sauce", 1, "tbsp", "seasoning")],
         garnish="extra green peppercorns", spice=2),
    dict(key="kdav", rom="Kdav", km="ហឹរ", en="Spicy Holy Basil (Cha Kdav)",
         desc="The fiery 'cha kdav' — pounded chili and garlic with a forest of holy basil.",
         arom="Pound the bird's-eye chili and garlic to a rough paste.",
         arom_ing=[ing("bird's-eye chili", 5, "whole", "kroeung"),
                   ing("garlic", 4, "cloves", "kroeung")],
         add="Add long beans, then pile in holy basil at the end.",
         add_ing=[ing("yardlong beans", 80, "g", "veg", "cut in 4 cm lengths"),
                  ing("holy basil", 1, "large handful", "veg")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning"),
                 ing("dark soy sauce", 1, "tsp", "seasoning")],
         garnish="more holy basil", spice=3),
    dict(key="kapi", rom="Kapi", km="កាពិ", en="Shrimp Paste",
         desc="Deeply savoury stir-fry built on Kampot shrimp paste (kapi).",
         arom="Fry the garlic, then melt in the shrimp paste until aromatic.",
         arom_ing=[ing("shrimp paste (kapi)", 1, "tbsp", "kroeung"),
                   ing("garlic", 4, "cloves", "kroeung", "minced"),
                   ing("lemongrass", 1, "stalk", "kroeung", "minced")],
         add="Add eggplant and chili; stir-fry until the eggplant softens.",
         add_ing=[ing("Thai eggplant", 2, "whole", "veg", "quartered"),
                  ing("fresh red chili", 2, "whole", "veg", "sliced")],
         season=[ing("palm sugar", 2, "tsp", "seasoning", "to balance the kapi")],
         garnish="Thai basil", spice=2),
    dict(key="khtum", rom="Khtum Sor", km="ខ្ទឹមស", en="Garlic & Spring Onion",
         desc="A quick everyday stir-fry — lots of garlic, spring onion and white pepper.",
         arom="Fry the minced garlic in hot oil until pale gold and fragrant.",
         arom_ing=[ing("garlic", 6, "cloves", "kroeung", "minced")],
         add="Add big lengths of spring onion and sliced onion.",
         add_ing=[ing("spring onion", 4, "stalks", "veg", "cut in 5 cm lengths"),
                  ing("onion", 1, "half", "veg", "sliced")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning"),
                 ing("light soy sauce", 1, "tbsp", "seasoning")],
         garnish="ground white pepper", spice=0),
    dict(key="prahok", rom="Prahok", km="ប្រហុក", en="Fermented Fish (Prahok)",
         desc="Earthy and pungent — built on prahok, the cornerstone of Khmer flavour.",
         arom="Fry minced lemongrass and garlic, then stir in strained prahok liquid.",
         arom_ing=[ing("prahok (fermented fish)", 1, "tbsp", "kroeung", "mashed & strained"),
                   ing("lemongrass", 2, "stalks", "kroeung", "minced"),
                   ing("garlic", 4, "cloves", "kroeung", "minced"),
                   ing("kaffir lime leaf", 3, "leaves", "kroeung", "shredded")],
         add="Add sliced chili and pea eggplant.",
         add_ing=[ing("pea eggplant", 50, "g", "veg"),
                  ing("fresh red chili", 2, "whole", "veg", "sliced")],
         season=[ing("palm sugar", 1, "tsp", "seasoning")],
         garnish="shredded kaffir lime leaf", spice=2),
    dict(key="chu_paem", rom="Chu Paem", km="ជូរផ្អែម", en="Sweet & Sour",
         desc="Bright Khmer-Chinese sweet and sour stir-fry with pineapple and tomato.",
         arom="Fry the garlic until fragrant.",
         arom_ing=[ing("garlic", 3, "cloves", "kroeung", "minced")],
         add="Add pineapple, tomato, cucumber and onion.",
         add_ing=[ing("pineapple", 100, "g", "veg", "chunks"),
                  ing("tomato", 1, "whole", "veg", "wedges"),
                  ing("cucumber", 1, "half", "veg", "sliced"),
                  ing("onion", 1, "half", "veg", "wedges")],
         season=[ing("tomato ketchup", 2, "tbsp", "seasoning"),
                 ing("rice vinegar", 1, "tbsp", "seasoning"),
                 ing("palm sugar", 1, "tbsp", "seasoning")],
         garnish="spring onion", spice=1),
    dict(key="kari-powder", rom="Kari", km="ការី", en="Dry Curry-Powder",
         desc="A quick dry stir-fry perfumed with Khmer curry powder, onion and egg.",
         arom="Fry the garlic and onion, then bloom the curry powder in the oil.",
         arom_ing=[ing("garlic", 3, "cloves", "kroeung", "minced"),
                   ing("onion", 1, "whole", "kroeung", "sliced"),
                   ing("curry powder", 1, "tbsp", "kroeung")],
         add="Add celery and beaten egg, tossing until the egg ribbons through.",
         add_ing=[ing("Chinese celery", 2, "stalks", "veg", "cut in 4 cm lengths"),
                  ing("egg", 1, "whole", "veg", "beaten")],
         season=[ing("oyster sauce", 1, "tbsp", "seasoning"),
                 ing("evaporated milk", 2, "tbsp", "seasoning")],
         garnish="spring onion and ground white pepper", spice=1),
    dict(key="tao-jiew", rom="Tao Jiew", km="តៅជ្យូ", en="Fermented Soybean",
         desc="A savoury Khmer-Chinese stir-fry built on salty fermented soybean paste.",
         arom="Fry the garlic and ginger, then stir in the fermented soybean paste.",
         arom_ing=[ing("fermented soybean paste (tao jiew)", 1.5, "tbsp", "kroeung"),
                   ing("garlic", 3, "cloves", "kroeung", "minced"),
                   ing("ginger", 1, "thumb", "kroeung", "julienned")],
         add="Add sliced chili and big lengths of spring onion.",
         add_ing=[ing("spring onion", 3, "stalks", "veg", "cut in 5 cm lengths"),
                  ing("fresh red chili", 2, "whole", "veg", "sliced")],
         season=[ing("palm sugar", 2, "tsp", "seasoning", "to balance the salt")],
         garnish="spring onion", spice=1),
]

def build_cha(style, prot):
    name_en = "Stir-fried {} {}".format(style["en"], prot["en"])
    name_rom = "Cha {} {}".format(style["rom"], prot["rom"])
    name_km = "ឆា{}{}".format(style["km"], prot["km"])
    ingredients = []
    ingredients.append(ing(prot["en"].lower(), 500, "g", "main", prot["prep"]))
    ingredients += style["arom_ing"]
    ingredients += style["add_ing"]
    ingredients += SEASON_BASE + style["season"]
    ingredients.append(RICE_SIDE)
    steps = [
        {"step": 1, "text": style["arom"],
         "tip": "Pounding releases more aroma than blending, but a blender is fine."},
        {"step": 2, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
        {"step": 3, "text": "Heat 2 tbsp oil in a wok over high heat until shimmering."},
        {"step": 4, "text": "Add the aromatics and stir-fry 1–2 minutes until fragrant and the raw smell is gone."},
        {"step": 5, "text": "Add the {} and stir-fry {}, about {} minutes.".format(
            prot["en"].lower(), prot["cook"], prot["min"])},
        {"step": 6, "text": style["add"]},
        {"step": 7, "text": "Season with fish sauce, palm sugar{} and a small splash of water; toss to coat.".format(
            "" if not style["season"] else " and " + ", ".join(s["item"] for s in style["season"]))},
        {"step": 8, "text": "Taste and adjust, then finish with {}.".format(style["garnish"])},
    ]
    steps.append(steamed_rice_step(9))
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="stir-fry", subcategory="cha", description=style["desc"],
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 15, 30), cook=prot["min"] + rng(name_rom + "c", 5, 12),
        tags=["stir-fry", "cha", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["wok", "mortar and pestle"],
        kroeung=[i["item"] for i in style["arom_ing"]],
    )

# --------------------------------------------------------------------------- #
# CHA — stir-fries by vegetable pairing
# --------------------------------------------------------------------------- #
VEG_PAIRS = [
    dict(key="morning-glory", rom="Trakuon", km="ត្រកួន", en="Morning Glory",
         item=ing("morning glory (water spinach)", 1, "bunch", "veg", "cut in 6 cm lengths")),
    dict(key="yardlong-bean", rom="Sandaek Kuo", km="សណ្ដែកគួរ", en="Yardlong Beans",
         item=ing("yardlong beans", 200, "g", "veg", "cut in 4 cm lengths")),
    dict(key="bitter-melon", rom="Mreah", km="ម្រះ", en="Bitter Melon",
         item=ing("bitter melon", 1, "whole", "veg", "deseeded, sliced")),
    dict(key="eggplant", rom="Trab", km="ត្រប់", en="Eggplant",
         item=ing("eggplant", 2, "whole", "veg", "cut into wedges")),
    dict(key="cabbage", rom="Spey Kdaop", km="ស្ពៃក្ដោប", en="Cabbage",
         item=ing("cabbage", 0.25, "head", "veg", "roughly chopped")),
    dict(key="chinese-broccoli", rom="Spey Khiew", km="ស្ពៃខៀវ", en="Chinese Broccoli",
         item=ing("Chinese broccoli (gai lan)", 1, "bunch", "veg", "cut in 5 cm lengths")),
    dict(key="bamboo", rom="Tumpeang", km="ទំពាំង", en="Bamboo Shoot",
         item=ing("bamboo shoot", 200, "g", "veg", "sliced, boiled first")),
    dict(key="banana-flower", rom="Trayong Chek", km="ត្រយោងចេក", en="Banana Blossom",
         item=ing("banana blossom", 1, "whole", "veg", "shredded, soaked in lime water")),
    dict(key="pumpkin", rom="Lpov", km="ល្ពៅ", en="Pumpkin",
         item=ing("pumpkin", 300, "g", "veg", "cut into thin wedges")),
    dict(key="long-bean-sprout", rom="Sandaek Bandos", km="សណ្ដែកបណ្ដុះ", en="Bean Sprouts",
         item=ing("bean sprouts", 150, "g", "veg")),
    dict(key="okra", rom="Bekpoit", km="បែកពោះ", en="Okra",
         item=ing("okra", 150, "g", "veg", "halved lengthwise")),
    dict(key="water-mimosa", rom="Knhong Chruk", km="គ្នុង", en="Water Mimosa",
         item=ing("water mimosa", 1, "bunch", "veg", "cut in 6 cm lengths")),
    dict(key="chayote", rom="Sou", km="ស៊ូ", en="Chayote",
         item=ing("chayote", 2, "whole", "veg", "peeled and sliced")),
    dict(key="snake-gourd", rom="Nonong", km="នោងនោង", en="Snake Gourd",
         item=ing("snake gourd", 1, "whole", "veg", "peeled and sliced")),
    dict(key="ridge-gourd", rom="Ronong", km="រនោង", en="Ridge Gourd (Luffa)",
         item=ing("ridge gourd", 2, "whole", "veg", "peeled and cut into wedges")),
    dict(key="winter-melon", rom="Trasok", km="ត្រសក់", en="Winter Melon",
         item=ing("winter melon", 300, "g", "veg", "peeled and cubed")),
    dict(key="cauliflower", rom="Phka Spey", km="ផ្កាស្ពៃ", en="Cauliflower",
         item=ing("cauliflower", 0.5, "head", "veg", "broken into florets")),
    dict(key="broccoli", rom="Phka Spey Khiew", km="ផ្កាស្ពៃខៀវ", en="Broccoli",
         item=ing("broccoli", 0.5, "head", "veg", "broken into florets")),
    dict(key="choy-sum", rom="Spey Phka", km="ស្ពៃផ្កា", en="Choy Sum",
         item=ing("choy sum", 1, "bunch", "veg", "cut in 5 cm lengths")),
    dict(key="napa-cabbage", rom="Spey Chrok", km="ស្ពៃជ្រក់", en="Napa Cabbage",
         item=ing("napa cabbage", 0.3, "head", "veg", "roughly chopped")),
    dict(key="lotus-stem", rom="Daem Chhouk", km="ដើមឈូក", en="Lotus Stem",
         item=ing("lotus stem", 200, "g", "veg", "peeled and sliced diagonally")),
    dict(key="sweet-potato-leaf", rom="Sloek Damlong", km="ស្លឹកដំឡូង", en="Sweet Potato Leaves",
         item=ing("sweet potato leaves", 1, "bunch", "veg", "tender tips only")),
    dict(key="pumpkin-tips", rom="Tumpeang Lpov", km="ទំពាំងល្ពៅ", en="Pumpkin Vine Tips",
         item=ing("pumpkin vine tips", 1, "bunch", "veg", "peeled and cut")),
    dict(key="mustard-green", rom="Spey Khmao", km="ស្ពៃខ្មៅ", en="Mustard Greens",
         item=ing("mustard greens", 1, "bunch", "veg", "cut in 5 cm lengths")),
]

def build_cha_veg(veg, prot):
    name_en = "Stir-fried {} with {}".format(veg["en"], prot["en"])
    name_rom = "Cha {} {}".format(veg["rom"], prot["rom"])
    name_km = "ឆា{}{}".format(veg["km"], prot["km"])
    ingredients = [
        ing(prot["en"].lower(), 300, "g", "main", prot["prep"]),
        veg["item"],
        ing("garlic", 4, "cloves", "kroeung", "minced"),
        ing("oyster sauce", 1.5, "tbsp", "seasoning"),
    ] + SEASON_BASE + [RICE_SIDE]
    steps = [
        {"step": 1, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
        {"step": 2, "text": "Mince the garlic and have the {} washed and cut.".format(veg["en"].lower())},
        {"step": 3, "text": "Heat 2 tbsp oil in a wok over high heat; fry the garlic until fragrant."},
        {"step": 4, "text": "Add the {} and stir-fry {}, about {} minutes.".format(
            prot["en"].lower(), prot["cook"], prot["min"])},
        {"step": 5, "text": "Add the {} and stir-fry over high heat until tender-crisp.".format(veg["en"].lower()),
         "tip": "Keep the heat high so the vegetable stays bright and never stews."},
        {"step": 6, "text": "Season with oyster sauce, fish sauce and a pinch of palm sugar; toss quickly."},
        steamed_rice_step(7),
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="stir-fry", subcategory="cha-vegetable",
        description="A fast, high-heat home stir-fry of {} with {}.".format(veg["en"].lower(), prot["en"].lower()),
        spice=0, difficulty="easy",
        prep=rng(name_rom + "p", 10, 20), cook=prot["min"] + rng(name_rom + "c", 4, 8),
        tags=["stir-fry", "cha", veg["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["wok"], kroeung=["garlic"],
    )

# --------------------------------------------------------------------------- #
# SAMLOR — soups & stews
# --------------------------------------------------------------------------- #
SAMLOR_STYLES = [
    dict(key="machu-kreung", rom="Samlor Machu Kreung", km="សម្លម្ជូរគ្រឿង", en="Sour Lemongrass Soup",
         desc="The beloved sour-and-aromatic soup built on lemongrass kroeung and tamarind.",
         base="Bring stock to a boil and stir in the lemongrass kroeung.",
         base_ing=KROEUNG_YELLOW + [ing("stock or water", 1.2, "litre", "main")],
         veg=[ing("water mimosa", 1, "bunch", "veg"),
              ing("tomato", 2, "whole", "veg", "wedges"),
              ing("pineapple", 100, "g", "veg", "chunks")],
         sour=[ing("tamarind paste", 2, "tbsp", "seasoning")],
         garnish="rice-paddy herb (ngo om) and sawtooth coriander", spice=1),
    dict(key="korko", rom="Samlor Korko", km="សម្លការគោ", en="Khmer Country Stew",
         desc="The national vegetable stew — a dozen vegetables thickened with toasted ground rice.",
         base="Boil the kroeung in stock with toasted ground rice until aromatic.",
         base_ing=KROEUNG_YELLOW + [ing("stock or water", 1.5, "litre", "main"),
                                    ing("toasted ground rice", 2, "tbsp", "seasoning", "key thickener"),
                                    ing("prahok", 1, "tbsp", "seasoning", "strained")],
         veg=[ing("green papaya", 200, "g", "veg", "cubed"),
              ing("pumpkin", 200, "g", "veg", "cubed"),
              ing("Thai eggplant", 3, "whole", "veg", "quartered"),
              ing("long beans", 100, "g", "veg"),
              ing("moringa leaves", 1, "handful", "veg")],
         sour=[],
         garnish="extra moringa leaves", spice=1),
    dict(key="machu-youn", rom="Samlor Machu Youn", km="សម្លម្ជូរយួន", en="Sour Tamarind Soup",
         desc="A clear, bracingly sour soup with pineapple, tomato and bean sprouts.",
         base="Bring stock to a boil with smashed garlic and lemongrass.",
         base_ing=[ing("stock or water", 1.2, "litre", "main"),
                   ing("lemongrass", 2, "stalks", "kroeung", "bruised"),
                   ing("garlic", 3, "cloves", "kroeung", "smashed")],
         veg=[ing("pineapple", 150, "g", "veg", "chunks"),
              ing("tomato", 2, "whole", "veg", "wedges"),
              ing("bean sprouts", 100, "g", "veg"),
              ing("taro stem", 100, "g", "veg", "peeled, sliced")],
         sour=[ing("tamarind paste", 3, "tbsp", "seasoning")],
         garnish="fried garlic, sawtooth coriander and rice-paddy herb", spice=1),
    dict(key="ktis", rom="Samlor Ktis", km="សម្លខ្ទិះ", en="Coconut Kroeung Soup",
         desc="A rich, coconut-thickened kroeung soup — mellow, fragrant and a little sweet.",
         base="Fry the kroeung in a little coconut cream, then pour in the rest of the coconut milk.",
         base_ing=KROEUNG_RED + COCONUT,
         veg=[ing("Thai eggplant", 3, "whole", "veg", "quartered"),
              ing("yardlong beans", 100, "g", "veg")],
         sour=[],
         garnish="kaffir lime leaf and fresh chili", spice=2),
    dict(key="proher", rom="Samlor Proher", km="សម្លប្រហើរ", en="Aromatic Herb Soup",
         desc="A clear, herb-forward soup fragrant with lemongrass and basil.",
         base="Simmer stock with bruised lemongrass, galangal and kaffir lime leaf.",
         base_ing=[ing("stock or water", 1.2, "litre", "main"),
                   ing("lemongrass", 2, "stalks", "kroeung", "bruised"),
                   ing("galangal", 3, "slices", "kroeung"),
                   ing("kaffir lime leaf", 4, "leaves", "kroeung")],
         veg=[ing("napa cabbage", 200, "g", "veg", "chopped"),
              ing("daikon", 150, "g", "veg", "sliced")],
         sour=[],
         garnish="Asian basil and spring onion", spice=0),
    dict(key="sngor", rom="Sngor Chruok", km="ស្ងោរជ្រក់", en="Hot & Sour Clear Soup",
         desc="A light, tangy clear soup brightened with lime and chili at the table.",
         base="Bring stock to a boil with bruised lemongrass and galangal.",
         base_ing=[ing("stock or water", 1.2, "litre", "main"),
                   ing("lemongrass", 2, "stalks", "kroeung", "bruised"),
                   ing("galangal", 3, "slices", "kroeung")],
         veg=[ing("tomato", 2, "whole", "veg", "wedges"),
              ing("oyster mushroom", 100, "g", "veg"),
              ing("napa cabbage", 150, "g", "veg")],
         sour=[ing("lime juice", 3, "tbsp", "seasoning", "added off the heat")],
         garnish="coriander, chili and a final squeeze of lime", spice=2),
]

def build_samlor(style, prot):
    name_en = "{} with {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    ingredients = [ing(prot["en"].lower(), 400, "g", "main", prot["prep"])]
    ingredients += style["base_ing"] + style["veg"] + style["sour"] + [
        ing("fish sauce", 2, "tbsp", "seasoning"),
        ing("palm sugar", 2, "tsp", "seasoning"),
        RICE_SIDE,
    ]
    steps = [
        {"step": 1, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
        {"step": 2, "text": style["base"],
         "tip": "Bruising or pounding the aromatics first lets them give up more flavour."},
        {"step": 3, "text": "Add the {} and simmer {}, about {} minutes.".format(
            prot["en"].lower(), prot["cook"], prot["min"])},
        {"step": 4, "text": "Add the vegetables ({}) and simmer until just tender.".format(
            ", ".join(v["item"] for v in style["veg"]))},
        {"step": 5, "text": "Season with fish sauce and palm sugar" + (
            ", then balance with " + ", ".join(s["item"] for s in style["sour"]) if style["sour"] else "") + "."},
        {"step": 6, "text": "Taste — it should sing of salty, sweet and sour. Finish with {}.".format(style["garnish"])},
        steamed_rice_step(7),
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="soup", subcategory="samlor", description=style["desc"],
        spice=style["spice"], difficulty="medium",
        prep=rng(name_rom + "p", 20, 35), cook=prot["min"] + rng(name_rom + "c", 10, 20),
        tags=["soup", "samlor", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["soup pot", "mortar and pestle"],
        kroeung=[i["item"] for i in style["base_ing"] if i["group"] == "kroeung"],
    )

# --------------------------------------------------------------------------- #
# CURRY & AMOK
# --------------------------------------------------------------------------- #
CURRY_STYLES = [
    dict(key="amok", rom="Amok", km="អាម៉ុក", en="Steamed Coconut Curry (Amok)",
         desc="Cambodia's signature dish — a silky coconut kroeung mousse steamed in banana leaf.",
         steps_kind="amok", spice=1, diff="medium"),
    dict(key="kari", rom="Kari", km="ការី", en="Khmer Red Curry",
         desc="A fragrant, lightly sweet coconut red curry — eaten with bread or rice noodles.",
         steps_kind="kari", spice=2, diff="medium"),
    dict(key="saraman", rom="Saraman", km="សារ៉ាម៉ាន", en="Saraman Peanut Curry",
         desc="A rich, mild peanut-and-coconut curry of Cham–Khmer heritage, gently spiced.",
         steps_kind="saraman", spice=1, diff="medium"),
    dict(key="char-krohom", rom="Char Krohom", km="ឆាក្រហម", en="Red Kroeung Dry Curry",
         desc="A dry, intensely aromatic red-kroeung curry stir-fried until thick and glossy.",
         steps_kind="char", spice=3, diff="medium"),
    dict(key="kari-khiew", rom="Kari Khiew", km="ការីខៀវ", en="Green Coconut Curry",
         desc="A fresh, herbaceous green-kroeung coconut curry, fragrant with basil.",
         steps_kind="kari", spice=2, diff="medium"),
]

def build_curry(style, prot):
    name_en = "{} {}".format(style["en"], prot["en"]) if style["key"] != "amok" \
        else "{} {}".format(prot["en"], "Amok")
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    base = [ing(prot["en"].lower(), 500, "g", "main", prot["prep"])] + KROEUNG_RED + COCONUT
    base += [ing("fish sauce", 2, "tbsp", "seasoning"), ing("palm sugar", 1, "tbsp", "seasoning")]
    if style["key"] == "amok":
        base += [ing("egg", 1, "whole", "seasoning", "binds the mousse"),
                 ing("banana leaf cups", 4, "whole", "equipment", "or small bowls"),
                 ing("noni or cabbage leaf", 4, "leaves", "veg", "lining the cups"),
                 ing("kaffir lime leaf", 3, "leaves", "garnish", "shredded")]
        steps = [
            {"step": 1, "text": "Pound the red kroeung to a very smooth paste — smoothness is everything in amok."},
            {"step": 2, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
            {"step": 3, "text": "In a bowl, whisk the kroeung with coconut milk, egg, fish sauce and palm sugar until thick and creamy.",
             "tip": "Add the coconut milk a little at a time so the mixture emulsifies."},
            {"step": 4, "text": "Fold in the {} until well coated.".format(prot["en"].lower())},
            {"step": 5, "text": "Line banana-leaf cups with a soft leaf, spoon in the mixture and top with coconut cream."},
            {"step": 6, "text": "Steam over medium heat 20–25 minutes until set like a soft custard."},
            {"step": 7, "text": "Garnish with coconut cream and shredded kaffir lime leaf; serve with rice."},
        ]
    elif style["key"] == "saraman":
        base += [ing("roasted peanuts", 4, "tbsp", "seasoning", "ground"),
                 ing("potato", 2, "whole", "veg", "chunks"),
                 ing("toasted coconut", 2, "tbsp", "seasoning")]
        steps = [
            {"step": 1, "text": "Fry the red kroeung in a little coconut cream until the oil splits and it smells fragrant."},
            {"step": 2, "text": "Stir in the ground roasted peanuts and toasted coconut."},
            {"step": 3, "text": "Add the {} ({}) and seal in the paste.".format(prot["en"].lower(), prot["prep"])},
            {"step": 4, "text": "Pour in the coconut milk and add the potato; simmer gently."},
            {"step": 5, "text": "Simmer {} and the potato is soft, about {} minutes.".format(prot["cook"], prot["min"] + 15)},
            {"step": 6, "text": "Season with fish sauce and palm sugar; it should be mild, nutty and rich."},
            steamed_rice_step(7),
        ]
    elif style["key"] == "kari":
        base += [ing("sweet potato", 1, "whole", "veg", "chunks"),
                 ing("onion", 1, "whole", "veg", "wedges"),
                 ing("curry powder", 1, "tbsp", "seasoning"),
                 ing("baguette", 2, "whole", "serving", "to serve")]
        steps = [
            {"step": 1, "text": "Fry the red kroeung and curry powder in coconut cream until aromatic and the oil splits."},
            {"step": 2, "text": "Add the {} ({}) and brown lightly.".format(prot["en"].lower(), prot["prep"])},
            {"step": 3, "text": "Pour in coconut milk and enough water to cover; add sweet potato and onion."},
            {"step": 4, "text": "Simmer until {} and the vegetables are tender, about {} minutes.".format(prot["cook"], prot["min"] + 15)},
            {"step": 5, "text": "Season with fish sauce and palm sugar."},
            {"step": 6, "text": "Serve hot with crusty baguette or fresh rice noodles (num banh chok)."},
        ]
    else:  # char (dry)
        base += [ing("yardlong beans", 80, "g", "veg"),
                 ing("kaffir lime leaf", 4, "leaves", "garnish", "shredded"),
                 ing("fresh chili", 3, "whole", "veg", "sliced")]
        steps = [
            {"step": 1, "text": "Fry the red kroeung in oil over medium-high heat until deeply fragrant and darkened."},
            {"step": 2, "text": "Add the {} ({}) and stir-fry to coat in the paste.".format(prot["en"].lower(), prot["prep"])},
            {"step": 3, "text": "Add a splash of coconut cream and the long beans; stir-fry until the sauce clings, about {} minutes.".format(prot["min"])},
            {"step": 4, "text": "Season with fish sauce and palm sugar; cook until almost dry and glossy."},
            {"step": 5, "text": "Finish with shredded kaffir lime leaf and sliced chili."},
            steamed_rice_step(6),
        ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="curry", subcategory=style["key"], description=style["desc"],
        spice=style["spice"], difficulty=style["diff"],
        prep=rng(name_rom + "p", 25, 40), cook=prot["min"] + rng(name_rom + "c", 15, 25),
        tags=["curry", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=base, instructions=steps,
        equipment=(["steamer", "banana leaf cups", "mortar and pestle"] if style["key"] == "amok"
                   else ["pot", "mortar and pestle"]),
        kroeung=[i["item"] for i in KROEUNG_RED],
    )

# --------------------------------------------------------------------------- #
# AING / DOT — grilled & roasted
# --------------------------------------------------------------------------- #
GRILL_STYLES = [
    dict(key="aing-kreung", rom="Aing Kreung", km="អាំងគ្រឿង", en="Lemongrass-Marinated Grill",
         marinade="Blend lemongrass kroeung with fish sauce, palm sugar and a little oil into a marinade.",
         m_ing=KROEUNG_YELLOW + [ing("fish sauce", 2, "tbsp", "seasoning"),
                                 ing("palm sugar", 1, "tbsp", "seasoning"),
                                 ing("vegetable oil", 1, "tbsp", "seasoning")],
         dip="Serve with tuk meric — lime juice, salt, black Kampot pepper and chili.",
         spice=1),
    dict(key="dot", rom="Dot", km="ដុត", en="Salt-Roasted",
         marinade="Rub generously with salt, smashed garlic and white pepper.",
         m_ing=[ing("salt", 1, "tbsp", "seasoning"),
                ing("garlic", 4, "cloves", "seasoning", "smashed"),
                ing("white pepper", 1, "tsp", "seasoning")],
         dip="Serve with tuk trey p'aem — sweet-sour fish-sauce dip with chili and peanuts.",
         spice=0),
    dict(key="chakak", rom="Chakak", km="ចាក់ឈ្នាន់", en="Honey-Glazed Skewers",
         marinade="Marinate in honey, soy, garlic and lemongrass, then thread onto skewers.",
         m_ing=[ing("honey", 2, "tbsp", "seasoning"),
                ing("light soy sauce", 2, "tbsp", "seasoning"),
                ing("garlic", 4, "cloves", "seasoning", "minced"),
                ing("lemongrass", 2, "stalks", "seasoning", "minced"),
                ing("bamboo skewers", 8, "whole", "equipment", "soaked")],
         dip="Serve with pickled vegetables and a chili-lime dip.",
         spice=1),
]

def build_grill(style, prot):
    name_en = "Grilled {} {}".format(style["en"].split(" ", 1)[-1] if False else "", prot["en"]).replace("  ", " ").strip()
    name_en = "{} {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    ingredients = [ing(prot["en"].lower(), 600, "g", "main", prot["prep"])] + style["m_ing"]
    ingredients += [ing("lime", 1, "whole", "garnish"), RICE_SIDE]
    steps = [
        {"step": 1, "text": style["marinade"]},
        {"step": 2, "text": "Coat the {} ({}) in the marinade and rest at least 30 minutes (overnight is better).".format(
            prot["en"].lower(), prot["prep"]),
         "tip": "Marinating overnight gives the deepest flavour and colour."},
        {"step": 3, "text": "Light a charcoal grill and let it burn down to glowing embers (or heat a grill pan)."},
        {"step": 4, "text": "Grill the {} over medium coals, turning and basting, {}.".format(prot["en"].lower(), prot["cook"])},
        {"step": 5, "text": style["dip"]},
        {"step": 6, "text": "Serve with steamed rice and fresh herbs and cucumber."},
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="grilled", subcategory=style["key"],
        description="Charcoal-grilled {} — {}".format(prot["en"].lower(), style["en"].lower()) + ".",
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 30, 60), cook=prot["min"] + rng(name_rom + "c", 5, 12),
        tags=["grilled", "aing", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["charcoal grill", "skewers"] if style["key"] == "chakak" else ["charcoal grill"],
        kroeung=[i["item"] for i in style["m_ing"] if i["group"] == "kroeung"],
    )

# --------------------------------------------------------------------------- #
# CHIEN — fried
# --------------------------------------------------------------------------- #
FRY_STYLES = [
    dict(key="chien-sot", rom="Chien", km="ចៀន", en="Crispy Fried",
         desc="Simply fried until golden and crisp, served with a dipping sauce.",
         coat="Pat dry and dust lightly with seasoned rice flour.",
         c_ing=[ing("rice flour", 4, "tbsp", "seasoning"),
                ing("salt", 1, "tsp", "seasoning"),
                ing("white pepper", 0.5, "tsp", "seasoning")],
         finish="Serve with sweet chili sauce or tuk trey p'aem.", spice=0),
    dict(key="chien-teuk-trey", rom="Chien Teuk Trey", km="ចៀនទឹកត្រី", en="Fish-Sauce Glazed Fried",
         desc="Fried crisp, then tossed in a sticky caramelised fish-sauce glaze.",
         coat="Pat dry; no batter needed.",
         c_ing=[ing("fish sauce", 3, "tbsp", "seasoning"),
                ing("palm sugar", 2, "tbsp", "seasoning"),
                ing("garlic", 3, "cloves", "seasoning", "minced")],
         finish="Toss the fried pieces in the caramel until glazed; finish with chili and spring onion.", spice=1),
    dict(key="chien-chu-paem", rom="Chien Chu Paem", km="ចៀនជូរផ្អែម", en="Sweet & Sour Fried",
         desc="Fried crisp and bathed in a bright sweet-and-sour sauce with pineapple.",
         coat="Coat in a light tempura-style batter and fry until crisp.",
         c_ing=[ing("rice flour", 4, "tbsp", "seasoning"),
                ing("cornstarch", 2, "tbsp", "seasoning"),
                ing("pineapple", 100, "g", "veg", "chunks"),
                ing("tomato ketchup", 2, "tbsp", "seasoning"),
                ing("rice vinegar", 2, "tbsp", "seasoning"),
                ing("palm sugar", 2, "tbsp", "seasoning")],
         finish="Pour the warm sweet-and-sour sauce over the fried pieces just before serving.", spice=1),
    dict(key="chien-khnhei", rom="Chien Khnhei", km="ចៀនខ្ញី", en="Crispy Ginger Fried",
         desc="Fried crisp and showered with crisp-fried shredded ginger and garlic.",
         coat="Pat dry and dust with seasoned flour.",
         c_ing=[ing("rice flour", 4, "tbsp", "seasoning"),
                ing("young ginger", 1, "thumb", "seasoning", "finely julienned"),
                ing("garlic", 4, "cloves", "seasoning", "sliced")],
         finish="Crisp the ginger and garlic in the oil and scatter over the top with spring onion.", spice=0),
]

def build_fry(style, prot):
    name_en = "{} {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    ingredients = [ing(prot["en"].lower(), 500, "g", "main", prot["prep"])] + style["c_ing"]
    ingredients += [ing("oil for frying", 500, "ml", "seasoning"), RICE_SIDE]
    steps = [
        {"step": 1, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
        {"step": 2, "text": style["coat"]},
        {"step": 3, "text": "Heat oil to 170°C. Fry the {} {} and crisp.".format(prot["en"].lower(), prot["cook"]),
         "tip": "Fry in small batches so the oil stays hot and the crust stays crisp."},
        {"step": 4, "text": "Drain on a rack."},
        {"step": 5, "text": style["finish"]},
        steamed_rice_step(6),
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="fried", subcategory=style["key"], description=style["desc"],
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 15, 25), cook=prot["min"] + rng(name_rom + "c", 5, 10),
        tags=["fried", "chien", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["wok or deep fryer"], kroeung=[],
    )

# --------------------------------------------------------------------------- #
# NHOAM / PLEAH — salads
# --------------------------------------------------------------------------- #
SALAD_STYLES = [
    dict(key="nhoam", rom="Nhoam", km="ញាំ", en="Khmer Herb Salad",
         desc="A vibrant tossed salad of poached protein, crunchy vegetables and a forest of herbs.",
         veg=[ing("shredded cabbage", 200, "g", "veg"),
              ing("carrot", 1, "whole", "veg", "julienned"),
              ing("Asian basil & mint", 1, "handful", "veg")],
         method="poach", spice=2),
    dict(key="nhoam-svay", rom="Nhoam Svay", km="ញាំស្វាយ", en="Green Mango Salad",
         desc="Tart green mango tossed with protein, chili, and roasted peanuts.",
         veg=[ing("green mango", 2, "whole", "veg", "shredded"),
              ing("shallot", 2, "whole", "veg", "sliced"),
              ing("roasted peanuts", 3, "tbsp", "garnish", "crushed")],
         method="poach", spice=2),
    dict(key="nhoam-trayong", rom="Nhoam Trayong Chek", km="ញាំត្រយោងចេក", en="Banana Blossom Salad",
         desc="Delicately bitter banana blossom with poached protein and a lime dressing.",
         veg=[ing("banana blossom", 1, "whole", "veg", "shredded, soaked in lime water"),
              ing("Asian basil", 1, "handful", "veg"),
              ing("fried shallots", 2, "tbsp", "garnish")],
         method="poach", spice=2),
    dict(key="pleah", rom="Pleah", km="ភ្លៀ", en="Lime-Cured Salad (Ceviche-Style)",
         desc="Thinly sliced protein 'cooked' in lime juice with lemongrass and herbs.",
         veg=[ing("lemongrass", 2, "stalks", "veg", "very finely sliced"),
              ing("shallot", 3, "whole", "veg", "sliced"),
              ing("sawtooth coriander & mint", 1, "handful", "veg")],
         method="cure", spice=3),
    dict(key="nhoam-trayoung", rom="Nhoam Phkar", km="ញាំផ្កា", en="Pomelo & Herb Salad",
         desc="Juicy pomelo segments with poached protein, coconut and herbs.",
         veg=[ing("pomelo", 1, "whole", "veg", "segmented"),
              ing("toasted coconut", 3, "tbsp", "garnish"),
              ing("mint & coriander", 1, "handful", "veg")],
         method="poach", spice=1),
]

def build_salad(style, prot):
    name_en = "{} with {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    dressing = [ing("lime juice", 4, "tbsp", "dressing"),
                ing("fish sauce", 2, "tbsp", "dressing"),
                ing("palm sugar", 2, "tbsp", "dressing"),
                ing("garlic", 2, "cloves", "dressing", "minced"),
                ing("bird's-eye chili", 2, "whole", "dressing", "minced")]
    ingredients = [ing(prot["en"].lower(), 300, "g", "main", prot["prep"])] + style["veg"] + dressing
    if style["method"] == "cure":
        prep_step = {"step": 1, "text": "Slice the {} very thinly and toss with half the lime juice; leave 10 minutes until it turns opaque.".format(prot["en"].lower()),
                     "tip": "Use only the freshest seafood/meat for a lime-cured pleah."}
    else:
        prep_step = {"step": 1, "text": "Poach or grill the {} ({}) until just cooked, then slice thinly.".format(prot["en"].lower(), prot["prep"])}
    steps = [
        prep_step,
        {"step": 2, "text": "Whisk the dressing — lime juice, fish sauce, palm sugar, garlic and chili — until the sugar dissolves."},
        {"step": 3, "text": "Combine the {} with {}.".format(prot["en"].lower(), ", ".join(v["item"] for v in style["veg"]))},
        {"step": 4, "text": "Pour over the dressing and toss well just before serving."},
        {"step": 5, "text": "Pile onto a plate and top with extra herbs, peanuts and fried shallots."},
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="salad", subcategory=style["key"], description=style["desc"],
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 15, 30), cook=rng(name_rom + "c", 0, 10),
        tags=["salad", "nhoam", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["mixing bowl"], kroeung=[],
    )

# --------------------------------------------------------------------------- #
# NOODLES & RICE
# --------------------------------------------------------------------------- #
NOODLE_STYLES = [
    dict(key="kuy-teav", rom="Kuy Teav", km="គុយទាវ", en="Rice Noodle Soup",
         desc="Cambodia's beloved breakfast noodle soup in a clear pork-and-dried-seafood broth.",
         kind="soup", noodle="flat rice noodles"),
    dict(key="mi-cha", rom="Mi Cha", km="មីឆា", en="Stir-fried Egg Noodles",
         desc="Wok-tossed yellow egg noodles with protein, vegetables and a savoury sauce.",
         kind="fried", noodle="fresh egg noodles"),
    dict(key="kuy-teav-cha", rom="Kuy Teav Cha", km="គុយទាវឆា", en="Stir-fried Rice Noodles",
         desc="Wide rice noodles stir-fried over high heat with dark soy and bean sprouts.",
         kind="fried", noodle="wide rice noodles"),
    dict(key="num-banh-chok", rom="Num Banh Chok", km="នំបញ្ចុក", en="Khmer Rice Noodles",
         desc="Fresh fermented rice vermicelli under a lemongrass fish gravy, piled with raw herbs.",
         kind="gravy", noodle="fresh rice vermicelli (num banh chok)"),
    dict(key="ka-tieu", rom="Kao Poun", km="ខាវប៉ុន", en="Coconut Noodle Soup",
         desc="Rice vermicelli in a rich, mildly spiced coconut-kroeung gravy.",
         kind="coconut", noodle="rice vermicelli"),
    dict(key="kuy-teav-kho", rom="Kuy Teav Kho", km="គុយទាវខ", en="Dry Rice Noodles",
         desc="'Dry' kuy teav — noodles tossed in a savoury sauce with the broth served on the side.",
         kind="fried", noodle="flat rice noodles"),
    dict(key="banh-hoy", rom="Banh Hoy", km="បាញ់ហយ", en="Rice Vermicelli Plate",
         desc="Soft rice vermicelli served with grilled protein, herbs and a fish-sauce dressing.",
         kind="fried", noodle="fine rice vermicelli (banh hoy)"),
]

def build_noodle(style, prot):
    name_en = "{} with {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    common = [ing(style["noodle"], 400, "g", "main"),
              ing(prot["en"].lower(), 250, "g", "main", prot["prep"]),
              ing("bean sprouts", 100, "g", "veg"),
              ing("spring onion & coriander", 1, "handful", "garnish"),
              ing("fried garlic oil", 2, "tbsp", "garnish")]
    if style["kind"] == "soup":
        common += [ing("pork or chicken stock", 1.5, "litre", "main"),
                   ing("dried squid or shrimp", 20, "g", "main", "for the broth"),
                   ing("rock sugar", 1, "tsp", "seasoning"),
                   ing("fish sauce", 2, "tbsp", "seasoning")]
        steps = [
            {"step": 1, "text": "Simmer the stock with dried seafood, rock sugar and a little fish sauce for 30 minutes; keep hot.",
             "tip": "Skim the broth often to keep it crystal clear."},
            {"step": 2, "text": "Cook the {} ({}) in the broth until done; slice if needed.".format(prot["en"].lower(), prot["prep"])},
            {"step": 3, "text": "Blanch the noodles and bean sprouts; divide between bowls."},
            {"step": 4, "text": "Top with the {} and ladle over the hot broth.".format(prot["en"].lower())},
            {"step": 5, "text": "Finish with fried garlic oil, spring onion and coriander; serve with lime, chili and herbs on the side."},
        ]
    elif style["kind"] == "fried":
        common += [ing("garlic", 3, "cloves", "kroeung", "minced"),
                   ing("egg", 1, "whole", "main"),
                   ing("Chinese broccoli", 1, "bunch", "veg", "cut in 5 cm lengths"),
                   ing("oyster sauce", 2, "tbsp", "seasoning"),
                   ing("dark soy sauce", 1, "tsp", "seasoning")]
        steps = [
            {"step": 1, "text": "Soak or loosen the noodles so they don't clump."},
            {"step": 2, "text": "Heat a wok screaming hot; fry the garlic, then the {} {}.".format(prot["en"].lower(), prot["cook"])},
            {"step": 3, "text": "Push aside, scramble the egg, then add the noodles and Chinese broccoli."},
            {"step": 4, "text": "Season with oyster sauce, dark soy and a pinch of sugar; toss over high heat until smoky.",
             "tip": "Don't overcrowd — fry in two batches for proper 'wok hei'."},
            {"step": 5, "text": "Add bean sprouts at the end, toss once and plate. Top with herbs and fried garlic oil."},
        ]
    elif style["kind"] == "gravy":
        common += KROEUNG_YELLOW + [ing("coconut milk", 200, "ml", "main"),
                                    ing("grilled fish", 300, "g", "main", "flaked"),
                                    ing("prahok", 1, "tbsp", "seasoning", "strained"),
                                    ing("banana blossom, cucumber, long beans & herbs", 1, "platter", "veg", "raw, to serve")]
        steps = [
            {"step": 1, "text": "Pound the kroeung smooth and simmer in stock with strained prahok."},
            {"step": 2, "text": "Add the flaked grilled fish (and your chosen {}) and the coconut milk; simmer into a fragrant gravy.".format(prot["en"].lower())},
            {"step": 3, "text": "Season with fish sauce and palm sugar to a savoury, slightly sweet balance."},
            {"step": 4, "text": "Loosen the fresh rice vermicelli into nests in each bowl."},
            {"step": 5, "text": "Ladle the warm gravy over and pile high with raw banana blossom, cucumber, long beans and herbs."},
        ]
    else:  # coconut
        common += KROEUNG_RED + [ing("coconut milk", 400, "ml", "main"),
                                 ing("ground roasted peanuts", 2, "tbsp", "seasoning")]
        steps = [
            {"step": 1, "text": "Fry the red kroeung in coconut cream until the oil splits and it is fragrant."},
            {"step": 2, "text": "Add the {} ({}), then the coconut milk and a little stock; simmer into a rich gravy.".format(prot["en"].lower(), prot["prep"])},
            {"step": 3, "text": "Stir in ground peanuts and season with fish sauce and palm sugar."},
            {"step": 4, "text": "Blanch the vermicelli into bowls and ladle over the coconut gravy."},
            {"step": 5, "text": "Top with bean sprouts, herbs and fried garlic oil."},
        ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="noodles", subcategory=style["key"], description=style["desc"],
        spice=2 if style["kind"] in ("gravy", "coconut") else 1, difficulty="medium",
        prep=rng(name_rom + "p", 20, 40), cook=rng(name_rom + "c", 20, 45),
        tags=["noodles", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=common, instructions=steps,
        equipment=["wok"] if style["kind"] == "fried" else ["stock pot"],
        kroeung=[i["item"] for i in common if i.get("group") == "kroeung"],
    )

def build_fried_rice(prot):
    name_en = "Fried Rice with {}".format(prot["en"])
    name_rom = "Bai Cha {}".format(prot["rom"])
    name_km = "បាយឆា{}".format(prot["km"])
    ingredients = [
        ing("day-old cooked jasmine rice", 4, "cups", "main"),
        ing(prot["en"].lower(), 200, "g", "main", prot["prep"]),
        ing("egg", 2, "whole", "main"),
        ing("garlic", 3, "cloves", "kroeung", "minced"),
        ing("onion", 1, "half", "veg", "diced"),
        ing("spring onion", 2, "stalks", "veg", "sliced"),
        ing("light soy sauce", 2, "tbsp", "seasoning"),
        ing("oyster sauce", 1, "tbsp", "seasoning"),
        ing("fish sauce", 1, "tbsp", "seasoning"),
    ]
    steps = [
        {"step": 1, "text": "Use cold, day-old rice and break up any clumps.",
         "tip": "Fresh rice turns mushy — day-old rice fries up separate and light."},
        {"step": 2, "text": "Heat a wok very hot; fry the garlic, then the {} {}.".format(prot["en"].lower(), prot["cook"])},
        {"step": 3, "text": "Push aside and scramble the eggs."},
        {"step": 4, "text": "Add the rice and onion; toss over high heat to coat and heat through."},
        {"step": 5, "text": "Season with soy, oyster and fish sauces; toss until smoky and fragrant."},
        {"step": 6, "text": "Finish with spring onion. Serve with sliced cucumber, lime and chili sauce."},
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="rice", subcategory="bai-cha",
        description="Wok-tossed Khmer fried rice with {}.".format(prot["en"].lower()),
        spice=0, difficulty="easy",
        prep=rng(name_rom + "p", 10, 20), cook=rng(name_rom + "c", 8, 15),
        tags=["rice", "bai-cha", prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["wok"], kroeung=["garlic"],
    )

# --------------------------------------------------------------------------- #
# KHO — caramel braises
# --------------------------------------------------------------------------- #
KHO_STYLES = [
    dict(key="kho", rom="Kho", km="ខ", en="Palm-Sugar Caramel Braise",
         desc="Slow-braised in a sweet-savoury palm-sugar caramel with coconut water.",
         extra=[ing("coconut water", 250, "ml", "main"),
                ing("hard-boiled eggs", 2, "whole", "main", "optional"),
                ing("garlic", 4, "cloves", "kroeung", "smashed")],
         caramel="palm sugar", spice=0),
    dict(key="kho-khmav", rom="Kho Khmav", km="ខខ្មៅ", en="Dark Soy Braise",
         desc="A dark, glossy braise lacquered with dark soy and palm-sugar caramel.",
         extra=[ing("dark soy sauce", 2, "tbsp", "seasoning"),
                ing("star anise", 1, "whole", "seasoning"),
                ing("garlic", 4, "cloves", "kroeung", "smashed")],
         caramel="palm sugar", spice=0),
    dict(key="kho-khnhei", rom="Kho Khnhei", km="ខខ្ញី", en="Ginger Braise",
         desc="Braised with plenty of young ginger until tender and aromatic.",
         extra=[ing("young ginger", 1, "thumb", "kroeung", "julienned"),
                ing("coconut water", 200, "ml", "main"),
                ing("garlic", 3, "cloves", "kroeung", "smashed")],
         caramel="palm sugar", spice=1),
    dict(key="kho-marech", rom="Kho Marech", km="ខម្រេច", en="Black Pepper Braise",
         desc="A peppery caramel braise heavy with cracked Kampot black pepper.",
         extra=[ing("Kampot black pepper", 1, "tbsp", "seasoning", "coarsely cracked"),
                ing("coconut water", 200, "ml", "main"),
                ing("garlic", 4, "cloves", "kroeung", "smashed")],
         caramel="palm sugar", spice=1),
]

def build_kho(style, prot):
    name_en = "{} {}".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    ingredients = [ing(prot["en"].lower(), 500, "g", "main", prot["prep"]),
                   ing("palm sugar", 3, "tbsp", "seasoning", "for the caramel"),
                   ing("fish sauce", 3, "tbsp", "seasoning")]
    ingredients += style["extra"] + [RICE_SIDE]
    steps = [
        {"step": 1, "text": "Melt the palm sugar in a heavy pot until it caramelises to a deep amber.",
         "tip": "Take the caramel just to amber — too dark and it turns bitter."},
        {"step": 2, "text": "Add the smashed garlic and the {} ({}); turn to coat in the caramel.".format(prot["en"].lower(), prot["prep"])},
        {"step": 3, "text": "Add fish sauce and the braising liquid, plus the other aromatics."},
        {"step": 4, "text": "Cover and braise gently until {} and the sauce is syrupy, about {} minutes.".format(prot["cook"], prot["min"] + 20)},
        {"step": 5, "text": "Uncover and reduce until glossy and clinging."},
        steamed_rice_step(6),
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="braised", subcategory="kho", description=style["desc"],
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 10, 20), cook=prot["min"] + rng(name_rom + "c", 20, 35),
        tags=["braised", "kho", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["heavy pot"], kroeung=[],
    )

# --------------------------------------------------------------------------- #
# SAMLOR MACHU — sour soup by main vegetable
# --------------------------------------------------------------------------- #
MACHU_VEG = [
    dict(key="papaya", rom="Lhong", km="ល្ហុង", en="Green Papaya",
         item=ing("green papaya", 300, "g", "veg", "peeled and cubed")),
    dict(key="pineapple", rom="Mnoas", km="ម្នាស់", en="Pineapple",
         item=ing("pineapple", 250, "g", "veg", "chunks")),
    dict(key="taro-stem", rom="Tror Yong", km="ត្រយ៉ូង", en="Taro Stem",
         item=ing("taro stem", 250, "g", "veg", "peeled and sliced")),
    dict(key="banana-flower", rom="Trayong Chek", km="ត្រយោងចេក", en="Banana Blossom",
         item=ing("banana blossom", 1, "whole", "veg", "shredded")),
    dict(key="water-lily", rom="Pka Pruol", km="ផ្ការំពើ", en="Water Lily Stem",
         item=ing("water lily stems", 1, "bunch", "veg", "peeled, cut in 5 cm lengths")),
    dict(key="winter-melon", rom="Trasok", km="ត្រសក់", en="Winter Melon",
         item=ing("winter melon", 300, "g", "veg", "peeled and cubed")),
    dict(key="bamboo", rom="Tumpeang", km="ទំពាំង", en="Bamboo Shoot",
         item=ing("bamboo shoot", 250, "g", "veg", "sliced, pre-boiled")),
    dict(key="lotus-root", rom="Mream Chhouk", km="មើមឈូក", en="Lotus Root",
         item=ing("lotus root", 250, "g", "veg", "sliced")),
    dict(key="snake-gourd", rom="Nonong", km="នោងនោង", en="Snake Gourd",
         item=ing("snake gourd", 1, "whole", "veg", "peeled and sliced")),
    dict(key="morning-glory", rom="Trakuon", km="ត្រកួន", en="Morning Glory",
         item=ing("morning glory", 1, "bunch", "veg", "cut in 6 cm lengths")),
    dict(key="tamarind-leaf", rom="Sloek Ampil", km="ស្លឹកអម្ពិល", en="Young Tamarind Leaves",
         item=ing("young tamarind leaves", 1, "handful", "veg")),
    dict(key="sour-leaf", rom="Sloek Mchu", km="ស្លឹកម្ជូរ", en="Sour Leaf",
         item=ing("sour leaf (sorrel)", 1, "handful", "veg")),
]

def build_machu_veg(veg, prot):
    name_en = "Sour Soup with {} & {}".format(veg["en"], prot["en"])
    name_rom = "Samlor Machu {} {}".format(veg["rom"], prot["rom"])
    name_km = "សម្លម្ជូរ{}{}".format(veg["km"], prot["km"])
    ingredients = [
        ing(prot["en"].lower(), 350, "g", "main", prot["prep"]),
        veg["item"],
        ing("stock or water", 1.2, "litre", "main"),
        ing("lemongrass", 2, "stalks", "kroeung", "bruised"),
        ing("garlic", 3, "cloves", "kroeung", "smashed"),
        ing("tamarind paste", 2, "tbsp", "seasoning"),
        ing("fish sauce", 2, "tbsp", "seasoning"),
        ing("palm sugar", 2, "tsp", "seasoning"),
        ing("sawtooth coriander & rice-paddy herb", 1, "handful", "garnish"),
        RICE_SIDE,
    ]
    steps = [
        {"step": 1, "text": "Bring the stock to a boil with bruised lemongrass and smashed garlic."},
        {"step": 2, "text": "Add the {} ({}) and simmer until almost cooked.".format(prot["en"].lower(), prot["prep"])},
        {"step": 3, "text": "Add the {} and simmer until tender.".format(veg["en"].lower())},
        {"step": 4, "text": "Season with tamarind, fish sauce and palm sugar; balance to a clean sour-salty-sweet.",
         "tip": "Add tamarind gradually and taste — sourness should brighten, not dominate."},
        {"step": 5, "text": "Finish with sawtooth coriander and rice-paddy herb; serve with rice."},
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="soup", subcategory="samlor-machu", description="A bright Khmer sour soup of {} with {}.".format(veg["en"].lower(), prot["en"].lower()),
        spice=1, difficulty="easy",
        prep=rng(name_rom + "p", 15, 30), cook=prot["min"] + rng(name_rom + "c", 10, 20),
        tags=["soup", "samlor", "machu", veg["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["soup pot"], kroeung=["lemongrass"],
    )

# --------------------------------------------------------------------------- #
# CHHNGANH — steamed dishes
# --------------------------------------------------------------------------- #
STEAMED_STYLES = [
    dict(key="khnhei", rom="Chamhoy Khnhei", km="ចំហុយខ្ញី", en="Steamed with Ginger & Spring Onion",
         desc="Gently steamed and finished with hot ginger, spring onion and a soy drizzle.",
         top=[ing("young ginger", 1, "thumb", "garnish", "julienned"),
              ing("spring onion", 3, "stalks", "garnish", "shredded"),
              ing("light soy sauce", 2, "tbsp", "seasoning"),
              ing("coriander", 1, "handful", "garnish")],
         spice=0),
    dict(key="khmav", rom="Chamhoy Tuk Khmav", km="ចំហុយទឹកខ្មៅ", en="Steamed in Black Bean Sauce",
         desc="Steamed over fermented black beans, garlic and chili.",
         top=[ing("fermented black beans", 2, "tbsp", "seasoning", "rinsed"),
              ing("garlic", 4, "cloves", "seasoning", "minced"),
              ing("fresh chili", 2, "whole", "garnish", "sliced")],
         spice=1),
    dict(key="machu", rom="Chamhoy Machu", km="ចំហុយម្ជូរ", en="Steamed with Sour Plum & Lime",
         desc="Steamed with pickled sour plum, lime and chili for a tangy lift.",
         top=[ing("pickled sour plum", 2, "whole", "seasoning"),
              ing("lime juice", 2, "tbsp", "seasoning"),
              ing("fresh chili", 2, "whole", "garnish", "sliced"),
              ing("garlic", 3, "cloves", "seasoning", "minced")],
         spice=2),
]

def build_steamed(style, prot):
    name_en = "{} ({})".format(style["en"], prot["en"])
    name_rom = "{} {}".format(style["rom"], prot["rom"])
    name_km = "{}{}".format(style["km"], prot["km"])
    ingredients = [ing(prot["en"].lower(), 600, "g", "main", prot["prep"])] + style["top"] + [RICE_SIDE]
    steps = [
        {"step": 1, "text": "Prepare the {}: {}.".format(prot["en"].lower(), prot["prep"])},
        {"step": 2, "text": "Arrange on a heatproof plate and scatter over the aromatics."},
        {"step": 3, "text": "Steam over rapidly boiling water {}.".format(prot["cook"]),
         "tip": "Don't over-steam — pull it the moment it is just cooked to keep it tender."},
        {"step": 4, "text": "Drizzle over the sauce, top with the fresh garnish, and serve with rice."},
    ]
    return dict(
        name_km=name_km, name_rom=name_rom, name_en=name_en,
        category="steamed", subcategory="chhnganh", description=style["desc"],
        spice=style["spice"], difficulty="easy",
        prep=rng(name_rom + "p", 10, 20), cook=prot["min"] + rng(name_rom + "c", 4, 12),
        tags=["steamed", "chhnganh", style["key"], prot["key"], prot["group"]],
        dietary=_dietary(prot),
        ingredients=ingredients, instructions=steps,
        equipment=["steamer"], kroeung=[],
    )

# --------------------------------------------------------------------------- #
# DESSERTS, DRINKS, SNACKS
# --------------------------------------------------------------------------- #
STICKY_FILLINGS = [
    ("Mango", "ស្វាយ", "Svay"), ("Durian", "ធុរេន", "Thuren"), ("Jackfruit", "ខ្នុរ", "Khnor"),
    ("Ripe Banana", "ចេកទុំ", "Chek Tum"), ("Taro", "ត្រាវ", "Trav"), ("Red Bean", "សណ្ដែកក្រហម", "Sandaek Krohom"),
    ("Black Bean", "សណ្ដែកខ្មៅ", "Sandaek Khmav"), ("Sweet Corn", "ពោត", "Poat"), ("Pumpkin", "ល្ពៅ", "Lpov"),
    ("Mung Bean", "សណ្ដែកបាយ", "Sandaek Bay"), ("Coconut", "ដូង", "Doung"), ("Egg Custard", "សង់ខ្យា", "Sankhya"),
    ("Toasted Sesame", "ល្ង", "Lng"), ("Black Sticky Rice", "ដំណើបខ្មៅ", "Damnaeb Khmav"),
]

def build_sticky_dessert(name_en, km, rom, idx):
    title_en = "Sweet Sticky Rice with {}".format(name_en)
    title_rom = "Bai Damnaeb {}".format(rom)
    title_km = "បាយដំណើប{}".format(km)
    ingredients = [
        ing("glutinous (sticky) rice", 2, "cups", "main", "soaked overnight"),
        ing("coconut milk", 400, "ml", "main"),
        ing("palm sugar", 4, "tbsp", "seasoning"),
        ing("salt", 0.5, "tsp", "seasoning"),
        ing("pandan leaf", 2, "leaves", "seasoning", "knotted"),
        ing(name_en.lower(), 1, "portion", "main", "to serve"),
    ]
    steps = [
        {"step": 1, "text": "Steam the soaked sticky rice over high heat 25–30 minutes until tender."},
        {"step": 2, "text": "Warm the coconut milk with palm sugar, salt and pandan until the sugar dissolves (do not boil)."},
        {"step": 3, "text": "Fold most of the sweet coconut milk through the hot rice and rest 15 minutes to absorb.",
         "tip": "Keep a little coconut sauce back to spoon over at the end."},
        {"step": 4, "text": "Serve the sticky rice with the {} and the reserved coconut sauce.".format(name_en.lower())},
    ]
    return dict(
        name_km=title_km, name_rom=title_rom, name_en=title_en,
        category="dessert", subcategory="sticky-rice",
        description="Fragrant coconut sticky rice served with {}.".format(name_en.lower()),
        spice=0, difficulty="easy",
        prep=480, cook=rng(title_rom, 30, 45),
        tags=["dessert", "sticky-rice", slugify(name_en)],
        dietary=["vegetarian", "vegan", "gluten-free"],
        ingredients=ingredients, instructions=steps,
        equipment=["steamer"], kroeung=[],
    )

SWEET_SOUP_ITEMS = [
    ("Mung Bean", "សណ្ដែកបាយ", "Sandaek Bay"), ("Taro", "ត្រាវ", "Trav"), ("Lotus Seed", "គ្រាប់ឈូក", "Krob Chhouk"),
    ("Banana & Tapioca", "ចេកខ្ទិះ", "Chek Ktis"), ("Pumpkin", "ល្ពៅ", "Lpov"), ("Sweet Corn", "ពោត", "Poat"),
    ("Palm Fruit", "ត្នោត", "Thnaot"), ("Longan", "មៀន", "Mean"), ("Water Chestnut", "ហែវ", "Heo"),
    ("Black Sticky Rice", "បបរដំណើបខ្មៅ", "Babor Khmav"), ("Sago & Coconut", "សាគូ", "Sakou"),
    ("Job's Tears", "ស្រូវសាលី", "Srov Sali"), ("Sweet Potato", "ដំឡូងជ្វា", "Damlong Chvea"),
    ("Cassava", "ដំឡូងមី", "Damlong Mi"), ("Red Ruby Water Chestnut", "ត្បទ្ទឹម", "Tabotim"),
    ("Sticky Rice Balls", "បាបិន", "Babin"), ("Lotus Seed & Longan", "គ្រាប់ឈូកមៀន", "Krob Chhouk Mean"),
    ("Pearl Sago & Corn", "សាគូពោត", "Sakou Poat"),
]

def build_sweet_soup(name_en, km, rom):
    title_en = "Sweet Coconut Soup with {}".format(name_en)
    title_rom = "Bobor Pongaem {}".format(rom)
    title_km = "បបរផ្អែម{}".format(km)
    ingredients = [
        ing(name_en.lower(), 250, "g", "main", "prepared / soaked as needed"),
        ing("coconut milk", 400, "ml", "main"),
        ing("palm sugar", 5, "tbsp", "seasoning"),
        ing("salt", 0.25, "tsp", "seasoning"),
        ing("pandan leaf", 2, "leaves", "seasoning", "knotted"),
        ing("tapioca pearls", 3, "tbsp", "main", "optional, for body"),
    ]
    steps = [
        {"step": 1, "text": "Simmer the {} in water with pandan until soft.".format(name_en.lower())},
        {"step": 2, "text": "Add palm sugar and a pinch of salt; stir until dissolved."},
        {"step": 3, "text": "Pour in the coconut milk and warm through gently without hard-boiling.",
         "tip": "Boiling can split the coconut milk — keep it at a gentle simmer."},
        {"step": 4, "text": "Serve warm or over ice as a sweet dessert soup (bong-aem)."},
    ]
    return dict(
        name_km=title_km, name_rom=title_rom, name_en=title_en,
        category="dessert", subcategory="sweet-soup",
        description="A warm Khmer sweet soup of {} in pandan-scented coconut milk.".format(name_en.lower()),
        spice=0, difficulty="easy",
        prep=rng(title_rom, 10, 20), cook=rng(title_rom + "c", 20, 40),
        tags=["dessert", "sweet-soup", "bong-aem", slugify(name_en)],
        dietary=["vegetarian", "vegan", "gluten-free"],
        ingredients=ingredients, instructions=steps,
        equipment=["pot"], kroeung=[],
    )

SMOOTHIE_FRUITS = [
    ("Mango", "ស្វាយ", "Svay"), ("Banana", "ចេក", "Chek"), ("Avocado", "ប័រ", "Bo"),
    ("Durian", "ធុរេន", "Thuren"), ("Dragonfruit", "ស្រកានាគ", "Srok Neak"), ("Sapodilla", "ល្មុត", "Lmut"),
    ("Custard Apple", "ទៀប", "Tiep"), ("Jackfruit", "ខ្នុរ", "Khnor"), ("Watermelon", "ឪឡឹក", "Ouluk"),
    ("Pineapple", "ម្នាស់", "Mnoas"), ("Soursop", "ទៀបបារាំង", "Tiep Barang"), ("Longan", "មៀន", "Mean"),
    ("Coconut", "ដូង", "Doung"), ("Papaya", "ល្ហុង", "Lhong"),
    ("Strawberry", "ស្ត្របឺរី", "Strawberry"), ("Guava", "ត្របែក", "Trabek"),
    ("Rambutan", "សាវម៉ាវ", "Sav Mao"), ("Lychee", "គូលែន", "Kulen"),
    ("Passionfruit", "ផ្លែសាវម៉ាវ", "Sao Mao"), ("Mangosteen", "មង្ឃុត", "Mongkhut"),
]

def build_smoothie(name_en, km, rom):
    title_en = "{} Shake".format(name_en)
    title_rom = "Teuk Krolok {}".format(rom)
    title_km = "ទឹកក្រឡុក{}".format(km)
    ingredients = [
        ing("ripe " + name_en.lower(), 1, "cup", "main", "chilled"),
        ing("sweetened condensed milk", 2, "tbsp", "seasoning"),
        ing("crushed ice", 1, "cup", "main"),
        ing("sugar syrup", 1, "tbsp", "seasoning", "to taste"),
        ing("a pinch of salt", 1, "pinch", "seasoning"),
    ]
    steps = [
        {"step": 1, "text": "Add the {}, condensed milk, ice and a little syrup to a blender.".format(name_en.lower())},
        {"step": 2, "text": "Blend until smooth and frothy; taste and adjust sweetness with a pinch of salt.",
         "tip": "A pinch of salt makes tropical fruit taste sweeter and rounder."},
        {"step": 3, "text": "Pour into a tall glass and serve immediately over ice."},
    ]
    return dict(
        name_km=title_km, name_rom=title_rom, name_en=title_en,
        category="drink", subcategory="smoothie",
        description="A creamy Cambodian street-style {} shake.".format(name_en.lower()),
        spice=0, difficulty="easy",
        prep=rng(title_rom, 3, 8), cook=0,
        tags=["drink", "smoothie", "teuk-krolok", slugify(name_en)],
        dietary=["vegetarian", "gluten-free"],
        ingredients=ingredients, instructions=steps,
        equipment=["blender"], kroeung=[],
    )

OTHER_DRINKS = [
    ("Iced Coffee with Condensed Milk", "កាហ្វេទឹកដោះគោ", "Kafe Teuk Dohko",
     ["dark-roast coffee", "sweetened condensed milk", "ice"],
     ["Brew strong coffee using a phin or dripper.", "Stir 2 tbsp condensed milk into the hot coffee.", "Pour over a glass of ice and stir well."]),
    ("Sugarcane Juice", "ទឹកអំពៅ", "Teuk Ampov",
     ["fresh sugarcane", "kumquat or lime", "ice"],
     ["Press the sugarcane through a juicer.", "Squeeze in a kumquat or lime for brightness.", "Serve very cold over ice."]),
    ("Palm Sugar Iced Tea", "តែទឹកត្នោត", "Tae Teuk Thnaot",
     ["black tea", "palm sugar syrup", "ice", "lime"],
     ["Brew strong black tea and cool.", "Sweeten with palm sugar syrup.", "Serve over ice with a squeeze of lime."]),
    ("Young Coconut Water", "ទឹកដូងខ្ចី", "Teuk Doung Khchey",
     ["young coconut", "ice"],
     ["Open a chilled young coconut.", "Pour the water over ice and scrape in the soft flesh.", "Serve immediately."]),
    ("Lime Soda", "ទឹកក្រូចឆ្មារ", "Teuk Krooch Chhmar",
     ["fresh lime", "sugar syrup", "soda water", "salt"],
     ["Squeeze fresh lime into a glass with syrup.", "Add a small pinch of salt.", "Top with soda water and ice."]),
    ("Roasted Rice Tea", "ទឹកអង្ករលីង", "Teuk Angkor Ling",
     ["roasted rice", "pandan", "rock sugar"],
     ["Toast rice until deep golden and fragrant.", "Simmer with pandan and a little rock sugar.", "Strain and serve hot or iced."]),
    ("Tamarind Juice", "ទឹកអម្ពិល", "Teuk Ampil",
     ["tamarind pulp", "sugar", "salt", "ice"],
     ["Soak tamarind pulp in warm water and strain.", "Sweeten and add a pinch of salt.", "Serve cold over ice."]),
    ("Soy Milk", "ទឹកសណ្ដែក", "Teuk Sandaek",
     ["soybeans", "pandan", "sugar"],
     ["Blend soaked soybeans with water and strain.", "Simmer with pandan, skimming foam.", "Sweeten and serve hot or cold."]),
]

def build_other_drink(name_en, km, rom, items, steps_text):
    return dict(
        name_km=km, name_rom=rom, name_en=name_en,
        category="drink", subcategory="beverage",
        description="A classic Cambodian {}.".format(name_en.lower()),
        spice=0, difficulty="easy",
        prep=rng(rom, 3, 10), cook=rng(rom + "c", 0, 15),
        tags=["drink", slugify(name_en)],
        dietary=["vegetarian"],
        ingredients=[ing(x, group="main") for x in items],
        instructions=[{"step": i + 1, "text": t} for i, t in enumerate(steps_text)],
        equipment=[], kroeung=[],
    )

SNACKS = [
    ("Num Pang Pâté", "នំបុ័ងប៉ាតេ", "Num Pang Pate",
     "Cambodian baguette sandwich layered with pâté, pickles, herbs and chili.",
     ["baguette", "pork pâté", "Cambodian pork roll (cha)", "pickled carrot & daikon", "cucumber", "coriander", "chili", "soy sauce"],
     ["Split a crisp baguette and toast lightly.", "Spread with pâté and a swipe of butter.",
      "Layer the sliced pork roll, pickled vegetables and cucumber.", "Top with coriander, chili and a dash of soy; close and serve."]),
    ("Grilled Pork Skewers", "សាច់ជ្រូកអាំង", "Sach Chrouk Aing",
     "Lemongrass-marinated pork skewers grilled over charcoal.",
     ["pork shoulder", "lemongrass", "garlic", "fish sauce", "palm sugar", "honey"],
     ["Marinate sliced pork in lemongrass, garlic, fish sauce, palm sugar and honey.",
      "Thread onto soaked skewers.", "Grill over charcoal, basting, until caramelised.", "Serve with rice or in a baguette."]),
    ("Num Kachay (Chive Cakes)", "នំកុយឆាយ", "Num Kachay",
     "Pan-fried rice-flour cakes stuffed with garlic chives, served with a sweet-sour dip.",
     ["rice flour", "tapioca starch", "garlic chives", "fish sauce dip"],
     ["Make a soft rice-flour batter and steam into rounds with chopped chives.",
      "Pan-fry until crisp and golden on both sides.", "Serve hot with a sweet-sour fish-sauce dip."]),
    ("Num Krok (Coconut Cakes)", "នំគ្រក", "Num Krok",
     "Crispy-bottomed, custardy coconut-rice cakes cooked in a dimpled pan.",
     ["rice flour", "coconut milk", "sugar", "spring onion", "salt"],
     ["Whisk rice flour, coconut milk, a little sugar and salt into a batter.",
      "Heat a num krok pan and oil the wells.", "Fill the wells and cook until the bottoms crisp and tops set.",
      "Top with spring onion; serve warm in pairs."]),
    ("Fried Spring Rolls", "នំចចេវ", "Cha Gio / Nem Chien",
     "Crispy fried rolls filled with pork, glass noodles and vegetables.",
     ["spring roll wrappers", "ground pork", "glass noodles", "carrot", "wood-ear mushroom", "egg"],
     ["Mix the pork, soaked glass noodles, grated carrot and mushroom.",
      "Roll tightly in wrappers, sealing with egg.", "Deep-fry until golden and crisp.",
      "Serve with lettuce, herbs and a sweet-sour dip."]),
    ("Fresh Summer Rolls", "នំចារ", "Nime Chow",
     "Soft rice-paper rolls of pork, shrimp, herbs and vermicelli with peanut dip.",
     ["rice paper", "poached shrimp", "pork", "rice vermicelli", "lettuce & herbs", "peanut dipping sauce"],
     ["Dip rice paper briefly to soften.", "Layer lettuce, herbs, vermicelli, pork and shrimp.",
      "Roll tightly, folding in the sides.", "Serve with a peanut-hoisin dipping sauce."]),
    ("Fried Banana", "ចេកចៀន", "Chek Chien",
     "Batter-fried bananas, crunchy outside and soft within.",
     ["ripe bananas", "rice flour", "sesame seeds", "sugar", "coconut"],
     ["Make a light batter with rice flour, sesame, a little sugar and coconut.",
      "Coat the bananas.", "Deep-fry until deep golden and crisp.", "Drain and serve hot, optionally with palm-sugar syrup."]),
    ("Grilled Sticky Rice in Bamboo", "ក្រឡាន", "Kralan",
     "Sticky rice, black beans and coconut roasted inside a bamboo tube.",
     ["sticky rice", "black-eyed beans", "coconut milk", "grated coconut", "salt", "bamboo tube"],
     ["Mix soaked sticky rice with beans, coconut milk and salt.",
      "Pack loosely into a bamboo tube lined with banana leaf.",
      "Roast over charcoal, turning, until cooked and fragrant.", "Peel back the bamboo and slice to serve."]),
    ("Steamed Banana Cake", "នំចេក", "Num Chek",
     "Soft steamed cake of ripe banana, sticky rice and coconut.",
     ["ripe bananas", "sticky rice", "coconut milk", "sugar", "banana leaf"],
     ["Combine sliced banana with soaked sticky rice, coconut milk and sugar.",
      "Wrap in banana leaf parcels.", "Steam 30–40 minutes until set.", "Cool slightly and serve."]),
    ("Pork & Rice (Bai Sach Chrouk)", "បាយសាច់ជ្រូក", "Bai Sach Chrouk",
     "Cambodia's classic breakfast — grilled marinated pork over broken rice.",
     ["pork", "broken rice", "garlic", "coconut water", "pickles", "clear broth"],
     ["Marinate thinly sliced pork in garlic, coconut water and a little sugar.",
      "Grill over charcoal until caramelised.", "Serve over warm broken rice with pickled vegetables.",
      "Add a small bowl of clear broth on the side."]),
    ("Khmer Custard (Sankhya)", "សង់ខ្យា", "Sankhya",
     "Silky steamed palm-sugar and coconut egg custard.",
     ["eggs", "palm sugar", "coconut milk", "pandan", "salt"],
     ["Whisk eggs with palm sugar until dissolved.", "Stir in coconut milk and pandan extract.",
      "Strain into a dish or hollowed pumpkin.", "Steam gently until just set; chill before serving."]),
    ("Pumpkin Custard (Sankhya Lapov)", "សង់ខ្យាល្ពៅ", "Sankhya Lapov",
     "Coconut-egg custard steamed inside a whole kabocha pumpkin.",
     ["kabocha pumpkin", "eggs", "palm sugar", "coconut milk", "pandan"],
     ["Cut a lid in the pumpkin and scoop out the seeds.", "Whisk eggs, palm sugar, coconut milk and pandan; strain.",
      "Pour the custard into the pumpkin.", "Steam 45–60 minutes until set; cool and slice into wedges."]),
    ("Rice Porridge (Bobor)", "បបរ", "Bobor",
     "Comforting rice porridge, plain or with chicken or fish.",
     ["jasmine rice", "stock", "ginger", "fish sauce", "spring onion", "fried garlic"],
     ["Simmer rice in plenty of stock with ginger until broken down and creamy.",
      "Season with fish sauce and white pepper.", "Add cooked chicken or fish if using.",
      "Top with spring onion, fried garlic and herbs."]),
    ("Num Ansom Chek", "នំអន្សមចេក", "Num Ansom Chek",
     "Banana sticky-rice logs wrapped in banana leaf and boiled — a festival treat.",
     ["sticky rice", "ripe banana", "black beans", "coconut", "banana leaf"],
     ["Season soaked sticky rice with coconut and salt.", "Wrap around a banana and beans in banana leaf into a log.",
      "Tie firmly and boil several hours.", "Cool, unwrap and slice into rounds."]),
    ("Num Kom", "នំគម", "Num Kom",
     "Pyramid-shaped sticky-rice dumplings with sweet coconut or savoury filling.",
     ["glutinous rice flour", "grated coconut", "palm sugar", "banana leaf"],
     ["Make a soft glutinous dough.", "Fill with sweet coconut-palm-sugar paste.",
      "Shape into pyramids and wrap in banana leaf.", "Steam until cooked through."]),
]

def build_snack(name_en, km, rom, desc, items, steps_text):
    cat = "dessert" if any(w in name_en for w in ("Custard", "Banana Cake", "Num Kom", "Ansom")) else "snack"
    return dict(
        name_km=km, name_rom=rom, name_en=name_en,
        category=cat, subcategory="street-food",
        description=desc,
        spice=0, difficulty="medium",
        prep=rng(rom, 15, 40), cook=rng(rom + "c", 10, 60),
        tags=["snack", "street-food", slugify(name_en)],
        dietary=[],
        ingredients=[ing(x, group="main") for x in items],
        instructions=[{"step": i + 1, "text": t} for i, t in enumerate(steps_text)],
        equipment=[], kroeung=[],
    )

# --------------------------------------------------------------------------- #
# ICONIC signature dishes (hand-written)
# --------------------------------------------------------------------------- #
def iconic():
    out = []
    out.append(dict(
        name_km="អាម៉ុកត្រី", name_rom="Amok Trey", name_en="Fish Amok",
        category="curry", subcategory="amok",
        description="Cambodia's national dish: a fragrant, mousse-like steamed fish curry set with coconut and yellow kroeung in banana leaf.",
        description_km="ម្ហូបជាតិកម្ពុជា — ការីត្រីចំហុយក្នុងស្លឹកចេក ឈ្ងុយឈ្ងប់ ផ្សំជាមួយទឹកដូងនិងគ្រឿងលឿង។",
        spice=1, difficulty="medium", prep=40, cook=25,
        tags=["signature", "national-dish", "fish", "steamed", "coconut"],
        dietary=["pescatarian", "gluten-free"],
        ingredients=[
            ing("snakehead or catfish fillet", 500, "g", "main", "sliced"),
        ] + KROEUNG_YELLOW + COCONUT + [
            ing("egg", 1, "whole", "seasoning"),
            ing("fish sauce", 2, "tbsp", "seasoning"),
            ing("palm sugar", 1, "tbsp", "seasoning"),
            ing("noni or young cabbage leaves", 6, "leaves", "veg", "to line the cups"),
            ing("banana leaf cups", 4, "whole", "equipment"),
        ],
        instructions=[
            {"step": 1, "text": "Pound the yellow kroeung to a very smooth paste.",
             "textKm": "បុកគ្រឿងលឿងឱ្យល្អិតៗ។"},
            {"step": 2, "text": "Whisk the kroeung with coconut milk, egg, fish sauce and palm sugar until thick and creamy.",
             "textKm": "កូរគ្រឿងជាមួយទឹកដូង ពងមាន់ ទឹកត្រី និងស្ករត្នោត ឱ្យក្រាស់និងរលោង។",
             "tip": "Add coconut milk gradually so the mixture stays emulsified and silky.",
             "tipKm": "ដាក់ទឹកដូងបន្តិចម្ដងៗ ដើម្បីឱ្យល្បាយនៅរលោងស្អិតគ្នា។"},
            {"step": 3, "text": "Fold the sliced fish through the mixture.",
             "textKm": "បញ្ចូលសាច់ត្រីហាន់ ហើយលាយចូលគ្នាស្រួលបួល។"},
            {"step": 4, "text": "Line banana-leaf cups with soft leaves and fill with the fish mixture.",
             "textKm": "តម្រៀបស្លឹកចេកក្នុងពែង បន្ទាប់មកដាក់សាច់ត្រីដែលលាយរួច។"},
            {"step": 5, "text": "Steam over medium heat 20–25 minutes until set like a soft custard.",
             "textKm": "ចំហុយដោយភ្លើងមធ្យម ២០–២៥ នាទី រហូតទាល់តែកក ដូចសង់ខ្យាទន់។"},
            {"step": 6, "text": "Top with coconut cream and shredded kaffir lime leaf; serve with rice.",
             "textKm": "ដាក់ខ្ទិះដូងពីលើ និងស្លឹកក្រូចសើច។ បរិភោគជាមួយបាយ។"},
        ],
        equipment=["steamer", "banana leaf cups", "mortar and pestle"],
        kroeung=[i["item"] for i in KROEUNG_YELLOW],
    ))
    out.append(dict(
        name_km="ឡុកឡាក់", name_rom="Loc Lac", name_en="Beef Loc Lac",
        category="stir-fry", subcategory="signature",
        description="Cubes of seared marinated beef tossed in a tangy sauce, served over lettuce and tomato with a black-pepper-lime dip.",
        description_km="សាច់គោកាត់ជាដុំ ប្រឡាក់និងឆាជាមួយទឹកជ្រលក់ឆ្ងាញ់ បរិភោគជាមួយសាឡាត់ ប៉េងប៉ោះ និងទឹកម្រេចក្រូចឆ្មារ។",
        spice=1, difficulty="easy", prep=20, cook=10,
        tags=["signature", "beef", "stir-fry"],
        dietary=[],
        ingredients=[
            ing("beef sirloin", 500, "g", "main", "cut into 2 cm cubes"),
            ing("garlic", 4, "cloves", "kroeung", "minced"),
            ing("oyster sauce", 2, "tbsp", "seasoning"),
            ing("light soy sauce", 1, "tbsp", "seasoning"),
            ing("tomato ketchup", 1, "tbsp", "seasoning"),
            ing("palm sugar", 1, "tbsp", "seasoning"),
            ing("lettuce, tomato & onion", 1, "platter", "veg", "to serve"),
            ing("Kampot black pepper", 1, "tbsp", "garnish", "for the dip"),
            ing("lime", 2, "whole", "garnish", "for the dip"),
        ],
        instructions=[
            {"step": 1, "text": "Marinate the beef cubes in garlic, oyster sauce, soy, ketchup and palm sugar for 20 minutes.",
             "textKm": "ប្រឡាក់សាច់គោដុំ ជាមួយខ្ទឹមស ទឹកអយស្ទ័រ ស៊ីអ៊ីវ អ៊ីខាប់ និងស្ករត្នោត រយៈពេល ២០ នាទី។"},
            {"step": 2, "text": "Make the dip: mix lime juice with salt and cracked Kampot black pepper.",
             "textKm": "ធ្វើទឹកជ្រលក់៖ លាយទឹកក្រូចឆ្មារ ជាមួយអំបិល និងម្រេចខ្មៅកំពតបុក។"},
            {"step": 3, "text": "Sear the beef in a screaming-hot wok in batches until browned but still pink inside.",
             "textKm": "ឆាសាច់គោក្នុងខ្ទះក្ដៅខ្លាំង ជាដំណាក់ៗ ឱ្យខាងក្រៅលឿង តែខាងក្នុងនៅផ្កាឈូក។",
             "tip": "High heat and small batches give a good sear without overcooking.",
             "tipKm": "ភ្លើងខ្លាំង និងឆាម្ដងបន្តិចៗ ដើម្បីសាច់គោក្រៀមខាងក្រៅ តែមិនឆ្អិនពេក។"},
            {"step": 4, "text": "Arrange lettuce, tomato and sliced onion on a plate and pile the beef on top.",
             "textKm": "រៀបចានដោយដាក់សាឡាត់ ប៉េងប៉ោះ និងខ្ទឹមបារាំងហាន់ បន្ទាប់មកដាក់សាច់គោពីលើ។"},
            {"step": 5, "text": "Serve with rice, a fried egg, and the black-pepper-lime dip.",
             "textKm": "បរិភោគជាមួយបាយ ពងមាន់ចៀន និងទឹកម្រេចក្រូចឆ្មារ។"},
        ],
        equipment=["wok"], kroeung=["garlic"],
    ))
    out.append(dict(
        name_km="ប្រហុកខ្ទិះ", name_rom="Prahok Ktis", name_en="Prahok Ktis (Pork & Coconut Dip)",
        category="dip", subcategory="signature",
        description="A rich coconut, pork and fermented-fish dip eaten with a big platter of raw vegetables.",
        description_km="ប្រហុកខ្ទិះ — ទឹកជ្រលក់ប្រហុក ផ្សំជាមួយសាច់ជ្រូក និងទឹកដូងក្រាស់ បរិភោគជាមួយបន្លែស្រស់។",
        spice=2, difficulty="medium", prep=20, cook=25,
        tags=["signature", "prahok", "dip", "pork", "coconut"],
        dietary=[],
        ingredients=[
            ing("ground pork", 300, "g", "main"),
            ing("prahok (fermented fish)", 2, "tbsp", "seasoning", "mashed & strained"),
        ] + KROEUNG_RED + COCONUT + [
            ing("palm sugar", 2, "tbsp", "seasoning"),
            ing("Thai eggplant", 3, "whole", "veg", "diced"),
            ing("raw vegetable platter", 1, "platter", "serving", "cucumber, long beans, cabbage, herbs"),
        ],
        instructions=[
            {"step": 1, "text": "Fry the red kroeung in coconut cream until the oil splits and it is fragrant.",
             "textKm": "ឆាគ្រឿងក្រហមជាមួយខ្ទិះដូង រហូតទាល់តែប្រេងបែក ហើយឈ្ងុយ។"},
            {"step": 2, "text": "Add the ground pork and cook until browned.",
             "textKm": "ដាក់សាច់ជ្រូកកិន ហើយឆារហូតទាល់តែលឿង។"},
            {"step": 3, "text": "Stir in the strained prahok and the rest of the coconut milk; simmer to a thick dip.",
             "textKm": "ដាក់ប្រហុកដែលច្រោះរួច និងទឹកដូងដែលនៅសល់។ ដាំឱ្យក្រាស់ជាទឹកជ្រលក់។"},
            {"step": 4, "text": "Add diced eggplant and palm sugar; simmer until thick and glossy.",
             "textKm": "ដាក់ត្រប់ហាន់ និងស្ករត្នោត។ ដាំបន្តរហូតទាល់តែក្រាស់ និងភ្លឺ។"},
            {"step": 5, "text": "Serve warm with a generous platter of raw and blanched vegetables and rice.",
             "textKm": "បរិភោគក្ដៅៗ ជាមួយចានបន្លែស្រស់ បន្លែស្ងោរ និងបាយ។"},
        ],
        equipment=["pan", "mortar and pestle"], kroeung=[i["item"] for i in KROEUNG_RED],
    ))
    out.append(dict(
        name_km="គុយទាវ", name_rom="Kuy Teav Phnom Penh", name_en="Phnom Penh Noodle Soup",
        category="noodles", subcategory="signature",
        description="The iconic morning noodle soup: rice noodles in a clear pork-and-dried-seafood broth with all the toppings.",
        description_km="គុយទាវភ្នំពេញ — ភ្ញាក់ព្រឹកដ៏ល្បី គុយទាវក្នុងទឹកស៊ុបស្អាតពីឆ្អឹងជ្រូកនិងសុីហ្វូដស្ងួត ផ្សំជាមួយគ្រឿងគ្រប់យ៉ាង។",
        spice=1, difficulty="medium", prep=30, cook=90,
        tags=["signature", "noodles", "breakfast", "pork"],
        dietary=[],
        ingredients=[
            ing("pork bones", 1, "kg", "main", "for the broth"),
            ing("dried squid", 30, "g", "main"),
            ing("flat rice noodles", 400, "g", "main"),
            ing("pork mince & sliced pork", 250, "g", "main"),
            ing("shrimp", 8, "whole", "main"),
            ing("bean sprouts", 100, "g", "veg"),
            ing("fried garlic oil", 2, "tbsp", "garnish"),
            ing("spring onion, coriander & lime", 1, "handful", "garnish"),
        ],
        instructions=[
            {"step": 1, "text": "Simmer pork bones and dried squid 1–2 hours into a clear, sweet broth; skim often.",
             "textKm": "ដាំឆ្អឹងជ្រូក និងមឹកស្ងួត ១–២ ម៉ោង ឱ្យបានទឹកស៊ុបស្អាតផ្អែម។ ច្រោះញឹកញាប់។",
             "tip": "A clear broth is the mark of a good kuy teav — never let it boil hard.",
             "tipKm": "ទឹកស៊ុបស្អាត ជាសញ្ញានៃគុយទាវឆ្ងាញ់ — កុំឱ្យទឹកដាំរុះៗខ្លាំង។"},
            {"step": 2, "text": "Season the broth with rock sugar, salt and fish sauce.",
             "textKm": "បន្ថែមរសជាតិដោយស្ករអំពៅ អំបិល និងទឹកត្រី។"},
            {"step": 3, "text": "Cook the pork and shrimp toppings in the broth.",
             "textKm": "ដាំសាច់ជ្រូក និងបង្គា ក្នុងទឹកស៊ុបឱ្យឆ្អិន។"},
            {"step": 4, "text": "Blanch the noodles and bean sprouts; divide between bowls and add toppings.",
             "textKm": "ស្ងោរគុយទាវ និងសណ្ដែកបណ្ដុះ បន្ទាប់មកចែកដាក់ចាន ហើយដាក់គ្រឿងពីលើ។"},
            {"step": 5, "text": "Ladle over the hot broth; finish with fried garlic oil, herbs and lime.",
             "textKm": "ស្នូរទឹកស៊ុបក្ដៅពីលើ ហើយដាក់ប្រេងខ្ទឹមចៀន ស្លឹក និងក្រូចឆ្មារ។"},
        ],
        equipment=["stock pot"], kroeung=[],
    ))
    out.append(dict(
        name_km="សម្លម្ជូរគ្រឿងសាច់គោ", name_rom="Samlor Machu Kreung Sach Ko", name_en="Sour Lemongrass Beef Soup",
        category="soup", subcategory="signature",
        description="A deeply aromatic sour soup of beef and lemongrass kroeung — a Khmer comfort-food classic.",
        description_km="សម្លម្ជូរគ្រឿងសាច់គោ — សម្លម្ជូរឈ្ងុយជាមួយសាច់គោ និងគ្រឿងលឿង ម្ហូបបោះតាមទម្លាប់របស់ខ្មែរ។",
        spice=2, difficulty="medium", prep=30, cook=60,
        tags=["signature", "soup", "beef", "sour"],
        dietary=[],
        ingredients=[ing("beef shank & tripe", 500, "g", "main", "cut into pieces")] + KROEUNG_YELLOW + [
            ing("stock or water", 1.5, "litre", "main"),
            ing("tamarind paste", 3, "tbsp", "seasoning"),
            ing("water mimosa & long beans", 200, "g", "veg"),
            ing("fish sauce", 2, "tbsp", "seasoning"),
            ing("rice-paddy herb & sawtooth coriander", 1, "handful", "garnish"),
        ],
        instructions=[
            {"step": 1, "text": "Simmer the beef until tender, 45–60 minutes.",
             "textKm": "ដាំសាច់គោឱ្យទន់ ៤៥–៦០ នាទី។"},
            {"step": 2, "text": "Stir in the lemongrass kroeung and simmer until fragrant.",
             "textKm": "ដាក់គ្រឿងស្លឹកគ្រៃ ហើយដាំបន្តរហូតទាល់តែឈ្ងុយ។"},
            {"step": 3, "text": "Add tamarind, fish sauce and palm sugar; balance the sour-salty-sweet.",
             "textKm": "បន្ថែមអំពិល ទឹកត្រី និងស្ករត្នោត។ ដាក់ឱ្យរសជាតិសម — ជូរ ប្រៃ ផ្អែម។"},
            {"step": 4, "text": "Add the vegetables and simmer until just tender.",
             "textKm": "ដាក់បន្លែ ហើយដាំរហូតទាល់តែទើបទន់។"},
            {"step": 5, "text": "Finish with rice-paddy herb and sawtooth coriander; serve with rice.",
             "textKm": "ដាក់ម្អមនិងជីអង្កាមពីលើ បរិភោគជាមួយបាយ។"},
        ],
        equipment=["soup pot", "mortar and pestle"], kroeung=[i["item"] for i in KROEUNG_YELLOW],
    ))
    return out

# --------------------------------------------------------------------------- #
# dietary helper
# --------------------------------------------------------------------------- #
def _dietary(prot):
    if prot["group"] == "veg" and prot["key"] != "egg":
        return ["vegetarian"]
    if prot["key"] == "egg":
        return ["vegetarian"]
    if prot["group"] == "seafood":
        return ["pescatarian"]
    return []

# --------------------------------------------------------------------------- #
# Khmer translation layer
# Centralized so the bulk of the catalog gets Khmer text without authoring it
# per-recipe. Coverage is partial — iconic dishes are fully translated inline,
# combinatorial dishes get Khmer descriptions via family lookup and Khmer step
# text via regex phrase rules. Contributions to widen coverage are welcome.
# --------------------------------------------------------------------------- #
KM_DESC_BY_FAMILY = {
    # cha aromatic
    "stir-fry-cha-kreung":      "ឆាជាមួយគ្រឿងលឿង — ភាពឈ្ងុយឈ្ងប់ដ៏ប្រពៃណីរបស់ខ្មែរ។",
    "stir-fry-cha-khnhei":      "ឆាជាមួយខ្ញី — ភាពស្រស់ និងស្រាល។",
    "stir-fry-cha-marech":      "ឆាជាមួយម្រេចខៀវកំពត — ភាពឈ្ងុយ និងក្រអូប។",
    "stir-fry-cha-kdav":        "ឆាហឹរ — ម្ទេស ខ្ទឹមស និងស្លឹកជាក់ច្រើន។",
    "stir-fry-cha-kapi":        "ឆាជាមួយកាពិ — រសជាតិឆ្ងាញ់ ជ្រាលជ្រៅ។",
    "stir-fry-cha-khtum":       "ឆាជាមួយខ្ទឹមស និងស្លឹកខ្ទឹមបារាំង — ម្ហូបប្រចាំថ្ងៃ។",
    "stir-fry-cha-prahok":      "ឆាជាមួយប្រហុក — រសជាតិប្រពៃណីខ្មែរដ៏ខ្លាំង។",
    "stir-fry-cha-chu_paem":    "ឆាជូរផ្អែម — ម្នាស់ ប៉េងប៉ោះ និងការ៉ុត។",
    "stir-fry-cha-kari-powder": "ឆាការី — ម្សៅការី ខ្ទឹមបារាំង និងពងមាន់។",
    "stir-fry-cha-tao-jiew":    "ឆាជាមួយតៅជ្យូ — រសជាតិប្រៃ ស្ទីលខ្មែរ-ចិន។",
    # samlor
    "soup-samlor-machu-kreung": "សម្លម្ជូរគ្រឿង — សម្លម្ជូរឈ្ងុយ ផ្សំជាមួយគ្រឿងលឿង។",
    "soup-samlor-korko":        "សម្លការ — សម្លប្រពៃណីខ្មែរ ផ្សំជាមួយបន្លែច្រើនយ៉ាង។",
    "soup-samlor-machu-youn":   "សម្លម្ជូរយួន — ស្រាល ត្រជាក់ និងរសជូរច្បាស់។",
    "soup-samlor-ktis":         "សម្លខ្ទិះ — ទឹកដូងក្រាស់ ឈ្ងុយ និងផ្អែមបន្តិច។",
    "soup-samlor-proher":       "សម្លប្រហើរ — ស្រាល ឈ្ងុយក្រអូបនៃស្លឹក។",
    "soup-samlor-sngor":        "ស្ងោរជ្រក់ — ស្រាល ជូរ ត្រជាក់ ដោយទឹកក្រូចឆ្មារ។",
    # curry
    "curry-amok":         "ការីអាម៉ុក — ការីចំហុយក្នុងស្លឹកចេក ផ្សំទឹកដូងនិងគ្រឿងលឿង។",
    "curry-kari":         "ការីក្រហមខ្មែរ — ឈ្ងុយ ផ្អែមបន្តិច បរិភោគជាមួយនំបុ័ងឬនំបញ្ចុក។",
    "curry-saraman":      "ការីសារាម៉ាន់ — ការីសណ្ដែកដី ស្រាល និងផ្អែម។",
    "curry-char-krohom":  "ឆាការីក្រហម — ការីក្រហមឈ្ងុយ ឆាស្ងួត។",
    "curry-kari-khiew":   "ការីខៀវ — ការីបៃតង ស្រស់ និងឈ្ងុយ។",
    # grilled
    "grilled-aing-aing-kreung": "អាំងជាមួយគ្រឿង — ប្រឡាក់ឱ្យឈ្ងុយ ហើយអាំងលើភ្លើងធ្យូង។",
    "grilled-aing-dot":         "ដុតអំបិល — ដុតលើភ្លើងធ្យូងរហូតក្រអូប។",
    "grilled-aing-chakak":      "ចាក់ឈ្នាន់ — ឈ្នាន់សាច់ ប្រឡាក់ជាមួយទឹកឃ្មុំ ហើយអាំង។",
    # fried
    "fried-chien-chien-sot":       "ចៀនស្ងួត — ក្រៀម និងឆ្ងាញ់។",
    "fried-chien-chien-teuk-trey": "ចៀនទឹកត្រី — លាបទឹកត្រី និងស្ករត្នោត។",
    "fried-chien-chien-chu-paem":  "ចៀនជូរផ្អែម — ផ្សំជាមួយម្នាស់ និងទឹកជូរផ្អែម។",
    "fried-chien-chien-khnhei":    "ចៀនខ្ញី — បាញ់ខ្ញី និងខ្ទឹមហើយក្រៀម។",
    # salad
    "salad-nhoam-nhoam":           "ញាំខ្មែរ — សាច់និងបន្លែស្រស់ ផ្សំជាមួយទឹកជ្រលក់។",
    "salad-nhoam-nhoam-svay":      "ញាំស្វាយ — ស្វាយខ្ចីជូរ ម្ទេស និងសណ្ដែកដី។",
    "salad-nhoam-nhoam-trayong":   "ញាំត្រយោងចេក — ត្រយោងចេក ផ្សំជាមួយទឹកក្រូចឆ្មារ។",
    "salad-nhoam-pleah":           "ភ្លៀ — សាច់ស្រស់ មុជទឹកក្រូចឆ្មារ បៀបឆាសុីវី។",
    "salad-nhoam-nhoam-trayoung":  "ញាំក្រូចថ្លុង — ផ្អែម ត្រជាក់ និងស្រស់។",
    # noodles
    "noodles-kuy-teav":      "គុយទាវ — ភ្ញាក់ព្រឹកដ៏ល្បីរបស់ខ្មែរ។",
    "noodles-mi-cha":        "មីឆា — មីពណ៌លឿង ឆាជាមួយសាច់និងបន្លែ។",
    "noodles-kuy-teav-cha":  "គុយទាវឆា — ឆាលើភ្លើងខ្លាំង ផ្សំជាមួយស៊ីអ៊ីវខ្មៅ។",
    "noodles-num-banh-chok": "នំបញ្ចុក — នំបញ្ចុកស្រស់ ផ្សំជាមួយទឹកគ្រឿង និងបន្លែ។",
    "noodles-ka-tieu":       "ខាវប៉ុន — នំបញ្ចុក ផ្សំជាមួយទឹកដូងគ្រឿងក្រហម។",
    "noodles-kuy-teav-kho":  "គុយទាវខ — គុយទាវខ្លាប់ ផ្សំជាមួយទឹកជ្រលក់។",
    "noodles-banh-hoy":      "បាញ់ហយ — នំបញ្ចុកស្រស់ ផ្សំជាមួយសាច់អាំង។",
    # kho (caramel braise)
    "braised-kho-kho":        "ខ — ឆ្ងាញ់ផ្អែម ផ្សំជាមួយស្ករត្នោត និងទឹកដូងខ្ចី។",
    "braised-kho-kho-khmav":  "ខខ្មៅ — លាបជាមួយស៊ីអ៊ីវខ្មៅ និងស្ករត្នោត។",
    "braised-kho-kho-khnhei": "ខខ្ញី — ផ្សំជាមួយខ្ញី ឱ្យទន់ និងឈ្ងុយ។",
    "braised-kho-kho-marech": "ខម្រេច — ផ្សំជាមួយម្រេចកំពត។",
    # steamed
    "steamed-chhnganh-khnhei": "ចំហុយជាមួយខ្ញី — ស្រស់ និងស្រាល។",
    "steamed-chhnganh-khmav":  "ចំហុយជាមួយទឹកខ្មៅ — សណ្ដែកខ្មៅ ខ្ទឹមស និងម្ទេស។",
    "steamed-chhnganh-machu":  "ចំហុយម្ជូរ — ផ្លែឈើជូរ និងទឹកក្រូចឆ្មារ។",
    # rice
    "rice-bai-cha": "បាយឆា — ឆាក្ដៅជាមួយសាច់ បន្លែ និងពងមាន់។",
    # other drinks (hand-written, not smoothies)
    "drink-iced-coffee-with-condensed-milk": "កាហ្វេទឹកដោះគោ — កាហ្វេក្ដៅខ្លាំង ផ្សំជាមួយទឹកដោះគោផ្អែម ហើយចាក់លើទឹកកក។",
    "drink-sugarcane-juice":                 "ទឹកអំពៅ — ស្រស់ត្រជាក់ ផ្អែមធម្មជាតិ ផ្សំជាមួយក្រូចសើច។",
    "drink-palm-sugar-iced-tea":             "តែទឹកត្នោត — តែខ្មៅ ផ្អែមដោយស្ករត្នោត ផ្សំទឹកក្រូចឆ្មារ។",
    "drink-young-coconut-water":             "ទឹកដូងខ្ចី — ស្រស់ ត្រជាក់ និងផ្អែមធម្មជាតិ។",
    "drink-lime-soda":                       "ទឹកក្រូចឆ្មារសូដា — ស្រស់ ត្រជាក់ ផ្សំអំបិលបន្តិច។",
    "drink-roasted-rice-tea":                "តែអង្ករលីង — អង្ករលីង ផ្សំជាមួយស្លឹកតើយ និងស្ករអំពៅ។",
    "drink-tamarind-juice":                  "ទឹកអម្ពិល — ផ្អែម ជូរ ត្រជាក់ លាយជាមួយស្ករ និងអំបិលបន្តិច។",
    "drink-soy-milk":                        "ទឹកសណ្ដែក — ទឹកសណ្ដែកសៀង ផ្សំជាមួយស្លឹកតើយ ផ្អែមៗ បរិភោគក្ដៅឬត្រជាក់។",
    # snacks / street food (hand-written)
    "snack-street-food-num-pang-pâté":                       "នំបុ័ងប៉ាតេ — នំបុ័ងខ្មែរ លាបប៉ាតេ ផ្សំសាច់ បន្លែជ្រក់ និងម្ទេស។",
    "snack-street-food-grilled-pork-skewers":                "សាច់ជ្រូកអាំង — សាច់ជ្រូកប្រឡាក់ស្លឹកគ្រៃ អាំងលើភ្លើងធ្យូង។",
    "snack-street-food-num-kachay-chive-cakes":              "នំកុយឆាយ — នំម្សៅអង្ករ ផ្ទុកស្លឹកគុយឆាយ បរិភោគជាមួយទឹកជ្រលក់ជូរផ្អែម។",
    "snack-street-food-num-krok-coconut-cakes":              "នំគ្រក — នំទឹកដូងស្រួយ ខាងក្នុងទន់ ដុតក្នុងថាសសម្បក។",
    "snack-street-food-fried-spring-rolls":                  "នំចចេវ — នំចៀនស្រួយ ផ្ទុកសាច់ជ្រូក មីស និងបន្លែ។",
    "snack-street-food-fresh-summer-rolls":                  "នំចារ — នំខ្ចប់ស្រួយ ផ្ទុកសាច់ បង្គា និងបន្លែស្រស់។",
    "snack-street-food-fried-banana":                        "ចេកចៀន — ចេកចៀន ខាងក្រៅស្រួយ ខាងក្នុងទន់។",
    "snack-street-food-grilled-sticky-rice-in-bamboo":       "ក្រឡាន — បាយដំណើប សណ្ដែក និងទឹកដូង ដុតក្នុងបំពង់ឫស្សី។",
    "snack-street-food-steamed-banana-cake":                 "នំចេក — នំចំហុយ ផ្សំជាមួយចេក បាយដំណើប និងទឹកដូង។",
    "snack-street-food-pork-rice-bai-sach-chrouk":           "បាយសាច់ជ្រូក — ភ្ញាក់ព្រឹកដ៏ល្បី សាច់ជ្រូកអាំងលើបាយចំការ។",
    "snack-street-food-khmer-custard-sankhya":               "សង់ខ្យា — សង់ខ្យាស្ករត្នោត និងទឹកដូងចំហុយ។",
    "snack-street-food-pumpkin-custard-sankhya-lapov":       "សង់ខ្យាល្ពៅ — សង់ខ្យាចំហុយក្នុងផ្លែល្ពៅ។",
    "snack-street-food-rice-porridge-bobor":                 "បបរ — បបរស្រូវឆ្អិន ផ្សំជាមួយសាច់ ឬ ត្រី បរិភោគក្ដៅៗ។",
    "snack-street-food-num-ansom-chek":                      "នំអន្សមចេក — បាយដំណើប ផ្សំជាមួយចេក រុំស្លឹកចេក ហើយស្ងោរ។",
    "snack-street-food-num-kom":                             "នំគម — នំដំណើបរូបពីរ៉ាមីត ផ្ទុកសណ្ដែកផ្អែម រុំស្លឹកចេក ហើយចំហុយ។",
}

# English-lowercase → Khmer lookups used by phrase rules
_KM_PROT_EN = {p["en"].lower(): p["km"] for p in PROTEINS}
_KM_PROT_EN["mixed vegetables"] = "បន្លែ"
_KM_PROT_EN["clams"] = "ងាវ"

_KM_VEG_EN = {v["en"].lower(): v["km"] for v in VEG_PAIRS}
_KM_VEG_EN.update({v["en"].lower(): v["km"] for v in MACHU_VEG})

_KM_FRUIT_EN   = {n.lower(): km for n, km, _ in SMOOTHIE_FRUITS}
_KM_FILLING_EN = {n.lower(): km for n, km, _ in STICKY_FILLINGS}
_KM_FILLING_EN.update({n.lower(): km for n, km, _ in SWEET_SOUP_ITEMS})

KM_PREP = {
    "cut into bite-sized pieces":            "កាត់ជាដុំៗតូច",
    "cut into thin slices":                  "ហាន់ជាបន្ទះស្ដើង",
    "sliced thin against the grain":         "ហាន់ស្ដើងបញ្ច្រាសខ្សែ",
    "chopped into pieces":                   "កាត់ជាដុំៗ",
    "cleaned and jointed":                   "សម្អាត ហើយកាត់តាមសន្លាក់",
    "cut into thick fillet slices":          "ហាន់ជាបន្ទះក្រាស់",
    "peeled and deveined":                   "ចេញសំបក និងសរសៃ",
    "cleaned and scored into rings":         "សម្អាត ហើយហាន់ជាកង់",
    "cleaned and quartered":                 "សម្អាត ហើយកាត់ជា ៤",
    "scrubbed":                              "សម្អាតសំបក",
    "cubed and lightly fried until golden":  "ហាន់ជាគូប ហើយចៀនបន្តិចឱ្យលឿង",
    "lightly beaten":                        "វាយបន្តិច",
    "torn or sliced":                        "កាត់ ឬ ហាន់",
}

KM_COOK = {
    "until cooked through and no longer pink": "រហូតទាល់តែឆ្អិន ហើយបាត់ពណ៌ផ្កាឈូក",
    "until cooked through":                    "រហូតទាល់តែឆ្អិន",
    "until just browned but still tender":     "រហូតទាល់តែលឿងស្រាល តែនៅទន់",
    "until tender":                            "រហូតទាល់តែទន់",
    "until the flesh turns opaque and flakes": "រហូតទាល់តែសាច់ត្រីពណ៌ស និងបែកជាដុំៗ",
    "until they curl and turn pink":           "រហូតទាល់តែបង្គាក្រឡុំ និងមានពណ៌ផ្កាឈូក",
    "until just opaque (do not overcook)":     "រហូតទាល់តែទើបឆ្អិន (កុំឆ្អិនពេក)",
    "until the shells turn bright orange":     "រហូតទាល់តែសំបកក្ដាមមានពណ៌ទឹកក្រូច",
    "until the shells open":                   "រហូតទាល់តែសំបករបោះ",
    "until heated through":                    "រហូតទាល់តែក្ដៅ",
    "until softly set":                        "រហូតទាល់តែទន់ ហើយកក",
    "until softened and glossy":               "រហូតទាល់តែទន់ និងភ្លឺ",
    "until tender-crisp":                      "រហូតទាល់តែទន់និងក្រៀម",
}

def _km_prot(s):    return _KM_PROT_EN.get(s.lower(), s)
def _km_veg(s):     return _KM_VEG_EN.get(s.lower(), s)
def _km_prep(s):    return KM_PREP.get(s.lower(), s)
def _km_cook(s):    return KM_COOK.get(s.lower(), s)
def _km_fruit(s):   return _KM_FRUIT_EN.get(s.lower(), s)
def _km_filling(s): return _KM_FILLING_EN.get(s.lower(), s)

# Regex phrase → Khmer template. Applied to description AND each step text.
PHRASE_RULES = [
    # --- parameterized descriptions ---
    (re.compile(r"^A fast, high-heat home stir-fry of (.+?) with (.+?)\.$"),
     lambda m: "ម្ហូបឆាដ៏លឿនជាមួយ" + _km_veg(m.group(1)) + " និង" + _km_prot(m.group(2)) + "។"),
    (re.compile(r"^A bright Khmer sour soup of (.+?) with (.+?)\.$"),
     lambda m: "សម្លម្ជូរស្រស់ ផ្សំជាមួយ" + _km_veg(m.group(1)) + " និង" + _km_prot(m.group(2)) + "។"),
    (re.compile(r"^Fragrant coconut sticky rice served with (.+?)\.$"),
     lambda m: "បាយដំណើបទឹកដូងក្រអូប ផ្សំជាមួយ" + _km_filling(m.group(1)) + "។"),
    (re.compile(r"^A warm Khmer sweet soup of (.+?) in pandan-scented coconut milk\.$"),
     lambda m: "បបរផ្អែម" + _km_filling(m.group(1)) + " ក្នុងទឹកដូងស្លឹកតើយ។"),
    (re.compile(r"^A creamy Cambodian street-style (.+?) shake\.$"),
     lambda m: "ទឹកក្រឡុក" + _km_fruit(m.group(1)) + " ស្ទីលខ្មែរ។"),

    # --- common cooking step phrases ---
    (re.compile(r"^Prepare the (.+?): (.+?)\.$"),
     lambda m: "រៀបចំ" + _km_prot(m.group(1)) + "៖ " + _km_prep(m.group(2)) + "។"),
    (re.compile(r"^Heat 2 tbsp oil in a wok over high heat[^.]*\.$"),
     lambda m: "ដាក់ប្រេង ២ ស្លាបព្រាក្នុងខ្ទះ ហើយដុំឱ្យក្ដៅខ្លាំង។"),
    (re.compile(r"^Add the aromatics and stir-fry 1–2 minutes until fragrant.*$"),
     lambda m: "ដាក់គ្រឿងផ្សំ ហើយឆា ១–២ នាទី រហូតទាល់តែឈ្ងុយ និងបាត់ក្លិនឆៅ។"),
    (re.compile(r"^Add the (.+?) and stir-fry (.+?), about (\d+) minutes\.$"),
     lambda m: "ដាក់" + _km_prot(m.group(1)) + " ហើយឆា " + _km_cook(m.group(2)) + " ប្រហែល " + m.group(3) + " នាទី។"),
    (re.compile(r"^Add the (.+?) and simmer (.+?), about (\d+) minutes\.$"),
     lambda m: "ដាក់" + _km_prot(m.group(1)) + " ហើយដាំ " + _km_cook(m.group(2)) + " ប្រហែល " + m.group(3) + " នាទី។"),
    (re.compile(r"^Season with fish sauce, palm sugar and a small splash of water.*$"),
     lambda m: "បន្ថែមទឹកត្រី ស្ករត្នោត និងទឹកបន្តិច។ កូរឱ្យសម។"),
    (re.compile(r"^Season with fish sauce and palm sugar.*$"),
     lambda m: "បន្ថែមទឹកត្រី និងស្ករត្នោត។"),
    (re.compile(r"^Serve hot with steamed jasmine rice\.$"),
     lambda m: "បរិភោគជាមួយបាយក្ដៅ។"),
    (re.compile(r"^Bring the stock to a boil with bruised lemongrass and smashed garlic\.$"),
     lambda m: "ដាំទឹកស៊ុបជាមួយស្លឹកគ្រៃបុក និងខ្ទឹមសបុក។"),
    (re.compile(r"^Mince the garlic and have the (.+?) washed and cut\.$"),
     lambda m: "កិនខ្ទឹមស ហើយលាង " + _km_veg(m.group(1)) + " ឱ្យស្អាតហើយកាត់រួច។"),
    (re.compile(r"^Add the (.+?) and stir-fry over high heat until tender-crisp\.$"),
     lambda m: "ដាក់" + _km_veg(m.group(1)) + " ហើយឆាលើភ្លើងខ្លាំង រហូតទាល់តែទន់និងក្រៀម។"),
]

def _apply_km(record):
    """Populate Khmer fields where translations are available (in-place)."""
    if "descriptionKm" not in record:
        fam = record.get("imageFamily", "")
        if fam in KM_DESC_BY_FAMILY:
            record["descriptionKm"] = KM_DESC_BY_FAMILY[fam]
    if "descriptionKm" not in record:
        d = record.get("description", "")
        for pat, rep in PHRASE_RULES:
            m = pat.match(d)
            if m:
                try:
                    record["descriptionKm"] = rep(m)
                except Exception:
                    pass
                break
    for step in record.get("instructions", []):
        if "textKm" in step:
            continue
        t = step.get("text", "")
        for pat, rep in PHRASE_RULES:
            m = pat.match(t)
            if m:
                try:
                    step["textKm"] = rep(m)
                except Exception:
                    pass
                break

# --------------------------------------------------------------------------- #
# assemble
# --------------------------------------------------------------------------- #
def generate():
    recipes = []

    # iconic first
    recipes += iconic()

    # cha by aromatic style
    for style in CHA_STYLES:
        for prot in ALL_PROT:
            recipes.append(build_cha(style, prot))
    # cha by vegetable
    for veg in VEG_PAIRS:
        for prot in MEAT_SEA + [P["tofu"], P["egg"]]:
            recipes.append(build_cha_veg(veg, prot))
    # samlor
    for style in SAMLOR_STYLES:
        for prot in MEAT_SEA + [P["tofu"]]:
            recipes.append(build_samlor(style, prot))
    # curry & amok
    for style in CURRY_STYLES:
        for prot in MEAT_SEA + [P["tofu"], P["vegetable"]]:
            recipes.append(build_curry(style, prot))
    # grilled
    for style in GRILL_STYLES:
        for prot in MEAT_SEA + [P["tofu"]]:
            recipes.append(build_grill(style, prot))
    # fried
    for style in FRY_STYLES:
        for prot in MEAT_SEA + [P["tofu"]]:
            recipes.append(build_fry(style, prot))
    # salads
    for style in SALAD_STYLES:
        prots = SEAFOOD if style["method"] == "cure" else (MEAT_SEA + [P["tofu"]])
        for prot in prots:
            recipes.append(build_salad(style, prot))
    # noodles
    for style in NOODLE_STYLES:
        for prot in MEAT_SEA + [P["tofu"]]:
            recipes.append(build_noodle(style, prot))
    # caramel braises (kho)
    for style in KHO_STYLES:
        for prot in MEAT_SEA + [P["tofu"], P["egg"]]:
            recipes.append(build_kho(style, prot))
    # sour soup by vegetable (samlor machu)
    for veg in MACHU_VEG:
        for prot in MEAT_SEA + [P["tofu"]]:
            recipes.append(build_machu_veg(veg, prot))
    # steamed (chhnganh)
    for style in STEAMED_STYLES:
        for prot in MEAT_SEA:
            recipes.append(build_steamed(style, prot))
    # fried rice
    for prot in ALL_PROT:
        recipes.append(build_fried_rice(prot))

    # desserts
    for name_en, km, rom in STICKY_FILLINGS:
        recipes.append(build_sticky_dessert(name_en, km, rom, 0))
    for name_en, km, rom in SWEET_SOUP_ITEMS:
        recipes.append(build_sweet_soup(name_en, km, rom))
    # drinks
    for name_en, km, rom in SMOOTHIE_FRUITS:
        recipes.append(build_smoothie(name_en, km, rom))
    for d in OTHER_DRINKS:
        recipes.append(build_other_drink(*d))
    # snacks
    for s in SNACKS:
        recipes.append(build_snack(*s))

    # ----- finalize: ids, slugs, totals, dedupe -----
    seen = set()
    final = []
    counter = 1
    for r in recipes:
        key = r["name_rom"].lower()
        if key in seen:
            continue
        seen.add(key)
        rid = "khm-{:04d}".format(counter)
        slug = slugify(r["name_en"])
        total = r.get("prep", 0) + r.get("cook", 0)
        # image family: protein variants of one base dish share a single image.
        # signature/iconic dishes get their own (unique) family from the slug.
        strip = {"chicken", "pork", "beef", "duck", "frog", "fish", "shrimp", "squid",
                 "crab", "clam", "tofu", "egg", "mushroom", "vegetable", "meat", "seafood", "veg"}
        tags = r.get("tags", [])
        if "signature" in tags:
            family = slug
        else:
            family = "-".join(t for t in tags if t not in strip) or slug
        record = {
            "id": rid,
            "slug": slug,
            "name": {"km": r["name_km"], "romanized": r["name_rom"], "en": r["name_en"]},
            "category": r["category"],
            "subcategory": r.get("subcategory", ""),
            "cuisine": "Khmer",
            "description": r["description"],
            "imageFamily": family,
            "image": "images/dishes/{}.jpg".format(slug),
            "tags": tags,
            "dietary": r.get("dietary", []),
            "spiceLevel": r.get("spice", 0),
            "difficulty": r.get("difficulty", "easy"),
            "servings": rng(rid, 2, 6),
            "time": {
                "prepMinutes": r.get("prep", 0),
                "cookMinutes": r.get("cook", 0),
                "totalMinutes": total,
            },
            "kroeung": r.get("kroeung", []),
            "equipment": r.get("equipment", []),
            "ingredients": r["ingredients"],
            "instructions": r["instructions"],
        }
        if r.get("description_km"):
            record["descriptionKm"] = r["description_km"]
        _apply_km(record)
        final.append(record)
        counter += 1

    return final


def main():
    recipes = generate()
    meta = {
        "schemaVersion": "1.0",
        "title": "Khmer Chief — Cambodian Recipe Catalog",
        "description": "Website-ready catalog of Cambodian (Khmer) dishes with structured ingredients and step-by-step cooking instructions.",
        "cuisine": "Khmer",
        "language": {"primary": "en", "names": ["km", "romanized", "en"]},
        "count": len(recipes),
        "categories": sorted({r["category"] for r in recipes}),
        "generatedAt": datetime.date(2026, 5, 28).isoformat(),
        "license": "CC-BY-4.0 (recipes are traditional / generated for demonstration)",
    }
    doc = {"meta": meta, "recipes": recipes}
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
    # JS wrapper so the static page works by double-clicking (no server / no fetch needed)
    with open("khmer_data.js", "w", encoding="utf-8") as f:
        f.write("window.KHMER_MENU = ")
        json.dump(doc, f, ensure_ascii=False)
        f.write(";\n")
    print("Wrote {} recipes to {} (+ khmer_data.js)".format(len(recipes), OUT_FILE))
    # category breakdown
    from collections import Counter
    c = Counter(r["category"] for r in recipes)
    for cat, n in sorted(c.items(), key=lambda x: -x[1]):
        print("  {:12s} {}".format(cat, n))


if __name__ == "__main__":
    main()
