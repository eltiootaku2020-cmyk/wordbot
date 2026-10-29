#!/usr/bin/env python3
"""Static audit for the Isekai sin Destino SpicyChat preset.

This validates files and internal consistency only. It does not emulate SpicyChat
or prove that an imported bot will follow every prompt instruction.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "proyectos" / "isekai-sin-destino"
JSON_PATH = BASE / "LOREBOOK_IMPORT.json"
CONFIG_PATH = BASE / "CONFIG_LIGERA.md"
MASTER_PATH = BASE / "LOREBOOK_MAESTRA.md"
SCHEMA_PATH = BASE / "REGISTRO_INTERNO_ESQUEMA.md"
README_PATH = BASE / "README.md"
RULES_PATH = BASE / "CUADRO_REGLAS_PRIORITARIAS.md"

errors: list[str] = []
checks = 0


def ok(condition: bool, message: str) -> None:
    global checks
    checks += 1
    if not condition:
        errors.append(message)


def read(path: Path) -> str:
    ok(path.is_file(), f"Falta archivo requerido: {path.relative_to(ROOT)}")
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def normalized_keyword(value: object) -> str:
    return " ".join(str(value).casefold().split())


raw = read(JSON_PATH)
try:
    payload = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"ERROR: JSON inválido en {JSON_PATH.relative_to(ROOT)}: {exc}")
    sys.exit(1)

ok(isinstance(payload, dict), "La raíz del JSON debe ser un objeto.")
entries_data = payload.get("entries", {})
ok(isinstance(entries_data, dict), "La propiedad 'entries' debe ser un objeto.")
entries = list(entries_data.values()) if isinstance(entries_data, dict) else []
ok(len(entries) == 77, f"Se esperaban 77 entradas, se encontraron {len(entries)}.")

uids = [entry.get("uid") for entry in entries if isinstance(entry, dict)]
ok(len(uids) == len(entries), "Cada entrada debe ser un objeto.")
ok(all(isinstance(uid, int) for uid in uids), "Todos los UID deben ser enteros.")
ok(len(set(uids)) == len(uids), "Hay UID duplicados.")

all_keywords: list[tuple[str, int, str]] = []
for entry in entries:
    if not isinstance(entry, dict):
        continue
    uid = entry.get("uid", "?")
    content = entry.get("content")
    ok(isinstance(content, str), f"UID {uid}: 'content' debe ser texto.")
    if isinstance(content, str):
        ok(len(content) < 1000, f"UID {uid}: Content tiene {len(content)} caracteres (el límite interno es <1000).")
    for field in ("key", "keysecondary"):
        value = entry.get(field, [])
        ok(isinstance(value, list), f"UID {uid}: '{field}' debe ser una lista.")
        if not isinstance(value, list):
            continue
        for keyword in value:
            normalized = normalized_keyword(keyword)
            ok(bool(normalized), f"UID {uid}: hay una palabra clave vacía.")
            all_keywords.append((normalized, uid, str(keyword)))

seen: dict[str, tuple[int, str]] = {}
for normalized, uid, original in all_keywords:
    if normalized in seen:
        previous_uid, previous_original = seen[normalized]
        errors.append(
            f"Palabra clave duplicada tras normalizar: {original!r} "
            f"(UID {uid}) y {previous_original!r} (UID {previous_uid})."
        )
    else:
        seen[normalized] = (uid, original)
checks += 1
if len(seen) != len(all_keywords):
    pass
else:
    print(f"OK: {len(all_keywords)} palabras clave únicas.")

by_uid = {
    entry.get("uid"): entry
    for entry in entries
    if isinstance(entry, dict) and isinstance(entry.get("uid"), int)
}

required_content = {
    70: ["/guardar", "No inventes datos", "180 tokens"],
    71: ["goblin", "se enteran después", "última ubicación confirmada"],
    72: ["No registrado", "No inventes campos", "objeto"],
    73: ["frases cortadas", "Ivar", "si se enteran después"],
    74: ["sensación interna", "alcance", "coste", "duración"],
    75: ["pañuelo gastado", "cordel de cáñamo", "Sin dinero", "Son posibilidades, no regalos"],
    77: ["Δ pp", "sube/baja/sin cambio", "intención no es resultado"],
}
for uid, fragments in required_content.items():
    entry = by_uid.get(uid)
    ok(isinstance(entry, dict), f"Falta UID requerido {uid}.")
    if not isinstance(entry, dict):
        continue
    content = str(entry.get("content", "")).casefold()
    for fragment in fragments:
        ok(fragment.casefold() in content, f"UID {uid}: falta contenido requerido {fragment!r}.")

config = read(CONFIG_PATH)
master = read(MASTER_PATH)
schema = read(SCHEMA_PATH)
readme = read(README_PATH)
rules_doc = read(RULES_PATH)

field_specs = [
    ("Personality", "### Personality", "### Scenario", 5000),
    ("Scenario", "### Scenario", "### Greeting", 4000),
    ("Greeting", "### Greeting", "### Example Dialogue", 2000),
    ("Example Dialogue", "### Example Dialogue", "### Tags", 4000),
]

personality_text: str | None = None
for label, start_heading, end_heading, limit in field_specs:
    start = config.find(start_heading)
    end = config.find(end_heading, start + len(start_heading)) if start >= 0 else -1
    ok(start >= 0 and end > start, f"No se pudo localizar el campo {label} en CONFIG_LIGERA.md.")
    if start < 0 or end <= start:
        continue
    section = config[start:end]
    open_fence = section.find("~~~text\n")
    close_fence = section.find("\n~~~", open_fence + 8) if open_fence >= 0 else -1
    ok(open_fence >= 0 and close_fence > open_fence, f"{label}: falta bloque de texto delimitado.")
    if open_fence < 0 or close_fence <= open_fence:
        continue
    field_text = section[open_fence + len("~~~text\n"):close_fence]
    if label == "Personality":
        personality_text = field_text
    ok(len(field_text) <= limit, f"{label}: {len(field_text)} caracteres supera el límite {limit}.")
    count_match = re.search(r"Caracteres:\s*([\d.,]+)/([\d.,]+)\.", section)
    ok(count_match is not None, f"{label}: falta el contador de caracteres.")
    if count_match:
        declared_count = int(re.sub(r"[.,]", "", count_match.group(1)))
        declared_limit = int(re.sub(r"[.,]", "", count_match.group(2)))
        ok(declared_count == len(field_text), f"{label}: contador declara {declared_count}, longitud real {len(field_text)}.")
        ok(declared_limit == limit, f"{label}: contador declara límite {declared_limit}, se esperaba {limit}.")
    if label == "Personality":
        ok(len(field_text) < 5000, f"Personality debe dejar margen bajo 5000; tiene {len(field_text)}.")
        for phrase in (
            "REGISTRO CERRADO",
            "No registrado",
            "/vinculos",
            "PNJ solo saben",
        ):
            ok(phrase.casefold() in field_text.casefold(), f"Personality: falta regla {phrase!r}.")

# The standalone install sheet must carry the exact same Personality block.
rules_start = rules_doc.find("## Bloque para copiar en Personality")
rules_end = rules_doc.find("## Cómo funciona el mapa", rules_start)
ok(rules_start >= 0 and rules_end > rules_start, "No se localizó Personality en CUADRO_REGLAS_PRIORITARIAS.md.")
if rules_start >= 0 and rules_end > rules_start:
    rules_section = rules_doc[rules_start:rules_end]
    rules_open = rules_section.find("~~~text\n")
    rules_close = rules_section.find("\n~~~", rules_open + 8) if rules_open >= 0 else -1
    ok(rules_open >= 0 and rules_close > rules_open, "El cuadro de reglas no tiene un bloque Personality válido.")
    if rules_open >= 0 and rules_close > rules_open:
        rules_personality = rules_section[rules_open + len("~~~text\n"):rules_close]
        ok(personality_text is not None and rules_personality == personality_text, "Personality de CONFIG_LIGERA.md y CUADRO_REGLAS_PRIORITARIAS.md no coincide.")
        rules_count = re.search(r"Tiene \*\*(\d+) caracteres\*\*", rules_section)
        ok(rules_count is not None, "Falta el contador de caracteres en el cuadro de reglas.")
        if rules_count:
            ok(int(rules_count.group(1)) == len(rules_personality), "El contador de Personality del cuadro de reglas no coincide con su texto.")

for phrase in (
    "No registrado",
    "Δ0",
    "sin cambio",
    "historial de comidas",
    "Cada 1–2 respuestas",
    "sensación interna",
):
    ok(phrase.casefold() in schema.casefold(), f"Esquema interno: falta regla {phrase!r}.")

# Clock checks only apply to operational configuration and master canon.
for label, text in (("CONFIG_LIGERA.md", config), ("LOREBOOK_MAESTRA.md", master)):
    for obsolete in ("08:03", "08:15", "Mañana I (06:00", "Noche II (21:00"):
        ok(obsolete not in text, f"{label}: contiene ejemplo horario obsoleto {obsolete!r}.")
    for block in (
        "Madrugada (00:00–03:59)",
        "Amanecer (04:00–07:59)",
        "Mañana (08:00–11:59)",
        "Mediodía (12:00–15:59)",
        "Tarde (16:00–19:59)",
        "Noche (20:00–23:59)",
    ):
        ok(block in text, f"{label}: falta bloque horario {block!r}.")

master_headers = re.findall(r"^### Entrada (7[0-7]) — .+$", master, flags=re.MULTILINE)
ok(len(master_headers) == 8, f"La Lorebook maestra debe tener 8 encabezados Entry 70–77; encontró {len(master_headers)}.")
ok(sorted(int(uid) for uid in master_headers) == list(range(70, 78)), "La Lorebook maestra debe numerar una vez cada Entry 70–77, sin duplicados.")

master_uid_map = [(71, 70), (72, 71), (73, 72), (74, 73), (75, 74), (76, 75), (77, 77)]
for ordinal, uid in master_uid_map:
    marker = f"### Entrada {ordinal} — "
    start = master.find(marker)
    ok(start >= 0, f"Falta la entrada {ordinal} en la Lorebook maestra.")
    if start < 0:
        continue
    possible_ends = [
        position for position in (
            master.find("\n### Entrada ", start + len(marker)),
            master.find("\n### 34.1. Diagnóstico", start + len(marker)),
        ) if position >= 0
    ]
    end = min(possible_ends) if possible_ends else len(master)
    section = master[start:end]
    content_marker = "**Content:** "
    ok(content_marker in section, f"Entrada maestra {ordinal}: falta Content.")
    if content_marker in section:
        master_content = section.split(content_marker, 1)[1].strip()
        canonical_entry = by_uid.get(uid)
        ok(isinstance(canonical_entry, dict), f"Falta UID {uid} para entrada maestra {ordinal}.")
        if isinstance(canonical_entry, dict):
            ok(
                master_content == str(canonical_entry.get("content", "")).strip(),
                f"Entrada maestra {ordinal} no coincide con el Content de JSON UID {uid}.",
            )

ok("v1.19" in readme, "README de Isekai no menciona la revisión v1.19.")

if errors:
    print(f"FALLO: {len(errors)} problema(s) encontrados en {checks} comprobaciones.")
    for error in errors:
        print(f" - {error}")
    sys.exit(1)

print(f"OK: auditoría de Isekai v1.19 aprobada ({checks} comprobaciones).")
print(" - 77 entradas; UID y palabras clave únicos.")
print(f" - Content máximo: {max(len(str(e.get('content', ''))) for e in entries)} caracteres (<1000).")
print(" - Contadores y límites de Personality/Scenario/Greeting/Example Dialogue válidos.")
print(" - Esquema, porcentajes, objetos, Eco vegetal, diálogo y reloj coherentes.")
