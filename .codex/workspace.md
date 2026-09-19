# Workspace Settings for Codex

If you are reading this file, it is user-authored workspace-wide agent behavior
settings. Find and comply with any items or references described here.

## Additional Context
- **Mandatory locale-specific tutorial validation:** KR/EN/JP may intentionally use different menu/theme orders for the same mode and stage. Never assume a translated tutorial or matching stage index implies matching gameplay. Preserve these differences when copying runtime code, tutorials, or generator logic across locales.
- Before completing any change to tutorials, stage/menu order, recipes, ingredient supply, or their generators, inspect each affected locale's actual generated `.ow` independently. Trace `stageMode` and `Global.STAGE_CODE[Global.stage]` through `MENU_LIST`, `FRIDGE_LIST`, and any additional ingredient supply, then compare the effective orders (`currentMenu`/`loadingMenu`) and `hintText` after `setHint` runs. Check that every tutorial order and cooking instruction belongs to the actual stage theme and can be prepared with the available ingredients and recipes. Check tutorial enabled/disabled paths and practice-mode entry paths where applicable; generator byte equality alone does not establish gameplay correctness.
- Regression case (2026-09-19): JP Classic Casual Dining uses theme 6 (fish/sushi/rice bowls), instead of KR/EN theme 4 (dumplings), at zero-based stage indexes 7, 10, and 13. Player-facing stage 8 is `Global.stage == 7`. Its inherited dumpling tutorial overwrote the fish order list and caused progression failure. At the user's request, the JP stage-7 tutorial now uses exactly `203, 211, 209, 202, 223, 220, 196, 214, 215, 226, 219` in that order, with concise Japanese recipe hints. Preserve this locale-specific replacement during synchronization. Only the first `loadingMenu` cycle is restricted; keep `currentMenu` and its normal 13-item refill unchanged, including omitted tutorial dishes 210 and 213. Verify the current tables rather than treating this historical mapping as permanently fixed.
- In validation reports, distinguish player-facing stage numbers from zero-based indexes, record any intentional locale-specific tutorial omissions, and state whether verification was static or performed in-game. Do not claim an in-game pass based only on builder checks.
- In this workspace, `.codex/` is intentionally tracked by git for workspace memory and artifacts. Do not re-add `.codex/` to `.gitignore` unless explicitly requested.
- Workspace-local artifacts and history should be stored under `.codex/artifact/`.
- Before every task that can modify an `.ow` file or one of its generators, treat the current `.ow` file as potentially hand-edited. First compare it read-only against the generator's prospective output; do not run a write-producing build before this comparison.
- If the current `.ow` file differs from generated output, treat the `.ow` file as authoritative unless the user explicitly says otherwise. Reverse-sync its manual changes into the generator, translation mappings, or explicit override data before making the requested change.
- After editing, run a check that compares the actual `.ow` file with generated output byte-for-byte. A check that merely validates an in-memory generated result is insufficient. Never allow generator execution to silently roll back manual `.ow` edits.
- Version strings in this project use the edit date as `vYYMMDD`. Whenever modifying any project file, update all relevant `vYYMMDD` occurrences in that file to the current date. For example, edits made on 2026-05-31 should use `v260531`.
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
  - Match indentation of generated `Custom String` chains to the localized reference file already accepted in the workspace.
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
