# `en.txt` Jetpack Cat Port Session

## Date

- 2026-04-15

## Scope

Port the current `ko.txt` Jetpack Cat gameplay feature set into `en.txt` while preserving the existing English locale structure and avoiding duplicate application of changes already present in `en.txt`.

## Starting Point

Before this port:

- `en.txt` already contained the array-compression related `Wait(0.100, Ignore Condition);` additions.
- `en.txt` already used the `Super Drink` durability scaling change of `* 10` and `/ 10`.
- `en.txt` did **not** yet contain the `Jetpack Cat` customer flow and related structural changes from the latest `ko.txt`.

This meant the job was not a full-file sync. It was a targeted gameplay/structure port.

## Changes Made

### 1. Declarations were updated first

- Added new subroutines at the top declaration block:
  - `27: validateServe`
  - `28: changeHero`

This matched the established workspace rule that subroutine and variable declarations must be introduced at the top before their use sites are edited.

### 2. Table and path model was expanded

- Expanded `Global.tableOrderCode` from 14 slots to 19 slots.
- Added the five extra `TABLE_PATH` blocks used by `Jetpack Cat`.
- Added the matching five extra table-position helper entries and five extra `TABLE_POSITION` entries.

Meaning:

- `en.txt` now uses the same 19-slot customer/table model as the current `ko.txt`.

### 3. Release-note and version text was updated in English

- Updated the build string to `v260415`.
- Replaced the old English in-world changelog with the new `Delivery Cat` / jetpack update announcement.

English text used:

- New customer: `Delivery Cat`
- New changes:
  - 6-player ServingBall fallback now switches to jetpack mode
  - suspicious drink chopping buff rebalance
  - code optimization

### 4. Hero-change logic was extracted into `changeHero`

- Replaced the inline hero-change interaction logic with `Call Subroutine(changeHero);`
- Added `rule("Player: Change Hero")`
- The new subroutine begins with `Stop Forcing Player To Be Hero(Event Player);`

Meaning:

- `en.txt` now shares the same reusable restoration path as `ko.txt`, which is required by the forced `Jetpack Cat` flow.

### 5. 6-player serveBot fallback was ported

- Preserved the existing `< 6 players` branch that still creates `Hero(Wrecking Ball)` as `ServingBall`.
- Added the `== 6 players` branch that:
  - announces jetpack equip
  - forces the player into `Hero(Jetpack Cat)`
  - sets move speed to `180`
  - enables controller smash HUD
  - waits through the shop phase
  - restores the player through `changeHero`

Meaning:

- Full teams no longer depend on an open dummy-bot slot for this perk flow.

### 6. `Jetpack Cat` was added as a formal customer type

- Added `Hero(Jetpack Cat)` to the customer hero mapping array.
- Shifted the merchant fallback route from `Global.TABLE_PATH[14]` to `Global.TABLE_PATH[19]`.
- Extended the localized customer-name list with `Delivery Cat`.
- Extended color / score / orderCount / orderTimeOut / byOrder arrays for the new customer type.

Values ported from `ko.txt`:

- score: `-10`
- order count: `1`
- order timeout: `40`
- by-order: `False`

### 7. Dummy customer movement and success effects were updated

- Added the `tableIndex >= 14` movement branch for `Jetpack Cat`.
- Added the aggressive path-reverse decrement:
  - `Event Player.controlingIndex -= Event Player.tableIndex >= 14 ? 10 : 1;`
- Added the special success effect branch that renders the sphere around the moving `Jetpack Cat` instead of only at the table position.
- Added the accelerated exit segment for customers in the new delivery lane.

Meaning:

- The new tables are treated as a delivery route, not just extra static seating.

### 8. `validateServe` was extracted and the extra serve zone was ported

- Added `rule("Global subroutine: validate serve")`
- Replaced duplicated inline serve-validation logic with `Call Subroutine(validateServe);`
- Added the extra pre-check zone around `Vector(196.440, -3, 205.170)` that only triggers on exact item matches

Meaning:

- `en.txt` now uses the same shared serve-validation logic and extra delivery validation region as `ko.txt`.

### 9. Customer spawning and queue logic was expanded

- Updated `callCustomer` table-range selection to support:
  - normal customers: `0..11`
  - `Freja`: `12..13`
  - `Jetpack Cat`: `14..18`
- Added the dedicated `Jetpack Cat` spawn position:
  - `Vector(125.630, 4, 219.530)`
- Treated `Jetpack Cat` like `Mercy` and `Sombra` for reserved-order handling.
- Added the additional queue-pressure behavior:
  - `Global.loadNext += 1`

### 10. Wave composition was updated

- Added `Hero(Jetpack Cat)` to the English `Global.CUSTOMER_LIST` stage-mode waves in the same places used by the current `ko.txt`.

Meaning:

- The feature is not dormant in `en.txt`; it is now wired into actual encounter generation.

### 11. Path offset references were shifted

- Updated `Player: Ability 1` teleport route:
  - `svbTableIndex + 15` -> `svbTableIndex + 20`
- Updated `Player routine: serveBot` helper route:
  - `svbTableIndex + 15` -> `svbTableIndex + 20`

These shifts were required because the five new `Jetpack Cat` path blocks sit between the old table routes and the helper routes.

### 12. Mobility guard was added

- Updated `Player: Double Jump` to exclude `Hero(Jetpack Cat)`

Meaning:

- Prevents the forced-hero fallback flow from interacting badly with existing jump systems.

## Validation

Static verification performed:

- Confirmed `subroutines` now contains `validateServe` and `changeHero`.
- Confirmed `Global.tableOrderCode` uses 19 slots.
- Confirmed `changeHero` call and rule both exist.
- Confirmed `validateServe` call sites and rule both exist.
- Confirmed `Hero(Jetpack Cat)` is present in:
  - customer mapping
  - customer display name list
  - customer wave arrays
  - call-customer table-range logic
- Confirmed `Player: Ability 1` and `serveBot` both use `+20` path offsets.
- Confirmed `Player: Double Jump` excludes `Hero(Jetpack Cat)`.
- Confirmed no remaining `svbTableIndex + 15` references remain in `en.txt`.

## Remaining Risk

- No in-game Workshop runtime validation has been run yet.
- The reverse-path decrement for the new delivery lane remains structurally fragile and should be tested live.
- English-facing text was translated during the port and should be reviewed in-game for fit and tone.
