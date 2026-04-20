# Port `ko.txt` `HEAD` Changes Into `cafe_kr.txt`

Port the post-`338c7321f9f4aed9688c6d8cb70aaa13f729be1d` `ko.txt` feature set into `cafe_kr.txt` while preserving cafe-specific item ids, menu tables, and content identity.

## Analysis Summary

- `cafe_kr.txt` has no commits after `338c7321`; it still reflects the pre-`260415..260417` structure.
- At `338c7321`, `Global.CUSTOMER_LIST` matched between restaurant and cafe, but `Global.STAGE_CODE` already diverged.
- `ko.txt` `HEAD` adds three major feature groups:
  - new customer / path / table model changes (`Jetpack Cat`, `Reinhardt`, `Junker Queen`, 19-slot table model)
  - new shared subroutines and failure flow (`validateServe`, `changeHero`, `stageFail`)
  - stage-mode expansion from 4 modes to 6 modes, with updated score/fail/scaffold logic
- Cafe already diverges on semantic ids and content tables:
  - `KNIFE`
  - `PERK_LIST`
  - `UPGRADE_CODE`
  - `ITEM_NAME` / menu-related arrays
  - `STAGE_CODE`
  - cooking station semantics (`오븐`, `제빙기`, `ICE_*`)

## User Review Required

> [!IMPORTANT]
> This plan assumes the goal is behavioral parity with current `ko.txt`, not literal line-by-line parity.
> Cafe-specific item ids, starter items, and random item pools will be remapped by role, not copied by raw number.

> [!IMPORTANT]
> This plan also assumes the cafe variant should adopt the same 6-mode scaffold as current `ko.txt`, but `Global.STAGE_CODE` itself will not be finalized by Codex in the structural port pass.
> During implementation, `Global.STAGE_CODE = ...` should be left as explicit `//TODO` placeholders for the user to fill in manually.

> [!WARNING]
> The highest-risk part is the cafe-side design for the two extra modes. `Customer_LIST` can follow the restaurant expansion pattern, but `STAGE_CODE` cannot be copied directly because the cafe menu graph differs.

## Proposed Changes

### 1. Structural Scaffold In [`cafe_kr.txt`](file:///Users/jony/VscProjects/ow_restaurant/cafe_kr.txt)

- Expand `subroutines` to add:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Port the shared structural refactors from current `ko.txt`:
  - hero-change extraction
  - serve-validation extraction
  - centralized stage-fail handling
- Update all call sites to use the new subroutines rather than keeping duplicated inline logic.

### 2. Cafe-Specific Mode Expansion In [`cafe_kr.txt`](file:///Users/jony/VscProjects/ow_restaurant/cafe_kr.txt)

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
- Replace the expanded cafe `Global.STAGE_CODE` body with explicit `//TODO` placeholders for the user to edit later.
- Expand `Global.CUSTOMER_LIST` to the 6-mode structure using the restaurant `HEAD` wave pattern as the source template, because the old shared baseline indicates the customer-wave model is portable.

### 3. Customer / Path Feature Port In [`cafe_kr.txt`](file:///Users/jony/VscProjects/ow_restaurant/cafe_kr.txt)

- Port the `Jetpack Cat`, `Reinhardt`, and `Junker Queen` customer feature set from current `ko.txt`.
- Expand the table/path model from 14 to 19 slots if the delivery-lane coordinates remain valid in the cafe variant.
- Update:
  - `Global.tableOrderCode`
  - `Global.TABLE_PATH`
  - `Global.TABLE_POSITION`
  - helper-route offsets (`+15` -> `+20`)
  - customer metadata arrays
  - customer spawn / movement / reserved-order logic
  - serve success / failure branches
- Preserve cafe-only cooking/item semantics while applying the new customer behaviors.
- When a touched structure does not contain cafe-specific content already, port the current `ko.txt` version directly rather than re-deriving it.
- This direct-port rule is expected to apply to shared structural content such as:
  - `Global.CUSTOMER_LIST`
  - new customer/path scaffolding where no cafe-specific alternative exists yet
  - common subroutine bodies and shared control-flow refactors

### 4. Item-Code Remap Layer In [`cafe_kr.txt`](file:///Users/jony/VscProjects/ow_restaurant/cafe_kr.txt)

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
  - upgrade-shop random tool/shoe pools
  - serve-bot / serving-ball perk handling
- Build a pre-port inventory of these cafe-sensitive item-code sites before implementation so each touched branch has an explicit remap decision recorded.

### 5. Cafe-Specific Text and UI In [`cafe_kr.txt`](file:///Users/jony/VscProjects/ow_restaurant/cafe_kr.txt)

- Update visible build/version text and changelog text to reflect the new cafe port.
- Preserve cafe-specific naming and station text:
  - `오븐`
  - `제빙기`
  - cafe recipe-book link / presentation
- Only adopt restaurant-facing text where the new feature requires equivalent cafe messaging.

## Recommended Execution Order

1. Port the subroutine scaffold and 6-mode framework first.
2. Prepare the cafe-sensitive item-code/remap inventory before editing create-item branches.
3. Port customer/path behavior and table-model changes second, directly copying `ko.txt` where no cafe-specific alternative exists.
4. Remap every touched item/perk/knife code site while preserving existing cafe values where applicable.
5. Leave `Global.STAGE_CODE` as explicit `//TODO` placeholders for the user rather than inventing final values.
6. Finish with cafe-specific text and scoreboard cleanup.
7. Run static searches for stale pre-port patterns before any runtime test.

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
- Search for restaurant ids accidentally copied into cafe-only pools where semantic remap is expected.

### Manual Verification

- Practice mode:
  - mode rotation
  - starter item spawn
  - random practice item generation
- Item/perk flow:
  - knife order delivery
  - random tool / shoe purchases
  - serving-ball related perk path
- Customer flow:
  - normal table path
  - extra delivery-lane path if enabled
  - special-customer serve success / fail branches
- Score / fail flow:
  - new mode fail thresholds
  - `stageFail` behavior
  - scoreboard thresholds and mode labels
