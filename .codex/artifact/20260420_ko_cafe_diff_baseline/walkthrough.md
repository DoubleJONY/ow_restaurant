# `ko.txt` / `cafe_kr.txt` Baseline Diff Session

## Date

- 2026-04-20

## Recorded Context

- Baseline commit: `338c7321f9f4aed9688c6d8cb70aaa13f729be1d`
- Current `HEAD`: `83e18fab328dacc51b490c744082bb30318a8142`
- `ko.txt` touched by 7 commits after the baseline:
  - `ab7d944` (`260415`)
  - `3b11f80` (`260415`)
  - `8db9d01` (`260415`)
  - `57f23fc` (`260416`)
  - `cf0d232` (`260416`)
  - `eb07122` (`260417`)
  - `83e18fa` (`260417`)
- `git diff --stat 338c7321..HEAD -- ko.txt`:
  - `531 insertions`
  - `184 deletions`

## Recorded `ko.txt` Change Groups

- Expanded the restaurant table/path model from 14 slots to 19 slots.
- Added reusable subroutines:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Added `Jetpack Cat`, `Reinhardt`, and `Junker Queen` customer flows.
- Expanded stage mode handling from 4 modes to 6 modes.
- Updated `Global.CUSTOMER_LIST` and `Global.STAGE_CODE` for the new feature set.
- Added the 6-player `itemPerk == 7` fallback that forces the player into `Hero(Jetpack Cat)`.
- Added solo-play `Wrecking Ball` support at stage start.
- Added an extra delivery-zone serve validation path near `Vector(196.440, -3, 205.170)`.
- Reworked failure handling around the new `stageFail` subroutine and stage-mode-specific fail limits.

## Pending

- Compare the current `ko.txt` state against `cafe_kr.txt`, while treating `338c7321f9f4aed9688c6d8cb70aaa13f729be1d` as the baseline for "new since then" changes.

## `cafe_kr.txt` Baseline Check

- `git diff --quiet 338c7321f9f4aed9688c6d8cb70aaa13f729be1d..HEAD -- cafe_kr.txt` returned `0`.
- Result: `cafe_kr.txt` has no commits after the baseline.
- Therefore, "baseline -> current" differences exist only on the `ko.txt` side.
- Practically, comparing current `ko.txt` to current `cafe_kr.txt` for post-baseline work is equivalent to comparing:
  - current `ko.txt`
  - baseline-era `cafe_kr.txt`

## Current `ko.txt` vs Current `cafe_kr.txt`

### 1. Table and path model diverged

- `ko.txt` expanded `Global.tableOrderCode` to 19 slots and added the extra route/table data for the delivery lane.
- `cafe_kr.txt` still uses the old 14-slot model.
- `ko.txt` also shifted serve-bot helper path offsets from `+15` to `+20`, while `cafe_kr.txt` still uses `+15`.

### 2. New reusable subroutines exist only in `ko.txt`

- `ko.txt` declares and uses:
  - `validateServe`
  - `changeHero`
  - `stageFail`
- `cafe_kr.txt` still keeps the older inline implementations for serve validation, hero-change handling, and repeated stage-fail logic.

### 3. Stage-mode model diverged

- `ko.txt` now uses 6 stage modes.
- `cafe_kr.txt` still uses 4 stage modes.
- The old cafe-side arrays remain in place for:
  - mode selection rotation
  - difficulty mapping
  - stage time
  - fail limits
  - mode labels / HUD colors

### 4. New customer feature set is missing from `cafe_kr.txt`

- `ko.txt` added `Jetpack Cat`, `Reinhardt`, and `Junker Queen` as formal customer types and updated the related metadata arrays.
- `cafe_kr.txt` `Global.CUSTOMER_LIST` and `Global.STAGE_CODE` still reflect the older 4-mode customer wave model.
- The associated customer-specific logic is also absent on the cafe side:
  - `Reinhardt` multi-serve / score scaling / tip behavior
  - `Junker Queen` serve-fail crowd-disruption behavior
  - `Jetpack Cat` movement, spawn, and reserved-order behavior

### 5. Serve validation flow diverged

- `ko.txt` added the extra delivery-zone validation near `Vector(196.440, -3, 205.170)` and routes serving through `validateServe`.
- `cafe_kr.txt` still uses the older inline serve-check branch around the cafe serve area and item code `18` reset path.

### 6. Start-stage and fail-flow handling diverged

- `ko.txt` moved fail handling into `stageFail`, changed bonus-stage handling to `Global.stageMode == 4`, and uses stage-mode-based `Global.failEnd`.
- `cafe_kr.txt` still uses:
  - bonus stage: `Global.stageMode == 3`
  - difficulty-based `Global.failEnd`
  - repeated inline fail-count logic

### 7. Perk / helper behavior diverged

- `ko.txt` added the 6-player forced-`Hero(Jetpack Cat)` fallback for the serve-bot style perk flow and added solo auto-support at stage start.
- `cafe_kr.txt` still has the older Wrecking Ball summon branch and does not contain the forced `Jetpack Cat` path.

## Porting Caution

- `cafe_kr.txt` is not just "behind" `ko.txt`; it is also a different gameplay variant.
- Some `ko.txt` changes are clearly restaurant-specific and should not be copied mechanically into cafe logic:
  - table-count expansion to 19
  - delivery-lane path data
  - restaurant-specific serve-zone coordinates
  - restaurant-specific item codes and perk mappings
- The safe interpretation for follow-up work is:
  - cafe currently preserves the pre-`260415..260417` structure
  - any port should be selective, not a blind sync

## Same-Commit Structural Notes (`338c7321`)

### `CUSTOMER_LIST` status

- `338c7321:ko.txt` and `338c7321:cafe_kr.txt` use the same `Global.CUSTOMER_LIST` block.
- The customer-wave structure itself is shared between the two variants at that commit.
- The divergence appears immediately below it in `Global.STAGE_CODE`, not in `Global.CUSTOMER_LIST`.

### `createItemData` item-code differences

- There are two kinds of differences in the third `Global.createItemData` parameter:
  - direct literal differences
  - indirect differences through `KNIFE`, `PERK_LIST`, and `UPGRADE_CODE`

#### Direct literal differences

- Initial practice item:
  - restaurant: `357`
  - cafe: `12`
- Initial stage-mode starter item array:
  - restaurant: `Array(354, 357, 357, 360)[Global.stageMode]`
  - cafe: `Array(12, 12, 12, 16, 4)[Global.stageMode]`
- Initial second starter item:
  - restaurant: `434`
  - cafe: `351`
- Ordered knife spawn:
  - restaurant: `Random Integer(62, 65)`
  - cafe: `Random Integer(2, 5)`
- Ordered premium knife spawn:
  - restaurant: `354`
  - cafe: `7`
- Tip / reset item:
  - restaurant: `432`
  - cafe: `18`
- Practice-mode random spawn pool:
  - restaurant: `Array(61, 62, 63, 64, 65, 265, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 433, 434)`
  - cafe: `Array(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 351)`
- Shop `UPGRADE_CODE == 1` random tool pool:
  - restaurant: `Array(352, 352, 352, 352, 353, 356, 356, 356, 356, 357, 357, 360, 361, 361, 433, 433, 433, 434, 434)`
  - cafe: `Array(8, 8, 8, 8, 9, 11, 11, 11, 11, 12, 12, 15, 16, 16, 17, 17, 351, 351)`
- Shop `UPGRADE_CODE == 2` random shoe pool:
  - restaurant: `Array(355, 355, 355, 355, 355, 358, 358, 358, 359)`
  - cafe: `Array(10, 10, 10, 10, 10, 13, 13, 13, 14)`
- Shop `UPGRADE_CODE == 9` item:
  - restaurant: `432`
  - cafe: `18`

#### Indirect array-driven differences

- Knife re-drop lines use `Global.KNIFE[Event Player.knifeCode]`, but the underlying arrays differ:
  - restaurant: `Array(61, 265, 62, 63, 64, 65, 354)`
  - cafe: `Array(1, 6, 2, 3, 4, 5, 7)`
- Perk re-drop lines use `Global.PERK_LIST[...]`, but the arrays differ:
  - restaurant tool perks: `Array(352, 353, 356, 357, 360, 361, 433, 434)`
  - cafe tool perks: `Array(8, 9, 11, 12, 15, 16, 17, 351)`
  - restaurant foot perks: `Array(355, 358, 359)`
  - cafe foot perks: `Array(10, 13, 14)`
- Upgrade purchase lines use `Global.UPGRADE_CODE[...]`, and the first upgrade output differs:
  - restaurant: `Array(265, -1, -2)`
  - cafe: `Array(6, -1, -2)`

#### Non-equivalent branch

- Restaurant has a special `itemPerk == 6` branch that spawns stage-driven item codes:
  - `Array(420, 424, 421, 422, 423, 425, 426, 427, 428, 429, 430, 431)[Random Value In Array(Global.STAGE_CODE[Global.stage])]`
- Cafe does not have the same create-item branch there; its nearby branch is the Wrecking Ball summon path.
