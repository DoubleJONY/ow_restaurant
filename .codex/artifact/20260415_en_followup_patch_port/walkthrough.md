# `en.txt` Follow-Up Patch Port Session

## Date

- 2026-04-15

## Scope

Apply the latest post-`Jetpack Cat` gameplay patch from `ko.txt` into `en.txt`, while keeping existing English locale text where possible and only introducing explicit new translations requested by the user.

Requested translations used:

- `거대식가` -> `Gentle Giant`
- `시끄러운 손님` -> `Karen`
- `스타 비스트로` -> `Buzzy Restaurant`
- `폭군의 셰프` -> `Chef du Roi`

## Starting Point

Before this session:

- `en.txt` already contained the earlier `Jetpack Cat` port.
- `en.txt` did not yet include the later `ko.txt` expansion to 6 mode variants, the new `Reinhardt` / `Junker Queen` customer logic, or the new `stageFail` subroutine flow.
- Existing English locale strings were already in place for older features and needed to be preserved where practical.

## Changes Made

### 1. Declaration order was kept aligned

- Added `29: stageFail` to the top `subroutines` declaration block before using it.

This follows the workspace rule that new declarations must appear in the top declaration section first.

### 2. Global mode metadata was expanded to 6 modes

- Expanded `Global.totalScore` from 4 entries to 6 entries.
- Expanded stage-mode color arrays used by the top-right build HUD and mode-selection HUD.
- Expanded mode-name arrays in:
  - the host mode-selection HUD
  - the player spawn title display
  - the scoreboard summary

New English names used:

- `Buzzy Restaurant`
- `Chef du Roi`

### 3. Global mode-dependent values were updated

- `Global.difficulty` became `Array(4, 0, 1, 2, 1, 2)[Global.stageMode]`
- `Global.storageLevel` became `Array(7, 3, 3, 0, -1, -1)[Global.stageMode]`
- `Global.stageTime` became `Array(999, 300, 300, 240, 180, 600)[Global.stageMode]`
- Starter item selection became `Array(354, 357, 357, 360, 360, 360)[Global.stageMode]`

### 4. English release-note text was updated conservatively

- Preserved existing English structure and only changed text where the new patch required it.
- Updated the in-world changelog section to mention:
  - `Delivery Cat`
  - `Gentle Giant`
  - `Karen`
  - new modes `Buzzy Restaurant` and `Chef du Roi`

Existing English UI strings outside the new feature scope were intentionally left in place.

### 5. `Hero(Reinhardt)` and `Hero(Junker Queen)` were added to customer logic

- Added both heroes to the Team 2 customer hero mapping array.
- Extended customer display-name strings with:
  - `Gentle Giant`
  - `Karen`
- Extended customer metadata arrays:
  - `playerColor`
  - `score`
  - `orderCount`
  - `orderTimeOut`
  - `byOrder`

Additional gameplay behavior ported:

- `Gentle Giant` moves slower on entry and is scaled up.
- `Gentle Giant` can request 9 material drops in the additional-material branch.
- The multi-serve customer branch was expanded from `Zarya` only to `Reinhardt || Zarya`.
- `Gentle Giant` now uses `9` as the multi-serve target count, with HUD text updated accordingly.
- Successful partial serves in this branch add `+10` to both `Global.systemScore` and `Global.stageScore`.
- `Gentle Giant` also uses a higher tip chance (`50`).

### 6. Failure handling was reworked around `stageFail`

- Added a dedicated `rule("Global subroutine: Stage Fail")`.
- Replaced repeated inline failure-count logic in `startStage` with `Call Subroutine(stageFail);`.
- Updated `Global.failEnd` from difficulty-based values to stage-mode-based values:
  - `Array(99, 5, 3, 2, 3, 1)[Global.stageMode]`
- Adjusted `Global.isBonusStage` to the newer `Global.stageMode == 4` behavior.
- Preserved the existing English failure messages while adopting the new structure.

### 7. `serveFail` was updated for the new customers

- Added `customerStatus == 6` remap behavior before looking up the failure text.
- Added the new confusion failure text:
  - `Fled in confusion!`
- Extended score-loss scaling so `Hero(Reinhardt)` multiplies the penalty by `9`.
- Allowed `Global.stageMode == 5` to trigger the same sudden stage-end pressure as the newer `ko.txt` logic.

Additional hero-specific behavior:

- `Hero(Junker Queen)` now triggers a stun/confusion burst on failure.
- `Hero(Reinhardt)` and `Hero(Ramattra)` both drop perk items through `dropTips`.

### 8. `Hero(Junker Queen)` targeting logic was tightened after the initial port

The first pass matched the broad `ko.txt` style of affecting Team 2 players by index. After review, this was narrowed in `en.txt`.

Final behavior:

- `Hero(Junker Queen)` now only affects nearby Team 2 customers within distance `5`.
- The target set is built with:
  - `Filtered Array(All Players(Team 2), ...)`
  - `Has Spawned(Current Array Element)`
  - `Current Array Element != Event Player`
  - `Current Array Element.controlingIndex != -1`
  - `Distance Between(Position Of(Current Array Element), Position Of(Event Player)) < 5`
- Only that filtered set receives `.customerStatus = 6`

Meaning:

- The effect now targets real nearby customers instead of raw Team 2 slots.

### 9. `dataInit3` was expanded to match the newer `ko.txt` tables

- Expanded `Global.CUSTOMER_LIST` from 4 stage-mode groups to 6.
- Expanded `Global.STAGE_CODE` from 4 groups to 6.

The new stage-mode groups include waves containing:

- `Hero(Reinhardt)`
- `Hero(Junker Queen)`
- existing `Jetpack Cat` and related special-customer mixes

### 10. Mode-selection and scoring behavior was updated

- `Host Player: Select Mode` now rotates with `% 6`.
- Added the `stageMode == 5` initialization branch that:
  - grants `$500` to players
  - boosts fryer/grill/pot/pan power
  - spawns starter item `354`
- Updated `validateServe` per-serve team score bonus to use:
  - `Global.stageMode < 4 ? True : False`
- Updated scoreboard rank thresholds to use:
  - `Global.stageMode >= 4 ? ... : ...`

## Notes on Preserved English Text

The user asked to keep existing English resources where possible.

This session therefore:

- kept older English strings such as existing `A-mei-zing`, `Swift Served`, and prior UI wording unless the new patch directly required structural or naming changes
- only introduced the requested new names for the new customers and modes
- kept pre-existing English message structure in `startStage`, `serveFail`, and scoreboard text wherever the new gameplay patch did not force a rewrite

## Validation

Static verification performed:

- Confirmed `29: stageFail` exists in the top declaration block.
- Confirmed the 6-mode labels appear in mode-selection, spawn title, and scoreboard summary.
- Confirmed the requested translations appear in the new-customer and new-mode text.
- Confirmed `Hero(Reinhardt)` and `Hero(Junker Queen)` are present in customer mapping and wave tables.
- Confirmed the `Dummy: Spawn` multi-serve branch now includes `Hero(Reinhardt)`.
- Confirmed `Global.failEnd` now depends on `Global.stageMode`.
- Confirmed `Host Player: Select Mode` now rotates with `% 6`.
- Confirmed `validateServe` uses `Global.stageMode < 4`.
- Confirmed scoreboard rank thresholds use `Global.stageMode >= 4`.
- Confirmed the final `Hero(Junker Queen)` branch only applies `customerStatus = 6` to nearby Team 2 customers within radius `5`.

## Remaining Risk

- No in-game Workshop runtime validation has been run yet.
- `ko.txt` itself still contains additional rough edges from the original feature patch, so runtime behavior should be verified in practice mode and in the new 6-mode flows.
- The new `Junker Queen` radius-limited filter is safer than the original slot-based version, but it is still worth validating in live Team 2 crowd situations.
