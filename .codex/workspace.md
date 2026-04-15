# Workspace Settings for Codex

If you are reading this file, it is user-authored workspace-wide agent behavior
settings. Find and comply with any items or references described here.

## Workflow Reference
- Use `~/.codex/workflow/taskPlanner.md` for this workspace.

## Additional Context
- In this workspace, `.codex/` is intentionally tracked by git for workspace memory and artifacts. Do not re-add `.codex/` to `.gitignore` unless explicitly requested.
- Workspace-local artifacts and history should be stored under `.codex/artifact/`.
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
