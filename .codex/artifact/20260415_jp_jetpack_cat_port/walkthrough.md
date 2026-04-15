# `jp.txt` Jetpack Cat Port Session

## Date

- 2026-04-15

## Scope

Port the current `ko.txt` Jetpack Cat gameplay feature set into `jp.txt` while preserving the existing Japanese locale structure and applying a localized customer name suitable for the JP script.

## Translation Choice

- Korean source name: `배달냥이`
- Chosen Japanese translation: `配達にゃんこ`

Reasoning:

- `配達` keeps the delivery meaning direct and natural.
- `にゃんこ` preserves the cute tone of `냥이`.
- It fits the existing playful customer naming style better than stiffer options such as `配達猫`.

## Starting Point

Before this port:

- `jp.txt` had already received some adjacent structural changes from earlier sessions, including the array-compression refactors.
- `jp.txt` did not yet fully match the latest `ko.txt` Jetpack Cat feature set.
- Parts of the hero-change and customer-path area were still on the older 14-slot model.
- The visible Japanese changelog was still on `v260412`.

This made the job a partial structural sync rather than a simple text-only translation pass.

## Changes Made

### 1. Declarations were updated first

- Added new subroutines at the top declaration block:
  - `27: validateServe`
  - `28: changeHero`

This preserved the workspace rule that new declarations must appear before downstream use sites.

### 2. Table and path model was expanded

- Expanded `Global.tableOrderCode` from 14 slots to 19 slots.
- Added the five extra `TABLE_PATH` blocks used by `Jetpack Cat`.
- Added the matching five extra `TABLE_POSITION` entries.

Meaning:

- `jp.txt` now uses the same 19-slot customer/table model as the current `ko.txt` and `en.txt`.

### 3. Japanese release-note text was updated

- Updated the build string to `v260415`.
- Replaced the old in-world JP changelog with the new delivery-cat announcement.

Japanese-facing text now includes:

- New customer: `配達にゃんこ`
- New changes:
  - 6-player `ServingBall` fallback now switches to jetpack mode
  - suspicious drink smash/chop balance adjustment
  - large code optimization pass

### 4. Hero-change logic was extracted into `changeHero`

- Replaced the inline hero-change interaction body with `Call Subroutine(changeHero);`
- Added `rule("Player: Change Hero")`
- The subroutine begins with `Stop Forcing Player To Be Hero(Event Player);`

Meaning:

- `jp.txt` now has the same reusable restoration path required by the forced `Jetpack Cat` flow.

### 5. 6-player serveBot fallback was ported

- Preserved the existing `< 6 players` branch that still creates `Hero(Wrecking Ball)` as `サービングボール`.
- Added the `== 6 players` branch that:
  - announces jetpack equip
  - forces the player into `Hero(Jetpack Cat)`
  - sets move speed to `180`
  - enables the smash HUD
  - restores the player through `changeHero` after the open phase ends

### 6. `Jetpack Cat` was added as a formal customer type

- Added `Hero(Jetpack Cat)` to the customer hero mapping array.
- Shifted the merchant fallback route from `Global.TABLE_PATH[14]` to `Global.TABLE_PATH[19]`.
- Extended the JP customer-name list with `配達にゃんこ`.
- Extended color / score / orderCount / orderTimeOut / byOrder arrays for the new customer type.

Ported values:

- score: `-10`
- order count: `1`
- order timeout: `40`
- by-order: `False`

### 7. Dummy customer movement and success effects were updated

- Added the `tableIndex >= 14` movement branch for `Jetpack Cat`.
- Added the accelerated air-lane movement using boosted `customerSpeed`.
- Added the special success effect branch that renders the sphere around the moving `Jetpack Cat` instead of only at the table position.

Meaning:

- The new JP tables are treated as a delivery lane rather than just extra static seats.

### 8. `validateServe` was extracted and the extra serve zone was ported

- Added `rule("Global subroutine: validate serve")`
- Replaced duplicated inline serve-validation logic with `Call Subroutine(validateServe);`
- Added the extra delivery-zone pre-check around `Vector(196.440, -3, 205.170)` that only triggers on exact item matches

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

- Added `Hero(Jetpack Cat)` to the Japanese `Global.CUSTOMER_LIST` stage-mode waves in the same places used by the current `ko.txt`.

Meaning:

- The feature is now active in encounter generation for `jp.txt`, not merely translated in UI text.

### 11. Path offset references were shifted

- Updated `Player: Ability 1` teleport route:
  - `svbTableIndex + 15` -> `svbTableIndex + 20`
- Updated `Player routine: serveBot` helper route:
  - `svbTableIndex + 15` -> `svbTableIndex + 20`

### 12. Mobility guard was added

- Updated `Player: Double Jump` to exclude `Hero(Jetpack Cat)`

Meaning:

- Prevents the forced-hero fallback flow from colliding with the existing jump system.

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
- Confirmed old `v260412` visible changelog text was replaced with `v260415`.
- Confirmed no remaining `svbTableIndex + 15` or `TABLE_PATH[14]` helper-route references remain in `jp.txt`.

## Remaining Risk

- No in-game Workshop runtime validation has been run yet.
- The forced `Jetpack Cat` phase and delivery-lane movement should be tested live in the Workshop runtime.
- The Japanese localization text fits the current tone, but should still be reviewed in-game for line length and visual fit.
