# Port `en.txt` `HEAD` Changes Into `gc_en.txt`

Port the post-`338c7321f9f4aed9688c6d8cb70aaa13f729be1d` `en.txt` feature set into `gc_en.txt` while preserving `gc_en`-specific recipe tables, menu graph, item ids, and GC-branch perk-index layout.

## Analysis Summary

- `gc_en.txt` has no commits after `338c7321`; the post-`260415..260417` feature work landed only in `en.txt`.
- Structurally, `gc_en.txt` is aligned with `gc_kr.txt`, not with current `en.txt`:
  - no `ICE_NEEDED` / `ICE_RESULT`
  - no split `dataInit2_1` / `dataInit2_2`
  - same general station model as `gc_kr` (`Fryer`, `Pot`, `Grill`, `Pan`)
  - still on the old 4-mode scaffold
- `gc_en.txt` is not a locale view over current `en.txt`.
  - it still carries the GC-branch `dataInit2` recipe/menu graph
  - it does not yet have `validateServe`, `changeHero`, `stageFail`
  - it does not yet have the 6-mode scaffold
  - it does not yet have `Jetpack Cat`, `Reinhardt`, `Junker Queen`, or the 19-slot table model
- `gc_en.txt` is very close to `gc_kr.txt`, but it is not byte-for-byte equivalent.
  - one `PERK_LIST` slot differs
  - one `STAGE_CODE` entry differs

## Baseline Relationships

- `gc_en.txt` and `gc_kr.txt` share the same GC-branch structure:
  - same `UPGRADE_CODE`
  - same `KNIFE`
  - same serving-ball perk index (`itemPerk == 6`)
  - same reset/tip item flow using `18`
  - same 4-mode scaffold
- `gc_en.txt` and current `en.txt` diverge in the same broad way that `gc_kr.txt` and current `ko.txt` diverge:
  - old 4-mode scaffold vs current 6-mode scaffold
  - old inline serve/fail flow vs new subroutine scaffold
  - old 14-slot table model vs new 19-slot table model
  - old customer set vs new customer set including `Jetpack Cat`, `Reinhardt`, `Junker Queen`

## Known `gc_en`-Specific Differences

- `Global.PERK_LIST` differs from `gc_kr.txt`:
  - `gc_kr.txt`: `Array(Array(8, 9, 11, 12, 15, 16, 17), Array(10, 13, 14))`
  - `gc_en.txt`: `Array(Array(8, 8, 11, 12, 15, 16, 17), Array(10, 13, 14))`
- `Global.STAGE_CODE` differs from `gc_kr.txt` in one known entry:
  - `gc_kr.txt` has `... Array(4), Array(8), Array(7) ...`
  - `gc_en.txt` has `... Array(4), Array(6), Array(7) ...`
- These may be intentional GC English-branch fixes or accidental drift.
- Implementation should not silently normalize them away without first preserving the current `gc_en` intent in the artifact notes.

## User Review Required

> [!IMPORTANT]
> This plan assumes the goal is behavioral parity with current `en.txt`, not literal line-by-line parity.
> `gc_en` item ids, menu tables, and recipe tables should be preserved or remapped by role, not copied by raw number.

> [!IMPORTANT]
> This plan follows the same policy already used for the cafe and GC Korean variants:
> `Global.STAGE_CODE` should not be finalized during the structural port.
> During implementation, the expanded `gc_en` `Global.STAGE_CODE = ...` body should be left as explicit `//TODO` placeholders for the user to fill in manually.

> [!WARNING]
> `gc_en.txt` is structurally easy to port but easy to regress in its GC data layer.
> The current `en.txt` `HEAD` patch does not require a `dataInit2` port, so overwriting `gc_en:dataInit2` with restaurant-side arrays would be a regression.

## Proposed Changes

### 1. Structural Scaffold In `gc_en.txt`

- Expand `subroutines` to add:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Port the shared structural refactors from current `en.txt`:
  - hero-change extraction
  - serve-validation extraction
  - centralized stage-fail handling
- Update call sites to use the new subroutines rather than keeping duplicated inline logic.

### 2. Preserve `gc_en` Data Layer

- Treat `gc_en:dataInit2` as `gc_en`-owned content, not as a target for restaurant-side table replacement.
- Do not overwrite `gc_en`-specific arrays such as:
  - `POT_TIME`
  - `POT_RESULT`
  - `PAN_NEEDED`
  - `PAN_RESULT`
  - `RAW_MIX`
  - `RAW_RESULT`
  - `MENU_LIST`
  - `HAZARD_MENU_LIST`
  - `FRIDGE_LIST`
  - `WEAVER_MENU_LIST`
  - `STAGE_NAME`
- Only touch `dataInit2` if a future structural dependency requires a minimal local adjustment.
- The current `en.txt` `HEAD` patch analysis indicates no required `dataInit2` changes for this port pass.

### 3. `gc_en` Mode Expansion In `gc_en.txt`

- Expand the 4-mode scaffold to 6 modes in the same structural positions used by current `en.txt`:
  - HUD labels
  - mode colors
  - `Global.totalScore`
  - `Global.difficulty`
  - `Global.storageLevel`
  - `Global.stageTime`
  - `Global.failEnd`
  - scoreboard thresholds
  - host mode rotation
- Do not finalize `Global.STAGE_CODE` values in this pass.
- Replace the expanded `gc_en` `Global.STAGE_CODE` body with explicit `//TODO` placeholders for the user to edit later.
- Expand `Global.CUSTOMER_LIST` to the 6-mode structure using current `en.txt` as the source template, because the old shared baseline indicates the customer-wave model is portable across localized restaurant and GC files.

### 4. Customer / Path Feature Port In `gc_en.txt`

- Port the `Jetpack Cat`, `Reinhardt`, and `Junker Queen` customer feature set from current `en.txt`.
- Expand the table/path model from 14 to 19 slots.
- Update:
  - `Global.tableOrderCode`
  - `Global.TABLE_PATH`
  - `Global.TABLE_POSITION`
  - helper-route offsets (`+15` -> `+20`)
  - customer metadata arrays
  - customer spawn / movement / reserved-order logic
  - serve success / failure branches
- Directly port shared structural content from `en.txt` where no `gc_en`-specific alternative exists.
- This direct-port rule is expected to apply to:
  - `Global.CUSTOMER_LIST`
  - common subroutine bodies
  - shared control-flow refactors
  - table/path scaffolding

### 5. Item-Code Remap Layer In `gc_en.txt`

- Audit every touched `Global.createItemData = Array(..., <item>, ...)` site before implementation.
- Remap literals and branch indices by semantic role instead of raw restaurant ids.
- Use `gc_en` arrays as the authoritative source:
  - `Global.KNIFE`
  - `Global.PERK_LIST`
  - `Global.UPGRADE_CODE`
- Known remap-sensitive areas:
  - initial starter items
  - practice-mode random item spawn
  - ordered knife delivery
  - perk drop / re-drop
  - tip-drop reset item
  - upgrade-shop random tool / shoe pools
  - serving-ball perk handling
  - any branch that references `itemPerk == n` directly
- Known `gc_en` index mismatch to preserve:
  - serving-ball perk is `itemPerk == 6`
  - current `en.txt` serving-ball logic lives on a different perk index
- Build a pre-port inventory so each touched branch has an explicit remap decision recorded.

### 6. Track `gc_en`-Only Anomalies

- Preserve the current `gc_en`-specific `PERK_LIST` and `STAGE_CODE` differences in the artifact trail.
- During implementation, avoid “fixing” them implicitly unless the user explicitly wants normalization to `gc_kr`.
- If a touched branch depends on the `PERK_LIST` first-array index layout, treat `gc_en`’s current table as the source of truth for that pass.

### 7. Text and UI In `gc_en.txt`

- Update visible build/version text and changelog text to reflect the new `gc_en` port.
- Preserve `gc_en`-specific stage naming and presentation.
- Only adopt restaurant-facing text where the new feature requires equivalent `gc_en` messaging.

## Recommended Execution Order

1. Port the new subroutine scaffold and 6-mode framework first.
2. Freeze `gc_en:dataInit2` as protected content before touching gameplay rules.
3. Prepare the `gc_en` item-code and perk-index remap inventory.
4. Port customer/path behavior and table-model changes next, directly copying `en.txt` where no `gc_en`-specific alternative exists.
5. Remap every touched item/perk/knife code site while preserving existing `gc_en` values where applicable.
6. Preserve the current `gc_en`-only `PERK_LIST` and `STAGE_CODE` anomalies unless the user explicitly asks to normalize them.
7. Leave `Global.STAGE_CODE` as explicit `//TODO` placeholders for the user rather than inventing final values.
8. Finish with `gc_en`-specific text and scoreboard cleanup.
9. Run static verification before any runtime test.

## Verification Plan

### Automated / Static Checks

- Search for stale 4-mode assumptions:
  - `% 4`
  - `Array(4, 0, 1, 1)`
  - `Array(300, 300, 180, 180)[Global.difficulty]`
- Search for stale pre-delivery helper offsets:
  - `+ 15`
  - `TABLE_PATH[14]`
- Search for old failure flow still inlined:
  - repeated `Global.failCount += True;`
  - missing `Call Subroutine(stageFail);`
- Search for missing new-customer coverage:
  - `Hero(Jetpack Cat)`
  - `Hero(Reinhardt)`
  - `Hero(Junker Queen)`
- Search for restaurant ids accidentally copied into `gc_en`-only pools where semantic remap is expected.
- Verify that `gc_en:dataInit2` recipe/menu arrays were not replaced by restaurant-side arrays during the structural port.
- Verify that `gc_en` retains or intentionally updates:
  - `Global.PERK_LIST`
  - `Global.STAGE_CODE`

### Manual Verification

- Practice mode:
  - mode rotation
  - starter item spawn
  - random practice item generation
- Item / perk flow:
  - knife order delivery
  - random tool / shoe purchases
  - serving-ball related perk path
  - tip-drop reset item
- Customer flow:
  - normal table path
  - extra delivery-lane path
  - special-customer serve success / fail branches
- Data integrity:
  - `gc_en` menu sets still load correctly
  - fridge/menu/hazard/weaver tables still match `gc_en` content
  - no restaurant-side recipe table leaked into `gc_en`
- Locale integrity:
  - `gc_en` stage names and upgrade text remain English
  - no unintended regression from the known `PERK_LIST` / `STAGE_CODE` differences
- Score / fail flow:
  - new mode fail thresholds
  - `stageFail` behavior
  - scoreboard thresholds and mode labels
