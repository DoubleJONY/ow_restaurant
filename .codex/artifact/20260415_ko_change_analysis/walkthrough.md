# `ko.txt` Change Analysis Session

## Date

- 2026-04-15

## Scope

Analyze the current uncommitted `ko.txt` changes against the last committed version:

- Base commit: `338c732`
- Commit label in file history: `260414`

The goal of this note is to explain the surrounding logic and gameplay meaning of the current modifications, not just list the diff.

## Summary

This change set is not a small text update. It introduces a new `Jetpack Cat` customer flow, expands the table/path model from 14 to 19 slots, and adds a 6-player fallback where the old `serveBot` item no longer spawns a dummy bot and instead temporarily transforms a player into `Jetpack Cat`.

At the same time, duplicated logic was extracted into two new subroutines:

- `validateServe`
- `changeHero`

## Main Findings

### 1. Table model expansion

Before this change:

- `Global.tableOrderCode` had 14 slots.
- `Global.TABLE_POSITION` had 14 entries.
- Normal customers used tables `0..11`.
- `Freja` used tables `12..13`.

After this change:

- `Global.tableOrderCode` has 19 slots.
- `Global.TABLE_POSITION` has 19 entries.
- Five new table positions were added at indexes `14..18`.

Meaning:

- The Workshop layout now has a dedicated extra customer range beyond the old `Freja` section.
- This new range is used by `Jetpack Cat`.

### 2. Path index shifts across the file

Before this change:

- The shop NPC fallback path used `Global.TABLE_PATH[14]`.
- `serveBot` helper routes used `Global.TABLE_PATH[tableIndex + 15]`.

After this change:

- The shop NPC fallback path moved to `Global.TABLE_PATH[19]`.
- `serveBot` helper routes moved to `Global.TABLE_PATH[tableIndex + 20]`.

Meaning:

- The inserted `Jetpack Cat` path blocks sit between the old customer paths and the helper/return paths.
- Existing path logic had to be shifted to keep index-based lookups valid.

### 3. Hero-change logic was centralized for reuse

Before this change:

- The hero-change interaction directly executed temporary allowed-hero restriction, respawn wait, teleport, facing reset, and move-speed reset.

After this change:

- The same logic was moved into `changeHero`.
- The new subroutine starts with `Stop Forcing Player To Be Hero(Event Player);`.

Meaning:

- This is partly cleanup, but it also enables safe recovery after temporary forced-hero states.
- The new 6-player `Jetpack Cat` transformation depends on this shared restore path.

### 4. `itemPerk == 7` now has a full 6-player fallback

Before this change:

- When `Event Player.itemPerk == 7` and team size was below 6, the code spawned a `Wrecking Ball` dummy bot as `serveBot`.
- There was no separate `== 6` branch.

After this change:

- `< 6 players`: behavior stays the same, still spawns the `Wrecking Ball` `serveBot`.
- `== 6 players`: the user is forced into `Hero(Jetpack Cat)` instead.

New 6-player branch behavior:

- Forces the player to `Jetpack Cat`.
- Sets move speed to `180`.
- Marks `Event Player.isController = True`.
- Gives the melee-based material-smash HUD immediately.
- Waits through the active shop session.
- Restores the player through `changeHero` when the shop closes.

Meaning:

- The old design needed a free player slot for the dummy `serveBot`.
- At 6 players, that slot is unavailable, so the player becomes the substitute.

### 5. `Jetpack Cat` is now a formal customer type

Before this change:

- Customer index mapping ended at `Hero(Ramattra)`.
- Name/color/score/order/time arrays ended at 18 customer types.

After this change:

- `Hero(Jetpack Cat)` was appended to the customer type mapping.
- A new localized customer name was added: `배달냥이`.
- New customer metadata was added: score `-10`, order count `1`, order timeout `40`, by-order flag `False`.

Meaning:

- This is not just a cosmetic hero swap.
- `Jetpack Cat` is integrated into the full customer pipeline with its own behavior profile.

### 6. `Jetpack Cat` uses dedicated spawn/table selection rules

Before this change:

- Table selection only distinguished normal customers `0..11` and `Freja` `12..13`.
- Reservation handling applied to `Mercy` and `Sombra`.

After this change:

- `Jetpack Cat` prefers table range `14..18`.
- It spawns from `Vector(125.630, 4, 219.530)`.
- It is also treated as a reserved-order customer, like `Mercy` and `Sombra`.
- It additionally increments `Global.loadNext` by `1`.

Meaning:

- `Jetpack Cat` is designed to inject extra pressure into the call flow.
- The many-incoming-orders release note is backed by actual queue acceleration logic.

### 7. `Jetpack Cat` movement is a custom delivery path, not a normal seat walk

Before this change:

- Only the old special-case logic existed for `Freja`-related table handling at `tableIndex >= 12`.

After this change:

- `tableIndex >= 14` gets a new movement branch.
- Early route steps raise speed to `18.66` and hold `Secondary Fire`.
- Later route steps fall back to `5.500` and release `Secondary Fire`.
- On exit, the customer accelerates again near the final route segment.

Meaning:

- The new five tables are effectively a delivery lane for a moving customer archetype.
- This is not just more seats; it is a different arrival/departure pattern.

### 8. Serve validation was extracted and also extended

Before this change:

- All serve validation lived inline inside `itemPhysics`.
- Only the existing restaurant serve area performed the full serve-check sequence.

After this change:

- The old inline block was moved into `validateServe`.
- A new pre-check region was added around `Vector(196.440, -3, 205.170)` with radius `23`.
- This new pre-check finds nearby customers within `2.8`, only accepts exact order matches, and immediately calls `validateServe`.

Meaning:

- This is more than refactoring.
- There is now a second delivery-validation zone that appears to support the new `Jetpack Cat` route.

Important detail:

- The new zone only auto-validates exact matches.
- Cash reset item `432` and normal wrong-delivery handling still depend on the legacy serve path logic.

### 9. `validateServe` preserves old scoring and failure semantics

The extracted subroutine still performs the same core effects as before:

- correct dish: sets customer status to `1` or `4`, applies score/cook credit, applies by-order penalty when needed, and destroys the served item
- item code `432`: sets customer status to `5`
- wrong dish: sets customer status to `2`, subtracts score, and increments miss count

Meaning:

- The refactor does not appear to intentionally rebalance the core serve result model.
- It mainly reduces duplication and enables the new extra delivery zone.

### 10. Customer waves were updated to actually include `Jetpack Cat`

`Global.CUSTOMER_LIST` was modified so that `Jetpack Cat` is now part of multiple stage-mode wave arrays.

Meaning:

- The feature is fully connected to encounter generation.
- This is not a dormant or debug-only customer type.

### 11. Mobility compatibility was tightened

`Player: Double Jump` now excludes `Hero Of(Event Player) != Hero(Jetpack Cat)`.

Meaning:

- Forced `Jetpack Cat` control would otherwise stack with existing jump/mobility systems.
- This is likely a conflict-prevention fix for the new 6-player transformation path.

## Risks / Open Questions

### 1. Reverse path logic for new tables is unusual

When the shop closes during entry, reverse movement now uses `Event Player.controlingIndex -= Event Player.tableIndex >= 14 ? 10 : 1;`.

This is much more aggressive than the legacy decrement-by-1 behavior and should be runtime-tested in Workshop because index skipping in these path arrays is fragile.

### 2. Release note mentions a suspicious-drink cut-balance change, but the visible diff does not show it

The new in-world changelog text says the suspicious drink cut buff was rebalanced. However, within the current `ko.txt` diff, the obvious related logic still appears unchanged.

Possible explanations:

- the balancing change happened elsewhere before this local diff
- the release note was updated ahead of the actual code change
- the adjustment is subtle and not in the currently reviewed branch of logic

## Bottom Line

The current `ko.txt` changes primarily implement a new `Jetpack Cat` customer and a full-team fallback for the `serveBot` item. The supporting code changes are mostly structural: expanded table/path arrays, shifted helper path offsets, extracted reusable subroutines, and added a second serve-validation zone.
