#!/usr/bin/env python3
"""Build jp_deluxe.ow from the current canonical KR Deluxe structure.

KR Deluxe remains authoritative for runtime code and canonical item indexes.
The standalone JP edition contributes legacy ORG localization only; explicit
Japanese Deluxe tables and reviewed translation overlays provide the rest.
"""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
KR_SCRIPT_DIR = ROOT / "scripts" / "kr_deluxe"
EN_SCRIPT_DIR = ROOT / "scripts" / "en_deluxe"
sys.path.insert(0, str(KR_SCRIPT_DIR))
sys.path.insert(0, str(EN_SCRIPT_DIR))

import build_deluxe_data as data_builder  # noqa: E402
import build_en_deluxe as locale_tools  # noqa: E402
import build_kr_deluxe as kr_builder  # noqa: E402


TARGET = ROOT / "jp_deluxe.ow"
KR_TARGET = ROOT / "kr_deluxe.ow"
BUILD_DIR = ROOT / "build" / "jp_deluxe"
ITEM_TABLE = Path(__file__).with_name("item_name_translations.tsv")
LOCALIZED_TABLES = Path(__file__).with_name("localized_tables.tsv")
MANUAL_TRANSLATIONS = Path(__file__).with_name("manual_translations.tsv")
LEGACY_CONTEXT_REMAP = Path(__file__).with_name("legacy_context_remap.tsv")
OUTPUT_OVERRIDES = Path(__file__).with_name("output_overrides.tsv")
RELEASE_CODE_OVERRIDES = Path(__file__).with_name("release_code_overrides.jsonl")
JP_SOURCE = ROOT / "jp.ow"
EN_TARGET = ROOT / "en_deluxe.ow"

EDITIONS = ("org", "cafe", "gc")
EDITION_LABEL = {"org": "ORG", "cafe": "CAFE", "gc": "GC"}
ITEM_COUNTS = {"org": 476, "cafe": 399, "gc": 464}
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
PINNED_HANGUL_LITERALS = {
    ("Global: Setting", 73): "Gummybear&변기클라우드\r\n難易度 : ★★★☆☆",
    ("Player: Spawn", 13): "한국어 : SPXXM\r\nEnglish : HTNZ3\r\n日本語 : 4ND1P",
    ("Player: Reload button", 2): "변기클라우드",
}
PINNED_RUNTIME_LITERALS = {
    ("Player: Reload button", 1): "{0}",
    ("Global subroutine: Save Progress", 0): "{0}",
    ("Global subroutine: Save Progress", 1): "{0}",
    ("Global subroutine: Load Progress", 0): "{0}",
    ("Global subroutine: Load Progress", 2): "{0}",
}
PINNED_OUTPUT_LITERALS = PINNED_HANGUL_LITERALS | PINNED_RUNTIME_LITERALS
FORBIDDEN_JAPANESE = ("豚",)
JAPANESE_SECONDS_CONTEXTS = {
    ("Dummy: Spawn", 34),
    ("Dummy: Spawn", 37),
    ("Dummy: Spawn", 41),
    ("Dummy: Spawn", 64),
}
JSON_STRING_TOKEN = r'"(?:\\.|[^"\\])*"'


class BuildError(RuntimeError):
    pass


def read_ow(path: Path) -> str:
    return data_builder.read_ow(path)


def load_verified_kr_baseline() -> str:
    """Refuse to build over a hand-edited KR file not captured by its generator."""
    prospective = kr_builder.build_text().replace("\r\n", "\n").encode("utf-8")
    if not KR_TARGET.exists():
        raise BuildError(f"missing canonical KR target: {KR_TARGET}")
    actual = KR_TARGET.read_bytes()
    if actual != prospective:
        actual_sha = hashlib.sha256(actual).hexdigest().upper()
        prospective_sha = hashlib.sha256(prospective).hexdigest().upper()
        raise BuildError(
            "kr_deluxe.ow differs from its prospective generator output; "
            f"reverse-sync manual edits first: actual={actual_sha} generated={prospective_sha}"
        )
    return read_ow(KR_TARGET)


def json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def contains_hangul(value: str) -> bool:
    return bool(re.search(r"[가-힣]", value))


def allowed_hangul(rule: str, ordinal: int, value: str) -> bool:
    return PINNED_HANGUL_LITERALS.get((rule, ordinal)) == value


def decode_tsv_escapes(value: str) -> str:
    return (
        value.replace("\\r", "\r")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .replace("\\x20", " ")
    )


def replace_assignment_in_subroutine(
    text: str, subroutine: str, name: str, expression: str
) -> str:
    start, end = kr_builder.rule_span_by_subroutine(text, subroutine)
    rule = text[start:end]
    assignment = data_builder.find_assignment(rule, name)
    replacement = f"\t\tGlobal.{name} = {expression};"
    rule = rule[: assignment.start] + replacement + rule[assignment.end :]
    return text[:start] + rule + text[end:]


def values_from_text(text: str, subroutine: str, name: str) -> list[object]:
    rule = data_builder.find_rule(text, subroutine)
    assignment = data_builder.find_assignment(rule, name)
    values = data_builder.eval_expr(assignment.expression)
    for _, _, index, patch_value in data_builder.find_patches(rule, name):
        values[index] = patch_value
    if not isinstance(values, list):
        raise BuildError(f"{subroutine}/{name} is not an array")
    return values


def validate_japanese(value: str, context: object) -> None:
    for forbidden in FORBIDDEN_JAPANESE:
        if forbidden in value:
            raise BuildError(f"forbidden Japanese text {forbidden!r} at {context!r}: {value!r}")


def serialized_string_expression(values: list[str]) -> tuple[str, int]:
    expression = data_builder.make_split_expression(values, "\t\t\t")
    if data_builder.eval_expr(expression) != values:
        raise BuildError("serialized string table failed to round-trip")
    chunks = [
        json.loads(match.group(1))
        for match in re.finditer(
            rf"Custom String\s*\(\s*({JSON_STRING_TOKEN})", expression
        )
    ]
    maximum = max(map(len, chunks), default=0)
    if maximum > 90:
        raise BuildError(f"serialized Custom String exceeds 90 characters: {maximum}")
    return expression, maximum


def read_item_table(kr_text: str) -> dict[str, list[str]]:
    en_text = read_ow(EN_TARGET)
    expected_sources: dict[str, tuple[list[object], list[object]]] = {}
    for edition in EDITIONS:
        subroutine = f"dataInit_{edition}1"
        expected_sources[edition] = (
            values_from_text(kr_text, subroutine, "ITEM_NAME"),
            values_from_text(en_text, subroutine, "ITEM_NAME"),
        )

    names: dict[str, list[str]] = {edition: [] for edition in EDITIONS}
    seen: set[tuple[str, int]] = set()
    with ITEM_TABLE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected_header = ("edition", "item_index", "kr", "en", "jp")
        if tuple(reader.fieldnames or ()) != expected_header:
            raise BuildError(f"unexpected ITEM_NAME table header: {reader.fieldnames!r}")
        for row in reader:
            label = row["edition"]
            if label not in EDITION_LABEL.values():
                raise BuildError(f"unknown ITEM_NAME edition: {label!r}")
            edition = label.lower()
            index = int(row["item_index"])
            key = (edition, index)
            if key in seen:
                raise BuildError(f"duplicate ITEM_NAME row: {key}")
            seen.add(key)
            kr_names, en_names = expected_sources[edition]
            if index != len(names[edition]):
                raise BuildError(
                    f"{label} ITEM_NAME index gap: expected {len(names[edition])}, got {index}"
                )
            if index >= len(kr_names) or index >= len(en_names):
                raise BuildError(f"{label} ITEM_NAME index out of range: {index}")
            if row["kr"] != kr_names[index] or row["en"] != en_names[index]:
                raise BuildError(
                    f"stale ITEM_NAME source identity at {label}:{index}: "
                    f"table={(row['kr'], row['en'])!r} "
                    f"current={(kr_names[index], en_names[index])!r}"
                )
            if not row["jp"]:
                raise BuildError(f"blank Japanese ITEM_NAME at {label}:{index}")
            validate_japanese(row["jp"], f"{label}:{index}")
            names[edition].append(row["jp"])

    for edition in EDITIONS:
        expected = ITEM_COUNTS[edition]
        if len(names[edition]) != expected:
            raise BuildError(
                f"{EDITION_LABEL[edition]} ITEM_NAME count {len(names[edition])} != {expected}"
            )
    if any(names[edition][9] != "怪しいスタンド" for edition in EDITIONS):
        raise BuildError("ITEM_NAME code 9 must be 怪しいスタンド in every edition")
    return names


def read_localized_tables(kr_text: str) -> dict[tuple[str, str], list[str]]:
    result: dict[tuple[str, str], list[str]] = {}

    jp_text = read_ow(JP_SOURCE)
    for table, expected in (("STAGE_NAME", 12), ("UPGRADE_NAME", 10)):
        values = values_from_text(jp_text, "dataInit2", table)
        if len(values) != expected or any(not isinstance(value, str) for value in values):
            raise BuildError(f"legacy JP {table} is invalid")
        result[("org", table)] = [str(value) for value in values]

    rows: dict[tuple[str, str], list[tuple[int, str, str]]] = defaultdict(list)
    with LOCALIZED_TABLES.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected_header = ("edition", "table", "item_index", "kr", "jp")
        if tuple(reader.fieldnames or ()) != expected_header:
            raise BuildError(f"unexpected localized-table header: {reader.fieldnames!r}")
        for row in reader:
            edition = row["edition"].lower()
            table = row["table"]
            if edition not in {"cafe", "gc"} or table not in {"STAGE_NAME", "UPGRADE_NAME"}:
                raise BuildError(f"invalid localized-table row: {row!r}")
            rows[(edition, table)].append((int(row["item_index"]), row["kr"], row["jp"]))

    for edition in ("cafe", "gc"):
        for table, expected in (("STAGE_NAME", 12), ("UPGRADE_NAME", 10)):
            source = values_from_text(kr_text, f"dataInit_{edition}2", table)
            entries = rows[(edition, table)]
            if len(entries) != expected:
                raise BuildError(f"{edition} {table} rows {len(entries)} != {expected}")
            localized: list[str] = []
            for expected_index, (index, kr_value, jp_value) in enumerate(entries):
                if index != expected_index or source[index] != kr_value:
                    raise BuildError(
                        f"stale {edition} {table} row {index}: {kr_value!r} != {source[index]!r}"
                    )
                if not jp_value:
                    raise BuildError(f"blank {edition} {table} row {index}")
                validate_japanese(jp_value, f"{edition}/{table}/{index}")
                localized.append(jp_value)
            result[(edition, table)] = localized
    return result


def localize_name_tables(text: str) -> tuple[str, dict[str, object]]:
    names = read_item_table(text)
    localized_tables = read_localized_tables(text)
    report: dict[str, object] = {
        "item_name_counts": {},
        "item_name_max_literal_chars": {},
        "stage_name_counts": {},
        "upgrade_name_counts": {},
    }
    for edition in EDITIONS:
        item_expression, maximum = serialized_string_expression(names[edition])
        text = replace_assignment_in_subroutine(
            text, f"dataInit_{edition}1", "ITEM_NAME", item_expression
        )
        report["item_name_counts"][edition] = len(names[edition])
        report["item_name_max_literal_chars"][edition] = maximum
        for table, key in (("STAGE_NAME", "stage_name_counts"), ("UPGRADE_NAME", "upgrade_name_counts")):
            values = localized_tables[(edition, table)]
            expression, _ = serialized_string_expression(values)
            text = replace_assignment_in_subroutine(
                text, f"dataInit_{edition}2", table, expression
            )
            report[key][edition] = len(values)
    return text, report


def patch_org_item_colors(text: str) -> tuple[str, list[dict[str, object]]]:
    """Preserve the legacy JP broth palette for the three narutomaki noodles."""
    start, end = kr_builder.rule_span_by_subroutine(text, "dataInit_org1")
    rule = text[start:end]
    assignment = data_builder.find_assignment(rule, "ITEM_COLOR")
    _, args, suffix = data_builder.unwrap_call(assignment.expression, "Mapped Array")
    if suffix or len(args) != 2:
        raise BuildError("ORG ITEM_COLOR mapped-array shape changed")
    values = data_builder.eval_expr(args[0])
    if not isinstance(values, list) or len(values) != ITEM_COUNTS["org"]:
        raise BuildError("ORG ITEM_COLOR base payload is invalid")
    changes: list[dict[str, object]] = []
    for index in (247, 249, 251):
        if values[index] != "C":
            raise BuildError(f"ORG ITEM_COLOR[{index}] anchor changed: {values[index]!r}")
        values[index] = "P"
        changes.append({"path": f"[{index}]", "kr": "C", "jp": "P"})
    replacement = data_builder.render_mapped_assignment(
        "Global.ITEM_COLOR", values, args[1], False
    )
    rule = rule[: assignment.start] + replacement + rule[assignment.end :]
    return text[:start] + rule + text[end:], changes


def jp_total_score_rows() -> dict[str, list[tuple[int, str]]]:
    setting = locale_tools.rules_by_title(read_ow(JP_SOURCE))["Global: Setting"]
    assignment = data_builder.find_assignment(setting.text, "totalScore")
    values = data_builder.eval_expr(assignment.expression)
    org: list[tuple[int, str]] = []
    for row in values:
        if not isinstance(row, list) or len(row) != 2:
            raise BuildError(f"legacy JP totalScore row is invalid: {row!r}")
        score, holder = row
        if not isinstance(score, (int, float)) or int(score) != score or not isinstance(holder, str):
            raise BuildError(f"legacy JP totalScore row is invalid: {row!r}")
        org.append((int(score), holder))
    if len(org) != 6:
        raise BuildError(f"legacy JP totalScore rows {len(org)} != 6")
    empty = [(0, "練習モード")] + [(0, "None")] * 5
    return {"org": org, "cafe": list(empty), "gc": list(empty)}


def total_score_expression(rows_by_edition: dict[str, list[tuple[int, str]]]) -> str:
    rows = rows_by_edition["org"] + rows_by_edition["cafe"] + rows_by_edition["gc"]
    rendered = ",\r\n\t\t\t".join(
        f"Array({score}, Custom String({json_string(holder)}))" for score, holder in rows
    )
    return (
        f"Array Slice(Array(\r\n\t\t\t{rendered}), "
        "Global.stageMode[0] * 6, 6)"
    )


def localize_total_score(text: str) -> tuple[str, dict[str, object]]:
    rows = jp_total_score_rows()
    expression = total_score_expression(rows)

    def patch(rule: str) -> str:
        assignment = data_builder.find_assignment(rule, "totalScore")
        replacement = f"\t\tGlobal.totalScore = {expression};"
        return rule[: assignment.start] + replacement + rule[assignment.end :]

    text = kr_builder.modify_rule(text, "Global: Setting", patch)
    report = {
        edition: [{"score": score, "holder": holder} for score, holder in values]
        for edition, values in rows.items()
    }
    return text, report


def serialized_numeric_expression(table: str, values: list[list[int]]) -> str:
    payload = data_builder.serialize_nested_numeric_list(table, values)
    chain = data_builder.make_custom_chain(payload, "\t\t\t")
    expression = f"String Split({chain}, Custom String(\"/\"))"
    observed = data_builder.decode_serialized_list_expression(table, expression)
    if observed != values:
        raise BuildError(f"{table} serialization round-trip failed")
    return expression


def patch_org_menu_tables(text: str) -> tuple[str, list[dict[str, object]]]:
    deltas: list[dict[str, object]] = []
    for table in ("MENU_LIST", "HAZARD_MENU_LIST", "FRIDGE_LIST"):
        rule = data_builder.find_rule(text, "dataInit_org2")
        assignment = data_builder.find_assignment(rule, table)
        values = data_builder.decode_serialized_list_expression(table, assignment.expression)
        if table == "MENU_LIST":
            expected = [85, 86, 87, 88, 89, 90, 96]
            replacement = [84, 85, 86, 87, 88, 89, 90, 96]
            if values[2] != expected:
                raise BuildError(f"ORG MENU_LIST[2] anchor changed: {values[2]!r}")
            values[2] = replacement
            deltas.append({"table": table, "path": "[2]", "kr": expected, "jp": replacement})
        elif table == "HAZARD_MENU_LIST":
            expected = [0, 190, 109, 110, 101, 102, 103, 120, 293, 145, 143]
            replacement = [0, 190, 109, 110, 101, 102, 103, 120, 293]
            if values[7] != expected:
                raise BuildError(f"ORG HAZARD_MENU_LIST[7] anchor changed: {values[7]!r}")
            values[7] = replacement
            deltas.append({"table": table, "path": "[7]", "kr": expected, "jp": replacement})
        else:
            if values[7][1] != 142:
                raise BuildError(f"ORG FRIDGE_LIST[7][1] anchor changed: {values[7][1]!r}")
            values[7][1] = 266
            deltas.append({"table": table, "path": "[7][1]", "kr": 142, "jp": 266})
        text = replace_assignment_in_subroutine(
            text, "dataInit_org2", table, serialized_numeric_expression(table, values)
        )
    return text, deltas


def patch_org_raw_recipes(text: str) -> tuple[str, list[dict[str, object]]]:
    start, end = kr_builder.rule_span_by_subroutine(text, "dataInit_org2")
    rule = text[start:end]
    mix_assignments = data_builder.find_all_assignments(rule, "RAW_MIX")
    result_assignments = data_builder.find_all_assignments(rule, "RAW_RESULT")
    if len(mix_assignments) != 2 or len(result_assignments) != 2:
        raise BuildError(
            f"ORG RAW assignment shape changed: mix={len(mix_assignments)} result={len(result_assignments)}"
        )
    left = [int(value) for value in data_builder.eval_expr(mix_assignments[0].expression)]
    right = [int(value) for value in data_builder.eval_expr(result_assignments[0].expression)]
    results = [int(value) for value in data_builder.eval_expr(result_assignments[1].expression)]
    if len({len(left), len(right), len(results)}) != 1:
        raise BuildError("ORG RAW arrays differ in length")

    changes = [
        ((144, 246, 247), (246, 267, 247)),
        ((144, 248, 249), (248, 267, 249)),
        ((144, 250, 251), (250, 267, 251)),
    ]
    report: list[dict[str, object]] = []
    for old, new in changes:
        matches = [
            index
            for index, triple in enumerate(zip(left, right, results))
            if triple == old or triple == (old[1], old[0], old[2])
        ]
        if len(matches) != 1:
            raise BuildError(f"ORG RAW recipe anchor {old!r} matched {matches!r}")
        index = matches[0]
        left[index], right[index], results[index] = new
        report.append({"row": index, "kr": old, "jp": new})

    mapper = "Index Of Array Value(Global.MIXING_RECIPE, Current Array Element)"
    replacements = [
        (
            mix_assignments[0].start,
            mix_assignments[0].end,
            data_builder.render_mapped_assignment("Global.RAW_MIX", left, mapper, False),
        ),
        (
            result_assignments[0].start,
            result_assignments[0].end,
            data_builder.render_mapped_assignment("Global.RAW_RESULT", right, mapper, False),
        ),
        (
            result_assignments[1].start,
            result_assignments[1].end,
            data_builder.render_mapped_assignment("Global.RAW_RESULT", results, mapper, False),
        ),
    ]
    rule = locale_tools.replace_spans(rule, replacements)
    return text[:start] + rule + text[end:], report


def patch_org_stage_code(text: str) -> tuple[str, list[dict[str, object]]]:
    rule = data_builder.find_rule(text, "dataInit_org3")
    assignment = data_builder.find_assignment(rule, "STAGE_CODE")
    _, mode_expressions, suffix = data_builder.unwrap_call(assignment.expression, "Array")
    if data_builder.normalize_expr(suffix) != "[Global.stageMode[1]]":
        raise BuildError(f"ORG STAGE_CODE mode selector changed: {suffix!r}")
    mode_one = data_builder.eval_expr(mode_expressions[1])
    paths = ((1, 7, 0), (1, 10, 0), (1, 13, 0))
    report: list[dict[str, object]] = []
    for path in paths:
        mode, stage, slot = path
        if mode != 1 or mode_one[stage][slot] != 4:
            actual = mode_one[stage][slot] if mode == 1 else "unsupported mode"
            raise BuildError(f"ORG STAGE_CODE{path} anchor changed: {actual!r}")
        mode_one[stage][slot] = 6
        report.append({"path": f"[{mode}][{stage}][{slot}]", "kr": 4, "jp": 6})
    rendered_mode = data_builder.render_array(mode_one, "\t\t\t")
    if assignment.expression.count(mode_expressions[1]) != 1:
        raise BuildError("ORG STAGE_CODE mode-1 expression is not uniquely anchored")
    expression = assignment.expression.replace(mode_expressions[1], rendered_mode, 1)
    text = replace_assignment_in_subroutine(text, "dataInit_org3", "STAGE_CODE", expression)
    return text, report


def localize_org_gameplay_data(text: str) -> tuple[str, dict[str, object]]:
    text, item_color_deltas = patch_org_item_colors(text)
    text, menu_deltas = patch_org_menu_tables(text)
    text, raw_deltas = patch_org_raw_recipes(text)
    text, stage_deltas = patch_org_stage_code(text)
    return text, {
        "item_color_deltas": item_color_deltas,
        "menu_deltas": menu_deltas,
        "raw_recipe_deltas": raw_deltas,
        "stage_code_deltas": stage_deltas,
    }


def patch_scoreboard_layout(text: str) -> tuple[str, list[dict[str, object]]]:
    """Keep the established JP vertical spacing for the left scoreboard column."""
    start, end = kr_builder.rule_span_by_subroutine(text, "gameSummary")
    rule = text[start:end]
    specs = (
        (r"(Local Player\.scbCutted\), Vector\(207\.140, )2\.200", r"\g<1>2.400", "cooked/cut", 2.200, 2.400),
        (r"(Local Player\.scbSurved\), Vector\(\s*207\.140, )2\.000", r"\g<1>2.200", "served", 2.000, 2.200),
        (r"(Local Player\.scbMissed\), Vector\(\s*207\.140, )1\.800", r"\g<1>2.000", "missed", 1.800, 2.000),
    )
    report: list[dict[str, object]] = []
    for pattern, replacement, label, kr_value, jp_value in specs:
        rule, count = re.subn(pattern, replacement, rule, count=1)
        if count != 1:
            raise BuildError(f"JP scoreboard layout anchor changed: {label}")
        report.append({"label": label, "kr_y": kr_value, "jp_y": jp_value})
    return text[:start] + rule + text[end:], report


def apply_shared_release_fixes(text: str) -> tuple[str, list[dict[str, object]]]:
    """Carry locale-neutral fixes already accepted by the released EN Deluxe."""
    report: list[dict[str, object]] = []
    replacements = (
        (
            "Global.totalScore[False] = (Global.totalScore[False] + True) % 5;",
            "Global.totalScore[False] = (Global.totalScore[False] + True) % 3;",
            "practice edition selector count",
        ),
        (
            "All Players(Team 1)[Global.superDrink].durability = All Players(Team 1)[Global.superDrink].durability / 10;",
            "All Players(Team 1)[Global.superDrink].durability = 100;",
            "Sandevistan durability activation",
        ),
        (
            "All Players(Team 1)[Global.superDrink].durability = All Players(Team 1)[Global.superDrink].durability * 10;",
            "All Players(Team 1)[Global.superDrink].durability = 1000;",
            "Sandevistan durability restoration",
        ),
    )
    for base, target, label in replacements:
        if text.count(base) != 1:
            raise BuildError(f"shared release-fix anchor changed: {label}")
        text = text.replace(base, target, 1)
        report.append({"label": label, "base": base, "target": target})

    start, end = kr_builder.rule_span_by_subroutine(text, "otherMenu")
    rule = text[start:end]
    else_start = rule.find(
        "\r\n\t\tElse;\r\n\t\t\tSmall Message(All Players(All Teams), Custom String("
    )
    if else_start < 0:
        raise BuildError("obsolete Other Menu branch anchor changed")
    end_marker = "\r\n\t\tEnd;"
    branch_end = rule.find(end_marker, else_start)
    if branch_end < 0:
        raise BuildError("obsolete Other Menu branch terminator changed")
    branch_end += len(end_marker)
    rule = rule[:else_start] + end_marker + rule[branch_end:]
    text = text[:start] + rule + text[end:]
    report.append({"label": "remove obsolete external Workshop-code branch"})
    return text, report


def apply_release_code_overrides(text: str) -> tuple[str, int]:
    """Apply reviewed JP-only structural edits without changing the KR baseline."""
    newline = "\r\n" if "\r\n" in text else "\n"
    count = 0
    with RELEASE_CODE_OVERRIDES.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            patch = json.loads(line)
            base = patch["base"].replace("\n", newline)
            target = patch["target"].replace("\n", newline)
            occurrences = text.count(base)
            if occurrences != 1:
                raise BuildError(
                    f"stale release code override at line {line_number}: "
                    f"base occurrences={occurrences}"
                )
            text = text.replace(base, target, 1)
            count += 1
    return text, count


def aligned_translation_maps(
    source_path: Path, target_path: Path
) -> tuple[dict[str, str], dict[tuple[str, int], str], dict[str, int]]:
    source_rules = locale_tools.rules_by_title(read_ow(source_path))
    target_rules = locale_tools.rules_by_title(read_ow(target_path))
    phrase_candidates: dict[str, set[str]] = defaultdict(set)
    context_candidates: dict[tuple[str, int], set[str]] = defaultdict(set)
    stats = {"rules": 0, "exact_rules": 0, "literals": 0, "local_context_literals": 0}

    def local_signatures(rule: locale_tools.RuleBlock) -> dict[tuple[str, str], list[locale_tools.CustomLiteral]]:
        literals = locale_tools.custom_literals(rule)
        signatures: dict[tuple[str, str], list[locale_tools.CustomLiteral]] = defaultdict(list)
        for index, literal in enumerate(literals):
            local_start = literal.start - rule.start
            local_end = literal.end - rule.start
            previous_end = literals[index - 1].end - rule.start if index else 0
            next_start = literals[index + 1].start - rule.start if index + 1 < len(literals) else len(rule.text)
            before = re.sub(r"\s+", "", rule.text[previous_end:local_start])[-240:]
            after = re.sub(r"\s+", "", rule.text[local_end:next_start])[:240]
            signatures[(before, after)].append(literal)
        return signatures

    for title in sorted(source_rules.keys() & target_rules.keys()):
        source_rule = source_rules[title]
        target_rule = target_rules[title]
        source_literals = locale_tools.custom_literals(source_rule)
        target_literals = locale_tools.custom_literals(target_rule)
        exact = (
            len(source_literals) == len(target_literals)
            and locale_tools.masked_rule(source_rule) == locale_tools.masked_rule(target_rule)
        )
        stats["rules"] += 1
        stats["exact_rules"] += int(exact)
        if exact:
            for source, target in zip(source_literals, target_literals):
                if not locale_tools.placeholders_compatible(source.value, target.value):
                    continue
                phrase_candidates[source.value].add(target.value)
                context_candidates[(title, source.ordinal)].add(target.value)
                stats["literals"] += 1

        if len(source_literals) == len(target_literals):
            source_signatures = local_signatures(source_rule)
            target_signatures = local_signatures(target_rule)
            for signature in source_signatures.keys() & target_signatures.keys():
                source_matches = source_signatures[signature]
                target_matches = target_signatures[signature]
                if len(source_matches) != 1 or len(target_matches) != 1:
                    continue
                source = source_matches[0]
                target = target_matches[0]
                if not locale_tools.placeholders_compatible(source.value, target.value):
                    continue
                phrase_candidates[source.value].add(target.value)
                context_candidates[(title, source.ordinal)].add(target.value)
                stats["local_context_literals"] += 1
    phrase_map = {
        source: next(iter(values))
        for source, values in phrase_candidates.items()
        if len(values) == 1
    }
    context_map = {
        key: next(iter(values))
        for key, values in context_candidates.items()
        if len(values) == 1
    }
    return phrase_map, context_map, stats


def exact_target_context_map(
    target_text: str, source_path: Path, localized_path: Path
) -> dict[tuple[str, int], str]:
    target_rules = locale_tools.rules_by_title(target_text)
    source_rules = locale_tools.rules_by_title(read_ow(source_path))
    localized_rules = locale_tools.rules_by_title(read_ow(localized_path))
    result: dict[tuple[str, int], str] = {}
    for title in target_rules.keys() & source_rules.keys() & localized_rules.keys():
        target_rule = target_rules[title]
        source_rule = source_rules[title]
        localized_rule = localized_rules[title]
        if locale_tools.masked_rule(target_rule) != locale_tools.masked_rule(source_rule):
            continue
        target_literals = locale_tools.custom_literals(target_rule)
        source_literals = locale_tools.custom_literals(source_rule)
        localized_literals = locale_tools.custom_literals(localized_rule)
        if len(target_literals) != len(source_literals) or len(source_literals) != len(localized_literals):
            continue
        for target, source, localized in zip(target_literals, source_literals, localized_literals):
            if target.value != source.value:
                continue
            if locale_tools.placeholders_compatible(target.value, localized.value):
                result[(title, target.ordinal)] = localized.value
    return result


def current_english_context_map(kr_text: str) -> dict[tuple[str, int], str]:
    kr_rules = locale_tools.rules_by_title(kr_text)
    en_rules = locale_tools.rules_by_title(read_ow(EN_TARGET))
    result: dict[tuple[str, int], str] = {}
    for title in kr_rules.keys() & en_rules.keys():
        kr_rule = kr_rules[title]
        en_rule = en_rules[title]
        kr_literals = locale_tools.custom_literals(kr_rule)
        en_literals = locale_tools.custom_literals(en_rule)
        if len(kr_literals) != len(en_literals):
            continue
        if locale_tools.masked_rule(kr_rule) != locale_tools.masked_rule(en_rule):
            continue
        for kr_literal, en_literal in zip(kr_literals, en_literals):
            if locale_tools.placeholders_compatible(kr_literal.value, en_literal.value):
                result[(title, kr_literal.ordinal)] = en_literal.value
    return result


def load_manual_translations() -> tuple[
    dict[str, str], dict[tuple[str, int | None, str], str]
]:
    global_map: dict[str, str] = {}
    context_map: dict[tuple[str, int | None, str], str] = {}
    with MANUAL_TRANSLATIONS.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = ("rule", "ordinal", "kr", "jp")
        if tuple(reader.fieldnames or ()) != expected:
            raise BuildError(f"unexpected manual-translation header: {reader.fieldnames!r}")
        for row in reader:
            kr_value = decode_tsv_escapes(row["kr"])
            jp_value = decode_tsv_escapes(row["jp"])
            if not kr_value or not jp_value:
                continue
            rule = row["rule"]
            ordinal = int(row["ordinal"]) if row["ordinal"].strip() else None
            if not locale_tools.placeholders_compatible(kr_value, jp_value):
                raise BuildError(f"manual placeholder mismatch: {kr_value!r} -> {jp_value!r}")
            validate_japanese(jp_value, (rule, ordinal, kr_value))
            if rule:
                key = (rule, ordinal, kr_value)
                if key in context_map and context_map[key] != jp_value:
                    raise BuildError(f"conflicting contextual manual translation: {key!r}")
                context_map[key] = jp_value
            elif kr_value in global_map and global_map[kr_value] != jp_value:
                raise BuildError(f"conflicting global manual translation: {kr_value!r}")
            else:
                global_map[kr_value] = jp_value
    return global_map, context_map


def load_legacy_context_remap(
    target_text: str,
) -> dict[tuple[str, int], str]:
    """Reuse shifted legacy JP literals only when the old Korean anchor is exact."""
    target_rules = locale_tools.rules_by_title(target_text)
    legacy_kr_rules = locale_tools.rules_by_title(read_ow(ROOT / "ko.ow"))
    legacy_jp_rules = locale_tools.rules_by_title(read_ow(JP_SOURCE))
    result: dict[tuple[str, int], str] = {}
    with LEGACY_CONTEXT_REMAP.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = (
            "target_rule",
            "target_ordinal",
            "legacy_rule",
            "legacy_kr_ordinal",
            "legacy_jp_ordinal",
        )
        if tuple(reader.fieldnames or ()) != expected:
            raise BuildError(f"unexpected legacy-context header: {reader.fieldnames!r}")
        for row in reader:
            target_key = (row["target_rule"], int(row["target_ordinal"]))
            legacy_kr_key = (row["legacy_rule"], int(row["legacy_kr_ordinal"]))
            legacy_jp_key = (row["legacy_rule"], int(row["legacy_jp_ordinal"]))
            if target_key in result:
                raise BuildError(f"duplicate legacy-context target: {target_key!r}")
            try:
                target_literal = locale_tools.custom_literals(target_rules[target_key[0]])[
                    target_key[1]
                ]
                legacy_kr_literal = locale_tools.custom_literals(
                    legacy_kr_rules[legacy_kr_key[0]]
                )[
                    legacy_kr_key[1]
                ]
                legacy_jp_literal = locale_tools.custom_literals(
                    legacy_jp_rules[legacy_jp_key[0]]
                )[
                    legacy_jp_key[1]
                ]
            except (KeyError, IndexError) as exc:
                raise BuildError(
                    "legacy-context location is missing: "
                    f"target={target_key!r} legacy_kr={legacy_kr_key!r} "
                    f"legacy_jp={legacy_jp_key!r}"
                ) from exc
            if target_literal.value != legacy_kr_literal.value:
                raise BuildError(
                    "legacy-context Korean anchor changed: "
                    f"target={target_key!r} legacy_kr={legacy_kr_key!r} "
                    f"current={target_literal.value!r} old={legacy_kr_literal.value!r}"
                )
            if not locale_tools.placeholders_compatible(
                target_literal.value, legacy_jp_literal.value
            ):
                raise BuildError(
                    "legacy-context placeholder mismatch: "
                    f"target={target_key!r} legacy_jp={legacy_jp_key!r}"
                )
            validate_japanese(legacy_jp_literal.value, target_key)
            result[target_key] = legacy_jp_literal.value
    return result


def translate_custom_strings(
    text: str, kr_text: str
) -> tuple[str, list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    direct_phrase, _direct_context, direct_stats = aligned_translation_maps(
        ROOT / "ko.ow", JP_SOURCE
    )
    en_phrase, _en_context, en_stats = aligned_translation_maps(
        ROOT / "en.ow", JP_SOURCE
    )
    exact_context = exact_target_context_map(kr_text, ROOT / "ko.ow", JP_SOURCE)
    remapped_context = load_legacy_context_remap(text)
    current_en = current_english_context_map(kr_text)
    manual_global, manual_context = load_manual_translations()
    used_global: set[str] = set()
    used_context: set[tuple[str, int | None, str]] = set()
    replacements: list[tuple[int, int, str]] = []
    inventory: list[dict[str, object]] = []
    unresolved: list[dict[str, object]] = []

    for rule in locale_tools.rule_blocks(text):
        for literal in locale_tools.custom_literals(rule):
            value = literal.value
            translated = value
            source = "unchanged"
            key = (rule.title, literal.ordinal)
            if rule.title not in DATA_RULE_TITLES:
                contextual = (rule.title, literal.ordinal, value)
                rule_wide = (rule.title, None, value)
                if contextual in manual_context:
                    translated = manual_context[contextual]
                    used_context.add(contextual)
                    source = "manual-context"
                elif rule_wide in manual_context:
                    translated = manual_context[rule_wide]
                    used_context.add(rule_wide)
                    source = "manual-context"
                elif value in manual_global:
                    translated = manual_global[value]
                    used_global.add(value)
                    source = "manual-global"
                elif key in JAPANESE_SECONDS_CONTEXTS:
                    if value.count("초") != 1:
                        raise BuildError(f"Japanese seconds anchor changed at {key}: {value!r}")
                    translated = value.replace("초", "秒", 1)
                    source = "duration-token"
                elif key in exact_context:
                    translated = exact_context[key]
                    source = "legacy-context"
                elif key in remapped_context:
                    translated = remapped_context[key]
                    source = "legacy-remap"
                elif value in direct_phrase:
                    translated = direct_phrase[value]
                    source = "legacy-phrase"
                elif key in current_en:
                    en_value = current_en[key]
                    if en_value in en_phrase:
                        translated = en_phrase[en_value]
                        source = "english-phrase-bridge"

                if not locale_tools.placeholders_compatible(value, translated):
                    raise BuildError(
                        f"placeholder mismatch at {key}: {value!r} -> {translated!r}"
                    )
                validate_japanese(translated, key)
                if translated != value:
                    replacements.append((literal.start, literal.end, json_string(translated)))
                elif contains_hangul(value) and allowed_hangul(
                    rule.title, literal.ordinal, value
                ):
                    source = "allowlisted"
                elif contains_hangul(value):
                    source = "unresolved"
                    unresolved.append(
                        {
                            "rule": rule.title,
                            "ordinal": literal.ordinal,
                            "kr": value,
                            "en": current_en.get(key, ""),
                            "placeholders": " ".join(locale_tools.placeholder_signature(value)),
                        }
                    )

            inventory.append(
                {
                    "rule": rule.title,
                    "ordinal": literal.ordinal,
                    "source": source,
                    "kr": value,
                    "jp": translated,
                    "en": current_en.get(key, ""),
                    "placeholders": " ".join(locale_tools.placeholder_signature(value)),
                }
            )

    unused_global = sorted(set(manual_global) - used_global)
    unused_context = sorted(set(manual_context) - used_context)
    if unused_global or unused_context:
        raise BuildError(
            f"unused manual translations: global={unused_global[:5]!r} "
            f"context={unused_context[:5]!r}"
        )

    stats: dict[str, object] = {
        "inventory": len(inventory),
        "translated": sum(row["jp"] != row["kr"] for row in inventory),
        "unresolved": len(unresolved),
        "allowlisted": sum(row["source"] == "allowlisted" for row in inventory),
        "manual_global_entries": len(manual_global),
        "manual_context_entries": len(manual_context),
        "direct_source": direct_stats,
        "english_bridge_source": en_stats,
    }
    return locale_tools.replace_spans(text, replacements), inventory, unresolved, stats


def apply_output_overrides(
    text: str, inventory: list[dict[str, object]]
) -> tuple[str, list[dict[str, object]], int]:
    overrides: dict[tuple[str, int], tuple[str, str]] = {}
    with OUTPUT_OVERRIDES.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        expected = ("rule", "ordinal", "base_json", "target_json")
        if tuple(reader.fieldnames or ()) != expected:
            raise BuildError(f"unexpected output-override header: {reader.fieldnames!r}")
        for row in reader:
            key = (row["rule"], int(row["ordinal"]))
            if key in overrides:
                raise BuildError(f"duplicate output override: {key}")
            if key[0] in DATA_RULE_TITLES:
                raise BuildError(f"output overrides may not target data-init rules: {key}")
            if key in PINNED_OUTPUT_LITERALS:
                raise BuildError(f"output override may not target a pinned control literal: {key}")
            base = json.loads(row["base_json"])
            target = json.loads(row["target_json"])
            if not locale_tools.placeholders_compatible(base, target):
                raise BuildError(f"output override placeholder mismatch: {key}")
            validate_japanese(target, key)
            overrides[key] = (base, target)

    replacements: list[tuple[int, int, str]] = []
    seen: set[tuple[str, int]] = set()
    by_key = {(str(row["rule"]), int(row["ordinal"])): row for row in inventory}
    for rule in locale_tools.rule_blocks(text):
        for literal in locale_tools.custom_literals(rule):
            key = (rule.title, literal.ordinal)
            if key not in overrides:
                continue
            base, target = overrides[key]
            if literal.value != base:
                raise BuildError(
                    f"stale output override at {key}: expected {base!r}, got {literal.value!r}"
                )
            replacements.append((literal.start, literal.end, json_string(target)))
            row = by_key[key]
            row["jp"] = target
            row["source"] = f"{row['source']}+output-override"
            seen.add(key)
    missing = sorted(set(overrides) - seen)
    if missing:
        raise BuildError(f"unused output overrides: {missing[:5]}")
    return locale_tools.replace_spans(text, replacements), inventory, len(overrides)


def mask_assignments_in_subroutine(
    text: str, subroutine: str, names: Iterable[str]
) -> str:
    start, end = kr_builder.rule_span_by_subroutine(text, subroutine)
    rule = text[start:end]
    replacements: list[tuple[int, int, str]] = []
    for name in names:
        assignments = data_builder.find_all_assignments(rule, name)
        for ordinal, assignment in enumerate(assignments):
            replacements.append(
                (
                    assignment.start,
                    assignment.end,
                    f"\t\tGlobal.{name} = __LOCALE_{name}_{ordinal}__;",
                )
            )
    rule = locale_tools.replace_spans(rule, replacements)
    return text[:start] + rule + text[end:]


def structural_fingerprint(text: str) -> tuple[str, str]:
    masked = text
    for edition in EDITIONS:
        masked = mask_assignments_in_subroutine(
            masked,
            f"dataInit_{edition}1",
            ("ITEM_NAME", "ITEM_COLOR") if edition == "org" else ("ITEM_NAME",),
        )
        masked = mask_assignments_in_subroutine(
            masked, f"dataInit_{edition}2", ("STAGE_NAME", "UPGRADE_NAME")
        )
        masked = mask_assignments_in_subroutine(
            masked, f"dataInit_{edition}3", ("STAGE_CODE",)
        )
    masked = mask_assignments_in_subroutine(
        masked,
        "dataInit_org2",
        ("RAW_MIX", "RAW_RESULT", "MENU_LIST", "HAZARD_MENU_LIST", "FRIDGE_LIST"),
    )

    def mask_total(rule: str) -> str:
        assignment = data_builder.find_assignment(rule, "totalScore")
        replacement = "\t\tGlobal.totalScore = __LOCALE_totalScore__;"
        return rule[: assignment.start] + replacement + rule[assignment.end :]

    masked = kr_builder.modify_rule(masked, "Global: Setting", mask_total)
    literal_replacements: list[tuple[int, int, str]] = []
    for rule in locale_tools.rule_blocks(masked):
        if rule.title in DATA_RULE_TITLES:
            continue
        literal_replacements.extend(
            (literal.start, literal.end, '"__CUSTOM_STRING_LITERAL__"')
            for literal in locale_tools.custom_literals(rule)
        )
    masked = locale_tools.replace_spans(masked, literal_replacements)
    normalized = re.sub(r"\s+", "", masked)
    for variable in ("scbCutted", "scbSurved", "scbMissed"):
        normalized = re.sub(
            rf"(LocalPlayer\.{variable}\),Vector\(207\.140,)(?:1\.800|2\.000|2\.200|2\.400)",
            rf"\1__JP_SCOREBOARD_Y__",
            normalized,
            count=1,
        )
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest().upper()
    return normalized, digest


def serialized_table_values(text: str, subroutine: str, name: str) -> list[list[int]]:
    rule = data_builder.find_rule(text, subroutine)
    assignment = data_builder.find_assignment(rule, name)
    return data_builder.decode_serialized_list_expression(name, assignment.expression)


def raw_recipe_triples(text: str, subroutine: str) -> list[tuple[int, int, int]]:
    rule = data_builder.find_rule(text, subroutine)
    mix_assignments = data_builder.find_all_assignments(rule, "RAW_MIX")
    result_assignments = data_builder.find_all_assignments(rule, "RAW_RESULT")
    if len(mix_assignments) != 2 or len(result_assignments) != 2:
        raise BuildError(
            f"{subroutine} RAW assignment shape changed: "
            f"mix={len(mix_assignments)} result={len(result_assignments)}"
        )
    left = [int(value) for value in data_builder.eval_expr(mix_assignments[0].expression)]
    right = [int(value) for value in data_builder.eval_expr(result_assignments[0].expression)]
    results = [int(value) for value in data_builder.eval_expr(result_assignments[1].expression)]
    if len({len(left), len(right), len(results)}) != 1:
        raise BuildError(f"{subroutine} RAW arrays differ in length")
    return list(zip(left, right, results))


def raw_assignment_shapes(text: str, subroutine: str) -> dict[str, object]:
    """Capture every RAW mapper/wrapper expression while excluding data payloads."""
    rule = data_builder.find_rule(text, subroutine)
    mix_assignments = data_builder.find_all_assignments(rule, "RAW_MIX")
    result_assignments = data_builder.find_all_assignments(rule, "RAW_RESULT")
    if len(mix_assignments) != 2 or len(result_assignments) != 2:
        raise BuildError(f"{subroutine} RAW assignment shape changed")
    mapper_shapes: list[tuple[str, str]] = []
    for assignment in (
        mix_assignments[0],
        result_assignments[0],
        result_assignments[1],
    ):
        _, args, suffix = data_builder.unwrap_call(assignment.expression, "Mapped Array")
        if len(args) != 2:
            raise BuildError(f"{subroutine} RAW mapped-array argument count changed")
        mapper_shapes.append(
            (data_builder.normalize_expr(args[1]), data_builder.normalize_expr(suffix))
        )
    return {
        "payload_mappers": mapper_shapes,
        "packed_mix": data_builder.normalize_expr(mix_assignments[1].expression),
    }


def stage_code_parts(text: str, subroutine: str) -> tuple[list[str], str]:
    rule = data_builder.find_rule(text, subroutine)
    assignment = data_builder.find_assignment(rule, "STAGE_CODE")
    _, parts, suffix = data_builder.unwrap_call(assignment.expression, "Array")
    return parts, data_builder.normalize_expr(suffix)


def mapped_assignment_shape(text: str, subroutine: str, name: str) -> tuple[str, str]:
    rule = data_builder.find_rule(text, subroutine)
    assignment = data_builder.find_assignment(rule, name)
    _, args, suffix = data_builder.unwrap_call(assignment.expression, "Mapped Array")
    if len(args) != 2:
        raise BuildError(f"{subroutine} {name} mapped-array shape changed")
    return data_builder.normalize_expr(args[1]), data_builder.normalize_expr(suffix)


def verify_final_localized_data(text: str, kr_text: str) -> dict[str, object]:
    """Decode the completed output and independently prove every approved data delta."""
    item_names = read_item_table(kr_text)
    localized_names = read_localized_tables(kr_text)
    localized_checks = 0
    for edition in EDITIONS:
        sub1 = f"dataInit_{edition}1"
        sub2 = f"dataInit_{edition}2"
        if values_from_text(text, sub1, "ITEM_NAME") != item_names[edition]:
            raise BuildError(f"{edition} final ITEM_NAME differs from authoritative table")
        localized_checks += 1
        for table in ("STAGE_NAME", "UPGRADE_NAME"):
            if values_from_text(text, sub2, table) != localized_names[(edition, table)]:
                raise BuildError(f"{edition} final {table} differs from authoritative table")
            localized_checks += 1

    kr_colors = values_from_text(kr_text, "dataInit_org1", "ITEM_COLOR")
    jp_colors = values_from_text(text, "dataInit_org1", "ITEM_COLOR")
    if mapped_assignment_shape(text, "dataInit_org1", "ITEM_COLOR") != mapped_assignment_shape(
        kr_text, "dataInit_org1", "ITEM_COLOR"
    ):
        raise BuildError("final ORG ITEM_COLOR palette mapper changed")
    expected_colors = list(kr_colors)
    for index in (247, 249, 251):
        expected_colors[index] = "P"
    if jp_colors != expected_colors:
        differing = [
            index
            for index, (kr_value, jp_value) in enumerate(zip(kr_colors, jp_colors))
            if kr_value != jp_value
        ]
        raise BuildError(f"final ORG ITEM_COLOR has unapproved deltas: {differing[:20]!r}")

    menu_specs: dict[str, tuple[tuple[int, ...], object]] = {
        "MENU_LIST": ((2,), [84, 85, 86, 87, 88, 89, 90, 96]),
        "HAZARD_MENU_LIST": ((7,), [0, 190, 109, 110, 101, 102, 103, 120, 293]),
        "FRIDGE_LIST": ((7, 1), 266),
    }
    for table, (path, replacement) in menu_specs.items():
        kr_values = serialized_table_values(kr_text, "dataInit_org2", table)
        expected_values = copy.deepcopy(kr_values)
        cursor: object = expected_values
        for index in path[:-1]:
            cursor = cursor[index]  # type: ignore[index]
        cursor[path[-1]] = replacement  # type: ignore[index]
        observed = serialized_table_values(text, "dataInit_org2", table)
        if observed != expected_values:
            raise BuildError(f"final ORG {table} differs outside approved path {path!r}")

    raw_changes = (
        ((144, 246, 247), (246, 267, 247)),
        ((144, 248, 249), (248, 267, 249)),
        ((144, 250, 251), (250, 267, 251)),
    )
    kr_org_raw = raw_recipe_triples(kr_text, "dataInit_org2")
    if len(kr_org_raw) != 306:
        raise BuildError(f"ORG RAW recipe count changed: {len(kr_org_raw)} != 306")
    expected_org_raw = list(kr_org_raw)
    changed_rows: list[int] = []
    for old, new in raw_changes:
        matches = [
            index
            for index, triple in enumerate(expected_org_raw)
            if triple == old or triple == (old[1], old[0], old[2])
        ]
        if len(matches) != 1:
            raise BuildError(f"final ORG RAW validation anchor {old!r} matched {matches!r}")
        row = matches[0]
        expected_org_raw[row] = new
        changed_rows.append(row)
    if raw_recipe_triples(text, "dataInit_org2") != expected_org_raw:
        raise BuildError("final ORG RAW recipes differ outside the three approved replacements")
    for edition in EDITIONS:
        subroutine = f"dataInit_{edition}2"
        if raw_assignment_shapes(text, subroutine) != raw_assignment_shapes(kr_text, subroutine):
            raise BuildError(f"final {edition.upper()} RAW mapper/wrapper semantics changed")
        if edition != "org" and raw_recipe_triples(text, subroutine) != raw_recipe_triples(
            kr_text, subroutine
        ):
            raise BuildError(f"final {edition.upper()} RAW recipes differ from KR Deluxe")

    stage_paths = ((7, 0), (10, 0), (13, 0))
    for edition in EDITIONS:
        subroutine = f"dataInit_{edition}3"
        kr_parts, kr_suffix = stage_code_parts(kr_text, subroutine)
        jp_parts, jp_suffix = stage_code_parts(text, subroutine)
        if kr_suffix != jp_suffix or len(kr_parts) != len(jp_parts):
            raise BuildError(f"final {edition.upper()} STAGE_CODE shape changed")
        if edition != "org":
            if [data_builder.normalize_expr(part) for part in jp_parts] != [
                data_builder.normalize_expr(part) for part in kr_parts
            ]:
                raise BuildError(f"final {edition.upper()} STAGE_CODE differs from KR Deluxe")
            continue
        for mode, (kr_part, jp_part) in enumerate(zip(kr_parts, jp_parts)):
            if mode != 1:
                if data_builder.normalize_expr(jp_part) != data_builder.normalize_expr(kr_part):
                    raise BuildError(f"final ORG STAGE_CODE mode {mode} changed unexpectedly")
                continue
            expected_mode = copy.deepcopy(data_builder.eval_expr(kr_part))
            for stage, slot in stage_paths:
                expected_mode[stage][slot] = 6
            if data_builder.eval_expr(jp_part) != expected_mode:
                raise BuildError("final ORG STAGE_CODE differs outside the three approved leaves")

    setting_rule = locale_tools.rules_by_title(text)["Global: Setting"]
    total_assignment = data_builder.find_assignment(setting_rule.text, "totalScore")
    expected_total = total_score_expression(jp_total_score_rows())
    if data_builder.normalize_expr(total_assignment.expression) != data_builder.normalize_expr(
        expected_total
    ):
        raise BuildError("final Japanese totalScore payload differs from the edition table")

    summary_rule = data_builder.find_rule(text, "gameSummary")
    scoreboard_values = {
        "scbCutted": "2.400",
        "scbSurved": "2.200",
        "scbMissed": "2.000",
    }
    for variable, y_value in scoreboard_values.items():
        pattern = rf"Local Player\.{variable}\), Vector\(\s*207\.140, {y_value}"
        if len(re.findall(pattern, summary_rule)) != 1:
            raise BuildError(f"final JP scoreboard coordinate is wrong for {variable}")

    return {
        "localized_table_checks": localized_checks,
        "org_item_color_changed_indices": [247, 249, 251],
        "org_menu_paths": ["MENU_LIST[2]", "HAZARD_MENU_LIST[7]", "FRIDGE_LIST[7][1]"],
        "org_raw_changed_rows": changed_rows,
        "raw_mapper_wrappers_unchanged": True,
        "org_stage_code_paths": ["[1][7][0]", "[1][10][0]", "[1][13][0]"],
        "cafe_gc_raw_unchanged": True,
        "cafe_gc_stage_code_unchanged": True,
        "total_score_rows": 18,
        "total_score_verified": True,
        "scoreboard_layout_verified": True,
    }


def verify_locale_neutral_source_shape(text: str) -> dict[str, object]:
    stack: list[tuple[str, int]] = []
    pairs = {")": "(", "]": "[", "}": "{"}
    in_string = False
    escaped = False
    for index, char in enumerate(text):
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            stack.append((char, index))
        elif char in pairs:
            if not stack or stack[-1][0] != pairs[char]:
                raise BuildError(f"unbalanced delimiter {char!r} at offset {index}")
            stack.pop()
    if in_string or stack:
        raise BuildError("unclosed string or delimiter in Japanese output")

    for name in (
        "dataInit_org1",
        "dataInit_org2",
        "dataInit_org3",
        "dataInit_cafe1",
        "dataInit_cafe2",
        "dataInit_cafe3",
        "dataInit_gc1",
        "dataInit_gc2",
        "dataInit_gc3",
        "dataInit_customerCommon",
        "menuInit",
        "otherMenu",
    ):
        if len(re.findall(rf"(?mi)^[ \t]+{re.escape(name)};\r?$", text)) != 1:
            raise BuildError(f"Japanese generated subroutine event count mismatch: {name}")
    if re.search(r"Mapped Array\s*\([^;]*Mapped Array\s*\(", text, re.DOTALL):
        raise BuildError("nested Mapped Array remains in Japanese output")

    global_section = text[text.index("\tglobal:") : text.index("\tplayer:")]
    globals_found = [
        (int(number), name)
        for number, name in re.findall(
            r"(?m)^[ \t]+(\d+):\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", global_section
        )
    ]
    if [number for number, _ in globals_found] != list(range(128)):
        raise BuildError("Japanese global variable IDs are not exactly 0..127")
    globals_by_id = dict(globals_found)
    if globals_by_id.get(100) != "ICE_NEEDED" or globals_by_id.get(105) != "ICE_RESULT":
        raise BuildError("Japanese global IDs 100/105 are not ICE_NEEDED/ICE_RESULT")
    if globals_by_id.get(126) != "DELUXE_DATA":
        raise BuildError("Japanese global variable 126 is not DELUXE_DATA")

    sub_start = text.index("subroutines\r\n{")
    sub_open = text.index("{", sub_start)
    sub_end = data_builder.scan_balanced(text, sub_open, "{", "}")
    sub_section = text[sub_start:sub_end]
    subs_found = [
        (int(number), name)
        for number, name in re.findall(
            r"(?m)^[ \t]+(\d+):\s*([A-Za-z_][A-Za-z0-9_]*)\s*$", sub_section
        )
    ]
    if [number for number, _ in subs_found] != list(range(len(kr_builder.SUBROUTINE_NAMES))):
        raise BuildError("Japanese subroutine IDs are not contiguous")
    if tuple(name for _, name in subs_found) != kr_builder.SUBROUTINE_NAMES:
        raise BuildError("Japanese subroutine declaration order changed")
    return {
        "delimiter_balance": True,
        "globals": len(globals_found),
        "subroutines": len(subs_found),
        "nested_mapped_arrays": 0,
    }


def validate_output(
    text: str,
    kr_text: str,
    inventory: list[dict[str, object]],
    unresolved: list[dict[str, object]],
    data_report: dict[str, object],
) -> dict[str, object]:
    if unresolved:
        raise BuildError(f"unresolved user-facing Japanese strings: {len(unresolved)}")
    rule_count = len(locale_tools.rule_blocks(text))
    kr_rule_count = len(locale_tools.rule_blocks(kr_text))
    if rule_count != kr_rule_count:
        raise BuildError(f"rule count changed: {rule_count} != {kr_rule_count}")

    placeholder_mismatches = [
        row
        for row in inventory
        if not locale_tools.placeholders_compatible(str(row["kr"]), str(row["jp"]))
    ]
    if placeholder_mismatches:
        raise BuildError(f"Custom String placeholder mismatches: {len(placeholder_mismatches)}")

    color_token = re.compile(r"\{\d+\}[Ff][Gg][0-9A-Fa-f]{8}>")
    color_mismatches = [
        row
        for row in inventory
        if Counter(color_token.findall(str(row["kr"])))
        != Counter(color_token.findall(str(row["jp"])))
    ]
    if color_mismatches:
        raise BuildError(f"Custom String color-markup mismatches: {len(color_mismatches)}")

    output_rules = locale_tools.rules_by_title(text)
    remaining_hangul: list[tuple[str, int, str]] = []
    maximum_literal = {"rule": "", "ordinal": -1, "characters": 0}
    for rule in output_rules.values():
        for literal in locale_tools.custom_literals(rule):
            literal_length = len(literal.value)
            if literal_length > maximum_literal["characters"]:
                maximum_literal = {
                    "rule": rule.title,
                    "ordinal": literal.ordinal,
                    "characters": literal_length,
                }
            if literal_length > 128:
                raise BuildError(
                    f"Custom String exceeds 128 characters at {(rule.title, literal.ordinal)}: "
                    f"{literal_length}"
                )
            if contains_hangul(literal.value) and not allowed_hangul(
                rule.title, literal.ordinal, literal.value
            ):
                remaining_hangul.append((rule.title, literal.ordinal, literal.value))
    if remaining_hangul:
        raise BuildError(f"unapproved Hangul Custom Strings remain: {len(remaining_hangul)}")
    for key, expected_value in PINNED_OUTPUT_LITERALS.items():
        try:
            observed = locale_tools.custom_literals(output_rules[key[0]])[key[1]].value
        except (KeyError, IndexError) as exc:
            raise BuildError(f"pinned Japanese control literal is missing: {key}") from exc
        if observed != expected_value:
            raise BuildError(
                f"pinned Japanese control literal changed at {key}: {observed!r}"
            )
    for forbidden in FORBIDDEN_JAPANESE:
        if forbidden in text:
            raise BuildError(f"forbidden Japanese text remains in output: {forbidden!r}")
    locale_paths = set(re.findall(r"ow-restaurant\.com/([A-Za-z]{2})", text))
    if locale_paths != {"ja"}:
        raise BuildError(f"Japanese recipe URL locale paths are wrong: {sorted(locale_paths)!r}")
    versions = set(re.findall(r"\bv\d{6}\b", text))
    if versions != {"v260902"}:
        raise BuildError(f"Japanese release version set is wrong: {sorted(versions)!r}")

    structure_baseline, _ = apply_shared_release_fixes(kr_text)
    structure_baseline, _ = locale_tools.suppress_korean_only_messages(structure_baseline)
    structure_baseline, _ = apply_release_code_overrides(structure_baseline)
    jp_structure, jp_structure_sha = structural_fingerprint(text)
    kr_structure, kr_structure_sha = structural_fingerprint(structure_baseline)
    if jp_structure != kr_structure:
        mismatch = next(
            (
                index
                for index, (kr_char, jp_char) in enumerate(zip(kr_structure, jp_structure))
                if kr_char != jp_char
            ),
            min(len(kr_structure), len(jp_structure)),
        )
        raise BuildError(
            f"non-localized structure differs from KR Deluxe at normalized offset {mismatch}"
        )

    source_rule_size = kr_builder.validate_assembled(kr_text)
    source_shape = verify_locale_neutral_source_shape(text)
    largest = {"name": "", "bytes": 0}
    for rule in locale_tools.rule_blocks(text):
        size = len(rule.text.replace("\r\n", "\n").encode("utf-8"))
        if size > largest["bytes"]:
            largest = {"name": rule.title, "bytes": size}
    if largest["bytes"] > source_rule_size["limit_bytes"]:
        raise BuildError(f"Japanese source rule exceeds 98 KiB: {largest}")

    output_data_assertions = verify_final_localized_data(text, kr_text)

    return {
        "rules": rule_count,
        "globals": source_shape["globals"],
        "subroutines": source_shape["subroutines"],
        "custom_string_calls": text.count("Custom String("),
        "kr_custom_string_calls": kr_text.count("Custom String("),
        "custom_string_call_delta": text.count("Custom String(") - kr_text.count("Custom String("),
        "array_call_delta": text.count("Array(") - kr_text.count("Array("),
        "remaining_unapproved_hangul": 0,
        "forbidden_japanese_occurrences": 0,
        "placeholder_mismatches": 0,
        "color_markup_mismatches": 0,
        "maximum_custom_string_literal": maximum_literal,
        "source_shape": source_shape,
        "structural_fingerprint_sha256": jp_structure_sha,
        "kr_structural_fingerprint_sha256": kr_structure_sha,
        "largest_rule": largest,
        "rule_limit_bytes": source_rule_size["limit_bytes"],
        "localized_data": data_report,
        "output_data_assertions": output_data_assertions,
    }


def tsv_value(value: object) -> str:
    return str(value).replace("\t", "\\t").replace("\r", "\\r").replace("\n", "\\n")


def write_tsv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    lines = ["\t".join(fields)]
    for row in rows:
        lines.append("\t".join(tsv_value(row.get(field, "")) for field in fields))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_reports(
    text: str,
    report: dict[str, object],
    inventory: list[dict[str, object]],
    unresolved: list[dict[str, object]],
) -> tuple[str, int]:
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    output = text.replace("\r\n", "\n")
    digest = hashlib.sha256(output.encode("utf-8")).hexdigest().upper()
    byte_count = len(output.encode("utf-8"))
    payload = dict(report)
    payload.update({"sha256": digest, "bytes": byte_count, "unresolved": len(unresolved)})
    source_paths = (
        KR_TARGET,
        EN_TARGET,
        JP_SOURCE,
        ITEM_TABLE,
        Path(__file__).with_name("item_name_translation_proposals.tsv"),
        LOCALIZED_TABLES,
        MANUAL_TRANSLATIONS,
        LEGACY_CONTEXT_REMAP,
        OUTPUT_OVERRIDES,
        RELEASE_CODE_OVERRIDES,
        Path(__file__),
    )
    payload["source_sha256"] = {
        path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest().upper()
        for path in source_paths
    }
    write_tsv(
        BUILD_DIR / "translation_inventory.tsv",
        inventory,
        ["rule", "ordinal", "source", "kr", "en", "jp", "placeholders"],
    )
    write_tsv(
        BUILD_DIR / "resolved_translation_map.tsv",
        [row for row in inventory if row["jp"] != row["kr"]],
        ["rule", "ordinal", "source", "kr", "en", "jp", "placeholders"],
    )
    write_tsv(
        BUILD_DIR / "unresolved_strings.tsv",
        unresolved,
        ["rule", "ordinal", "kr", "en", "placeholders"],
    )
    (BUILD_DIR / "validation.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return digest, byte_count


def build_text() -> tuple[
    str, dict[str, object], list[dict[str, object]], list[dict[str, object]]
]:
    kr_text = load_verified_kr_baseline()
    text, name_report = localize_name_tables(kr_text)
    text, total_score_report = localize_total_score(text)
    text, org_data_report = localize_org_gameplay_data(text)
    text, scoreboard_layout_report = patch_scoreboard_layout(text)
    text, shared_release_report = apply_shared_release_fixes(text)
    text, korean_only_message_count = locale_tools.suppress_korean_only_messages(text)
    text, release_override_count = apply_release_code_overrides(text)
    text, inventory, unresolved, translation_report = translate_custom_strings(text, kr_text)
    text, inventory, override_count = apply_output_overrides(text, inventory)
    translation_report["output_overrides"] = override_count
    translation_report["korean_only_messages_removed"] = korean_only_message_count
    translation_report["release_code_overrides"] = release_override_count
    translation_report["translated"] = sum(row["jp"] != row["kr"] for row in inventory)
    data_report = {
        "name_tables": name_report,
        "total_score": total_score_report,
        "org_gameplay_deltas": org_data_report,
        "scoreboard_layout_deltas": scoreboard_layout_report,
        "shared_release_fixes": shared_release_report,
    }
    report: dict[str, object] = {
        "localized_data": data_report,
        "translation": translation_report,
    }
    if not unresolved:
        report.update(validate_output(text, kr_text, inventory, unresolved, data_report))
    return text, report, inventory, unresolved


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check", action="store_true", help="compare actual jp_deluxe.ow byte-for-byte without writing"
    )
    mode.add_argument(
        "--report", action="store_true", help="write reports only, including while translations remain unresolved"
    )
    mode.add_argument(
        "--force-write",
        action="store_true",
        help="explicitly replace a divergent jp_deluxe.ow and refresh reports",
    )
    args = parser.parse_args()

    text, report, inventory, unresolved = build_text()
    output = text.replace("\r\n", "\n")
    digest = hashlib.sha256(output.encode("utf-8")).hexdigest().upper()
    byte_count = len(output.encode("utf-8"))
    if unresolved and not args.report:
        raise BuildError(
            f"{len(unresolved)} unresolved strings; run --report and complete manual_translations.tsv"
        )
    output_bytes = output.encode("utf-8")
    if args.check:
        if not TARGET.exists():
            raise BuildError(f"missing generated target: {TARGET}")
        current = TARGET.read_bytes()
        if current != output_bytes:
            current_digest = hashlib.sha256(current).hexdigest().upper()
            first_difference = next(
                (index for index, pair in enumerate(zip(current, output_bytes)) if pair[0] != pair[1]),
                min(len(current), len(output_bytes)),
            )
            raise BuildError(
                f"{TARGET.name} differs from generated output: "
                f"current={current_digest} generated={digest} first_byte={first_difference}"
            )
    elif args.report:
        write_reports(text, report, inventory, unresolved)
    elif not unresolved:
        if TARGET.exists() and TARGET.read_bytes() != output_bytes and not args.force_write:
            current_digest = hashlib.sha256(TARGET.read_bytes()).hexdigest().upper()
            raise BuildError(
                f"refusing to overwrite divergent {TARGET.name}: current={current_digest} "
                f"generated={digest}; reverse-sync manual edits or rerun with --force-write"
            )
        TARGET.write_bytes(output_bytes)
        write_reports(text, report, inventory, unresolved)
    print(
        f"rules={len(locale_tools.rule_blocks(text))} bytes={byte_count} "
        f"sha256={digest} unresolved={len(unresolved)}"
    )


if __name__ == "__main__":
    main()
