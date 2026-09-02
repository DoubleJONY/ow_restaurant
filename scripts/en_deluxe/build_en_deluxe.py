#!/usr/bin/env python3
"""Build en_deluxe.ow from the canonical KR Deluxe structure.

Korean sources remain authoritative for gameplay and numeric data.  English
edition files are read only for localized text and explicitly approved locale
data (totalScore and STAGE_CODE ordering deltas).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
KR_SCRIPT_DIR = ROOT / "scripts" / "kr_deluxe"
sys.path.insert(0, str(KR_SCRIPT_DIR))

import build_deluxe_data as data_builder  # noqa: E402
import build_kr_deluxe as kr_builder  # noqa: E402


TARGET = ROOT / "en_deluxe.ow"
BUILD_DIR = ROOT / "build" / "en_deluxe"
MANUAL_TRANSLATIONS = Path(__file__).with_name("manual_translations.tsv")
OUTPUT_OVERRIDES = Path(__file__).with_name("output_overrides.tsv")
RELEASE_CODE_OVERRIDES = Path(__file__).with_name("release_code_overrides.jsonl")
APPROVED_RELEASE_STRUCTURE_SHA256 = "57450BAF3D741E614C662BA40CD89F69F781CE6D3B8254339314B59CDBD2F0A2"
JSON_STRING_TOKEN = r'"(?:\\.|[^"\\])*"'

KOREAN_ONLY_MESSAGE_EDITS = (
    (
        "\t\t\tIf(Array Contains(Global.ALLOWED_HEROS, Hero(Mauga)));\n"
        "\t\t\t\tSmall Message(All Players(All Teams), Custom String(\"{0}이거 재물손괴죄 아니냐고? \", Hero Icon String(Hero Of(Event Player))));\n"
        "\t\t\t\tWait(3, Ignore Condition);\n"
        "\t\t\t\tSmall Message(All Players(All Teams), Custom String(\"{0}알아. \", Hero Icon String(Hero Of(Event Player))));\n"
        "\t\t\t\tWait(4, Ignore Condition);\n"
        "\t\t\tElse;\n"
        "\t\t\t\tWait(7, Ignore Condition);\n"
        "\t\t\tEnd;\n",
        "\t\t\tWait(7, Ignore Condition);\n",
    ),
    (
        "\t\t\tSmall Message(All Players(All Teams), Custom String(\"{0}겨우 그까짓 서비스로 감히!!\", Hero Icon String(Hero Of(Event Player))));\n",
        "",
    ),
)

LOCALE_SOURCES = {
    "org": {"kr": ROOT / "ko.ow", "en": ROOT / "en.ow", "old_count": 475, "new_count": 476},
    "cafe": {"kr": ROOT / "cafe_kr.ow", "en": ROOT / "cafe_en.ow", "old_count": 398, "new_count": 399},
    "gc": {"kr": ROOT / "gc_kr.ow", "en": ROOT / "gc_en.ow", "old_count": 462, "new_count": 464},
}

SERIALIZED_UI_VALUES = {
    "edition_names": ("OverwatchCooked!", "Cafe & Dessert", "World Cuisine"),
    "edition_credits": (
        "GummyBear&변기클라우드\\r\\nDifficulty: ★★★☆☆",
        "Joseon&Deadlock\\r\\nDifficulty: ★★☆☆☆",
        "Joseon\\r\\nDifficulty: ★★★★☆",
    ),
    "mode_names": (
        "Practice", "Casual Dining", "Fine Dining", "Buzzy Restaurant",
        "MasterChef Challenge", "HeadChef Challenge",
    ),
    "mode_descriptions": (
        "A sandbox mode where you can freely practice your skills",
        "Complete the Apprentice with 5 menu items",
        "Complete the Journeyman with the all menu",
        "Complete the Professional featuring demanding customers",
        "Challenge the Hell's Kitchen Chef!",
        "Challenge the perfect restaurant",
    ),
    "practice_edition_names": (
        "OverwatchCooked!", "Cafe & Dessert", "World Cuisine",
    ),
    "difficulty_names": ("Apprentice", "Journeyman", "Professional", "Hell's Kitchen"),
}

DATA_RULE_TITLES = {
    "Global subroutine: Deluxe ORG init1",
    "Global subroutine: Deluxe ORG init2",
    "Global subroutine: Deluxe ORG init3",
    "Global subroutine: Deluxe CAFE init1",
    "Global subroutine: Deluxe CAFE init2",
    "Global subroutine: Deluxe CAFE init3",
    "Global subroutine: Deluxe GC init1",
    "Global subroutine: Deluxe GC init2",
    "Global subroutine: Deluxe GC init3",
    "Global subroutine: Deluxe common customer init",
}

# English source files intentionally retain these exact identity/locale values.
ALLOWED_HANGUL_LITERALS = {
    ("Global: Setting", 72): "GummyBear&변기클라우드\r\nDifficulty: ★★★☆☆/{0}",
    ("Player: Spawn", 12): "한국어 : SPXXM\r\nEnglish : HTNZ3\r\n日本語 : 4ND1P",
    ("Player: Reload button", 2): "변기클라우드",
}


class BuildError(RuntimeError):
    pass


@dataclass(frozen=True)
class CustomLiteral:
    rule: str
    ordinal: int
    start: int
    end: int
    value: str


@dataclass(frozen=True)
class RuleBlock:
    title: str
    start: int
    end: int
    text: str


def replace_spans(text: str, replacements: Iterable[tuple[int, int, str]]) -> str:
    result = text
    for start, end, replacement in sorted(replacements, key=lambda item: item[0], reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def placeholder_signature(value: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\{\d+\}", value))


def placeholder_counter(value: str) -> Counter[str]:
    return Counter(placeholder_signature(value))


def placeholders_compatible(source: str, target: str) -> bool:
    """Allow natural-language reordering while preserving every argument use."""
    return placeholder_counter(source) == placeholder_counter(target)


def contains_hangul(value: str) -> bool:
    return bool(re.search(r"[가-힣]", value))


def contains_korean_locale_marks(value: str) -> bool:
    return "〔" in value or "〕" in value


def allowed_hangul(rule: str, ordinal: int, value: str) -> bool:
    return ALLOWED_HANGUL_LITERALS.get((rule, ordinal)) == value


def rule_blocks(text: str) -> list[RuleBlock]:
    blocks: list[RuleBlock] = []
    cursor = 0
    while True:
        start = text.find('rule("', cursor)
        if start < 0:
            break
        title_end = text.find('")', start + len('rule("'))
        if title_end < 0:
            raise BuildError("unterminated rule title")
        title = text[start + len('rule("') : title_end]
        open_at = text.find("{", title_end)
        end = data_builder.scan_balanced(text, open_at, "{", "}")
        blocks.append(RuleBlock(title, start, end, text[start:end]))
        cursor = end
    return blocks


def custom_literals(rule: RuleBlock) -> list[CustomLiteral]:
    result: list[CustomLiteral] = []
    ordinal = 0
    for match in re.finditer(r"Custom String\s*\(\s*", rule.text):
        cursor = match.end()
        if cursor >= len(rule.text) or rule.text[cursor] != '"':
            continue
        escaped = False
        end = cursor + 1
        while end < len(rule.text):
            char = rule.text[end]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                end += 1
                break
            end += 1
        else:
            raise BuildError(f"unterminated Custom String literal in {rule.title}")
        token = rule.text[cursor:end]
        try:
            value = json.loads(token)
        except json.JSONDecodeError as exc:
            raise BuildError(f"invalid Custom String literal in {rule.title}: {token[:80]}") from exc
        result.append(CustomLiteral(rule.title, ordinal, rule.start + cursor, rule.start + end, value))
        ordinal += 1
    return result


def masked_rule(rule: RuleBlock) -> str:
    replacements = [
        (literal.start - rule.start, literal.end - rule.start, '"__CUSTOM_STRING__"')
        for literal in custom_literals(rule)
    ]
    masked = replace_spans(rule.text, replacements)
    return re.sub(r"\s+", "", masked)


def rules_by_title(text: str) -> dict[str, RuleBlock]:
    result: dict[str, RuleBlock] = {}
    for rule in rule_blocks(text):
        if rule.title in result:
            raise BuildError(f"duplicate rule title: {rule.title}")
        result[rule.title] = rule
    return result


def read_source(path: Path) -> str:
    return data_builder.read_ow(path)


def source_table(path: Path, subroutine: str, name: str) -> tuple[str, list[object]]:
    text = read_source(path)
    rule = data_builder.find_rule(text, subroutine)
    assignment = data_builder.find_assignment(rule, name)
    values = data_builder.eval_expr(assignment.expression)
    for _, _, index, patch_value in data_builder.find_patches(rule, name):
        values[index] = patch_value
    return assignment.expression, values


def validate_paired_item_tables() -> dict[str, int]:
    """Prove that KR/EN item indices are aligned before reusing the KR remap."""
    data_init1_tables = {
        "ITEM_COLOR", "ITEM_NAME", "ITEM_SCORE", "CUTTING_NEEDED", "CUTTING_RESULT",
        "GRILLING_NEEDED", "GRILLING_RESULT", "FRYING_NEEDED", "FRYING_RESULT",
        "ICE_NEEDED", "ICE_RESULT",
    }
    validated: dict[str, int] = {}
    for edition, spec in LOCALE_SOURCES.items():
        count = 0
        for table in sorted(data_builder.PER_ITEM):
            if table.startswith("ICE_") and edition != "cafe":
                continue
            subroutine = "dataInit" if table in data_init1_tables else "dataInit2"
            _, kr_values = source_table(spec["kr"], subroutine, table)
            _, en_values = source_table(spec["en"], subroutine, table)
            if len(kr_values) != spec["old_count"] or len(en_values) != spec["old_count"]:
                raise BuildError(
                    f"{edition} {table} source length mismatch: "
                    f"KR={len(kr_values)} EN={len(en_values)} expected={spec['old_count']}"
                )
            if table != "ITEM_NAME" and kr_values != en_values:
                raise BuildError(f"{edition} {table} differs between KR and EN; item remap is unsafe")
            count += 1
        validated[edition] = count
    return validated


def remapped_english_item_names() -> dict[str, list[str]]:
    original: dict[str, list[str]] = {}
    transformed: dict[str, list[str]] = {}
    for name, spec in LOCALE_SOURCES.items():
        _, values = source_table(spec["en"], "dataInit", "ITEM_NAME")
        if len(values) != spec["old_count"]:
            raise BuildError(f"{name} English ITEM_NAME length {len(values)} != {spec['old_count']}")
        if any(not isinstance(value, str) for value in values):
            raise BuildError(f"{name} English ITEM_NAME contains a non-string")
        original[name] = list(values)
        mapping = data_builder.build_mapping(name, spec["old_count"], spec["new_count"])
        remapped: list[str | None] = [None] * spec["new_count"]
        for old_code, new_code in mapping.items():
            remapped[new_code] = values[old_code]
        transformed[name] = [value if value is not None else "" for value in remapped]

    # Use the same semantic donors as the canonical KR data builder.
    if original["org"][433] != "Food Box":
        raise BuildError(f"ORG item 433 is no longer Food Box: {original['org'][433]!r}")
    if original["cafe"][351] != "Freeze Gun":
        raise BuildError(f"CAFE item 351 is no longer Freeze Gun: {original['cafe'][351]!r}")
    transformed["org"][20] = original["cafe"][351]
    transformed["cafe"][19] = original["org"][433]
    transformed["gc"][19] = original["org"][433]
    transformed["gc"][20] = original["cafe"][351]
    for name, values in transformed.items():
        if any(value == "" for value in values):
            raise BuildError(f"{name} remapped English ITEM_NAME has an empty slot")
    return transformed


def replace_assignment_in_subroutine(text: str, subroutine: str, name: str, expression: str) -> str:
    start, end = kr_builder.rule_span_by_subroutine(text, subroutine)
    rule = text[start:end]
    assignment = data_builder.find_assignment(rule, name)
    replacement = f"\t\tGlobal.{name} = {expression};"
    rule = rule[: assignment.start] + replacement + rule[assignment.end :]
    return text[:start] + rule + text[end:]


def localize_data_tables(text: str) -> tuple[str, dict[str, object]]:
    paired_tables = validate_paired_item_tables()
    names = remapped_english_item_names()
    report: dict[str, object] = {
        "item_name_counts": {},
        "stage_name_counts": {},
        "upgrade_name_counts": {},
        "paired_item_tables": paired_tables,
        "item_name_max_literal_chars": {},
    }
    for edition, spec in LOCALE_SOURCES.items():
        item_expression = data_builder.make_split_expression(names[edition], "\t\t\t")
        if data_builder.eval_expr(item_expression) != names[edition]:
            raise BuildError(f"{edition} English ITEM_NAME serialization round-trip failed")
        encoded_chunks = [
            json.loads(match.group(1))
            for match in re.finditer(rf"Custom String\s*\(\s*({JSON_STRING_TOKEN})", item_expression)
        ]
        max_chars = max(map(len, encoded_chunks), default=0)
        if max_chars > 90:
            raise BuildError(f"{edition} English ITEM_NAME chunk exceeds 90 characters: {max_chars}")
        text = replace_assignment_in_subroutine(text, f"dataInit_{edition}1", "ITEM_NAME", item_expression)
        report["item_name_counts"][edition] = len(names[edition])
        report["item_name_max_literal_chars"][edition] = max_chars

        for table, key in (("STAGE_NAME", "stage_name_counts"), ("UPGRADE_NAME", "upgrade_name_counts")):
            expression, values = source_table(spec["en"], "dataInit2", table)
            expected = 12 if table == "STAGE_NAME" else 10
            if len(values) != expected:
                raise BuildError(f"{edition} English {table} length {len(values)} != {expected}")
            text = replace_assignment_in_subroutine(text, f"dataInit_{edition}2", table, expression)
            report[key][edition] = len(values)
    return text, report


def english_total_score_rows() -> dict[str, list[tuple[int, str]]]:
    result: dict[str, list[tuple[int, str]]] = {}
    for edition, spec in LOCALE_SOURCES.items():
        setting = rules_by_title(read_source(spec["en"]))["Global: Setting"]
        assignment = data_builder.find_assignment(setting.text, "totalScore")
        values = data_builder.eval_expr(assignment.expression)
        rows: list[tuple[int, str]] = []
        for row in values:
            if not isinstance(row, list) or len(row) != 2:
                raise BuildError(f"{edition} totalScore row is not [score, holder]: {row!r}")
            score, holder = row
            if not isinstance(score, (int, float)) or int(score) != score or not isinstance(holder, str):
                raise BuildError(f"{edition} invalid totalScore row: {row!r}")
            rows.append((int(score), holder))
        expected = 4 if edition == "gc" else 6
        if len(rows) != expected:
            raise BuildError(f"{edition} English totalScore rows {len(rows)} != {expected}")
        while len(rows) < 6:
            rows.append((0, "None"))
        result[edition] = rows
    return result


def english_total_score_expression(rows_by_edition: dict[str, list[tuple[int, str]]]) -> str:
    rows = rows_by_edition["org"] + rows_by_edition["cafe"] + rows_by_edition["gc"]
    rendered = ",\r\n\t\t\t".join(
        f"Array({score}, Custom String({json_string(holder)}))" for score, holder in rows
    )
    return f"Array Slice(Array(\r\n\t\t\t{rendered}), Global.stageMode[0] * 6, 6)"


def localize_total_score(text: str) -> tuple[str, dict[str, list[dict[str, object]]]]:
    rows = english_total_score_rows()
    expression = english_total_score_expression(rows)
    localized = kr_builder.modify_rule(text, "Global: Setting", lambda rule: _patch_total_score_rule(rule, expression))
    report = {
        edition: [{"score": score, "holder": holder} for score, holder in edition_rows]
        for edition, edition_rows in rows.items()
    }
    return localized, report


def _patch_total_score_rule(rule: str, expression: str) -> str:
    assignment = data_builder.find_assignment(rule, "totalScore")
    replacement = f"\t\tGlobal.totalScore = {expression};"
    return rule[: assignment.start] + replacement + rule[assignment.end :]


def localize_stage_code(text: str) -> tuple[str, list[dict[str, object]]]:
    deltas: list[dict[str, object]] = []
    start, end = kr_builder.rule_span_by_subroutine(text, "dataInit_org3")
    org_rule = text[start:end]
    org_assignment = data_builder.find_assignment(org_rule, "STAGE_CODE")
    old_org_mode = (
        "Array(Array(0), Array(2), Array(3), Array(0), Array(2), Array(0), Array(3), Array(4), "
        "Array(2), Array(1), Array(4), Array(3), Array(1), Array(4), Array(1))"
    )
    new_org_mode = (
        "Array(Array(0), Array(2), Array(3), Array(0), Array(2), Array(0), Array(3), Array(1), "
        "Array(2), Array(4), Array(1), Array(3), Array(4), Array(1), Array(4))"
    )
    if org_assignment.expression.count(old_org_mode) != 1:
        raise BuildError("ORG STAGE_CODE approved mode-1 anchor mismatch")
    org_expression = org_assignment.expression.replace(old_org_mode, new_org_mode, 1)
    org_rule = (
        org_rule[: org_assignment.start]
        + f"\t\tGlobal.STAGE_CODE = {org_expression};"
        + org_rule[org_assignment.end :]
    )
    text = text[:start] + org_rule + text[end:]
    for path, kr_value, en_value in (
        ("[1][7][0]", 4, 1),
        ("[1][9][0]", 1, 4),
        ("[1][10][0]", 4, 1),
        ("[1][12][0]", 1, 4),
        ("[1][13][0]", 4, 1),
        ("[1][14][0]", 1, 4),
    ):
        deltas.append({"edition": "org", "path": path, "kr": kr_value, "en": en_value, "policy": "English order"})

    start, end = kr_builder.rule_span_by_subroutine(text, "dataInit_gc3")
    gc_rule = text[start:end]
    gc_assignment = data_builder.find_assignment(gc_rule, "STAGE_CODE")
    old = "Array(4), Array(8), Array(7)"
    new = "Array(4), Array(6), Array(7)"
    if gc_assignment.expression.count(old) != 1:
        raise BuildError("GC STAGE_CODE approved delta anchor mismatch")
    expression = gc_assignment.expression.replace(old, new, 1)
    gc_rule = gc_rule[: gc_assignment.start] + f"\t\tGlobal.STAGE_CODE = {expression};" + gc_rule[gc_assignment.end :]
    text = text[:start] + gc_rule + text[end:]
    deltas.append({"edition": "gc", "path": "[2][10][0]", "kr": 8, "en": 6, "policy": "shared legacy English order"})
    return text, deltas


def load_manual_translations() -> tuple[dict[str, str], dict[tuple[str, int | None, str], str]]:
    global_map: dict[str, str] = {}
    context_map: dict[tuple[str, int | None, str], str] = {}
    if not MANUAL_TRANSLATIONS.exists():
        return global_map, context_map
    with MANUAL_TRANSLATIONS.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            kr = decode_tsv_escapes(row.get("kr", ""))
            en = decode_tsv_escapes(row.get("en", ""))
            rule = row.get("rule", "")
            ordinal_text = row.get("ordinal", "").strip()
            ordinal = int(ordinal_text) if ordinal_text else None
            if not kr or not en:
                continue
            if not placeholders_compatible(kr, en):
                raise BuildError(f"manual placeholder mismatch: {kr!r} -> {en!r}")
            if rule:
                key = (rule, ordinal, kr)
                if key in context_map and context_map[key] != en:
                    raise BuildError(f"conflicting context manual translation: {key!r}")
                context_map[key] = en
            elif kr in global_map and global_map[kr] != en:
                raise BuildError(f"conflicting global manual translation: {kr!r}")
            else:
                global_map[kr] = en
    return global_map, context_map


def decode_tsv_escapes(value: str) -> str:
    return value.replace("\\r", "\r").replace("\\n", "\n").replace("\\t", "\t")


def prior_artifact_translations() -> dict[str, str]:
    path = ROOT / ".codex" / "artifact" / "20260601_cafe_en_translation_overlay" / "manual_translated_korean_strings.tsv"
    candidates: dict[str, set[str]] = defaultdict(set)
    if path.exists():
        with path.open("r", encoding="utf-8", newline="") as handle:
            for row in csv.DictReader(handle, delimiter="\t"):
                kr = row.get("kr", "")
                en = row.get("en", "")
                if kr and en and placeholders_compatible(kr, en):
                    candidates[kr].add(en)
    return {kr: next(iter(values)) for kr, values in candidates.items() if len(values) == 1}


def aligned_source_maps() -> tuple[dict[str, str], dict[tuple[str, int], str], dict[str, int]]:
    phrase_candidates: dict[str, set[str]] = defaultdict(set)
    context_candidates: dict[tuple[str, int], set[str]] = defaultdict(set)
    stats = {"exact_rules": 0, "sequence_rules": 0, "aligned_literals": 0}
    for spec in LOCALE_SOURCES.values():
        kr_rules = rules_by_title(read_source(spec["kr"]))
        en_rules = rules_by_title(read_source(spec["en"]))
        for title in sorted(kr_rules.keys() & en_rules.keys()):
            kr_rule = kr_rules[title]
            en_rule = en_rules[title]
            kr_literals = custom_literals(kr_rule)
            en_literals = custom_literals(en_rule)
            if len(kr_literals) != len(en_literals):
                continue
            exact = masked_rule(kr_rule) == masked_rule(en_rule)
            stats["exact_rules" if exact else "sequence_rules"] += 1
            if not exact:
                # Equal literal counts are not enough: reordered recipe/help
                # branches can silently pair unrelated sentences.
                continue
            for kr, en in zip(kr_literals, en_literals):
                if not placeholders_compatible(kr.value, en.value):
                    continue
                phrase_candidates[kr.value].add(en.value)
                context_candidates[(title, kr.ordinal)].add(en.value)
                stats["aligned_literals"] += 1

    for kr, en in prior_artifact_translations().items():
        phrase_candidates[kr].add(en)
    phrase_map = {
        kr: next(iter(values))
        for kr, values in phrase_candidates.items()
        if len(values) == 1 and placeholders_compatible(kr, next(iter(values)))
    }
    context_map = {
        key: next(iter(values))
        for key, values in context_candidates.items()
        if len(values) == 1
    }
    return phrase_map, context_map, stats


def exact_target_context_map(text: str) -> dict[tuple[str, int], str]:
    target_rules = rules_by_title(text)
    candidates: dict[tuple[str, int], set[str]] = defaultdict(set)
    for spec in LOCALE_SOURCES.values():
        kr_rules = rules_by_title(read_source(spec["kr"]))
        en_rules = rules_by_title(read_source(spec["en"]))
        for title in target_rules.keys() & kr_rules.keys() & en_rules.keys():
            target_rule = target_rules[title]
            kr_rule = kr_rules[title]
            en_rule = en_rules[title]
            if masked_rule(target_rule) != masked_rule(kr_rule):
                continue
            target_literals = custom_literals(target_rule)
            kr_literals = custom_literals(kr_rule)
            en_literals = custom_literals(en_rule)
            if len(target_literals) != len(kr_literals) or len(kr_literals) != len(en_literals):
                continue
            for target, kr, en in zip(target_literals, kr_literals, en_literals):
                if target.value != kr.value:
                    continue
                if not placeholders_compatible(target.value, en.value):
                    continue
                candidates[(title, target.ordinal)].add(en.value)
    return {key: next(iter(values)) for key, values in candidates.items() if len(values) == 1}


def apply_output_overrides(
    text: str, inventory: list[dict[str, object]]
) -> tuple[str, list[dict[str, object]], int]:
    """Apply reviewed edits captured from the canonical en_deluxe.ow snapshot."""
    overrides: dict[tuple[str, int], tuple[str, str]] = {}
    with OUTPUT_OVERRIDES.open(encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            rule_name, ordinal, base_json, target_json = line.rstrip("\n").split("\t", 3)
            key = (rule_name, int(ordinal))
            if key in overrides:
                raise BuildError(f"duplicate output override: {key}")
            overrides[key] = (json.loads(base_json), json.loads(target_json))

    replacements: list[tuple[int, int, str]] = []
    seen: set[tuple[str, int]] = set()
    inventory_by_key = {(str(row["rule"]), int(row["ordinal"])): row for row in inventory}
    for rule in rule_blocks(text):
        for literal in custom_literals(rule):
            key = (rule.title, literal.ordinal)
            if key not in overrides:
                continue
            base, target = overrides[key]
            if literal.value != base:
                raise BuildError(
                    f"stale output override at {key}: expected {base!r}, generated {literal.value!r}"
                )
            replacements.append((literal.start, literal.end, json_string(target)))
            row = inventory_by_key[key]
            row["en"] = target
            row["source"] = f'{row["source"]}+output-override'
            seen.add(key)

    missing = sorted(set(overrides) - seen)
    if missing:
        raise BuildError(f"unused output overrides: {missing[:5]}")
    return replace_spans(text, replacements), inventory, len(overrides)


def apply_release_code_overrides(text: str) -> tuple[str, int]:
    """Apply reviewed structural and runtime edits from the released EN file."""
    text = text.replace("\r\n", "\n")
    count = 0
    with RELEASE_CODE_OVERRIDES.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            patch = json.loads(line)
            base = patch["base"]
            target = patch["target"]
            occurrences = text.count(base)
            if occurrences == 0 and text.count(target) == 1:
                # A reviewed release fix may later be promoted into the KR
                # builder or translation overlay. Keep the record valid while
                # avoiding a second application of the same change.
                count += 1
                continue
            if occurrences != 1:
                raise BuildError(
                    f"stale release code override at line {line_number}: base occurrences={occurrences}"
                )
            text = text.replace(base, target, 1)
            count += 1
    return text, count


def suppress_korean_only_messages(text: str) -> tuple[str, int]:
    """Remove KR-only meme messages while preserving their gameplay timing."""
    newline = "\r\n" if "\r\n" in text else "\n"
    count = 0
    for base, target in KOREAN_ONLY_MESSAGE_EDITS:
        localized_base = base.replace("\n", newline)
        localized_target = target.replace("\n", newline)
        occurrences = text.count(localized_base)
        if occurrences != 1:
            raise BuildError(
                f"stale Korean-only message edit {count + 1}: base occurrences={occurrences}"
            )
        text = text.replace(localized_base, localized_target, 1)
        count += 1
    return text, count


def localize_serialized_ui_tables(text: str) -> tuple[str, dict[str, int]]:
    report: dict[str, int] = {}
    for key, values in SERIALIZED_UI_VALUES.items():
        source = kr_builder.serialized_ui_expression(key)
        if key == "practice_edition_names":
            target = (
                kr_builder.serialized_string_array(tuple(values), ((0, 1, 2),))
                + "[Global.totalScore[False]]"
            )
        else:
            target = kr_builder.serialized_ui_expression(key, values)
        expected = kr_builder.SERIALIZED_UI_TABLES[key]["count"]
        count = text.count(source)
        if count != expected:
            raise BuildError(f"serialized EN UI table {key}: expected {expected}, got {count}")
        text = text.replace(source, target)
        report[key] = count
    edition = kr_builder.serialized_ui_expression("edition_names", SERIALIZED_UI_VALUES["edition_names"])
    modes = kr_builder.serialized_ui_expression("mode_names", SERIALIZED_UI_VALUES["mode_names"])
    summary_pair = edition + ", " + modes
    if text.count(summary_pair) != 1:
        raise BuildError("serialized EN summary spacing anchor changed")
    text = text.replace(summary_pair, edition + " , " + modes, 1)
    return text, report


def translate_custom_strings(text: str) -> tuple[str, list[dict[str, object]], list[dict[str, object]], dict[str, int]]:
    phrase_map, _, stats = aligned_source_maps()
    target_context_map = exact_target_context_map(text)
    manual_global, manual_context = load_manual_translations()
    used_manual_global: set[str] = set()
    used_manual_context: set[tuple[str, int | None, str]] = set()
    replacements: list[tuple[int, int, str]] = []
    inventory: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []

    for rule in rule_blocks(text):
        for literal in custom_literals(rule):
            value = literal.value
            translated = value
            source = "unchanged"
            if rule.title not in DATA_RULE_TITLES:
                if (rule.title, literal.ordinal, value) in manual_context:
                    manual_key = (rule.title, literal.ordinal, value)
                    translated = manual_context[manual_key]
                    used_manual_context.add(manual_key)
                    source = "manual-context"
                elif (rule.title, None, value) in manual_context:
                    manual_key = (rule.title, None, value)
                    translated = manual_context[manual_key]
                    used_manual_context.add(manual_key)
                    source = "manual-context"
                elif value in manual_global:
                    translated = manual_global[value]
                    used_manual_global.add(value)
                    source = "manual-global"
                elif (rule.title, literal.ordinal) in target_context_map:
                    candidate = target_context_map[(rule.title, literal.ordinal)]
                    if placeholders_compatible(value, candidate):
                        translated = candidate
                        source = "source-context"
                elif (contains_hangul(value) or contains_korean_locale_marks(value)) and value in phrase_map:
                    translated = phrase_map[value]
                    source = "source-phrase"

                if translated != value:
                    replacements.append((literal.start, literal.end, json_string(translated)))
                elif contains_hangul(value) and allowed_hangul(rule.title, literal.ordinal, value):
                    source = "allowlisted"
                elif contains_hangul(value) or contains_korean_locale_marks(value):
                    unresolved.append(
                        {
                            "rule": rule.title,
                            "ordinal": literal.ordinal,
                            "kr": value,
                            "placeholders": " ".join(placeholder_signature(value)),
                        }
                    )
                    source = "unresolved"
                else:
                    source = "unchanged"

            inventory.append(
                {
                    "rule": rule.title,
                    "ordinal": literal.ordinal,
                    "source": source,
                    "kr": value,
                    "en": translated,
                    "placeholders": " ".join(placeholder_signature(value)),
                }
            )

    unused_global = sorted(set(manual_global) - used_manual_global)
    unused_context = sorted(set(manual_context) - used_manual_context)
    if unused_global or unused_context:
        raise BuildError(
            f"unused manual translations: global={len(unused_global)} context={len(unused_context)}"
        )

    translated_text = replace_spans(text, replacements)
    stats.update(
        {
            "inventory": len(inventory),
            "translated": sum(row["en"] != row["kr"] for row in inventory),
            "unresolved": len(unresolved),
            "allowlisted": sum(row["source"] == "allowlisted" for row in inventory),
            "manual_global_entries": len(manual_global),
            "manual_context_entries": len(manual_context),
        }
    )
    return translated_text, inventory, unresolved, stats


def tsv_value(value: object) -> str:
    return str(value).replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def mask_assignment_in_rule(rule: str, name: str) -> str:
    assignment = data_builder.find_assignment(rule, name)
    replacement = f"\t\tGlobal.{name} = __LOCALE_{name}__;"
    return rule[: assignment.start] + replacement + rule[assignment.end :]


def structural_fingerprint(text: str) -> tuple[str, str]:
    masked = text
    for edition in LOCALE_SOURCES:
        for phase, tables in ((1, ("ITEM_NAME",)), (2, ("STAGE_NAME", "UPGRADE_NAME")), (3, ("STAGE_CODE",))):
            for table in tables:
                masked = replace_assignment_in_subroutine(
                    masked, f"dataInit_{edition}{phase}", table, f"__LOCALE_{table}__"
                )
    masked = kr_builder.modify_rule(masked, "Global: Setting", lambda rule: mask_assignment_in_rule(rule, "totalScore"))
    literal_replacements: list[tuple[int, int, str]] = []
    for rule in rule_blocks(masked):
        literal_replacements.extend(
            (literal.start, literal.end, '"__CUSTOM_STRING_LITERAL__"')
            for literal in custom_literals(rule)
        )
    masked = replace_spans(masked, literal_replacements)
    normalized = re.sub(r"\s+", "", masked)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()
    return normalized, digest


def locale_assignment_manifest(text: str) -> dict[str, str]:
    manifest: dict[str, str] = {}
    setting = rules_by_title(text)["Global: Setting"]
    manifest["Global: Setting/totalScore"] = data_builder.normalize_expr(
        data_builder.find_assignment(setting.text, "totalScore").expression
    )
    for edition in LOCALE_SOURCES:
        for phase, tables in ((1, ("ITEM_NAME",)), (2, ("STAGE_NAME", "UPGRADE_NAME")), (3, ("STAGE_CODE",))):
            start, end = kr_builder.rule_span_by_subroutine(text, f"dataInit_{edition}{phase}")
            rule = text[start:end]
            for table in tables:
                manifest[f"{edition}{phase}/{table}"] = data_builder.normalize_expr(
                    data_builder.find_assignment(rule, table).expression
                )
    return manifest


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    lines = ["\t".join(fields)]
    for row in rows:
        lines.append("\t".join(tsv_value(row.get(field, "")) for field in fields).rstrip())
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_output(
    text: str,
    locale_baseline: str,
    data_report: dict[str, object],
    stage_deltas: list[dict[str, object]],
    unresolved: list[dict[str, object]],
    inventory: list[dict[str, object]],
) -> dict[str, object]:
    kr_text = kr_builder.build_text()
    kr_structure_text, _ = suppress_korean_only_messages(kr_text)
    rule_count = len(rule_blocks(text))
    kr_rule_count = len(rule_blocks(kr_text))
    if rule_count != kr_rule_count:
        raise BuildError(f"rule count changed: {rule_count} != {kr_rule_count}")
    if unresolved:
        raise BuildError(f"unresolved user-facing strings: {len(unresolved)}")

    placeholder_mismatches = [
        row for row in inventory if not placeholders_compatible(str(row["kr"]), str(row["en"]))
    ]
    if placeholder_mismatches:
        raise BuildError(f"Custom String placeholder mismatches: {len(placeholder_mismatches)}")

    color_token = re.compile(r"\{\d+\}[Ff][Gg][0-9A-Fa-f]{8}>")
    color_mismatches = [
        row
        for row in inventory
        if Counter(color_token.findall(str(row["kr"]))) != Counter(color_token.findall(str(row["en"])))
    ]
    if color_mismatches:
        raise BuildError(f"Custom String color markup mismatches: {len(color_mismatches)}")

    remaining_hangul: list[dict[str, object]] = []
    for rule in rule_blocks(text):
        for literal in custom_literals(rule):
            if contains_hangul(literal.value) and not allowed_hangul(rule.title, literal.ordinal, literal.value):
                remaining_hangul.append({"rule": rule.title, "ordinal": literal.ordinal, "value": literal.value})
    if remaining_hangul:
        raise BuildError(f"unapproved Hangul Custom Strings remain: {len(remaining_hangul)}")
    if "ow-restaurant.com/ko" in text:
        raise BuildError("Korean recipe URL remains in English output")

    expected_locale = locale_assignment_manifest(locale_baseline)
    observed_locale = locale_assignment_manifest(text)
    release_localized_name_overrides = {"org1/ITEM_NAME", "cafe1/ITEM_NAME", "gc1/ITEM_NAME"}
    locale_mismatches = [
        key
        for key in expected_locale
        if expected_locale[key] != observed_locale.get(key)
        and key not in release_localized_name_overrides
    ]
    if locale_mismatches:
        raise BuildError(f"localized assignment changed during text overlay: {locale_mismatches}")
    locale_manifest_payload = json.dumps(observed_locale, ensure_ascii=False, sort_keys=True)
    locale_manifest_sha = hashlib.sha256(locale_manifest_payload.encode("utf-8")).hexdigest().upper()

    kr_structure, kr_structure_sha = structural_fingerprint(kr_structure_text)
    en_structure, en_structure_sha = structural_fingerprint(text)
    if en_structure != kr_structure and en_structure_sha != APPROVED_RELEASE_STRUCTURE_SHA256:
        mismatch = next(
            (index for index, (kr_char, en_char) in enumerate(zip(kr_structure, en_structure)) if kr_char != en_char),
            min(len(kr_structure), len(en_structure)),
        )
        raise BuildError(
            "non-localized structure differs from KR Deluxe at normalized offset "
            f"{mismatch}; observed={en_structure_sha} approved={APPROVED_RELEASE_STRUCTURE_SHA256}"
        )

    source_rule_size = kr_builder.validate_assembled(kr_text)
    largest = {"name": "", "bytes": 0}
    for rule in rule_blocks(text):
        size = len(rule.text.replace("\r\n", "\n").encode("utf-8"))
        if size > largest["bytes"]:
            largest = {"name": rule.title, "bytes": size}
    if largest["bytes"] > source_rule_size["limit_bytes"]:
        raise BuildError(f"English source rule exceeds 98 KiB: {largest}")

    return {
        "rules": rule_count,
        "globals": 128,
        "subroutines": len(kr_builder.SUBROUTINE_NAMES),
        "custom_string_calls": text.count("Custom String("),
        "kr_custom_string_calls": kr_text.count("Custom String("),
        "custom_string_call_delta": text.count("Custom String(") - kr_text.count("Custom String("),
        "array_call_delta": text.count("Array(") - kr_text.count("Array("),
        "localized_data": data_report,
        "stage_code_deltas": stage_deltas,
        "remaining_unapproved_hangul": 0,
        "placeholder_mismatches": 0,
        "color_markup_mismatches": 0,
        "locale_assignment_manifest_sha256": locale_manifest_sha,
        "structural_fingerprint_sha256": en_structure_sha,
        "kr_structural_fingerprint_sha256": kr_structure_sha,
        "largest_rule": largest,
        "rule_limit_bytes": source_rule_size["limit_bytes"],
    }


def build_text() -> tuple[str, dict[str, object], list[dict[str, object]], list[dict[str, object]]]:
    text = kr_builder.build_text()
    text, data_report = localize_data_tables(text)
    text, total_score_report = localize_total_score(text)
    text, stage_deltas = localize_stage_code(text)
    text, serialized_ui_report = localize_serialized_ui_tables(text)
    text, korean_only_message_count = suppress_korean_only_messages(text)
    locale_baseline = text
    text, inventory, unresolved, translation_stats = translate_custom_strings(text)
    text, inventory, override_count = apply_output_overrides(text, inventory)
    translation_stats["output_overrides"] = override_count
    translation_stats["korean_only_messages_removed"] = korean_only_message_count
    translation_stats["translated"] = sum(row["en"] != row["kr"] for row in inventory)
    text, release_override_count = apply_release_code_overrides(text)
    translation_stats["release_code_overrides"] = release_override_count
    preliminary = {
        "localized_data": data_report,
        "total_score": total_score_report,
        "stage_code_deltas": stage_deltas,
        "serialized_ui_tables": serialized_ui_report,
        "translation": translation_stats,
    }
    if not unresolved:
        preliminary.update(
            validate_output(text, locale_baseline, data_report, stage_deltas, unresolved, inventory)
        )
    return text, preliminary, inventory, unresolved


def write_reports(
    text: str,
    report: dict[str, object],
    inventory: list[dict[str, object]],
    unresolved: list[dict[str, object]],
) -> tuple[str, int]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = text.replace("\r\n", "\n")
    digest = hashlib.sha256(output.encode("utf-8")).hexdigest().upper()
    report = dict(report)
    report.update({"sha256": digest, "bytes": len(output.encode("utf-8")), "unresolved": len(unresolved)})
    write_tsv(
        BUILD_DIR / "translation_inventory.tsv",
        inventory,
        ["rule", "ordinal", "source", "kr", "en", "placeholders"],
    )
    resolved = [row for row in inventory if row["en"] != row["kr"]]
    write_tsv(
        BUILD_DIR / "resolved_translation_map.tsv",
        resolved,
        ["rule", "ordinal", "source", "kr", "en", "placeholders"],
    )
    write_tsv(
        BUILD_DIR / "unresolved_strings.tsv",
        unresolved,
        ["rule", "ordinal", "kr", "placeholders"],
    )
    write_tsv(
        BUILD_DIR / "stage_code_delta.tsv",
        report["stage_code_deltas"],
        ["edition", "path", "kr", "en", "policy"],
    )
    (BUILD_DIR / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return digest, len(output.encode("utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate without writing en_deluxe.ow")
    parser.add_argument("--report", action="store_true", help="write translation reports even with unresolved strings")
    args = parser.parse_args()

    text, report, inventory, unresolved = build_text()
    output = text.replace("\r\n", "\n")
    digest = hashlib.sha256(output.encode("utf-8")).hexdigest().upper()
    byte_count = len(output.encode("utf-8"))
    if unresolved and not args.report:
        raise BuildError(f"{len(unresolved)} unresolved strings; run --report and complete manual_translations.tsv")
    if args.check and TARGET.exists():
        current = TARGET.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current != output:
            current_digest = hashlib.sha256(current.encode("utf-8")).hexdigest().upper()
            raise BuildError(
                f"{TARGET.name} differs from generated output: current={current_digest} generated={digest}"
            )
    if args.report or not args.check:
        write_reports(text, report, inventory, unresolved)
    if not unresolved and not args.check:
        TARGET.write_bytes(output.encode("utf-8"))
    print(f"rules={len(rule_blocks(text))} bytes={byte_count} sha256={digest} unresolved={len(unresolved)}")


if __name__ == "__main__":
    main()
