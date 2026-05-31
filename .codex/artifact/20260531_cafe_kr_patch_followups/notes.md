# cafe_kr Patch Follow-up Notes

Date: 2026-05-31

## Context
- The current `cafe_kr.txt` is being used to test a work product produced by another Codex session.
- Follow-up changes mentioned by the user after this point should be treated as issues that the prior work missed.
- Record those follow-up items here so future patch or porting work for `cafe_kr.txt` explicitly checks them.

## Follow-up Items
- `cafe_kr.txt` line 793 HUD text:
  - The visible `Custom String` text was cafe-specific and should remain unchanged.
  - The nested `Custom Color(...)` expression was newly added/changed behavior and still needed to be ported.
  - Old color arrays only covered 5 values:
    - R: `Array(255, 140, 110, 255, 123)[Global.stageMode]`
    - G: `Array(50, 255, 180, 120, 38)[Global.stageMode]`
    - B: `Array(145, 180, 255, 120, 224)[Global.stageMode]`
  - Corrected color arrays cover the updated 6-value `Global.stageMode` mapping:
    - R: `Array(255, 140, 110, 255, 255, 38)[Global.stageMode]`
    - G: `Array(50, 255, 180, 225, 120, 38)[Global.stageMode]`
    - B: `Array(145, 180, 255, 120, 120, 65)[Global.stageMode]`
  - Future cafe patch reviews must inspect expressions inside otherwise cafe-localized strings; do not skip them just because the string content itself is locale/cafe-specific.
- Starting items for cafe modes:
  - This is a cafe-only criterion because it includes the cafe-only cooling gun item (`351`, `냉각총`).
  - It may be reused when porting the same cafe-specific logic to `cafe_en.txt`.
  - Starting items must be assigned by `Global.stageMode` as follows:
    - `0` practice: `Array(12)` = `청소기`
    - `1` casual dining: `Array(12, 351)` = `청소기`, `냉각총`
    - `2` fine dining: `Array(12, 351)` = `청소기`, `냉각총`
    - `3` star bistro: `Array(13, 3, 16)` = `대시 부츠`, `휴대용 칼`, `토치`
    - `4` master cook challenge: `Array(16, 351)` = `토치`, `냉각총`
    - `5` head chef challenge: `Array(14, 7, 16)` = `텔레포트 스펠`, `헤드셰프의 칼`, `토치`
  - Watch both `rule("Host Player: Select Mode")` and the start-item creation block around line 876. The existing structure intentionally splits some special-mode starting items between those locations.
  - Do not implement this as a nested per-mode item table like `Array(Array(...), ...)[Global.stageMode][index]`; that does not apply reliably in Workshop.
  - Keep the existing direct `Global.createItemData = Array(...); Call Subroutine(createItem);` pattern. Prefer changing the item-code indexes inside the existing `selectMode` and start-item blocks over introducing a new nested item-list loop.
  - Current split:
    - `selectMode` gives mode `3` item `16` and mode `5` item `7`.
    - The start block first item uses `Array(12, 12, 12, 13, 16, 14)[Global.stageMode]`.
    - The start block second item uses `Array(Null, 351, 351, 3, 351, 16)[Global.stageMode]`; mode `0` is handled by the practice branch and does not use this `Null`.
- `gameSummaryTP` scoreboard teleport sync:
  - `cafe_kr.txt` already had `26: gameSummaryTP` in the subroutine list, but the actual `rule("Global subroutine: Scoreboard TP")` and `Call Subroutine(gameSummaryTP);` replacements were missing.
  - Applied the same structure recorded for `jp.txt` and present in `ko.txt`:
    - Replace the initial scoreboard player-position teleport block with `Call Subroutine(gameSummaryTP);`.
    - Replace the second scoreboard player-position teleport block before per-player summary text with `Call Subroutine(gameSummaryTP);`.
    - Remove the later redundant teleport block after `Set Invisible(All Players(Team 1), All);`, matching the synced `ko.txt`/`jp.txt` structure.
    - Add `rule("Global subroutine: Scoreboard TP")` containing the six `Teleport(All Players(Team 1)[...])` calls.
  - Verification pattern: `rg -n "gameSummaryTP|Scoreboard TP|Teleport\(All Players\(Team 1\)\[4\]" cafe_kr.txt` should show two `Call Subroutine(gameSummaryTP);` lines and only one direct `Teleport(All Players(Team 1)[4]...)`, inside the `gameSummaryTP` rule.
- Cafe additional-material handling:
  - `ADDITIONAL_MATERIAL_LIST` in cafe files is for Lifeweaver / `요리 연구가` behavior only.
  - Do not port restaurant stage-11 / `정육식당` additional-material logic into cafe files; cafe stage/menu `11` is not the restaurant butchery stage.
  - In `cafe_kr.txt`, remove stage-11 conditions from additional-material paths:
    - The customer-bot-side `createItem` block should be gated only by `Hero Of(Event Player) == Hero(LifeWeaver)`.
    - The reserved-customer central-spawn `ADDITIONAL_MATERIAL_LIST[Global.reservedOrder]` block should be removed.
    - The stage-11 table-count throttling block near reserved-customer spawning should be removed.
    - Despawn slowing for additional-material items should not depend on `Global.stage` or `Global.totalScore == 11`; use `Array Contains(Global.ADDITIONAL_MATERIAL_LIST, Global.itemCode[...])`.
  - Compared with the previous committed `cafe_kr.txt`: the main central-spawn and table-throttle removals return that target area to the previous cafe behavior, but the result is not byte-for-byte identical because current code keeps the newer `Hero(LifeWeaver)` casing/formatting and the despawn condition was intentionally changed from stage-11-gated to cafe-wide additional-material handling.
- Practice-mode temporary opening text:
  - Match `ko.txt` for the practice customer start message.
  - `cafe_kr.txt` around line 1386 should use `Custom String("  연습용 손님이 입장합니다! ")`, not `Custom String("  임시 개장! 이제 실전입니다! ")`.
- Cafe practice tutorial removal:
  - `ko.txt` has tutorial / `hintText` logic, but cafe files do not. Do not keep a tutorial stage placeholder in cafe practice mode.
  - Remove only the first tutorial slot from cafe practice data:
    - In `CUSTOMER_LIST[0]`, remove the first Soldier-only set. Keep the next Soldier set as the normal practice customer set.
    - In `STAGE_CODE[0]`, remove one leading `Array(0)` from `Array(Array(0), Array(0), Array(0), Array(0), Array(0), Array(0))`, leaving five entries.
  - Shift practice special-stage checks accordingly:
    - `all customers`: stage `2`
    - `practice end`: stage `3`
    - `other menu/workshop code`: stage `4`
  - Remove the old tutorial-specific menu lock such as `Global.stage == 0 ? 0 : (...)`.
  - Do not remove the whole first top-level `STAGE_CODE` array; only remove one inner `Array(0)` entry.
  - Also update any direct practice `CUSTOMER_LIST` index writes. In `Host Player: Set Permission`, the old `ko.txt` indices `[2]` and `[1]` become `[1]` and `[0]` after removing cafe's tutorial slot.
- Practice other-code menu string caution:
  - The practice-mode "other menu" selector intentionally advertises other workshop versions, not necessarily the current file's own code.
  - When porting changes to other versions such as `쿡제요리` or `뉴 3호점`, do not automatically rewrite this string just because the target file/code changed.
  - In many cases this block should remain unchanged, or only the entry for the target file's own version should be swapped out so the selector continues to point to different versions.
  - Keep the display list around line 848 and the actual code message around line 1367 in sync if this block is intentionally edited.
- Jetpack Cat jump-button exception:
  - `ko.txt` has a Jetpack Cat exception in `rule("Player: Double Jump")`:
    - `Hero Of(Event Player) != Hero(Jetpack Cat);`
  - This condition prevents the generic double-jump / jump-disallow logic from interfering with Jetpack Cat.
  - Applied to `cafe_kr.txt` on 2026-05-31; cafe files should include the same condition when syncing Jump-button behavior.

## Future Work Guidance
- Before applying or reviewing future `cafe_kr.txt` patches, read this note and confirm that all follow-up items have been considered.
- Do not treat the other Codex output as complete if any item recorded here remains unchecked.
