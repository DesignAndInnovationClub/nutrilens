import pandas as pd
import re
from pathlib import Path


BASE = Path("data1")

ins_db   = pd.read_csv(BASE / "INS_Safety_Complete1.csv")
sugar_db = pd.read_csv(BASE / "sugar_aliases.csv")
combo_db = pd.read_csv(BASE / "combinations.csv")


INS_COL      = "INS Number"
NAME_COL     = "Name"
FUNCTION_COL = "Functional class"
SAFETY_COL   = "Safety Rating (Safe/Caution/High Risk)"
HEALTH_COL   = "Health Concern"
ADI_COL      = "ADI (Acceptable Daily Intake)"
EU_COL       = "EU Warning"
US_COL       = "US Warning"


ins_db["ins_lower"]  = ins_db[INS_COL].astype(str).str.lower().str.strip()
ins_db["name_lower"] = ins_db[NAME_COL].astype(str).str.lower().str.strip()


def extract_ins_numbers(ingredients: list) -> list:
    ins_found = []
    for ing in ingredients:
        matches = re.findall(r'INS\s*(\d+[a-zA-Z]*)', ing.upper())
        for m in matches:
            ins_found.append(f"INS {m}")
    return list(set(ins_found))

def find_by_name(ingredient: str):
    """
    Searches both INS Number and Name columns.
    Strips common label filler words before matching.
    """
    ing_lower = ingredient.lower().strip()

    filler = [
        "permitted", "nature identical", "added", "contains",
        "acidity regulator", "emulsifier", "colour", "color",
        "preservative", "antioxidant", "stabiliser", "stabilizer",
        "thickener", "flavour", "flavoring", "flavouring", "raising agent"
    ]
    cleaned = ing_lower
    for word in filler:
        cleaned = cleaned.replace(word, "").strip()

    if not cleaned:
        return None

    match = ins_db[ins_db["ins_lower"] == cleaned]
    if not match.empty:
        return match.iloc[0]

  
    match = ins_db[ins_db["name_lower"] == cleaned]
    if not match.empty:
        return match.iloc[0]

    # 3. Partial match — name contains ingredient OR ingredient contains name
    for _, row in ins_db.iterrows():
        name = row["name_lower"]
        ins  = row["ins_lower"]
        if (name in cleaned or cleaned in name or
                ins in cleaned or cleaned in ins):
            return row

    return None

# ── Layer 1: INS + Name lookup ───────────────────────────────────
def get_ins_context(ingredients: list, ins_numbers: list) -> str:
    matched = {}  # INS Number → row (deduplicates)

    # Pass 1 — match by extracted INS numbers
    for ins in ins_numbers:
        match = ins_db[ins_db["ins_lower"] == ins.lower()]
        if not match.empty:
            row = match.iloc[0]
            matched[row[INS_COL]] = row

    # Pass 2 — match remaining ingredients by Name column
    for ing in ingredients:
        row = find_by_name(ing)
        if row is not None:
            key = row[INS_COL]
            if key not in matched:
                matched[key] = row

    if not matched:
        return ""

    results = []
    for ins_num, row in matched.items():
        results.append(
            f"• {row[INS_COL]} ({row[NAME_COL]})\n"
            f"  Functional Class: {row[FUNCTION_COL]}\n"
            f"  Safety Rating:    {row[SAFETY_COL]}\n"
            f"  Health Concern:   {row[HEALTH_COL]}\n"
            f"  ADI:              {row[ADI_COL]}\n"
            f"  EU Warning:       {row[EU_COL]}\n"
            f"  US Warning:       {row[US_COL]}"
        )

    return "KNOWN ADDITIVES FROM INS DATABASE:\n" + "\n\n".join(results)


def get_sugar_context(ingredients: list) -> str:
    found = []
    for ing in ingredients:
        ing_lower = ing.lower()
        for _, row in sugar_db.iterrows():
            if row["alias"].lower() in ing_lower:
                found.append(f"{row['alias']} ({row['type']})")

    if not found:
        return ""
    return "HIDDEN SUGARS DETECTED:\n• " + "\n• ".join(set(found))

def get_combination_context(ingredients: list, ins_numbers: list) -> str:
    all_items = set()
    for ing in ingredients:
        all_items.add(ing.upper().strip())
    for ins in ins_numbers:
        all_items.add(ins.upper().strip())

    results = []
    for _, row in combo_db.iterrows():
        ing1 = str(row["ingredient_1"]).upper()
        ing2 = str(row["ingredient_2"]).upper()

        found1 = any(ing1 in item or item in ing1 for item in all_items)
        found2 = any(ing2 in item or item in ing2 for item in all_items)

        if found1 and found2:
            results.append(
                f"⚠️ COMBINATION RISK [{row['severity']}]\n"
                f"  {row['ingredient_1']} + {row['ingredient_2']}\n"
                f"  Reaction: {row['reaction']}\n"
                f"  Source:   {row['source']}"
            )

    return "DANGEROUS COMBINATIONS IN THIS PRODUCT:\n" + "\n\n".join(results) if results else ""

def build_rag_context(
    ingredients: list,
    category: str = "",
    budget: int = 30
) -> dict:
    ins_numbers = extract_ins_numbers(ingredients)

    layers = {
        "ins":          get_ins_context(ingredients, ins_numbers),
        "sugars":       get_sugar_context(ingredients),
        "combinations": get_combination_context(ingredients, ins_numbers),
    }

    layers["full_context"] = "\n\n".join([v for v in layers.values() if v])
    layers["ins_numbers"]  = ins_numbers

    return layers

