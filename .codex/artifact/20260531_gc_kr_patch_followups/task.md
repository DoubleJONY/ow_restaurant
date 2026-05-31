# gc_kr.txt Patch Task

Date: 2026-05-31

Target: `gc_kr.txt`

## Status

- [x] Read current `gc_kr.txt` structure.
- [x] Compare high-level shape against `cafe_kr.txt` and `ko.txt`.
- [x] Identify that `gc_kr.txt` is currently a 4-mode `P6ZAA v260212` build.
- [x] Identify that `gc_kr.txt` has no tutorial / `hintText` path and should stay that way.
- [x] Identify that `gc_kr:dataInit2` must be protected as Cook International data.
- [x] Create this artifact folder.
- [x] Create implementation plan.
- [x] Build a targeted diff map from shared system logic to `gc_kr.txt`.
- [x] Build item-index/remap inventory for touched `createItemData` and perk paths.
- [x] Patch `gc_kr.txt`.
- [x] Update visible version strings to `v260531`.
- [x] Apply or reject each `cafe_kr` follow-up fix with a recorded reason.
- [x] Run static `rg`/`git diff` verification.
- [x] Write final change summary.

## Working Assumptions

- `ko.txt` is the best source for shared system behavior.
- `cafe_kr.txt` is the best source for recently discovered follow-up bug fixes.
- `gc_kr.txt` keeps its own recipe/menu/fridge/weaver/hazard/additional-material arrays.
- `gc_kr.txt` should not receive tutorial or `hintText` logic.
- Starting items and perk indexes must be remapped by role, not copied by raw item ID.

## Completed Notes

- Shared behavior was ported from the validated cafe patch where it did not depend on cafe-only item systems.
- Cook International data arrays were preserved.
- Utility item literals were remapped by role instead of copied from cafe or `ko.txt`.
- Final verification notes are in `change_summary.md`.

## Known Risks

- Food/material IDs in `gc_kr.txt` are not interchangeable with `ko.txt`.
- `gc_kr.txt` has early utility-item indexes similar to cafe, so copied restaurant literals can silently break gameplay.
- Practice mode indexes differ from tutorial-enabled `ko.txt`.
- Additional-material behavior may be version-specific and must be reviewed before simplification.
- The current file has no `Jetpack Cat` behavior, so adding the double-jump exception only makes sense as part of the full customer/perk port.
