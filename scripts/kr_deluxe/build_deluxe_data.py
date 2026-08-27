#!/usr/bin/env python3
"""Build and validate canonical-index dataInit rules for kr_deluxe.ow.

The source OW files are read-only inputs.  This script writes generated rules and
machine-readable validation data under build/kr_deluxe; it never edits an input.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
BUILD_DIR = ROOT / "build" / "kr_deluxe"

EDITION_SPECS = {
    "org": {"path": ROOT / "ko.ow", "old_count": 475, "new_count": 476},
    "cafe": {"path": ROOT / "cafe_kr.ow", "old_count": 398, "new_count": 399},
    "gc": {"path": ROOT / "gc_kr.ow", "old_count": 462, "new_count": 464},
}

OUTER_ONLY = {
    "ITEM_COLOR",
    "ITEM_NAME",
    "ITEM_SCORE",
    "CUTTING_NEEDED",
    "GRILLING_NEEDED",
    "FRYING_NEEDED",
    "POT_TIME",
    "PAN_NEEDED",
    "ICE_NEEDED",
}

OUTER_AND_LEAVES = {
    "CUTTING_RESULT",
    "GRILLING_RESULT",
    "FRYING_RESULT",
    "POT_RESULT",
    "PAN_RESULT",
    "IMPACT_RESULT",
    "ADDITIONAL_MATERIAL_LIST",
    "ICE_RESULT",
}

PER_ITEM = OUTER_ONLY | OUTER_AND_LEAVES
LIST_TABLES = {"MENU_LIST", "HAZARD_MENU_LIST", "FRIDGE_LIST", "WEAVER_MENU_LIST", "MELT_LIST"}
RAW_TABLES = {"RAW_MIX", "RAW_RESULT"}

ACTIVE_DROPS = {
    "org": [8, 9, 11, 12, 15, 16, 17, 19],
    "cafe": [8, 9, 11, 12, 15, 16, 17, 20],
    "gc": [8, 9, 11, 12, 15, 16, 17],
}

# [0] first normal starter by stageMode, [1] second starter,
# [2] practice-mode equipment cycle, [3] weighted random-tool pool.
RUNTIME_CONFIGS = {
    "org": [
        [0, 12, 12, 16, 15, 16],
        [0, 17, 16, 13, 13, 14],
        [1, 6, 2, 3, 4, 5, 7, 8, 9, 11, 12, 15, 16, 19, 17, 10, 13, 14],
        [8, 8, 8, 8, 9, 11, 11, 11, 11, 12, 12, 15, 16, 16, 19, 19, 19, 17, 17],
    ],
    "cafe": [
        [12, 12, 12, 13, 16, 14],
        ["Null", 20, 20, 3, 20, 16],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20],
        [8, 8, 8, 8, 9, 11, 11, 11, 11, 12, 12, 15, 16, 16, 17, 17, 20, 20],
    ],
    "gc": [
        [12, 12, 12, 16, 15, 16],
        ["Null", 17, 16, 13, 13, 14],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17],
        [8, 8, 8, 8, 9, 11, 11, 11, 11, 12, 12, 15, 16, 16, 17, 17],
    ],
}


class ParseError(RuntimeError):
    pass


@dataclass
class Assignment:
    name: str
    start: int
    end: int
    expression: str


@dataclass
class EditionData:
    name: str
    source: str
    mapping: dict[int, int]
    old_count: int
    new_count: int
    rules: dict[int, str]
    assignments: dict[str, Assignment]
    values: dict[str, Any]
    color_second_arg: str
    color_palette: dict[str, str]


def normalize_expr(value: str) -> str:
    return re.sub(r"\s+", "", value)


def read_ow(path: Path) -> str:
    data = path.read_bytes()
    text = data.decode("utf-8")
    if "\r\n" not in text:
        raise ParseError(f"expected CRLF source: {path}")
    return text


def scan_balanced(text: str, start: int, opener: str, closer: str) -> int:
    if start >= len(text) or text[start] != opener:
        raise ParseError(f"expected {opener!r} at {start}")
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
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
        elif char == opener:
            depth += 1
        elif char == closer:
            depth -= 1
            if depth == 0:
                return index + 1
    raise ParseError(f"unclosed {opener!r} at {start}")


def split_top_level(text: str, delimiter: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    paren = bracket = brace = 0
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
        elif char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket -= 1
        elif char == "{":
            brace += 1
        elif char == "}":
            brace -= 1
        elif char == delimiter and paren == bracket == brace == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    parts.append(text[start:].strip())
    return parts


def unwrap_call(expression: str, expected: str | None = None) -> tuple[str, list[str], str]:
    expression = expression.strip()
    match = re.match(r"^([A-Za-z][A-Za-z 0-9]*)\s*\(", expression)
    if not match:
        raise ParseError(f"not a call: {expression[:80]!r}")
    name = match.group(1).strip()
    if expected is not None and name != expected:
        raise ParseError(f"expected {expected}, got {name}")
    open_at = expression.find("(", match.start())
    end = scan_balanced(expression, open_at, "(", ")")
    args = split_top_level(expression[open_at + 1 : end - 1])
    return name, args, expression[end:].strip()


def decode_string(token: str) -> str:
    token = token.strip()
    try:
        value = json.loads(token)
    except json.JSONDecodeError as exc:
        raise ParseError(f"invalid string literal {token[:100]!r}") from exc
    if not isinstance(value, str):
        raise ParseError(f"not a string literal: {token!r}")
    return value


def eval_expr(expression: str) -> Any:
    expression = expression.strip()
    if not expression:
        raise ParseError("empty expression")
    if expression.startswith('"'):
        return decode_string(expression)
    if re.fullmatch(r"-?\d+(?:\.\d+)?", expression):
        return float(expression) if "." in expression else int(expression)
    if expression in {"Null", "False", "True"}:
        return expression
    if expression == "Empty Array":
        return []

    name, args, suffix = unwrap_call(expression)
    if name == "Custom String":
        fmt = eval_expr(args[0])
        if not isinstance(fmt, str):
            raise ParseError("Custom String format is not a string")
        rendered = fmt
        for index, arg in enumerate(args[1:]):
            value = eval_expr(arg)
            if isinstance(value, list):
                raise ParseError("unexpected list Custom String argument in table payload")
            rendered = rendered.replace("{" + str(index) + "}", str(value))
        if suffix:
            raise ParseError(f"unexpected Custom String suffix {suffix!r}")
        return rendered
    if name == "String Split":
        source = eval_expr(args[0])
        separator = eval_expr(args[1])
        if not isinstance(source, str) or not isinstance(separator, str):
            raise ParseError("String Split arguments are not strings")
        if suffix:
            raise ParseError(f"unexpected String Split suffix {suffix!r}")
        return source.split(separator)
    if name == "Append To Array":
        result: list[Any] = []
        for arg in args:
            value = eval_expr(arg)
            result.extend(value if isinstance(value, list) else [value])
        if suffix:
            raise ParseError(f"unexpected Append To Array suffix {suffix!r}")
        return result
    if name == "Mapped Array":
        # Every serialized table in scope maps the first list.  The mapping
        # expression converts numeric strings or color keys at runtime.
        return eval_expr(args[0])
    if name == "Array":
        if suffix:
            raise ParseError(f"indexed Array is not a static table: {suffix!r}")
        return [eval_expr(arg) for arg in args]
    raise ParseError(f"unsupported expression call {name!r}")


def find_rule(text: str, subroutine: str) -> str:
    event = re.search(rf"\r\n\t\t{re.escape(subroutine)};\r\n", text)
    if not event:
        raise ParseError(f"subroutine event not found: {subroutine}")
    start = text.rfind('\r\nrule("', 0, event.start())
    if start < 0:
        if text.startswith('rule("'):
            start = 0
        else:
            raise ParseError(f"rule start not found for {subroutine}")
    else:
        start += 2
    open_at = text.find("{", start)
    end = scan_balanced(text, open_at, "{", "}")
    return text[start:end]


def find_assignment(block: str, name: str) -> Assignment:
    # Exported Workshop text is not indentation-stable: a few assignments use
    # spaces while their neighbours use tabs.  Match either without making the
    # renderer inherit that irrelevant formatting difference.
    match = re.search(rf"(?m)^[ \t]+Global\.{re.escape(name)}\s*=\s*", block)
    if not match:
        raise ParseError(f"assignment not found: {name}")
    expr_start = match.end()
    paren = bracket = 0
    in_string = False
    escaped = False
    for index in range(expr_start, len(block)):
        char = block[index]
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
        elif char == "(":
            paren += 1
        elif char == ")":
            paren -= 1
        elif char == "[":
            bracket += 1
        elif char == "]":
            bracket -= 1
        elif char == ";" and paren == bracket == 0:
            return Assignment(name, match.start(), index + 1, block[expr_start:index].strip())
    raise ParseError(f"unterminated assignment: {name}")


def find_all_assignments(block: str, name: str) -> list[Assignment]:
    assignments: list[Assignment] = []
    pattern = re.compile(rf"(?m)^[ \t]+Global\.{re.escape(name)}\s*=\s*")
    for match in pattern.finditer(block):
        expr_start = match.end()
        paren = bracket = 0
        in_string = escaped = False
        for index in range(expr_start, len(block)):
            char = block[index]
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
            elif char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket -= 1
            elif char == ";" and paren == bracket == 0:
                assignments.append(
                    Assignment(name, match.start(), index + 1, block[expr_start:index].strip())
                )
                break
        else:
            raise ParseError(f"unterminated assignment: {name}")
    return assignments


def find_patches(block: str, name: str) -> list[tuple[int, int, int, Any]]:
    result: list[tuple[int, int, int, Any]] = []
    pattern = re.compile(rf"(?m)^[ \t]+Global\.{re.escape(name)}\[(\d+)\]\s*=\s*")
    for match in pattern.finditer(block):
        expr_start = match.end()
        paren = bracket = 0
        in_string = escaped = False
        for index in range(expr_start, len(block)):
            char = block[index]
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
            elif char == "(":
                paren += 1
            elif char == ")":
                paren -= 1
            elif char == "[":
                bracket += 1
            elif char == "]":
                bracket -= 1
            elif char == ";" and paren == bracket == 0:
                result.append((match.start(), index + 1, int(match.group(1)), eval_expr(block[expr_start:index])))
                break
        else:
            raise ParseError(f"unterminated patch {name}[{match.group(1)}]")
    return result


def build_mapping(edition: str, old_count: int, new_count: int) -> dict[int, int]:
    mapping = {index: index for index in range(old_count)}
    if edition == "org":
        high = [61, 62, 63, 64, 65, 265, 354, 352, 353, 355, 356, 357, 358, 359, 360, 361, 434, 432]
        for low, old_high in enumerate(high, 1):
            mapping[low] = old_high
            mapping[old_high] = low
        mapping[433] = 19
        mapping[19] = 433
        mapping[20] = 475
        additions = {20}
    elif edition == "cafe":
        mapping[19] = 398
        mapping[20] = 351
        mapping[351] = 20
        additions = {19}
    elif edition == "gc":
        mapping[19] = 462
        mapping[20] = 463
        additions = {19, 20}
    else:
        raise ValueError(edition)
    image = set(mapping.values())
    if len(image) != old_count:
        raise ParseError(f"{edition} mapping is not injective")
    expected = set(range(new_count))
    if image | additions != expected or image & additions:
        raise ParseError(f"{edition} mapping/additions do not cover target namespace")
    return mapping


def map_leaf(value: Any, mapping: dict[int, int]) -> Any:
    if isinstance(value, list):
        return [map_leaf(item, mapping) for item in value]
    if isinstance(value, int):
        if value < 0:
            return value
        if value not in mapping:
            raise ParseError(f"item code outside mapping: {value}")
        return mapping[value]
    if value in {"False", "True", "Null"}:
        return value
    raise ParseError(f"unsupported item leaf: {value!r}")


def remap_outer(values: list[Any], mapping: dict[int, int], new_count: int, map_leaves: bool) -> list[Any]:
    result: list[Any] = [None] * new_count
    for old_index, value in enumerate(values):
        new_index = mapping[old_index]
        result[new_index] = map_leaf(value, mapping) if map_leaves else value
    return result


def parse_color_metadata(expression: str) -> tuple[str, dict[str, str]]:
    _, args, _ = unwrap_call(expression, "Mapped Array")
    second = args[1]
    array_start = second.find("Array(")
    if array_start < 0:
        raise ParseError("ITEM_COLOR palette Array not found")
    open_at = second.find("(", array_start)
    array_end = scan_balanced(second, open_at, "(", ")")
    colors = split_top_level(second[open_at + 1 : array_end - 1])
    split_at = second.find("String Split", array_end)
    if split_at < 0:
        raise ParseError("ITEM_COLOR palette key split not found")
    split_open = second.find("(", split_at)
    split_end = scan_balanced(second, split_open, "(", ")")
    keys = eval_expr(second[split_at:split_end])
    if len(keys) != len(colors):
        raise ParseError(f"color key/palette mismatch: {len(keys)} != {len(colors)}")
    return second, {str(key): color.strip() for key, color in zip(keys, colors)}


def parse_edition(name: str) -> EditionData:
    spec = EDITION_SPECS[name]
    source = read_ow(spec["path"])
    rules = {index: find_rule(source, sub) for index, sub in ((1, "dataInit"), (2, "dataInit2"), (3, "dataInit3"))}
    assignments: dict[str, Assignment] = {}
    values: dict[str, Any] = {}
    for table in sorted(PER_ITEM | LIST_TABLES | RAW_TABLES | {"UPGRADE_CODE", "KNIFE", "PERK_LIST"}):
        if table.startswith("ICE_") and name != "cafe":
            continue
        if table == "MELT_LIST" and name != "org":
            continue
        block = rules[1] if table in {
            "ITEM_COLOR", "ITEM_NAME", "ITEM_SCORE", "CUTTING_NEEDED", "CUTTING_RESULT",
            "GRILLING_NEEDED", "GRILLING_RESULT", "FRYING_NEEDED", "FRYING_RESULT",
            "ICE_NEEDED", "ICE_RESULT",
        } else rules[2]
        assignment = find_assignment(block, table)
        assignments[table] = assignment
        value = eval_expr(assignment.expression)
        if table in PER_ITEM:
            value = [int(item) if isinstance(item, str) and re.fullmatch(r"\d+", item) else item for item in value]
            patches = find_patches(block, table)
            for _, _, index, patch_value in patches:
                value[index] = patch_value
            if len(value) != spec["old_count"]:
                raise ParseError(f"{name} {table} length {len(value)} != {spec['old_count']}")
        values[table] = value
    color_second, palette = parse_color_metadata(assignments["ITEM_COLOR"].expression)
    return EditionData(
        name=name,
        source=source,
        mapping=build_mapping(name, spec["old_count"], spec["new_count"]),
        old_count=spec["old_count"],
        new_count=spec["new_count"],
        rules=rules,
        assignments=assignments,
        values=values,
        color_second_arg=color_second,
        color_palette=palette,
    )


def find_equivalent_color(target: EditionData, donor: EditionData, donor_index: int, fallback: str) -> str:
    donor_key = donor.values["ITEM_COLOR"][donor_index]
    donor_expr = donor.color_palette[str(donor_key)]
    normalized = normalize_expr(donor_expr)
    for key, expression in target.color_palette.items():
        if normalize_expr(expression) == normalized:
            return key
    for key, expression in target.color_palette.items():
        if fallback.lower() in expression.lower():
            return key
    raise ParseError(f"{target.name} has no equivalent color for donor {donor.name}[{donor_index}]: {donor_expr}")


def inject_new_records(editions: dict[str, EditionData], remapped: dict[str, dict[str, list[Any]]]) -> None:
    donors = {
        ("org", 20): ("cafe", 351, "Sky Blue"),
        ("cafe", 19): ("org", 433, "Rose"),
        ("gc", 19): ("org", 433, "Rose"),
        ("gc", 20): ("cafe", 351, "Sky Blue"),
    }
    for (target_name, new_code), (donor_name, donor_code, fallback) in donors.items():
        target = editions[target_name]
        donor = editions[donor_name]
        tables = remapped[target_name]
        tables["ITEM_NAME"][new_code] = donor.values["ITEM_NAME"][donor_code]
        tables["ITEM_COLOR"][new_code] = find_equivalent_color(target, donor, donor_code, fallback)
        tables["ITEM_SCORE"][new_code] = donor.values["ITEM_SCORE"][donor_code]
        for table in PER_ITEM - {"ITEM_NAME", "ITEM_COLOR", "ITEM_SCORE"}:
            if table not in tables:
                continue
            if table in donor.values:
                donor_value = donor.values[table][donor_code]
            elif table == "ICE_NEEDED":
                # The preserved box predates the cafe-only ice table.  Like the
                # other tools it must be explicitly non-processable there.
                donor_value = 99
            elif table == "ICE_RESULT":
                donor_value = 0
            else:
                raise ParseError(f"missing donor field {donor_name} {table}[{donor_code}]")
            if table in OUTER_AND_LEAVES and donor_value not in (0, "False", "Null"):
                raise ParseError(
                    f"cross-edition donor result needs an identity map: "
                    f"{donor_name} {table}[{donor_code}]={donor_value!r}"
                )
            tables[table][new_code] = donor_value


def remap_data(editions: dict[str, EditionData]) -> dict[str, dict[str, list[Any]]]:
    result: dict[str, dict[str, list[Any]]] = {}
    for name, edition in editions.items():
        tables: dict[str, list[Any]] = {}
        for table in PER_ITEM:
            if table not in edition.values:
                continue
            tables[table] = remap_outer(
                edition.values[table], edition.mapping, edition.new_count, table in OUTER_AND_LEAVES
            )
        result[name] = tables
    inject_new_records(editions, result)
    for name, tables in result.items():
        for table, values in tables.items():
            if len(values) != editions[name].new_count or any(value is None for value in values):
                raise ParseError(f"incomplete remapped table {name} {table}")
    return result


def encode_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def make_custom_chain(payload: str, indent: str, chunk_size: int = 82) -> str:
    chunks = [payload[index : index + chunk_size] for index in range(0, len(payload), chunk_size)] or [""]
    expression = f"Custom String({encode_string(chunks[-1])})"
    for chunk in reversed(chunks[:-1]):
        expression = (
            f"Custom String({encode_string(chunk + '{0}')},\r\n"
            f"{indent}\t{expression})"
        )
    return expression


def partition_entries(entries: list[str], max_payload: int = 1050) -> list[list[str]]:
    groups: list[list[str]] = []
    current: list[str] = []
    current_size = 0
    for entry in entries:
        added = len(entry) + (1 if current else 0)
        if current and current_size + added > max_payload:
            groups.append(current)
            current = []
            current_size = 0
        current.append(entry)
        current_size += len(entry) + (1 if len(current) > 1 else 0)
    if current:
        groups.append(current)
    return groups


def make_split_expression(entries: list[str], indent: str = "\t\t\t") -> str:
    for entry in entries:
        if "/" in entry:
            raise ParseError(f"table entry contains delimiter: {entry!r}")
    groups = partition_entries(entries)
    split_expressions = []
    for group in groups:
        payload = "/".join(group)
        chain = make_custom_chain(payload, indent + "\t")
        split_expressions.append(f"String Split({chain}, Custom String(\"/\"))")
    expression = split_expressions[-1]
    for item in reversed(split_expressions[:-1]):
        expression = f"Append To Array({item},\r\n{indent}{expression})"
    return expression


def scalar_to_text(value: Any) -> str:
    if isinstance(value, bool):
        return "True" if value else "False"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str) and value in {"False", "True", "Null"}:
        return value
    raise ParseError(f"cannot render scalar {value!r}")


def render_array(value: Any, indent: str = "\t\t") -> str:
    if not isinstance(value, list):
        return scalar_to_text(value)
    if not value:
        return "Empty Array"
    flat = all(not isinstance(item, list) for item in value)
    if flat:
        tokens = [scalar_to_text(item) for item in value]
        lines: list[str] = []
        current = ""
        for token in tokens:
            candidate = token if not current else current + ", " + token
            if current and len(indent) + len(candidate) > 130:
                lines.append(current)
                current = token
            else:
                current = candidate
        lines.append(current)
        if len(lines) == 1:
            return f"Array({lines[0]})"
        return "Array(" + (",\r\n" + indent + "\t").join(lines) + ")"
    inner = [render_array(item, indent + "\t") for item in value]
    return "Array(" + (",\r\n" + indent + "\t").join(inner) + ")"


def render_mapped_assignment(lhs: str, values: list[Any], second_arg: str, map_nested: bool) -> str:
    base: list[str] = []
    patches: list[tuple[int, Any]] = []
    for index, value in enumerate(values):
        if isinstance(value, list):
            base.append("0")
            patches.append((index, value))
        elif value in {"False", "Null"}:
            base.append("0")
        elif value == "True":
            base.append("1")
        else:
            base.append(str(value))
    split = make_split_expression(base, "\t\t\t")
    lines = [
        f"\t\t{lhs} = Mapped Array(",
        f"\t\t\t{split},",
        f"\t\t\t{second_arg});",
    ]
    for index, value in patches:
        lines.append(f"\t\t{lhs}[{index}] = {render_array(value, '\t\t')};")
    return "\r\n".join(lines)


def replace_spans(text: str, replacements: Iterable[tuple[int, int, str]]) -> str:
    result = text
    for start, end, replacement in sorted(replacements, key=lambda item: item[0], reverse=True):
        result = result[:start] + replacement + result[end:]
    return result


def mapping_second_arg(expression: str) -> str:
    _, args, _ = unwrap_call(expression, "Mapped Array")
    return args[1]


def render_per_item_rule(
    edition: EditionData, phase: int, transformed: dict[str, list[Any]], target_subroutine: str
) -> str:
    block = edition.rules[phase]
    replacements: list[tuple[int, int, str]] = []
    phase_table_names = {
        1: {
            "ITEM_COLOR", "ITEM_NAME", "ITEM_SCORE", "CUTTING_NEEDED", "CUTTING_RESULT",
            "GRILLING_NEEDED", "GRILLING_RESULT", "FRYING_NEEDED", "FRYING_RESULT",
            "ICE_NEEDED", "ICE_RESULT",
        },
        2: {
            "POT_TIME", "POT_RESULT", "PAN_NEEDED", "PAN_RESULT", "IMPACT_RESULT",
            "ADDITIONAL_MATERIAL_LIST",
        },
    }[phase]
    phase_tables = sorted(phase_table_names & edition.assignments.keys())
    for table in phase_tables:
        # Assignments record offsets are relative to their original phase block.
        assignment = find_assignment(block, table)
        values = transformed[table]
        lhs = f"Global.{table}"
        if edition.name == "cafe" and table == "ICE_NEEDED":
            lhs = "Global.ICE_NEEDED"
        elif edition.name == "cafe" and table == "ICE_RESULT":
            lhs = "Global.ICE_RESULT"
        if table == "ITEM_NAME":
            entries = [str(value) for value in values]
            replacement = f"\t\t{lhs} = {make_split_expression(entries, '\t\t\t')};"
        else:
            second = mapping_second_arg(assignment.expression)
            replacement = render_mapped_assignment(lhs, values, second, table in OUTER_AND_LEAVES)
        replacements.append((assignment.start, assignment.end, replacement))
        for patch_start, patch_end, _, _ in find_patches(block, table):
            replacements.append((patch_start, patch_end, ""))

    # The temporary numeric lookup must include every new item code.
    if phase == 1:
        lookup = find_assignment(block, "MIXING_RECIPE")
        lookup_values = [str(index) for index in range(edition.new_count)]
        lookup_replacement = (
            "\t\tGlobal.MIXING_RECIPE = "
            + make_split_expression(lookup_values, "\t\t\t")
            + ";"
        )
        replacements.append((lookup.start, lookup.end, lookup_replacement))

    result = replace_spans(block, replacements)
    result = re.sub(
        rf"(\r\n\t\t){'dataInit' if phase == 1 else 'dataInit' + str(phase)};\r\n",
        rf"\1{target_subroutine};\r\n",
        result,
        count=1,
    )
    result = re.sub(r'rule\("[^"]+"\)', f'rule("Global subroutine: Deluxe {edition.name.upper()} init{phase}")', result, count=1)
    return result


def recursively_map_list(value: Any, mapping: dict[int, int]) -> Any:
    if isinstance(value, list):
        return [recursively_map_list(item, mapping) for item in value]
    if isinstance(value, int):
        if value < 0:
            return value
        return mapping[value]
    if value in {"False", "True", "Null"}:
        return value
    raise ParseError(f"invalid list leaf {value!r}")


def render_phase2_rule(edition: EditionData, transformed: dict[str, list[Any]], target_subroutine: str) -> str:
    block = render_per_item_rule(edition, 2, transformed, target_subroutine)
    replacements: list[tuple[int, int, str]] = []

    raw_mix_assignment = find_assignment(block, "RAW_MIX")
    raw_result_assignment = find_assignment(block, "RAW_RESULT")
    old_mix = edition.values["RAW_MIX"]
    old_result = edition.values["RAW_RESULT"]
    if len(old_mix) != len(old_result):
        raise ParseError(f"{edition.name} RAW row count mismatch")
    new_mix = []
    new_left = []
    new_right = []
    new_result = []
    triples = []
    for packed, result in zip(old_mix, old_result):
        left, right = packed // 1000, packed % 1000
        mapped_left = edition.mapping[left]
        mapped_right = edition.mapping[right]
        mapped_result = edition.mapping[result]
        new_mix.append(mapped_left * 1000 + mapped_right)
        new_left.append(mapped_left)
        new_right.append(mapped_right)
        new_result.append(mapped_result)
        triples.append((left, right, result, mapped_left, mapped_right, mapped_result))
    numeric_mapper = "Index Of Array Value(Global.MIXING_RECIPE, Current Array Element)"
    # A literal RAW Array costs one Workshop element per recipe.  Decode the
    # two operands through the existing 0..N numeric lookup, combine them, then
    # reuse RAW_RESULT for the real result list.  This keeps the base-1000
    # runtime contract while reducing hundreds of elements per edition.
    raw_mix_replacement = "\r\n".join(
        [
            render_mapped_assignment("Global.RAW_MIX", new_left, numeric_mapper, False),
            render_mapped_assignment("Global.RAW_RESULT", new_right, numeric_mapper, False),
            "\t\tGlobal.RAW_MIX = Mapped Array(Global.RAW_MIX, Current Array Element * 1000 + Global.RAW_RESULT[Current Array Index]);",
        ]
    )
    raw_result_replacement = render_mapped_assignment(
        "Global.RAW_RESULT", new_result, numeric_mapper, False
    )
    replacements.extend(
        [
            (raw_mix_assignment.start, raw_mix_assignment.end, raw_mix_replacement),
            (raw_result_assignment.start, raw_result_assignment.end, raw_result_replacement),
        ]
    )

    for table in LIST_TABLES:
        if table not in edition.values:
            continue
        assignment = find_assignment(block, table)
        mapped = recursively_map_list(edition.values[table], edition.mapping)
        lhs = "Global.DELUXE_DATA[0]" if table == "MELT_LIST" else f"Global.{table}"
        replacements.append((assignment.start, assignment.end, f"\t\t{lhs} = {render_array(mapped)};"))

    # These statements are byte-for-byte/semantically common after canonical
    # remapping.  The dataInit2 dispatcher emits them once after the selected
    # edition returns.
    for table in (
        "upgradePrice", "UPGRADE_CODE", "KNIFE", "PERK_LIST", "KNIFE_AMOUNT", "KNIFE_DECREASE"
    ):
        assignment = find_assignment(block, table)
        replacements.append((assignment.start, assignment.end, ""))

    # Building the symmetric recipe adjacency arrays is also common.  Keep the
    # selected edition's compressed RAW data, but run this loop once in the
    # dispatcher instead of embedding it in all three variant rules.
    mixing_start = find_assignment(block, "MIXING_RECIPE").start
    menu_start = find_assignment(block, "MENU_LIST").start
    if mixing_start >= menu_start:
        raise ParseError(f"{edition.name} phase2 common mixing segment order changed")
    replacements.append((mixing_start, menu_start, ""))

    return replace_spans(block, replacements)


def render_phase3_rule(edition: EditionData, target_subroutine: str) -> str:
    block = edition.rules[3]
    old_name = "dataInit3"
    block = re.sub(rf"(\r\n\t\t){old_name};\r\n", rf"\1{target_subroutine};\r\n", block, count=1)
    block = re.sub(r'rule\("[^"]+"\)', f'rule("Global subroutine: Deluxe {edition.name.upper()} init3")', block, count=1)
    active = ACTIVE_DROPS[edition.name]
    # DELUXE_DATA[2] keeps the edition-specific runtime item pools together.
    runtime_config = RUNTIME_CONFIGS[edition.name]
    actions = block.find("\r\n\tactions\r\n\t{\r\n")
    if actions < 0:
        raise ParseError(f"actions block missing in {edition.name} init3")
    insert = actions + len("\r\n\tactions\r\n\t{\r\n")
    injected = (
        f"\t\tGlobal.DELUXE_DATA[1] = {render_array(active)};\r\n"
        f"\t\tGlobal.DELUXE_DATA[2] = {render_array(runtime_config)};\r\n"
    )
    block = block[:insert] + injected + block[insert:]
    # These difficulty scalars are identical in ORG/CAFE/GC and are emitted by
    # the dataInit3 dispatcher after the selected variant returns.
    common_scalars = (
        "customerCallTime", "setUpTime", "scoreDecrease", "despawnTime",
        "additionalScore", "failEnd",
    )
    block = replace_spans(
        block,
        [(assignment.start, assignment.end, "") for assignment in (
            find_assignment(block, name) for name in common_scalars
        )],
    )
    return block


def validate_semantics(editions: dict[str, EditionData], transformed: dict[str, dict[str, list[Any]]]) -> dict[str, Any]:
    report: dict[str, Any] = {"editions": {}}
    for name, edition in editions.items():
        tables = transformed[name]
        for table, original in edition.values.items():
            if table not in tables:
                continue
            new = tables[table]
            for old_index, old_value in enumerate(original):
                expected = map_leaf(old_value, edition.mapping) if table in OUTER_AND_LEAVES else old_value
                actual = new[edition.mapping[old_index]]
                if actual != expected:
                    raise ParseError(f"semantic mismatch {name} {table}[{old_index}] -> {edition.mapping[old_index]}")
        raw_count = len(edition.values["RAW_MIX"])
        report["editions"][name] = {
            "old_item_count": edition.old_count,
            "new_item_count": edition.new_count,
            "raw_rows": raw_count,
            "mapping_entries": len(edition.mapping),
            "per_item_tables": {table: len(tables[table]) for table in sorted(tables)},
            "active_drop": ACTIVE_DROPS[name],
        }
    return report


def validate_generated_tables(
    generated: str,
    editions: dict[str, EditionData],
    transformed: dict[str, dict[str, list[Any]]],
) -> dict[str, Any]:
    """Reparse the rendered rules and verify their serialized table payloads.

    validate_semantics checks the in-memory remap.  This second pass catches a
    renderer, replacement-span, or nested-patch bug between that remap and the
    actual Workshop text.
    """
    phase1 = {
        "ITEM_COLOR", "ITEM_NAME", "ITEM_SCORE", "CUTTING_NEEDED", "CUTTING_RESULT",
        "GRILLING_NEEDED", "GRILLING_RESULT", "FRYING_NEEDED", "FRYING_RESULT",
        "ICE_NEEDED", "ICE_RESULT",
    }
    report: dict[str, Any] = {}
    for name, edition in editions.items():
        blocks = {
            phase: find_rule(generated, f"dataInit_{name}{phase}") for phase in (1, 2, 3)
        }
        checked_tables = 0
        for table, expected in transformed[name].items():
            block = blocks[1 if table in phase1 else 2]
            lhs = table
            if name == "cafe" and table == "ICE_NEEDED":
                lhs = "ICE_NEEDED"
            elif name == "cafe" and table == "ICE_RESULT":
                lhs = "ICE_RESULT"
            assignment = find_assignment(block, lhs)
            if table == "ITEM_NAME":
                observed_names = eval_expr(assignment.expression)
                if observed_names != [str(value) for value in expected]:
                    raise ParseError(f"{name} generated ITEM_NAME payload mismatch")
            else:
                _, args, suffix = unwrap_call(assignment.expression, "Mapped Array")
                if suffix:
                    raise ParseError(f"{name} generated {table} has indexed Mapped Array suffix")
                observed_base = eval_expr(args[0])
                expected_base = [
                    "0" if isinstance(value, list) or value in {"False", "Null"}
                    else "1" if value == "True"
                    else str(value)
                    for value in expected
                ]
                if observed_base != expected_base:
                    raise ParseError(f"{name} generated {table} base payload mismatch")
                expected_second = mapping_second_arg(edition.assignments[table].expression)
                if normalize_expr(args[1]) != normalize_expr(expected_second):
                    raise ParseError(f"{name} generated {table} mapper mismatch")
                observed_patches = {
                    index: value for _, _, index, value in find_patches(block, lhs)
                }
                expected_patches = {
                    index: value for index, value in enumerate(expected) if isinstance(value, list)
                }
                if observed_patches != expected_patches:
                    raise ParseError(f"{name} generated {table} nested patch mismatch")
            checked_tables += 1

        lookup = [int(value) for value in eval_expr(find_assignment(blocks[1], "MIXING_RECIPE").expression)]
        if lookup != list(range(edition.new_count)):
            raise ParseError(f"{name} generated numeric lookup mismatch")

        for table in LIST_TABLES:
            if table not in edition.values:
                continue
            lhs = "DELUXE_DATA[0]" if table == "MELT_LIST" else table
            observed = eval_expr(find_assignment(blocks[2], lhs).expression)
            expected = recursively_map_list(edition.values[table], edition.mapping)
            if observed != expected:
                raise ParseError(f"{name} generated {table} recursive mapping mismatch")

        if eval_expr(find_assignment(blocks[3], "DELUXE_DATA[1]").expression) != ACTIVE_DROPS[name]:
            raise ParseError(f"{name} generated active-drop pool mismatch")
        if eval_expr(find_assignment(blocks[3], "DELUXE_DATA[2]").expression) != RUNTIME_CONFIGS[name]:
            raise ParseError(f"{name} generated runtime-config pool mismatch")
        report[name] = {
            "per_item_tables": checked_tables,
            "numeric_lookup": edition.new_count,
            "list_tables": len([table for table in LIST_TABLES if table in edition.values]),
            "round_trip": True,
        }
    return report


def validate_generated_raw(generated: str, editions: dict[str, EditionData]) -> dict[str, Any]:
    report: dict[str, Any] = {}
    for name, edition in editions.items():
        block = find_rule(generated, f"dataInit_{name}2")
        mix_assignments = find_all_assignments(block, "RAW_MIX")
        result_assignments = find_all_assignments(block, "RAW_RESULT")
        if len(mix_assignments) != 2 or len(result_assignments) != 2:
            raise ParseError(
                f"{name} generated RAW assignment shape: "
                f"mix={len(mix_assignments)} result={len(result_assignments)}"
            )
        observed_left = [int(value) for value in eval_expr(mix_assignments[0].expression)]
        observed_right = [int(value) for value in eval_expr(result_assignments[0].expression)]
        observed_result = [int(value) for value in eval_expr(result_assignments[1].expression)]
        expected_left: list[int] = []
        expected_right: list[int] = []
        expected_result: list[int] = []
        for packed, result in zip(edition.values["RAW_MIX"], edition.values["RAW_RESULT"]):
            expected_left.append(edition.mapping[packed // 1000])
            expected_right.append(edition.mapping[packed % 1000])
            expected_result.append(edition.mapping[result])
        if (observed_left, observed_right, observed_result) != (
            expected_left,
            expected_right,
            expected_result,
        ):
            raise ParseError(f"{name} generated RAW round-trip mismatch")
        if any(value >= 1000 for value in observed_left + observed_right + observed_result):
            raise ParseError(f"{name} generated RAW item code violates base-1000 contract")
        report[name] = {
            "rows": len(observed_left),
            "max_operand": max(observed_left + observed_right),
            "max_result": max(observed_result),
            "round_trip": True,
        }
    return report


def validate_custom_string_lengths(generated: str) -> dict[str, int]:
    payloads = [
        decode_string(match.group(1))
        for match in re.finditer(r'Custom String\(\s*("(?:\\.|[^"\\])*")', generated)
    ]
    if not payloads:
        raise ParseError("generated rules contain no Custom String payloads")
    maximum = max(len(payload) for payload in payloads)
    if maximum > 90:
        raise ParseError(f"generated Custom String payload exceeds 90 characters: {maximum}")
    return {"payloads": len(payloads), "max_characters": maximum}


def build() -> tuple[str, dict[str, Any]]:
    editions = {name: parse_edition(name) for name in EDITION_SPECS}
    transformed = remap_data(editions)
    rules: list[str] = []
    for name, edition in editions.items():
        rules.append(render_per_item_rule(edition, 1, transformed[name], f"dataInit_{name}1"))
        rules.append(render_phase2_rule(edition, transformed[name], f"dataInit_{name}2"))
        rules.append(render_phase3_rule(edition, f"dataInit_{name}3"))
    generated = "\r\n\r\n".join(rules) + "\r\n"
    report = validate_semantics(editions, transformed)
    report["generated_table_round_trip"] = validate_generated_tables(
        generated, editions, transformed
    )
    report["raw_round_trip"] = validate_generated_raw(generated, editions)
    report["custom_string_lengths"] = validate_custom_string_lengths(generated)
    report["source_sha256"] = {
        name: __import__("hashlib").sha256(edition.source.encode("utf-8")).hexdigest().upper()
        for name, edition in editions.items()
    }
    report["generated_rule_count"] = len(rules)
    return generated, report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="validate without writing generated output")
    args = parser.parse_args()
    generated, report = build()
    if not args.check:
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        (BUILD_DIR / "generated_data_init_rules.ow").write_bytes(generated.encode("utf-8"))
        (BUILD_DIR / "data_validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        mapping_lines = ["edition\told_code\tnew_code\tkind"]
        additions = {"org": [20], "cafe": [19], "gc": [19, 20]}
        for name, spec in EDITION_SPECS.items():
            mapping = build_mapping(name, spec["old_count"], spec["new_count"])
            mapping_lines.extend(
                f"{name}\t{old}\t{new}\texisting" for old, new in sorted(mapping.items())
            )
            mapping_lines.extend(
                f"{name}\tNEW\t{new}\tdonor" for new in additions[name]
            )
        (BUILD_DIR / "item_index_mapping.tsv").write_text(
            "\n".join(mapping_lines) + "\n", encoding="utf-8"
        )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
