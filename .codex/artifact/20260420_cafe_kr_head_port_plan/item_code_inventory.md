# cafe_kr item-code inventory

Pre-port inventory for cafe-sensitive code sites touched or deferred during the `ko.txt` `HEAD` structural port.

## Core arrays

- `Global.UPGRADE_CODE = Array(Array(6, -1, -2), Array(0, 1, 2), Array(3, 4, 5, 6), Array(7, 8, 9))`
- `Global.KNIFE = Array(1, 6, 2, 3, 4, 5, 7)`
- `Global.PERK_LIST = Array(Array(8, 9, 11, 12, 15, 16, 17, 351), Array(10, 13, 14))`

## Practice / setup item spawns

- Practice starter item: `12`
- Non-practice starter item pool: `Array(12, 12, 12, 16, 4)` in the legacy 4-mode scaffold
- Secondary starter item: `351`

## Ordered knives

- Standard ordered knives: `Random Integer(2, 5)`
- Premium ordered knife: `7`

## Tip / currency item

- Cash item spawned by upgrade purchase slot 9 and used by serve validation: `18`

## Random perk pools

- Random tool perk purchase pool:
  `Array(8, 8, 8, 8, 9, 11, 11, 11, 11, 12, 12, 15, 16, 16, 17, 17, 351, 351)`
- Random foot perk purchase pool:
  `Array(10, 10, 10, 10, 10, 13, 13, 13, 14)`

## Touched structural sites

- `Dummy: Spawn`
  Ordered knife delivery kept on cafe ids above.
- `Global: Setting`
  Starter items must continue to use cafe ids, not restaurant ids.
- `Global subroutine: validate serve`
  Wrong-serve currency item remains `18`.
- `Player: Ability 1` / `Player routine: serveBot`
  Serve-bot path offsets changed structurally, item ids unchanged.

## Deferred remap review

- 6-mode starter item design for new mode slots is not finalized.
- `Global.STAGE_CODE` for the new cafe-specific modes is still placeholder scaffolding.
- Any future direct copy from `ko.txt` involving `createItemData` should be checked against this file before landing.
