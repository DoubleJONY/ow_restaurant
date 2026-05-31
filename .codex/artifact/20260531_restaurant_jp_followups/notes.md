# Restaurant JP Follow-up Notes

Date: 2026-05-31

## Context
- This note records follow-up work performed while comparing and aligning `jp.txt` with `ko.txt` and `en.txt`.
- Treat this as local workspace memory for future Restaurant locale sync work.

## Git History Checks
- Checked `jp.txt` line 3428/3430 around:
  `Create Dummy Bot(First Of(Global.upgradeList[False]), Team 2, 17, Vector(196.268, True, 194.391), Null);`
- `git blame` showed the committed pre-edit line came from `95915e1` (`250322`, 2025-03-22) as `First Of(Global.upgradeList)`.
- Exact `First Of(Global.upgradeList[False])` history did not exist in committed `jp.txt`.
- Repository-wide search found related commit `b5922e2` (`260426`, 2026-04-26):
  - `en.txt` and `ko.txt` changed this dummy bot line to `Global.upgradeList[False]`.
  - `jp.txt` received nearby `Global.upgradeList[False]` initialization logic but did not change the dummy bot line at that time.
- Conclusion: for `jp.txt`, `[False]` was not previously committed and removed; it had been missed in JP while EN/KO had it.

## Applied JP Text Updates
- Updated `jp.txt` patch-note bug-fix text to Japanese:
  - `バグ修正`
  - `カジュアルダイニングで別の冷蔵庫が表示される問題を修正`
  - `カジュアルダイニングモードで商人が来ない不具合を修正`
- The current `jp.txt` line keeps the two bug-fix entries separated with `\r\n` before `{1}`.

## JP/KO Structural Diff Notes
- Compared `jp.txt` and `ko.txt` while ignoring ordinary translation differences and the Naruto-maki related item/name differences.
- Notable non-translation differences found:
  - `ko.txt` had `26: gameSummaryTP`, `Call Subroutine(gameSummaryTP)`, and `rule("Global subroutine: Scoreboard TP")`; `jp.txt` did not.
  - `ko.txt` had extra `Mauga/Roadhog/Reinhardt` unlock logic in the difficulty-4 upgrade path.
  - `ko.txt` had `Mauga`-dependent dummy bot naming and serve-fail message branches.
  - `ko.txt` had `Global.stage == 7` hint/loading-menu block that `jp.txt` lacked.
  - `Global.STAGE_CODE` differed in casual-dining entries: JP used `Array(6)` where KO used `Array(4)` in several positions.
  - Scoreboard text positions differed slightly between JP and KO.

## Applied gameSummaryTP Sync
- Added `26: gameSummaryTP` to the `jp.txt` subroutine list.
- Replaced both duplicated scoreboard teleport blocks in `jp.txt` with:
  `Call Subroutine(gameSummaryTP);`
- Added `rule("Global subroutine: Scoreboard TP")` to `jp.txt`.
- The new JP `gameSummaryTP` rule contains the six scoreboard `Teleport(All Players(Team 1)[...])` actions copied from KO's structure.
- Verification command result:
  - `rg -n "gameSummaryTP|Teleport\(All Players\(Team 1\)\[4\]" jp.txt`
  - Only one direct `Teleport(All Players(Team 1)[4]...)` remains in `jp.txt`, inside the new `gameSummaryTP` rule.

## Future Follow-ups
- Decide whether to port the remaining KO-only structural differences into JP:
  - `Mauga/Roadhog/Reinhardt` unlock path.
  - `Mauga`-dependent naming/failure-message branches.
  - `Global.stage == 7` hint/loading-menu block.
  - `Global.STAGE_CODE` `Array(6)` vs `Array(4)` casual-dining difference.
  - Scoreboard text-position adjustments.
- Before finalizing release edits, check workspace version policy in `.codex/workspace.md`; project files edited on 2026-05-31 should use `v260531` where relevant.
