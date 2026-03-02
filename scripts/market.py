#!/usr/bin/env python3
import json
import os
import re
import shutil
import sys
import tempfile
import unicodedata
from datetime import datetime, timezone

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATA_FILE = os.path.join(DATA_DIR, "shopping-list.json")
PAIRS_FILE = os.path.join(BASE_DIR, "references", "pairs.md")

DEFAULT_DATA = {"version": 1, "updatedAt": None, "items": []}

SYNONYMS = {
    "cafe em po": "cafe",
    "detergente liquido": "detergente",
    "cafezinho": "cafe",
}

CATEGORY_MAP = {
    "arroz": "mercearia",
    "feijao": "mercearia",
    "macarrao": "mercearia",
    "cafe": "mercearia",
    "acucar": "mercearia",
    "oleo": "mercearia",
    "alho": "hortifruti",
    "cebola": "hortifruti",
    "banana": "hortifruti",
    "maca": "hortifruti",
    "frango": "proteinas",
    "carne": "proteinas",
    "peixe": "proteinas",
    "leite": "laticinios",
    "queijo": "laticinios",
    "iogurte": "laticinios",
    "detergente": "limpeza",
    "agua sanitaria": "limpeza",
    "sabonete": "higiene",
    "shampoo": "higiene",
}

CATEGORY_FALLBACK = {
    "mercearia": ["feijao", "oleo", "acucar", "sal", "farinha"],
    "hortifruti": ["tomate", "cebola", "alho", "banana", "batata"],
    "proteinas": ["alho", "cebola", "limao", "ovos", "sal grosso"],
    "laticinios": ["pao", "manteiga", "cafe", "iogurte", "queijo"],
    "limpeza": ["esponja", "sabao em po", "desinfetante", "agua sanitaria"],
    "higiene": ["pasta de dente", "papel higienico", "shampoo", "condicionador"],
}

UNIT_PATTERN = r"^(kg|g|un|l|ml)$"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def singularize_basic(name: str) -> str:
    if name == "ovos":
        return "ovo"
    if name.endswith("s") and len(name) > 3 and not name.endswith("as") and not name.endswith("es"):
        return name[:-1]
    return name


def normalize_item_name(raw: str):
    raw = normalize_spaces(raw.lower())
    raw_no_acc = strip_accents(raw)
    mapped = SYNONYMS.get(raw_no_acc, raw_no_acc)
    mapped = singularize_basic(mapped)
    display = mapped
    return display, strip_accents(display)


def parse_qty_and_unit(token: str):
    t = token.strip().lower()
    m = re.match(r"^([0-9]+(?:[\.,][0-9]+)?)([a-z]+)?$", t)
    if not m:
        return None
    qty_raw, unit = m.group(1), (m.group(2) or "")
    qty = float(qty_raw.replace(",", "."))
    if qty <= 0:
        return None
    if unit and not re.match(UNIT_PATTERN, unit):
        return None
    return qty, (unit or "un")


def parse_leading_qty(args):
    if not args:
        return None
    first = args[0].strip().lower()
    m = re.match(r"^([0-9]+(?:[\.,][0-9]+)?)$", first)
    if not m:
        return None
    qty = float(m.group(1).replace(",", "."))
    if qty <= 0:
        return None
    return qty, "un"


def format_qty(qty: float) -> str:
    if qty.is_integer():
        return str(int(qty))
    return f"{qty:.2f}".rstrip("0").rstrip(".")


def format_qty_with_unit(qty: float, unit: str) -> str:
    qty_str = format_qty(qty)
    if unit == "un":
        return f"{qty_str} unidade" if qty == 1 else f"{qty_str} unidades"
    return f"{qty_str}{unit}"


def load_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DATA_FILE):
        return {**DEFAULT_DATA, "updatedAt": now_iso()}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict) or "items" not in data:
            raise ValueError("schema inválido")
        return data
    except Exception:
        backup = DATA_FILE + f".bak-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        try:
            shutil.copyfile(DATA_FILE, backup)
        except Exception:
            pass
        return {**DEFAULT_DATA, "updatedAt": now_iso(), "_corrupted": True}


def atomic_save(data):
    data["updatedAt"] = now_iso()
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix="shopping-list-", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DATA_FILE)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def parse_pairs_md(path: str):
    pairs = {}
    if not os.path.exists(path):
        return pairs
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            item, vals = line.split(":", 1)
            key = strip_accents(normalize_spaces(item.lower()))
            options = [strip_accents(normalize_spaces(v.lower())) for v in vals.split(",") if normalize_spaces(v)]
            pairs[key] = options
    return pairs


def existing_names_set(data):
    out = set()
    for it in data.get("items", []):
        out.add(strip_accents(it.get("name", "").lower()))
    return out


def suggest_for(item_norm_key: str, data):
    pairs = parse_pairs_md(PAIRS_FILE)
    existing = existing_names_set(data)

    suggestions = []
    if item_norm_key in pairs:
        suggestions.extend(pairs[item_norm_key])

    if len(suggestions) < 3:
        cat = CATEGORY_MAP.get(item_norm_key)
        if cat:
            suggestions.extend(CATEGORY_FALLBACK.get(cat, []))

    if len(suggestions) < 3:
        suggestions.extend(["arroz", "feijao", "oleo", "alho", "leite"])

    clean = []
    seen = set()
    for s in suggestions:
        n = strip_accents(normalize_spaces(s.lower()))
        if not n or n == item_norm_key or n in existing or n in seen:
            continue
        seen.add(n)
        clean.append(s)
        if len(clean) >= 5:
            break

    return clean[:5] if len(clean) >= 3 else clean[:3]


def cmd_add(args):
    if not args:
        print("Informe um item para adicionar.")
        return 1

    qty = 1.0
    unit = "un"
    item_parts = args[:]

    maybe_qty = parse_qty_and_unit(args[-1])
    if maybe_qty:
        qty, unit = maybe_qty
        item_parts = args[:-1]

    if not maybe_qty:
        leading_qty = parse_leading_qty(args)
        if leading_qty and len(args) > 1:
            qty, unit = leading_qty
            item_parts = args[1:]

    if not item_parts:
        print("Informe um item para adicionar.")
        return 1

    item_raw = " ".join(item_parts)
    item_display, item_key = normalize_item_name(item_raw)

    if not item_display:
        print("Informe um item para adicionar.")
        return 1

    data = load_data()
    corrupted = data.pop("_corrupted", False)

    found = None
    for it in data.get("items", []):
        n = strip_accents(normalize_spaces(it.get("name", "").lower()))
        u = it.get("unit", "un")
        if n == item_key and u == unit:
            found = it
            break

    if found:
        found["qty"] = float(found.get("qty", 0)) + qty
    else:
        data.setdefault("items", []).append(
            {
                "name": item_display,
                "qty": qty,
                "unit": unit,
                "addedAt": now_iso(),
            }
        )

    atomic_save(data)

    suggestions = suggest_for(item_key, data)

    msg = f"Adicionado: {item_display} ({format_qty_with_unit(qty, unit)})."
    print(msg)
    if suggestions:
        print("Sugestões para comprar junto: " + ", ".join(suggestions[:5]) + ".")
    if corrupted:
        print("Observação: o arquivo anterior estava corrompido, fiz backup e reset controlado.")
    return 0


def cmd_list(_args):
    data = load_data()
    corrupted = data.pop("_corrupted", False)
    items = data.get("items", [])

    if not items:
        print("Não tem nenhum item na sua lista. Comece adicionando alguma coisa.")
        if corrupted:
            print("Observação: o arquivo anterior estava corrompido, fiz backup e reset controlado.")
        return 0

    items_sorted = sorted(items, key=lambda x: x.get("name", ""))

    print("Sua lista de mercado:")
    for i, it in enumerate(items_sorted, start=1):
        name = it.get("name", "")
        qty = float(it.get("qty", 1))
        unit = it.get("unit", "un")
        print(f"{i}. {name} — {format_qty_with_unit(qty, unit)}")

    print(f"Total: {len(items_sorted)} itens")
    if corrupted:
        print("Observação: o arquivo anterior estava corrompido, fiz backup e reset controlado.")
    return 0


def main():
    if len(sys.argv) < 2:
        print("Uso: market.py <add|list> [args]")
        return 1

    command = sys.argv[1].strip().lower()
    args = sys.argv[2:]

    if command == "add":
        return cmd_add(args)
    if command == "list":
        return cmd_list(args)

    print("Comando inválido. Use: add ou list")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
