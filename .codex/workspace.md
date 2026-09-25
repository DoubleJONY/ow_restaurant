# Workspace Settings for Codex

If you are reading this file, it is user-authored workspace-wide agent behavior
settings. Find and comply with any items or references described here.

## Additional Context
- **Tutorial checks are a completion requirement, not optional:** after stage-order or tutorial changes, verify each affected locale against its current stage tables. Record the displayed stage number, zero-based index, actual theme, tutorial order, hint alignment, and recipe/ingredient reachability. Check tutorial enabled/disabled and applicable practice paths. Confirm the initial tutorial cycle refills from the full normal menu, including intentionally omitted tutorial dishes. A syntax check alone is insufficient.
- EN regression case (2026-09-19): Classic Casual Dining stage 8 (`Global.stage == 7`) uses Burger theme 1; stage 10 (`Global.stage == 9`) uses Dumpling theme 4. Reversed tutorial conditions caused uncraftable orders. The current EN `.ow` applies the burger tutorial at index 7 and the dumpling tutorial at index 9, preserving the normal menu refill. Always recheck current locale tables instead of inferring EN ordering from KR/JP.
- **Mandatory locale-specific tutorial validation:** KR/EN/JP may intentionally use different menu/theme orders for the same mode and stage. Never assume a translated tutorial or matching stage index implies matching gameplay. Preserve these differences when copying runtime code, tutorials, or generator logic across locales.
- Before completing any change to tutorials, stage/menu order, recipes, or ingredient supply, inspect each affected locale's actual `.ow` independently. Trace `stageMode` and `Global.STAGE_CODE[Global.stage]` through `MENU_LIST`, `FRIDGE_LIST`, and any additional ingredient supply, then compare the effective orders (`currentMenu`/`loadingMenu`) and `hintText` after `setHint` runs. Check that every tutorial order and cooking instruction belongs to the actual stage theme and can be prepared with the available ingredients and recipes. Check tutorial enabled/disabled paths and practice-mode entry paths where applicable; syntax checks alone do not establish gameplay correctness.
- Regression case (2026-09-19): JP Classic Casual Dining uses theme 6 (fish/sushi/rice bowls), instead of KR/EN theme 4 (dumplings), at zero-based stage indexes 7, 10, and 13. Player-facing stage 8 is `Global.stage == 7`. Its inherited dumpling tutorial overwrote the fish order list and caused progression failure. At the user's request, the JP stage-7 tutorial now uses exactly `203, 211, 209, 202, 223, 220, 196, 214, 215, 226, 219` in that order, with concise Japanese recipe hints. Preserve this locale-specific replacement during synchronization. Only the first `loadingMenu` cycle is restricted; keep `currentMenu` and its normal 13-item refill unchanged, including omitted tutorial dishes 210 and 213. Verify the current tables rather than treating this historical mapping as permanently fixed.
- In validation reports, distinguish player-facing stage numbers from zero-based indexes, record any intentional locale-specific tutorial omissions, and state whether verification was static or performed in-game. Do not claim an in-game pass based only on syntax checks.
- In this workspace, `.codex/` is intentionally tracked by git for workspace memory and artifacts. Do not re-add `.codex/` to `.gitignore` unless explicitly requested.
- Workspace-local artifacts and history should be stored under `.codex/artifact/`.
- **Source of truth (2026-09-25 transition):** root `.ow` files are the sole authoritative source for runtime code AND all game data, including items, recipes, menus, stages, and localized strings. Edit them directly. This supersedes older builder instructions in historical artifacts and prior session guidance.
- Builders are retired. Do not regenerate `.ow`, reverse-sync edits into builder metadata, compare against prospective generated output, or require builder checks/byte equality. Do not run historical builder scripts from `.codex/artifact/`.
- `reference/` contains historical translation/mapping/report/workbook snapshots only; `deprecated/` contains historical Workshop versions. Neither is a current data source or an input for generation. Consult them when useful, but resolve every conflict in favor of the current target `.ow`. Updating reference snapshots is not a completion requirement.
- After direct edits, run `python -B scripts/check_ow_syntax.py "*.ow"` and `git diff --check`. When changing the checker, also run `python -B -m unittest discover -s tests -v`. The default CI job discovers all root `.ow` files without a maintained file list. Historical files can be checked explicitly by path.
- Syntax checks are limited static checks, not game import/runtime or semantic validation. Inspect affected data references and execution order directly in the current `.ow`; retain the mandatory per-locale tutorial/data checks above. Preserve intentional KR/EN/JP differences and localize player-facing text.
- Version strings in this project use the edit date as `vYYMMDD`. Whenever modifying any project file, update all relevant `vYYMMDD` occurrences in that file to the current date. For example, edits made on 2026-09-25 should use `v260925`.
- Established Workshop table refactor pattern from `2026-04-14`:
  - For long numeric tables, prefer `Custom String` chains with `{0}` continuation plus `String Split(..., Custom String("/"))`.
  - Keep each string segment around 90 characters to avoid Workshop string-length issues.
  - If the final table must stay numeric, wrap the split result with `Mapped Array(..., Index Of Array Value(Global.MIXING_RECIPE, Current Array Element))`.
  - Use a temporary numeric lookup array in the same init subroutine before mapped conversions:
    `Global.MIXING_RECIPE = String Split("0..N", ...)`.
  - Restaurant files used `0..474`; cafe files used `0..397`.
  - Leave mixed-type tables such as `CUTTING_RESULT` as raw `Array(...)` unless a dedicated encoding/decoding scheme is introduced.
  - When converting numeric result tables, legacy `False` entries were rewritten to `0`.
  - Keep locale variants structurally aligned:
    `Global: Setting` host-select flow, `dataInit3` difficulty-variable init, `Call Subroutine(dataInit3);` reuse in difficulty-up logic, and no duplicate `Global.STAGE_CODE` reassignment in the difficulty-up block.
  - Match indentation of edited `Custom String` chains to the localized reference file already accepted in the workspace.
- Current recorded session:
  - `.codex/artifact/20260414_workshop_array_refactor/`
  - `.codex/artifact/20260415_ko_change_analysis/`
  - `.codex/artifact/20260415_en_jetpack_cat_port/`
  - `.codex/artifact/20260415_jp_jetpack_cat_port/`
  - `.codex/artifact/20260415_en_followup_patch_port/`
  - `.codex/artifact/20260415_jp_followup_patch_port/`
  - `.codex/artifact/20260420_ko_cafe_diff_baseline/`
  - `.codex/artifact/20260420_cafe_kr_head_port_plan/`
  - `.codex/artifact/20260420_cafe_en_head_port_plan/`
  - `.codex/artifact/20260420_gc_kr_head_port_plan/`
  - `.codex/artifact/20260420_gc_en_head_port_plan/`
  - `.codex/artifact/20260531_restaurant_jp_followups/`
  - `.codex/artifact/20260827_mixed_array_string_compression/`
  - `.codex/artifact/20260827_kr_deluxe_unification/`
  - `.codex/artifact/20260829_en_deluxe_creation_plan/`
