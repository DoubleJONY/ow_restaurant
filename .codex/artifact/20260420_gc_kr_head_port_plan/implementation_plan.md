# Port `ko.txt` `HEAD` Changes Into `gc_kr.txt`

Port the post-`338c7321f9f4aed9688c6d8cb70aaa13f729be1d` `ko.txt` feature set into `gc_kr.txt` while preserving `gc_kr`-specific recipe tables, menu graph, item ids, and perk-index layout.

## Analysis Summary

- `gc_kr.txt` has no commits after `338c7321`; the post-`260415..260417` feature work landed only in `ko.txt`.
- Structurally, `gc_kr.txt` is closer to `ko.txt` than the cafe variants are:
  - no `ICE_NEEDED` / `ICE_RESULT`
  - no split `dataInit2_1` / `dataInit2_2`
  - same general station model (`튀김기`, `솥`, `그릴`, `팬`)
- However, `gc_kr.txt` is not a shallow locale fork of `ko.txt`.
  - `dataInit2` contains a different recipe graph and different menu/stage data.
  - `STAGE_NAME`, `MENU_LIST`, `HAZARD_MENU_LIST`, `FRIDGE_LIST`, `WEAVER_MENU_LIST`, `RAW_MIX`, `RAW_RESULT`, `POT_*`, and `PAN_*` are all custom to `gc_kr`.
- At baseline, `Global.CUSTOMER_LIST` is effectively shared between `ko.txt` and `gc_kr.txt`, but `Global.STAGE_CODE` already diverges.
- Current `ko.txt` `HEAD` adds three main feature groups that `gc_kr.txt` still lacks:
  - new shared subroutines and failure flow (`validateServe`, `changeHero`, `stageFail`)
  - stage-mode expansion from 4 modes to 6 modes
  - new customer / path / table-model changes (`Jetpack Cat`, `Reinhardt`, `Junker Queen`, 19-slot table model)

## Baseline `338c` Differences

- `gc_kr.txt` has its own stage identity:
  - `Global.STAGE_NAME = "한식/일식/쌀국수/커리&필라프/리소토&파스타/소시지/스튜/비프&파이/버거&치킨/디저트/훠궈/타코"`
- `gc_kr.txt` uses a different item-id layer:
  - `Global.UPGRADE_CODE = Array(Array(6, -1, -2), ...)`
  - `Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7)`
  - `Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17), Array(10, 13, 14))`
- `gc_kr.txt` uses different literal item ids in gameplay:
  - tip/reset item path uses `18`
  - ordered knife paths use `2..5` and `7`
  - serving-ball perk is `itemPerk == 6`
- `gc_kr.txt` does not carry the restaurant `dataInit2` tables from `ko.txt`; it has a separate full data set and must keep it.

## User Review Required

> [!IMPORTANT]
> This plan assumes the goal is behavioral parity with current `ko.txt`, not literal line-by-line parity.
> `gc_kr` item ids, menu tables, and recipe tables should be preserved or remapped by role, not copied by raw number.

> [!IMPORTANT]
> This plan also assumes the same policy used for the cafe variants:
> `Global.STAGE_CODE` should not be finalized during the structural port.
> During implementation, the expanded `gc_kr` `Global.STAGE_CODE = ...` body should be left as explicit `//TODO` placeholders for the user to fill in manually.

> [!WARNING]
> `gc_kr.txt` is easier than `cafe_kr.txt` on structure, but easier to damage in `dataInit2`.
> The `ko.txt` `HEAD` patch does not require a `dataInit2` port, so overwriting `gc_kr:dataInit2` with restaurant-side arrays would be a regression.

## Proposed Changes

### 1. Structural Scaffold In `gc_kr.txt`

- Expand `subroutines` to add:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Port the shared structural refactors from current `ko.txt`:
  - hero-change extraction
  - serve-validation extraction
  - centralized stage-fail handling
- Update call sites to use the new subroutines rather than keeping duplicated inline logic.

### 2. Preserve `gc_kr` Data Layer

- Treat `gc_kr:dataInit2` as `gc_kr`-owned content, not as a target for restaurant-side table replacement.
- Do not overwrite `gc_kr`-specific arrays such as:
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
- The current `ko.txt` `HEAD` patch analysis indicates no required `dataInit2` changes for this port pass.

### 3. `gc_kr` Mode Expansion In `gc_kr.txt`

- Expand the 4-mode scaffold to 6 modes in the same structural positions used by current `ko.txt`:
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
- Replace the expanded `gc_kr` `Global.STAGE_CODE` body with explicit `//TODO` placeholders for the user to edit later.
- Expand `Global.CUSTOMER_LIST` to the 6-mode structure using current `ko.txt` as the source template, because the old shared baseline indicates the customer-wave model is portable.

### 4. Customer / Path Feature Port In `gc_kr.txt`

- Port the `Jetpack Cat`, `Reinhardt`, and `Junker Queen` customer feature set from current `ko.txt`.
- Expand the table/path model from 14 to 19 slots.
- Update:
  - `Global.tableOrderCode`
  - `Global.TABLE_PATH`
  - `Global.TABLE_POSITION`
  - helper-route offsets (`+15` -> `+20`)
  - customer metadata arrays
  - customer spawn / movement / reserved-order logic
  - serve success / failure branches
- Directly port shared structural content from `ko.txt` where no `gc_kr`-specific alternative exists.
- This direct-port rule is expected to apply to:
  - `Global.CUSTOMER_LIST`
  - common subroutine bodies
  - shared control-flow refactors
  - table/path scaffolding

### 5. Item-Code Remap Layer In `gc_kr.txt`

- Audit every touched `Global.createItemData = Array(..., <item>, ...)` site before implementation.
- Remap literals and branch indices by semantic role instead of raw restaurant ids.
- Use `gc_kr` arrays as the authoritative source:
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
- Known `gc_kr` index mismatch to preserve:
  - serving-ball perk is `itemPerk == 6`
  - `ko.txt` `HEAD` serving-ball logic lives on a different perk index
- Build a pre-port inventory so each touched branch has an explicit remap decision recorded.

### 6. Text and UI In `gc_kr.txt`

- Update visible build/version text and changelog text to reflect the new `gc_kr` port.
- Preserve `gc_kr`-specific stage naming and presentation.
- Only adopt restaurant-facing text where the new feature requires equivalent `gc_kr` messaging.

## Recommended Execution Order

1. Port the new subroutine scaffold and 6-mode framework first.
2. Freeze `gc_kr:dataInit2` as protected content before touching gameplay rules.
3. Prepare the `gc_kr` item-code and perk-index remap inventory.
4. Port customer/path behavior and table-model changes next, directly copying `ko.txt` where no `gc_kr`-specific alternative exists.
5. Remap every touched item/perk/knife code site while preserving existing `gc_kr` values where applicable.
6. Leave `Global.STAGE_CODE` as explicit `//TODO` placeholders for the user rather than inventing final values.
7. Finish with `gc_kr`-specific text and scoreboard cleanup.
8. Run static verification before any runtime test.

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
- Search for restaurant ids accidentally copied into `gc_kr`-only pools where semantic remap is expected.
- Verify that `gc_kr:dataInit2` recipe/menu arrays were not replaced by restaurant-side arrays during the structural port.

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
  - `gc_kr` menu sets still load correctly
  - fridge/menu/hazard/weaver tables still match `gc_kr` content
  - no restaurant-side recipe table leaked into `gc_kr`
- Score / fail flow:
  - new mode fail thresholds
  - `stageFail` behavior
  - scoreboard thresholds and mode labels
