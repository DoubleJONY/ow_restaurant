from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TABLE_PATH = ROOT / "scripts" / "jp_deluxe" / "item_name_translations.tsv"
SEED_PATH = ROOT / "scripts" / "jp_deluxe" / "item_name_seed_translations.tsv"
PARSER_DIR = ROOT / "scripts" / "kr_deluxe"

sys.path.insert(0, str(PARSER_DIR))
from build_deluxe_data import eval_expr, find_assignment, find_rule  # noqa: E402


DELUXE_SOURCES = (
    ("ORG", "dataInit_org1"),
    ("CAFE", "dataInit_cafe1"),
    ("GC", "dataInit_gc1"),
)
HEADER = ("edition", "item_index", "kr", "en", "jp")
SEED_HEADER = ("edition", "kr", "en", "jp", "reason")
SPECIAL_TRANSLATIONS = {
    ("싼데비슷한 드링크", "Sandevistan"): "怪しいスタンド",
}
FORBIDDEN_JP_TEXT = ("豚",)


def read_item_names(filename: str, subroutine: str | None = None) -> list[str]:
    text = (ROOT / filename).read_text(encoding="utf-8")
    if subroutine is not None:
        # The shared parser expects CRLF because the source edition files use
        # that format. Current Deluxe OW files are LF, so normalize in memory.
        text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        text = find_rule(text, subroutine)
    assignment = find_assignment(text, "ITEM_NAME")
    values = eval_expr(assignment.expression)
    if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
        raise RuntimeError(f"{filename}: ITEM_NAME is not a flat string array")
    return values


def validate_japanese(value: str, context: object) -> None:
    for forbidden in FORBIDDEN_JP_TEXT:
        if forbidden in value:
            raise RuntimeError(f"forbidden Japanese text {forbidden!r} in {context!r}: {value!r}")


def read_preserved_japanese() -> dict[tuple[str, str, str], str]:
    if not TABLE_PATH.exists():
        return {}

    indexed_rows: set[tuple[str, int]] = set()
    candidates: dict[tuple[str, str, str], set[str]] = {}
    with TABLE_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != HEADER:
            raise RuntimeError(f"unexpected table header: {reader.fieldnames!r}")
        for row in reader:
            index_key = (row["edition"], int(row["item_index"]))
            if index_key in indexed_rows:
                raise RuntimeError(f"duplicate table row: {index_key}")
            indexed_rows.add(index_key)
            if row["jp"]:
                validate_japanese(row["jp"], index_key)
                signature = (row["edition"], row["kr"], row["en"])
                candidates.setdefault(signature, set()).add(row["jp"])

    preserved: dict[tuple[str, str, str], str] = {}
    for signature, values in candidates.items():
        if len(values) != 1:
            raise RuntimeError(f"conflicting preserved Japanese values: {signature!r} -> {values!r}")
        preserved[signature] = next(iter(values))
    return preserved


def read_seed_translations() -> dict[tuple[str, str, str], str]:
    seeds: dict[tuple[str, str, str], str] = {}
    with SEED_PATH.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if tuple(reader.fieldnames or ()) != SEED_HEADER:
            raise RuntimeError(f"unexpected seed header: {reader.fieldnames!r}")
        for row in reader:
            key = (row["edition"], row["kr"], row["en"])
            if key in seeds:
                raise RuntimeError(f"duplicate seed row: {key}")
            if key[0] == "ORG" or not all(key) or not row["jp"]:
                raise RuntimeError(f"invalid seed row: {key}")
            validate_japanese(row["jp"], key)
            seeds[key] = row["jp"]
    return seeds


def unique_translation_map(
    rows: list[tuple[str, str, str]], key_indexes: tuple[int, ...]
) -> dict[tuple[str, ...], str]:
    candidates: dict[tuple[str, ...], set[str]] = {}
    for row in rows:
        key = tuple(row[index] for index in key_indexes)
        candidates.setdefault(key, set()).add(row[2])
    return {
        key: next(iter(values))
        for key, values in candidates.items()
        if len(values) == 1
    }


def build_rows() -> tuple[list[dict[str, str]], list[str]]:
    preserved = read_preserved_japanese()
    seeds = read_seed_translations()
    rows: list[dict[str, str]] = []
    summaries: list[str] = []

    current: dict[str, tuple[list[str], list[str]]] = {}
    for edition, subroutine in DELUXE_SOURCES:
        kr_names = read_item_names("kr_deluxe.ow", subroutine)
        en_names = read_item_names("en_deluxe.ow", subroutine)
        if len(kr_names) != len(en_names):
            raise RuntimeError(
                f"{edition}: KR/EN ITEM_NAME lengths differ: {len(kr_names)} != {len(en_names)}"
            )
        current[edition] = (kr_names, en_names)

    legacy_kr = read_item_names("ko.ow")
    legacy_en = read_item_names("en.ow")
    legacy_jp = read_item_names("jp.ow")
    if len({len(legacy_kr), len(legacy_en), len(legacy_jp)}) != 1:
        raise RuntimeError("legacy ORG KR/EN/JP ITEM_NAME lengths differ")
    legacy_rows = list(zip(legacy_kr, legacy_en, legacy_jp))
    legacy_by_pair = unique_translation_map(legacy_rows, (0, 1))
    legacy_by_kr = unique_translation_map(legacy_rows, (0,))

    org_kr, org_en = current["ORG"]
    org_jp: list[str] = []
    for kr_name, en_name in zip(org_kr, org_en):
        signature = ("ORG", kr_name, en_name)
        jp_name = SPECIAL_TRANSLATIONS.get((kr_name, en_name), "")
        if not jp_name:
            jp_name = preserved.get(signature, "")
        if not jp_name:
            jp_name = legacy_by_pair.get((kr_name, en_name), "")
        if not jp_name:
            jp_name = legacy_by_kr.get((kr_name,), "")
        validate_japanese(jp_name, signature)
        org_jp.append(jp_name)

    org_rows = list(zip(org_kr, org_en, org_jp))
    org_by_pair = unique_translation_map(org_rows, (0, 1))
    org_by_kr = unique_translation_map(org_rows, (0,))

    current_signatures: set[tuple[str, str, str]] = set()
    for edition, _subroutine in DELUXE_SOURCES:
        kr_names, en_names = current[edition]
        if edition == "ORG":
            jp_names = org_jp
        else:
            jp_names = []
            for kr_name, en_name in zip(kr_names, en_names):
                signature = (edition, kr_name, en_name)
                jp_name = SPECIAL_TRANSLATIONS.get((kr_name, en_name), "")
                if not jp_name:
                    jp_name = preserved.get(signature, "")
                if not jp_name:
                    jp_name = org_by_pair.get((kr_name, en_name), "")
                if not jp_name:
                    jp_name = org_by_kr.get((kr_name,), "")
                if not jp_name:
                    jp_name = seeds.get(signature, "")
                validate_japanese(jp_name, signature)
                jp_names.append(jp_name)

        for index, (kr_name, en_name, jp_name) in enumerate(zip(kr_names, en_names, jp_names)):
            current_signatures.add((edition, kr_name, en_name))
            rows.append(
                {
                    "edition": edition,
                    "item_index": str(index),
                    "kr": kr_name,
                    "en": en_name,
                    "jp": jp_name,
                }
            )
        summaries.append(f"{edition}={len(kr_names)}")

    unknown_seeds = sorted(set(seeds) - current_signatures)
    if unknown_seeds:
        raise RuntimeError(f"seed rows do not exist in current sources: {unknown_seeds}")

    for edition, _subroutine in DELUXE_SOURCES:
        special_rows = [
            row
            for row in rows
            if row["edition"] == edition
            and (row["kr"], row["en"]) in SPECIAL_TRANSLATIONS
        ]
        if len(special_rows) != len(SPECIAL_TRANSLATIONS):
            raise RuntimeError(f"{edition}: special ITEM_NAME rows are missing or duplicated")
        for row in special_rows:
            expected = SPECIAL_TRANSLATIONS[(row["kr"], row["en"])]
            if row["jp"] != expected:
                raise RuntimeError(f"{edition}: special Japanese ITEM_NAME changed: {row!r}")

    return rows, summaries


def render_table(rows: list[dict[str, str]]) -> bytes:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=HEADER, delimiter="\t", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue().encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build or validate the JP Deluxe ITEM_NAME translation table."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="compare the current table with the source ITEM_NAME arrays without writing",
    )
    args = parser.parse_args()

    rows, summaries = build_rows()
    expected = render_table(rows)
    digest = hashlib.sha256(expected).hexdigest().upper()
    blank_jp = sum(1 for row in rows if not row["jp"])
    result = f"rows={len(rows)} {' '.join(summaries)} blank_jp={blank_jp} sha256={digest}"

    if args.check:
        if not TABLE_PATH.exists():
            print(f"missing: {TABLE_PATH}", file=sys.stderr)
            return 1
        actual = TABLE_PATH.read_bytes()
        if actual != expected:
            print(f"mismatch: {TABLE_PATH}", file=sys.stderr)
            return 1
        print(f"check ok: {result}")
        return 0

    TABLE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TABLE_PATH.write_bytes(expected)
    print(f"wrote {TABLE_PATH}: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
