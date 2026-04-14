# Workshop Array Refactor Session

## Scope

Recorded the refactor pattern and session results for the Workshop locale files:

- `ko.txt`
- `en.txt`
- `jp.txt`
- `cafe_kr.txt`
- `cafe_en.txt`
- `gc_kr.txt`
- `gc_en.txt`
- `n3_kr.txt`

## Changes Made

- Replaced large numeric `Array(...)` tables with `Custom String` chains joined by `{0}` and decoded with `String Split(..., Custom String("/"))`.
- For tables that must resolve to numeric values, wrapped the split arrays with:

```ow
Mapped Array(String Split(...), Index Of Array Value(Global.MIXING_RECIPE, Current Array Element))
```

- Added temporary numeric lookup tables before the compressed mappings:
  - Restaurant files: `0..474`
  - Cafe files: `0..397`
- Kept `CUTTING_RESULT` in raw `Array(...)` form because it mixes `False`, integers, and `Array(a, b)` values.
- Converted legacy `False` entries to `0` only in the numeric tables that were moved into the string-compression pattern.
- Aligned locale init flow:
  - Host-select flow in `Global: Setting`
  - Difficulty-dependent values moved into `dataInit3`
  - Difficulty-up logic reuses `Call Subroutine(dataInit3);`
- Corrected cafe `scoreDecrease` to the six-slot structure:

```ow
Array(
    Array(Null, Null, Null, Null, Null, Null),
    Array(5, Null, 5, 5, 5, 5),
    Array(15, Null, 15, 35, 15, 15),
    Array(50, Null, 50, 50, 50, 50)
)[Global.difficulty]
```

- Re-aligned generated indentation in `cafe_en.txt` to match the accepted style already used in `cafe_kr.txt`.
- Removed the redundant `Global.STAGE_CODE = ...` reassignment from the difficulty-up block in `cafe_en.txt`.
- Removed the redundant `dataInit2` temporary numeric lookup from `cafe_en.txt`; the earlier `datalnit4` lookup already covers the later mapped tables.
- Applied the same host-select and compressed-table pattern to `gc_kr.txt`.
- Used a temporary numeric lookup range of `0..461` for `gc_kr.txt`.
- Updated `gc_kr.txt` to use the six-slot `scoreDecrease` structure and removed the duplicate difficulty-up `Global.STAGE_CODE` reassignment.
- Removed the redundant `dataInit2` temporary numeric lookup from `gc_kr.txt`; the earlier `dataInit` lookup already covers the later mapped tables.
- Applied the same host-select and compressed-table pattern to `gc_en.txt`.
- Used a temporary numeric lookup range of `0..461` for `gc_en.txt`.
- Moved the difficulty-dependent values in `gc_en.txt` into `dataInit3` and reduced the difficulty-up block to `Global.stageTime -= 30;` plus `Call Subroutine(dataInit3);`.
- Removed the redundant difficulty-up `Global.STAGE_CODE` reassignment from `gc_en.txt`.
- Applied the same host-select and compressed-table pattern to `n3_kr.txt`.
- Used a temporary numeric lookup range of `0..513` for `n3_kr.txt`.
- Moved the difficulty-dependent values in `n3_kr.txt` into `dataInit3` and reduced the difficulty-up block to `Global.stageTime -= 30;` plus `Call Subroutine(dataInit3);`.
- Normalized `n3_kr.txt` `scoreDecrease` from the broken four-slot shape to the six-slot structure used by the other non-cafe variants.
- Removed the redundant difficulty-up `Global.STAGE_CODE` reassignment from `n3_kr.txt`.

## Validation

- Verified transformed restaurant tables remained at `475` entries.
- Verified transformed cafe tables remained at `398` entries.
- Compared transformed tables in `cafe_en.txt` against `HEAD:cafe_en.txt`; decoded values matched exactly for:
  - `POT_TIME`
  - `POT_RESULT`
  - `PAN_NEEDED`
  - `PAN_RESULT`
  - `IMPACT_RESULT`
  - `CUTTING_NEEDED`
  - `GRILLING_NEEDED`
  - `GRILLING_RESULT`
  - `FRYING_NEEDED`
  - `FRYING_RESULT`
  - `ICE_NEEDED`
  - `ICE_RESULT`
- Confirmed `CUTTING_RESULT` stayed raw.
- Confirmed `cafe_en.txt` now has only one `Global.STAGE_CODE =` assignment and no duplicate difficulty-up reassignment.
- Confirmed `cafe_en.txt` now has only one temporary `Global.MIXING_RECIPE = String Split(...)` lookup and keeps the mapped `POT_TIME`/`POT_RESULT` tables intact.
- Verified transformed `gc_kr.txt` tables remained at `462` entries and matched `HEAD:gc_kr.txt` exactly for:
  - `CUTTING_NEEDED`
  - `GRILLING_NEEDED`
  - `GRILLING_RESULT`
  - `FRYING_NEEDED`
  - `FRYING_RESULT`
  - `POT_TIME`
  - `POT_RESULT`
  - `PAN_NEEDED`
  - `PAN_RESULT`
  - `IMPACT_RESULT`
- Confirmed `gc_kr.txt` now has only one `Global.STAGE_CODE =` assignment, two `Call Subroutine(dataInit3);` call sites, and no remaining stage-mode combo assignment.
- Confirmed `gc_kr.txt` now has only one temporary `Global.MIXING_RECIPE = String Split(...)` lookup and keeps the mapped `POT_TIME`/`POT_RESULT` tables intact.
- Verified transformed `gc_en.txt` tables remained at `462` entries and matched `HEAD:gc_en.txt` exactly for:
  - `CUTTING_NEEDED`
  - `GRILLING_NEEDED`
  - `GRILLING_RESULT`
  - `FRYING_NEEDED`
  - `FRYING_RESULT`
  - `POT_TIME`
  - `POT_RESULT`
  - `PAN_NEEDED`
  - `PAN_RESULT`
  - `IMPACT_RESULT`
- Confirmed `gc_en.txt` now has only one `Global.STAGE_CODE =` assignment, one temporary `Global.MIXING_RECIPE = String Split(...)` lookup, and no remaining stage-mode combo assignment.
- Verified transformed `n3_kr.txt` tables remained at `514` entries and matched `HEAD:n3_kr.txt` exactly for:
  - `CUTTING_NEEDED`
  - `GRILLING_NEEDED`
  - `GRILLING_RESULT`
  - `FRYING_NEEDED`
  - `FRYING_RESULT`
  - `POT_TIME`
  - `POT_RESULT`
  - `PAN_NEEDED`
  - `PAN_RESULT`
  - `IMPACT_RESULT`
- Confirmed `n3_kr.txt` now has only one `Global.STAGE_CODE =` assignment, one temporary `Global.MIXING_RECIPE = String Split(...)` lookup, two `Call Subroutine(dataInit3);` call sites, and no remaining stage-mode combo assignment.

## Remaining Risk

- No Workshop runtime test was executed in-game during this session.
- The current pattern depends on the temporary numeric lookup array being assigned before the mapped conversions in the relevant init subroutine.
