# cafe_kr.txt HEAD Diff Summary

Date: 2026-05-31

Target file: `cafe_kr.txt`

Diff base: current worktree vs `HEAD`

Diff size: `1063 insertions(+), 471 deletions(-)`

## High-Level Summary

This patch updates `cafe_kr.txt` from the older cafe version into the newer multi-mode cafe build, then applies the follow-up fixes found during manual testing.

The main behavioral changes are:

- Expand mode support from 4 modes to 6 `stageMode` values.
- Add and wire newer customer behavior, especially `Jetpack Cat`, `Reinhardt`, and `Junker Queen`.
- Expand table/path data and route logic for the newer customer/table layout.
- Split serving validation and stage-failure handling into subroutines.
- Sync scoreboard teleport handling through `gameSummaryTP`.
- Apply cafe-specific follow-up fixes for starting items, practice mode, additional materials, and version strings.

## Subroutines

Added subroutine slots:

- `19: setHint`
- `26: gameSummaryTP`
- `27: validateServe`
- `28: changeHero`
- `29: stageFail`

New rules added for those paths include:

- `rule("Global subroutine: validate serve")`
- `rule("Player: Changee Hero")`
- `rule("Global subroutine: Stage Fail")`
- `rule("Global subroutine: Scoreboard TP")`

## Version And HUD

- Updated visible cafe version strings from `v260212` to `v260531`.
- Updated the main right-side cafe HUD color arrays to the 6-mode `Global.stageMode` mapping.
- Updated mode-selection HUD strings to show six modes:
  - practice
  - casual dining
  - fine dining
  - star bistro
  - mastercook challenge
  - head chef challenge

## Mode And Stage System

- `Host Player: Select Mode` now cycles with `% 6` instead of `% 4`.
- `Global.difficulty`, `Global.storageLevel`, and `Global.stageTime` now use 6-entry `stageMode` mappings.
- Added mode-specific setup:
  - `stageMode == 3`: grants `Torch` (`16`) as part of Star Bistro setup.
  - `stageMode == 5`: grants starting money, boosts cooking station power, and grants `Head Chef Knife` (`7`) as part of Head Chef Challenge setup.
- `Global.failEnd` is now stage-mode based:
  - `Array(99, 5, 3, 2, 3, 1)[Global.stageMode]`
- Mastercook bonus-stage handling now keys from `stageMode == 4`.
- Head Chef Challenge gets stricter stage-failure behavior in late score checks.

## Starting Items

Starting item creation keeps the existing direct `createItemData` pattern.

Current intended split:

- Practice mode `0`: cleaner (`12`)
- Casual dining `1`: cleaner (`12`), cooling gun (`351`)
- Fine dining `2`: cleaner (`12`), cooling gun (`351`)
- Star bistro `3`: dash boots (`13`), portable knife (`3`), torch (`16`)
- Mastercook challenge `4`: torch (`16`), cooling gun (`351`)
- Head chef challenge `5`: teleport spell (`14`), head chef knife (`7`), torch (`16`)

Implementation points:

- First item array:
  - `Array(12, 12, 12, 13, 16, 14)[Global.stageMode]`
- Second item array:
  - `Array(Null, 351, 351, 3, 351, 16)[Global.stageMode]`
- Extra select-mode grants:
  - `stageMode == 3` grants `16`
  - `stageMode == 5` grants `7`

## Practice Mode Fixes

Cafe does not include the `ko.txt` tutorial / `hintText` flow, so the practice tutorial placeholder was removed.

Changes:

- Removed the first tutorial Soldier set from `CUSTOMER_LIST[0]`.
- Changed practice `STAGE_CODE[0]` from six `Array(0)` entries to five.
- Shifted practice special-stage indices:
  - all customers: `Global.stage == 2`
  - practice end: `Global.stage == 3`
  - other menu/workshop code: `Global.stage == 4`
- Removed the old tutorial-specific menu lock.
- Updated practice start message to:
  - `연습용 손님이 입장합니다!`
- Updated `Host Player: Set Permission` direct `CUSTOMER_LIST` writes after the removed tutorial slot:
  - Jetpack Cat override now writes `Global.CUSTOMER_LIST[1]`
  - Mauga/Roadhog/Reinhardt override now writes `Global.CUSTOMER_LIST[0]`

The practice "other menu" selector intentionally points to other workshop versions, not the current cafe code. For this cafe file it now advertises:

- `변기클라우드-모듬회밥` / `SPXXM`
- `Joseon-쿡제요리` / `P6ZAA`
- `Joseon-뉴 3호점` / `SSZ1Z1`
- `Gummybear-오리지널` / `8MAAN`

## Tables, Paths, And Serve Bot Routing

- Expanded `Global.tableOrderCode` from 14 to 19 entries.
- Expanded `Global.TABLE_PATH` and `Global.TABLE_POSITION` for the newer table layout.
- Updated path indexes for auxiliary movement:
  - merchant/customer fallback path now uses `Global.TABLE_PATH[19]`
  - serve bot delivery paths use `Global.TABLE_PATH[tableIndex + 20]`
- Added path/range handling for newer table groups:
  - normal tables
  - Freja table range
  - Jetpack Cat table range

## Customer System

The dummy customer index table was expanded to include:

- `Hero(Jetpack Cat)`
- `Hero(Reinhardt)`
- `Hero(Junker Queen)`

Related customer data arrays were expanded for:

- score
- order count
- timeout
- by-order behavior
- colors
- localized forced dummy names

Notable behavior additions:

- `Jetpack Cat`
  - uses airborne/extended table paths.
  - can spawn from `Vector(125.630, 4, 219.530)`.
  - receives a jump-button exception in `Player: Double Jump`.
  - has special serving-completion effects around its current position.
  - increments `Global.loadNext` for its burst ordering behavior.
- `Reinhardt`
  - scales larger and moves slower.
  - behaves like a multi-order customer with 9 orders.
  - uses larger score/failure multipliers.
- `Junker Queen`
  - gets custom failure behavior that can stun nearby Team 1 players and affect nearby Team 2 customers.
- `Mauga`
  - has alternate Korean forced-name/failure text when enabled in `ALLOWED_HEROS`.
- `Ramattra`
  - gains enhanced failure/tip logic and can disable `superDrink`.

## Additional Material Logic

Cafe-specific behavior was corrected so `ADDITIONAL_MATERIAL_LIST` is treated as LifeWeaver-only support.

Changes:

- Customer-side additional material creation is gated only by:
  - `Hero Of(Event Player) == Hero(LifeWeaver)`
- Removed restaurant stage-11 / butchery assumptions from cafe logic.
- Removed reserved-customer central-spawn additional-material logic.
- Removed stage-11 table-count throttling logic.
- Despawn slow handling now checks:
  - `Array Contains(Global.ADDITIONAL_MATERIAL_LIST, Global.itemCode[...])`
  - without checking stage/menu `11`.

## Item Physics And Serving

Serving validation was extracted into `validateServe`.

Changes:

- `itemPhysics` now detects near-table serving and calls `validateServe`.
- `validateServe` handles:
  - correct serving
  - tip item serving (`18`)
  - incorrect serving
  - by-order penalties
  - cooker/last-controller score updates
  - item cleanup
- Serving bonus logic now uses the updated mode boundary:
  - `Global.stageMode < 4`
- Direct delivery hit range now varies by `stageMode`.
- Item physics gained storage auto-place handling using `Global.storageIndex`.
- `Global.storageData` now stores:
  - item code
  - durability
  - progress
  - cooker data

## Stage Failure And Scoring

Repeated failure code inside `startStage` was replaced with:

- `Call Subroutine(stageFail)`

`stageFail` now centralizes:

- fail count increment
- failure message
- failure sound
- scoreboard fail count
- final game summary call when fail limit is reached

Scoreboard updates:

- mode labels expanded to six modes.
- rating thresholds now use `Global.stageMode >= 4` for challenge-mode scoring thresholds.
- scoreboard teleport blocks were replaced by `Call Subroutine(gameSummaryTP)`.
- the redundant late teleport block after invisibility was removed.
- `gameSummaryTP` now owns the six scoreboard teleport positions.

## Upgrades And Practice Tools

- `Global.upgradeList` is initialized and reused for deterministic rotation/randomization of upgrade item pools.
- `Host Player: Set Permission` in practice mode now:
  - pulls item codes from `Global.upgradeList[True]`
  - can temporarily unlock Jetpack Cat and Mauga/Reinhardt customer sets
  - updates `ALLOWED_HEROS` accordingly
- Upgrade purchase logic now rotates/randomizes tool and shoe item pools through `Global.upgradeList`.
- Upgrade price indexing was normalized in several places to use boolean indexes (`False`/`True`) where the existing code style expects them.

## Player Perk And Hero-Change Logic

- Added `changeHero` subroutine for restoring a player after forced hero changes.
- `itemPerk == 6` behavior now distinguishes:
  - fewer than 6 Team 1 players: summon serve ball
  - exactly 6 Team 1 players: force the player into `Hero(Jetpack Cat)` with controller controls
- Added `Hero(Jetpack Cat)` exception to `Player: Double Jump` so generic jump-disallow logic does not interfere with Jetpack Cat.

## Call Customer Flow

- `Global.loadNext` is reset at the start of customer calling.
- Customer table selection now supports:
  - normal table range
  - Freja range
  - Jetpack Cat range
- Jetpack Cat receives fallback table selection if its preferred extended range is unavailable.
- Dummy bot spawn location is conditional for Jetpack Cat.
- Reservation message formatting was kept functionally equivalent while the line layout changed.
- `Global.loadNext` decrement now uses `-= 1`.

## Known Follow-Up Fixes Included

The following manually found issues are included in the current `cafe_kr.txt` state:

- version string updated to `v260531`
- HUD stage color arrays expanded to six `stageMode` values
- cafe-specific starting items corrected, including cooling gun `351`
- `gameSummaryTP` scoreboard teleport rule added and wired
- cafe additional-material logic restricted to LifeWeaver behavior
- practice temporary-open message changed to `연습용 손님이 입장합니다!`
- cafe practice tutorial placeholder removed
- practice "other code" selector kept as cross-version code advertising
- Jetpack Cat double-jump exception added
- `Host Player: Set Permission` practice `CUSTOMER_LIST` indexes corrected after tutorial removal

## Verification Performed

Text-level checks were run against the current worktree:

- `git diff --stat -- cafe_kr.txt`
- `git diff --numstat -- cafe_kr.txt`
- `rg` checks for:
  - `v260531`
  - starting item arrays
  - practice mode shifted indices
  - five-entry practice `STAGE_CODE[0]`
  - Jetpack Cat exception
  - `gameSummaryTP`
  - `validateServe`
  - `stageFail`

No Overwatch Workshop import/runtime test was run from this environment.
