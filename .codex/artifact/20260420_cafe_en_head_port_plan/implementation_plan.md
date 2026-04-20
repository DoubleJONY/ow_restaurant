# Port `en.txt` `HEAD` Changes Into `cafe_en.txt`

Port the post-`338c7321f9f4aed9688c6d8cb70aaa13f729be1d` `en.txt` feature set into `cafe_en.txt` while preserving cafe-specific item ids, menu tables, ice-machine logic, and init-routine split structure.

## Analysis Summary

- `cafe_en.txt` has no commits after `338c7321`; it still reflects the pre-`260415..260417` structure, like `cafe_kr.txt`.
- At `338c7321`, `Global.CUSTOMER_LIST` matched between `en.txt` and `cafe_en.txt`, but `Global.STAGE_CODE` already diverged.
- Current `en.txt` `HEAD` adds the same three major feature groups already observed in `ko.txt` `HEAD`:
  - new customer / path / table model changes (`Jetpack Cat`, `Reinhardt`, `Junker Queen`, 19-slot table model)
  - new shared subroutines and failure flow (`validateServe`, `changeHero`, `stageFail`)
  - stage-mode expansion from 4 modes to 6 modes, with updated score/fail/scaffold logic
- Cafe already diverges on semantic ids and content tables:
  - `UPGRADE_CODE`
  - `KNIFE`
  - `PERK_LIST`
  - `ITEM_NAME` / menu-related arrays
  - `STAGE_CODE`
  - `ICE_NEEDED`
  - `ICE_RESULT`
- `cafe_en.txt` also differs structurally from `en.txt` in one important way:
  - long init content is split across `dataInit2_1` and `dataInit2_2`
  - current `en.txt` keeps the same content in a single `dataInit2`
  - the split appears to be size-management, not a semantic fork

## Baseline `338c` Differences

- `CUSTOMER_LIST` is identical between `338c:en.txt` and `338c:cafe_en.txt`.
- `STAGE_CODE` is cafe-specific and diverges immediately after the shared `CUSTOMER_LIST` block.
- `cafe_en.txt` uses cafe-side ids in:
  - `Global.UPGRADE_CODE = Array(Array(6, -1, -2), ...)`
  - `Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7)`
  - `Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17, 351), Array(10, 13, 14))`
- `cafe_en.txt` includes `ICE_NEEDED` / `ICE_RESULT`, while restaurant `en.txt` instead uses restaurant-side extra tables such as `MELT_LIST`.
- `cafe_en.txt` stage/menu identity is cafe-specific even though the customer-wave scaffold was shared at baseline.

## User Review Required

> [!IMPORTANT]
> This plan assumes the goal is behavioral parity with current `en.txt`, not literal line-by-line parity.
> Cafe-specific item ids and table values should be preserved or remapped by role, not copied by raw number.

> [!IMPORTANT]
> This plan mirrors the existing `cafe_kr` port policy:
> `Global.STAGE_CODE` should not be finalized during the structural port.
> During implementation, the expanded cafe `Global.STAGE_CODE = ...` block should be left as explicit `//TODO` placeholders for the user to fill in manually.

> [!WARNING]
> The highest edit-risk is not only item-id drift but also the split init layout in `cafe_en.txt`.
> Porting `en.txt:dataInit2` by blind copy would make later maintenance harder and increases the chance of dropping `ICE_*` or duplicating an init table.

## Proposed Changes

### 1. Structural Scaffold In `cafe_en.txt`

- Expand `subroutines` to add:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Port the shared structural refactors from current `en.txt`:
  - hero-change extraction
  - serve-validation extraction
  - centralized stage-fail handling
- Update all call sites to use the new subroutines rather than keeping duplicated inline logic.

### 2. Init-Routine Port Strategy In `cafe_en.txt`

- Treat `dataInit2_1` and `dataInit2_2` as one logical init unit during analysis and editing.
- Build a section map before editing:
  - which arrays currently live in `cafe_en.txt:dataInit2_1`
  - which arrays currently live in `cafe_en.txt:dataInit2_2`
  - where the equivalent content lives inside current `en.txt:dataInit2`
- Keep the split structure in `cafe_en.txt` unless the user later asks for normalization.
- Port init content by semantic block, not by raw contiguous line ranges.
- Preserve the existing call order in `Global: Setting`:
  - `Call Subroutine(dataInit);`
  - `Call Subroutine(dataInit2_1);`
  - `Call Subroutine(dataInit2_2);`
- Protect cafe-only init blocks during the port:
  - `ICE_NEEDED`
  - `ICE_RESULT`
- After porting, verify that each init table is assigned exactly once and no shared block is missing from the split pair.

### 3. Cafe-Specific Mode Expansion In `cafe_en.txt`

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
- Replace the expanded cafe `Global.STAGE_CODE` body with explicit `//TODO` placeholders for the user to edit later.
- Expand `Global.CUSTOMER_LIST` to the 6-mode structure using current `en.txt` as the source template, because the old shared baseline indicates the customer-wave model is portable.

### 4. Customer / Path Feature Port In `cafe_en.txt`

- Port the `Jetpack Cat`, `Reinhardt`, and `Junker Queen` customer feature set from current `en.txt`.
- Expand the table/path model from 14 to 19 slots if the delivery-lane coordinates remain valid in the cafe variant.
- Update:
  - `Global.tableOrderCode`
  - `Global.TABLE_PATH`
  - `Global.TABLE_POSITION`
  - helper-route offsets (`+15` -> `+20`)
  - customer metadata arrays
  - customer spawn / movement / reserved-order logic
  - serve success / failure branches
- Preserve cafe-only cooking and item semantics while applying the new customer behaviors.
- When a touched structure does not contain cafe-specific content already, port the current `en.txt` version directly rather than re-deriving it.
- This direct-port rule is expected to apply to shared structural content such as:
  - `Global.CUSTOMER_LIST`
  - new customer/path scaffolding where no cafe-specific alternative exists yet
  - common subroutine bodies and shared control-flow refactors

### 5. Item-Code Remap Layer In `cafe_en.txt`

- Audit every `Global.createItemData = Array(..., <item>, ...)` site touched by the restaurant patch.
- Remap literals and branch indices by semantic role instead of raw restaurant ids.
- If a branch already uses a valid cafe-side item code or cafe-side lookup array, preserve that value while porting only the surrounding logic.
- Use existing cafe arrays as the authoritative source:
  - `Global.KNIFE`
  - `Global.PERK_LIST`
  - `Global.UPGRADE_CODE`
  - `Global.ICE_NEEDED`
  - `Global.ICE_RESULT`
- Known remap-sensitive areas:
  - initial starter items
  - practice-mode random item spawn
  - ordered knife delivery
  - perk drop / re-drop
  - tip-drop reset item
  - upgrade-shop random tool / shoe pools
  - serve-bot / serving-ball perk handling
- Build a pre-port inventory of these cafe-sensitive item-code sites before implementation so each touched branch has an explicit remap decision recorded.

### 6. Cafe-Specific Text and UI In `cafe_en.txt`

- Update visible build/version text and changelog text to reflect the new cafe port.
- Preserve cafe-specific English naming and station identity.
- Only adopt restaurant-facing text where the new feature requires equivalent cafe messaging.

## Recommended Execution Order

1. Build the `dataInit2` section map first so split-init edits stay deterministic.
2. Port the new subroutine scaffold and 6-mode framework second.
3. Prepare the cafe-sensitive item-code/remap inventory before editing create-item branches.
4. Port customer/path behavior and table-model changes next, directly copying `en.txt` where no cafe-specific alternative exists.
5. Remap every touched item/perk/knife code site while preserving existing cafe values where applicable.
6. Leave `Global.STAGE_CODE` as explicit `//TODO` placeholders for the user rather than inventing final values.
7. Finish with cafe-specific text and scoreboard cleanup.
8. Run split-init integrity checks before any runtime test.

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
- Search for split-init integrity:
  - `Call Subroutine(dataInit2_1);`
  - `Call Subroutine(dataInit2_2);`
  - exactly one assignment each for `ICE_NEEDED` and `ICE_RESULT`
  - no duplicated `POT_*`, `PAN_*`, `MENU_LIST`, `UPGRADE_CODE`, `KNIFE`, or `PERK_LIST` blocks across both split routines
- Search for restaurant ids accidentally copied into cafe-only pools where semantic remap is expected.

### Manual Verification

- Practice mode:
  - mode rotation
  - starter item spawn
  - random practice item generation
- Item / perk flow:
  - knife order delivery
  - random tool / shoe purchases
  - serving-ball related perk path
- Customer flow:
  - normal table path
  - extra delivery-lane path if enabled
  - special-customer serve success / fail branches
- Init integrity:
  - game boot completes after split init calls
  - ice-machine items still transform correctly
  - no missing menu, fridge, or upgrade tables after initialization
- Score / fail flow:
  - new mode fail thresholds
  - `stageFail` behavior
  - scoreboard thresholds and mode labels
