# `jp.txt` Follow-Up Patch Port Session

## Date

- 2026-04-15

## Scope

Apply the latest post-`Jetpack Cat` gameplay patch from `ko.txt` into `jp.txt`, but validate against `en.txt` first because `en.txt` already contained some corrective follow-up edits.

The user explicitly called out `dataInit3` as an area that might diverge, so that part was treated as a verification point rather than a blind port.

## Starting Point

Before this session:

- `jp.txt` already had the earlier `Jetpack Cat` port.
- `jp.txt` did not yet fully contain the later 6-mode / new-customer / `stageFail` follow-up patch that had been added to `ko.txt`.
- `en.txt` had already received an extra corrective change in the `Hero(Junker Queen)` failure branch, narrowing the effect to nearby real Team 2 customers rather than raw Team 2 slots.
- Parts of the first `jp.txt` follow-up merge were structurally awkward enough that `Dummy: Spawn`, `Start stage`, and `Item physics` needed a careful re-check against `ko.txt`.

## Port Strategy

This session did not treat one locale as the sole source of truth. The chosen sources were:

- `ko.txt` for the main gameplay patch and expanded tables.
- `en.txt` for known corrective follow-up behavior that was safer than the broader original implementation.
- existing `jp.txt` for established Japanese-facing strings and localized wording.

In practice:

- `dataInit3`, `CUSTOMER_LIST`, `STAGE_CODE`, mode metadata, and score-cap behavior followed `ko.txt`.
- the `Hero(Junker Queen)` radius-limited failure logic followed the corrected `en.txt`.
- Japanese text resources were preserved or translated in-place instead of replaced with English wording.

## Changes Made

### 1. Latest follow-up patch was brought into `jp.txt`

Ported the same later feature set that had already been reviewed in `ko.txt` and `en.txt`:

- 6 stage-mode structure
- `stageFail` subroutine flow
- new customers:
  - `大食い巨人`
  - `クレーマー客`
- new modes:
  - `スター・ビストロ`
  - `シェフ・デュ・ロワ`

This included mode labels, mode-selection HUD, scoreboard labels, release-note text, and gameplay-dependent stage settings.

### 2. `dataInit3` was explicitly verified before porting

`dataInit3` was one of the main risk areas called out by the user, so it was checked against both `ko.txt` and `en.txt`.

Ported / verified values:

- `Global.customerCallTime`
- `Global.setUpTime`
- `Global.scoreDecrease`
- `Global.despawnTime`
- `Global.additionalScore = Global.stageMode == 5 ? 15 : Array(Null, 5, 10, 15)[Global.difficulty];`
- `Global.failEnd = Array(99, 5, 3, 2, 3, 1)[Global.stageMode];`
- expanded 6-group `Global.CUSTOMER_LIST`
- expanded 6-group `Global.STAGE_CODE`

Also corrected a casing typo introduced during the port:

- `Hero(Lifeweaver)` -> `Hero(LifeWeaver)`

## 3. `Hero(Junker Queen)` failure handling followed the safer `en.txt` fix

The broad original `ko.txt` version targeted Team 2 by slot iteration and distance checks. `en.txt` had already been tightened after review.

Final `jp.txt` behavior:

- `serveFail` now uses:
  - `Filtered Array(All Players(Team 2), ...)`
  - `Has Spawned(Current Array Element)`
  - `Current Array Element != Event Player`
  - `Current Array Element.controlingIndex != -1`
  - `Distance Between(Position Of(Current Array Element), Position Of(Event Player)) < 5`
- only that filtered set receives `.customerStatus = 6`

Meaning:

- only nearby real customers are affected
- merchants and irrelevant Team 2 slots are excluded

## 4. `ko.txt` remained authoritative where `en.txt` lagged

Some gameplay details in the current `en.txt` still differed from the newer `ko.txt`. In those spots the JP port followed `ko.txt`.

Most important example:

- both serve-success score cap sites now use:
  - `Modify Player Variable(Event Player, score, Max, Global.stageMode == 5 ? 5 : 10);`

This was preserved in:

- the `Reinhardt/Zarya` multi-serve completion path
- the normal final serve-success path

## 5. Structural cleanup was applied after the initial JP follow-up merge

After the first pass, some touched blocks were functionally intended but hard to trust because of malformed indentation and weak visual structure.

Cleaned / verified areas:

- `Dummy: Spawn`
- `Global subroutine: Start stage`
- `Global subroutine: Item physics`

Important note:

- the `Item physics` block around the `Else` branch after the serve-zone check was not changed semantically
- it was only normalized so the `serve -> pot -> storage` fallback structure is readable and consistent with `ko.txt`

## 6. Japanese resource cleanups were preserved

While keeping existing JP locale text, a few follow-up fixes were recorded as part of the patch:

- `プライヤー強化` -> `フライヤー強化`
- kept Japanese mode / customer text aligned with the new feature set
- preserved JP scoreboard / stage text rather than replacing it with English structure

## Validation

Static verification performed:

- confirmed `jp.txt` contains:
  - `% 6` mode rotation
  - `Global.difficulty = Array(4, 0, 1, 2, 1, 2)[Global.stageMode]`
  - `Global.storageLevel = Array(7, 3, 3, 0, -1, -1)[Global.stageMode]`
  - `Global.stageTime = Array(999, 300, 300, 240, 180, 600)[Global.stageMode]`
  - `Global.failEnd = Array(99, 5, 3, 2, 3, 1)[Global.stageMode]`
  - `All Players(Team 1).score += Global.stageMode < 4 ? True : False`
- confirmed `Hero(Junker Queen)` uses the nearby radius-5 filtered Team 2 branch in `serveFail`
- confirmed the two score-cap paths use `Global.stageMode == 5 ? 5 : 10`
- confirmed stale typos `Lifeweaver` and `プライヤー` were removed
- confirmed the `Dummy: Spawn` and `Start stage` `If / Else If / Else / End` token counts match `ko.txt`

One notable branch text split remains intentionally present:

- `営業完了!`
- `成功した営業!`

This reflects the branch structure currently carried in the JP follow-up patch, not an accidental duplication.

## Remaining Risk

- No in-game Workshop runtime validation has been run yet.
- The structural cleanup made the touched branches consistent with `ko.txt`, but they should still be exercised in Workshop runtime.
- The `Hero(Junker Queen)` narrowed radius-5 behavior is safer than the older slot-based version, but should still be tested with crowded Team 2 customer waves.
