# JP Deluxe ITEM_NAME baseline validation

Date: 2026-09-02

## Authoritative current sources

| Edition | Korean rule | English rule | Rows |
|---|---|---|---:|
| ORG | `kr_deluxe.ow:dataInit_org1` | `en_deluxe.ow:dataInit_org1` | 476 |
| CAFE | `kr_deluxe.ow:dataInit_cafe1` | `en_deluxe.ow:dataInit_cafe1` | 399 |
| GC | `kr_deluxe.ow:dataInit_gc1` | `en_deluxe.ow:dataInit_gc1` | 464 |

The standalone `ko.ow`, `en.ow`, `cafe_*.ow`, and `gc_*.ow` arrays are legacy index layouts and are not used for the current table's KR/EN data or indexes. `jp.ow` is consulted only as a legacy ORG Japanese translation source, matched by item names.

## Migration and validation rules

- Rows are aligned to the current Deluxe runtime item indexes.
- Shared tools and special items occupy common codes `0..20` in ORG, CAFE, and GC.
- Existing Japanese work is migrated and preserved by `(edition, kr, en)`, never by an obsolete numeric index.
- `싼데비슷한 드링크 / Sandevistan / 怪しいスタンド` is mandatory at code 9 for every edition.
- Japanese text containing `豚` is rejected because it triggers the profanity filter; use established `ポーク` terminology where applicable.
- A source count mismatch, stale seed identity, conflicting translation, forbidden text, or table byte mismatch fails the checker.

## Current fingerprints

| File | SHA-256 |
|---|---|
| `kr_deluxe.ow` | `8D69EDD520D98E3221B321C05123D06B68801E912C87792593AA0188DFACEAA0` |
| `en_deluxe.ow` | `73996191AA905D0016C86E0B74CE64434FC3EDDD0CD4982F574BE7707CDDA113` |
| `jp.ow` | `D5234D052ABA95BA17075DFB0EFD2DAE47BB2A8D6EB7D81F47718B59865E4AD5` |
| `item_name_seed_translations.tsv` | `D20D80CE4D56895D0CD99190A585E43049A9BA062C47F0C23EA03D59E1DEF1F5` |
| `item_name_translations.tsv` | `353ED2570DD8A5BA72BD31B7C3F14312E9736C97B4BD7CF16665C0CA2E59177C` |

The current Deluxe OW files contain manual work newer than their previously generated release snapshots. They are intentionally treated as authoritative for this table.

## Result

- Total rows: 1,339
- ORG: 476 populated / 0 empty
- CAFE: 399 populated / 0 empty
- GC: 464 populated / 0 empty
- Total Japanese cells populated: 1,339
- Total Japanese cells empty: 0
- Forbidden `豚` occurrences: 0
- Duplicate `(edition, item_index)` rows: 0
- `python -B scripts/jp_deluxe/build_item_name_table.py --check`: passed (`blank_jp=0`)
- `git diff --check`: passed

## Review proposal validation

- Proposal file: `scripts/jp_deluxe/item_name_translation_proposals.tsv`
- Proposal rows: 574 (`ORG=1`, `CAFE=274`, `GC=299`)
- Coverage: exactly every blank row in the authoritative table
- Basis counts: `composed=368`, `descriptive=50`, `localized=113`, `state_term=42`, `wordplay=1`
- Forbidden `豚` occurrences: 0
- Untranslated ASCII fragments in Japanese suggestions: 0
- Proposal SHA-256: `1CD95DEE3BAC5336F92AD09F27FCAFD331F38E760FD0A429D43E72D260EAF8E2`
- `python -B scripts\jp_deluxe\build_item_name_proposals.py --check`: passed

All 574 proposal values are integrated into the authoritative table. `python -B scripts/jp_deluxe/build_item_name_proposals.py --check` verifies that the recorded proposal keys and Japanese values remain applied.

## JP Deluxe generated-output validation

- Target: `jp_deluxe.ow`
- SHA-256: `5693C01A3C730C686D94CAC20E5CC225E5D99D00BA9FDE38182C9EE6BCCB6EAA`
- Bytes: `392083`
- Rules / globals / subroutines: `57 / 128 / 40`
- Custom String calls: `1560` (`+11` versus current KR Deluxe)
- Longest Custom String literal: `128` characters (`Player: Spawn`, ordinal 5)
- Largest rule: `Dummy: Spawn`, `37545` bytes; below the 98 KiB source limit
- Unresolved Japanese strings: `0`
- Placeholder mismatches: `0`
- color-markup mismatches: `0`
- Unapproved Hangul: `0`
- Forbidden `豚`: `0`
- Structural fingerprint equals the approved KR Deluxe baseline after locale-neutral release fixes and the reviewed JP-only patch-note override.
- Actual target bytes equal prospective builder output.

The final-output decoder independently verified:

- all nine ITEM_NAME/STAGE_NAME/UPGRADE_NAME tables;
- ORG ITEM_COLOR changes only at `247/249/251`;
- ORG MENU/Hazard/Fridge changes only at the approved three paths;
- all 306 ORG RAW recipes with changes only at rows `150/152/154`;
- unchanged RAW mapper expressions and base-1000 packing in all editions;
- ORG STAGE_CODE changes only at `[1][7][0]`, `[1][10][0]`, and `[1][13][0]`;
- unchanged CAFE/GC RAW and STAGE_CODE data;
- the 18-row edition-selected totalScore expression;
- the three Japanese scoreboard Y coordinates;
- pinned authentication, save/load, credit, and language-code literals.

Commands passed:

```powershell
python -B scripts\kr_deluxe\build_kr_deluxe.py --check
python -B scripts\en_deluxe\build_en_deluxe.py --check
python -B scripts\jp_deluxe\build_item_name_table.py --check
python -B scripts\jp_deluxe\build_item_name_proposals.py --check
python -B scripts\jp_deluxe\build_jp_deluxe.py --report
python -B scripts\jp_deluxe\build_jp_deluxe.py --check
git diff --check
```

Runtime Workshop import, profanity-filter behavior, three-edition play validation, and the final element count remain client-side release checks.

## Final locale policy decisions

- Empty high-score holder wording remains `None` for ORG, CAFE, and GC.
- The JP Deluxe public/update Workshop code remains `4ND1P`.

Both values in the generated target are final rather than temporary placeholders.
