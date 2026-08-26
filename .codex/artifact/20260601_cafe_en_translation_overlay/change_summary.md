# cafe_en Translation Overlay Summary

## Completed Work

- Backed up the pre-overlay `cafe_en.txt`.
- Backed up the `cafe_kr.txt` logic source used for the overlay.
- Rebuilt `cafe_en.txt` from latest `cafe_kr.txt` logic.
- Restored the English `Global.ITEM_NAME` block from the backup.
- Restored/expanded the English `Global.totalScore` block without copying KR high-score records.
- Applied safe context-matched translations first.
- Translated the remaining Korean `Custom String` values after reviewing the unresolved list.

## Preserved English Data

- `Global.ITEM_NAME`
  - Final parsed item count: 399.
  - Final Korean item names: 0.
  - This block remains the English version and was not rebuilt from KR.
- `Global.totalScore`
  - KR score values such as `6083`, `14315`, and `REVENGE` were not copied.
  - Final entries are:
    - `Practice`
    - `None`
    - `None`
    - `None`
    - `None`
    - `None`
- EN URL/code surface strings were restored to English path/code form.
  - Main HUD string now uses `Restaurant(Z1TBZ) v260531` and `ow-restaurant.com/en`.

## Translation Passes

- Safe context translation replacements: 43.
- Manual reviewed translation map entries: 165.
- Manual translation replacements: 206.
- Follow-up reference alignment:
  - Compared against `ko.txt` / `en.txt` context mappings.
  - Applied 39 `en.txt` reference translations for UI/message wording.
  - Ignored `old_cafe` numeric/data-string mismatches so current Cafe logic data would not be reverted.
  - Preserved Cafe-specific device/menu names such as `Ice Maker`, `Fryer&Ice Maker`, `Oven`, `Pan`, and `Pot`.
- Remaining Korean text in `cafe_en.txt`: 0 matches from `rg "[가-힣]"`.

## Verification

- Normalized logic comparison:
  - `Global.ITEM_NAME` and `Global.totalScore` were masked as intentional EN-specific blocks.
  - All other `Custom String` contents were masked.
  - Result: `cafe_en.txt` and `cafe_kr.txt` normalized logic matched exactly.
- Placeholder verification:
  - Compared `Custom String` placeholder sets outside preserved blocks.
  - KR count: 561.
  - EN count: 561.
  - Placeholder mismatches: 0.
- High-score leak check:
  - No `6083`, `14315`, or `REVENGE` match in `cafe_en.txt`.

## Generated Files

- `cafe_en.before_overlay.txt`
- `cafe_kr.logic_source.txt`
- `pre_overlay_cafe_kr.diff`
- `pre_overlay_git_status.txt`
- `safe_context_translation_report.tsv`
- `unresolved_korean_lines_after_safe_overlay.tsv`
- `manual_translation_map_count.txt`
- `translation_reference_mismatches_compact.tsv`
- `applied_en_reference_replacements.tsv`

## Notes

- `cafe_en.txt` has more lines than `cafe_kr.txt` because the preserved English `ITEM_NAME` block is split into more `Custom String(...)` chunks due to longer English item names.
- The current `cafe_kr.txt` still contains the earlier requested `[0]` / `[1]` to `[False]` / `[True]` conversion.
