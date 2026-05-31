# gc_kr.txt Item And Perk Remap Inventory

Date: 2026-05-31

Purpose: prevent raw `ko.txt` item IDs from being copied into `gc_kr.txt`.

## Utility Item IDs In gc_kr

These match the early utility-index model, not the current restaurant `ko.txt` item IDs.

- `1`: mass-produced knife
- `2`: carbon steel knife
- `3`: portable knife
- `4`: sharp knife
- `5`: Genji dagger
- `6`: premium kitchen knife
- `7`: head chef knife
- `8`: energy drink
- `9`: suspicious drink
- `10`: jump boots
- `11`: seasoning pack
- `12`: cleaner
- `13`: dash boots
- `14`: teleport spell
- `15`: cooking copy spell
- `16`: torch
- `17`: serving ball
- `18`: `$100`

## Core Arrays To Preserve

- `Global.UPGRADE_CODE = Array(Array(6, -1, -2), Array(0, 1, 2), Array(3, 4, 5, 6), Array(7, 8, 9))`
- `Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7)`
- `Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17), Array(10, 13, 14))`

Do not copy `ko.txt` values such as `352`, `357`, `361`, `433`, or `434`.

## ko.txt Role Mapping

Use this only when porting role-based new logic from `ko.txt`.

- `ko 357` cleaner -> `gc 12`
- `ko 434` serving ball -> `gc 17`
- `ko 361` torch -> `gc 16`
- `ko 358` dash boots -> `gc 13`
- `ko 360` cooking copy spell -> `gc 15`
- `ko 359` teleport spell -> `gc 14`
- `ko 63` portable knife -> `gc 3`
- `ko 354` head chef knife -> `gc 7`
- `ko 432` tip / money item -> `gc 18`

## Starting Item Plan

Use role-equivalent values, not raw `ko.txt` numbers.

- Practice `0`: cleaner only
- Casual dining `1`: cleaner + serving ball
- Fine dining `2`: cleaner + torch
- Star bistro `3`: torch + dash boots + portable knife
- Mastercook challenge `4`: cooking copy spell + dash boots
- Head chef challenge `5`: torch + teleport spell + head chef knife

Planned arrays:

- first starting item:
  - `Array(12, 12, 12, 16, 15, 16)[Global.stageMode]`
- second starting item:
  - `Array(Null, 17, 16, 13, 13, 14)[Global.stageMode]`
- select-mode extra grants:
  - `stageMode == 3`: item `3`
  - `stageMode == 5`: item `7`

## Perk Index Meaning In gc_kr

`Global.PERK_LIST[0]` has seven entries.

- `itemPerk == 0`: energy drink
- `itemPerk == 1`: suspicious drink
- `itemPerk == 2`: seasoning pack
- `itemPerk == 3`: cleaner
- `itemPerk == 4`: cooking copy spell
- `itemPerk == 5`: torch
- `itemPerk == 6`: serving ball

There is no cafe cooling-gun perk in `gc_kr`; do not port `itemPerk == 7` / ice-machine logic.

## Follow-Up Checkpoints

- Practice random item creation should use `Random Integer(1, 17)` or an equivalent `gc_kr` utility range.
- Tip drop should keep item `18`.
- Head chef knife should keep item `7`.
- Ordered special knives should keep random `2..5`, legendary `7`.
- Upgrade-shop random tool/shoe pools must use `Global.PERK_LIST`, not hard-coded restaurant IDs.
