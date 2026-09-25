# Shared head-chef controls - 2026-09-25

## Scope and source

Edited the current KR/EN/JP `.ow` files directly. Baseline commit: `87e2b8e` (260925 - remove builder). No builder or generation was used. All edited fragments are identical across locales after masking localized string literals; there are no EN-only optimizations.

## Behavior

- `selectMode` remains a global subroutine with no `Event Player`. Each iteration yields 0.016 seconds, then chooses the first team-1 player in the current array who has permission 3 and is holding Ability 2, Reload, or Jump. No eligible input loops without confirming. Selection is performed again for every input transaction, not permanently assigned to one chef.
- Ability 2/Reload change the shared theme/mode. When both are held both changes occur in the same transaction. These change buttons take priority over Jump. A single global action list handles confirmation once. Button release, actor removal, or loss of permission releases the input wait. Concurrent inputs are serialized by current array order; there is no fairness guarantee while one actor holds a change button.
- All permission-3 players see localized theme/mode selection instructions. At the user request, the added Start label and its Jump binding argument were removed from the mode HUD in all locales. Jump confirmation behavior is unchanged.
- Role targets use player variable `selectPlayer` (slot 56). The obsolete global declaration is removed. Each eligible team-1 player updates only their own target every 0.25 seconds, excluding dummy bots and distances over 5.
- Role/practice actions are per-player, gated by permission 3 and a completed initial mode/data setup (`stageTime != False`). The existing duration assignment is the gate: it occurs after `selectMode` and `dataInit`, and no other assignment to stageTime exists.
- Role cycling stays modulo 3, including the existing ability to demote a targeted head chef. It does not grant permission 3. Privilege loss cancels Abort When False waits, including the 3/6-second practice follow-ups.
- Practice creation retains its old no-target/difficulty-4 branch, item source, coordinates, long-hold follow-ups and cutting-station reset. No new distance restriction. The list mutation, createItemData assignment and createItem call contain no Wait, and createItem itself contains no Wait.
- The host's role assignment and fallback policy remain intact. Replaced zero-count Filtered Array checks with equivalent negated Is True For Any checks. The observed non-host C assignment is NOT claimed fixed: it requires an in-game trace of spawn/leave/restore paths.
- Remaining Host Player uses are only bootstrap dummy creation, initial host role assignment, host slot checks, and role assignment after a departure.

## Resource preservation

- After the user reported lingering mode HUDs, replaced the invalid bulk-delete assumption with a bounded global loop deleting scalar IDs 0..4 individually. scbRank is reused only after selection is confirmed; setup later resets it before gameplay.
- Intro world text (indices 3..6) and intro HUD (indices 0..2) also use bounded per-player scalar-delete loops. Their separate destruction times and object types are preserved. progressIndex is safe scratch here: loadProgress and saveProgress start later, and each player has their own index.
- Mode-5 starting money still targets the first six team-1 players, now by Array Slice assignment; removed six repeated waits/loop bookkeeping.
- Removed the redundant global host Rooted action; each spawned player retains their existing Rooted and Clear Status sequence.
- Combined duplicate target-rejection branches and reset the two cutting slots as an array.
- Used existing Workshop boolean index conventions in changed expressions.

## Static element estimate (NOT an in-game measurement)

The user supplied EN baseline is 32662/32768. A local syntax-tree delta model was checked against the counting rules in [OverPy astToWorkshop.ts](https://github.com/Zezombye/overpy/blob/master/src/compiler/astToWorkshop.ts): number literals cost 2, global reads cost 2, player reads add the actor expression, actions discount direct parameters, condition comparisons differ from expression comparisons, arrays add an extra element, and omitted Custom String arguments are accounted for. No OverPy compiler or output generation was run. The model is used only for a before/after estimate, not as an authoritative full-file engine counter.

| Changed rule | Estimated delta, identical in KR/EN/JP |
| --- | ---: |
| Global: Setting | +13 |
| Player: Spawn | -23 |
| Player: Left match | -4 |
| Head Chefs: Select Mode | -15 |
| Head Chefs: Select Permission | +7 |
| Head Chefs: Set Permission | +14 |
| Total | -8 |

Estimated EN: **32654/32768**, 8 below the supplied baseline. Actual game import and engine element count have not been verified. Do not report this estimate as an in-game pass.

## Verification

- 14 Python tests pass, including seven static control regressions.
- Root `.ow` syntax checks pass for all five files.
- `git diff --check` passes.
- Exactly six intended rules changed in each Deluxe file; the other 51 rules remain text-identical to the pre-edit snapshot. Data initialization, stage tables, recipes, tutorial rules, Interact permissions, and locale-specific tutorial/menu differences are unchanged.
- All locale edit fragments match after masking string literals.
- No in-game test has been run. Pending runtime checks: no chef at startup then first grant; two chefs changing/confirming; actor departure or demotion while holding input; same/different role targets; simultaneous item creation; long-hold privilege loss; role restoration; hero-unselected C with overlapping entry/leave events; Local Player text visibility and scalar HUD cleanup loops; imported element count at or below 32662.

## HUD follow-up

The original Array Slice arguments to Destroy HUD Text/Destroy In-World Text were not a valid assumption of bulk deletion. The user observed lingering mode/theme HUDs. All three newly introduced array-delete sites have been replaced in all locales with per-ID loops. The [Destroy HUD Text parameter](https://workshop.codes/wiki/articles/destroy-hud-text) is a single Text ID. No in-game re-test has been performed after this correction; static tests now check the exact visited ID ranges.
