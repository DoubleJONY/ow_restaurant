# gc_kr.txt Targeted Diff Map

Date: 2026-05-31

## Source Priority

- Use `cafe_kr.txt` for the latest shared-system fixes already validated in the cafe patch.
- Preserve `gc_kr.txt` recipe, menu, fridge, hazard, weaver, additional-material, item-name, and item-processing arrays.
- Remap touched utility item IDs by role because `gc_kr.txt` uses cafe-like early utility indexes.

## Applied Shared-System Areas

- 6-mode setup, mode HUD, mode selection, stage time, storage level, difficulty mapping.
- 19-table path/position model for Jetpack Cat/Freja table routing.
- `gameSummaryTP` subroutine and scoreboard teleport flow.
- `stageFail` subroutine and shared stage-fail handling.
- `validateServe` flow and updated direct-serve logic.
- Jetpack Cat exception in double-jump logic.
- Jetpack Cat/Reinhardt/Junker Queen customer support in customer/dummy/failure paths.
- Practice-mode customer injection through `Host Player: Set Permission`.
- Nested `upgradeList` pools for merchant/practice item cycling.

## Preserved Or Excluded

- Tutorial and `hintText` logic: not added.
- Cafe-only ice/cooling-gun mechanics: not added.
- Cafe-only item `351` as a tool/perk: not added. Remaining `351` occurrences are Cook International food IDs in data arrays.
- Cafe title strings: changed back to `레스토랑 - 쿡제요리`.
- Cafe upgrade labels `제빙기`/`오븐`: changed back to `튀김기`/`그릴`.

## Utility ID Remaps Used

- Cleaner/free starter item: `12`
- Torch: `16`
- Serving ball: `17`
- Dash boots: `13`
- Teleport spell: `14`
- Cooking copy spell: `15`
- Portable knife stage-mode bonus: `3`
- Head chef knife stage-mode bonus: `7`
- Money/tips item: `18`
