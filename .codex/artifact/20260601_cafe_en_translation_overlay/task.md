# cafe_en.txt Translation Overlay Port

## Objective

Update `cafe_en.txt` so its gameplay logic matches the latest `cafe_kr.txt`, while preserving English-specific strings and data.

The preferred strategy is not selective patch picking. Use latest `cafe_kr.txt` as the logic source, then reapply English strings from the backed-up `cafe_en.txt` and other reliable translation resources.

## Current Context

- `cafe_kr.txt` is the latest Cafe logic baseline.
- `cafe_en.txt` is an older English version that should be logically identical to `cafe_kr.txt` except for translated strings and English-specific metadata.
- `Global.totalScore` high-score records are language-specific and must not be copied from KR to EN.
- If new modes require new high-score slots, add neutral English entries such as `Array(0, Custom String("None"))`.
- Before this task, `[0]` and `[1]` array indexes in `cafe_kr.txt` were converted back to `[False]` and `[True]`. `cafe_en.txt` already had no exact `[0]` or `[1]` index patterns.

## Safety Rules

- Back up the current `cafe_en.txt` into this artifact before overriding it.
- Do not copy KR high-score values or KR high-score holder names into EN.
- Do not translate newly added KR strings during the initial overlay pass.
- Apply only high-confidence existing English translations automatically.
- Leave uncertain or newly added strings in Korean for a later review pass.
- Preserve placeholders such as `{0}`, `{1}`, line breaks such as `\r\n`, and `Custom String` argument structure.
- Preserve EN-specific URLs, route suffixes, workshop code text, version/code text, and user-facing language labels where applicable.
- Preserve the existing `cafe_en.txt` `Global.ITEM_NAME` block as a whole.
  - Parsed `ITEM_NAME` data was checked: both `cafe_kr.txt` and `cafe_en.txt` currently produce 399 split items.
  - The only practical difference is `Custom String(...)` chunking caused by longer English names.
  - Do not rebuild `ITEM_NAME` from KR during the overlay unless a later count mismatch is explicitly found.

## Planned Workflow

1. Record current repository state.
   - Check `git status`.
   - Treat `HEAD` as the baseline for final diff review.

2. Back up current resources.
   - Save current `cafe_en.txt` into this artifact directory.
   - Also save useful reference diffs or extracted string inventories if needed.

3. Extract translation candidates.
   - Extract `Custom String(...)` entries from backed-up `cafe_en.txt`.
   - Extract `Custom String(...)` entries from current `cafe_kr.txt`.
   - Record rule name, rough statement context, placeholder set, and raw text where practical.

4. Override `cafe_en.txt` with latest `cafe_kr.txt` logic.
   - Copy the current `cafe_kr.txt` content into `cafe_en.txt`.
   - At this stage, logic should match KR and many strings will still be Korean.

5. Restore EN-specific data.
   - Restore existing EN `Global.totalScore` records from the backup.
   - Add only neutral empty entries for new mode slots.
   - Restore EN URL/path/code/version text where appropriate.
   - Restore the backed-up EN `Global.ITEM_NAME` block unchanged, because its parsed item count already matches KR.

6. Reapply only safe existing translations.
   - Use backed-up `cafe_en.txt` translations when correspondence is clear.
   - Use `ko.txt` / `en.txt` only for exact shared strings where placeholder structure matches.
   - Do not apply translations when placeholder structure differs, multiple mappings exist, or the string appears to be new Cafe-specific text.

7. Generate unresolved string list.
   - List newly added Korean strings left untranslated.
   - List ambiguous translation candidates.
   - List EN-specific values requiring manual confirmation.

8. Review `HEAD` diff for string-content changes.
   - Inspect `git diff HEAD -- cafe_en.txt`.
   - Focus on cases where text inside `Custom String` changed substantially from previous EN.
   - Separate expected logic updates from potentially unintended copy/translation changes.

9. Translate remaining new strings.
   - Translate only after reviewing the string-content diff.
   - Match existing EN terminology and tone.
   - Keep placeholders, icon-string argument positions, URLs, and line breaks intact.

10. Final verification.
    - Check for remaining Korean text in `cafe_en.txt`.
    - Check placeholder consistency.
    - Check that KR high-score values were not copied into EN.
    - Check that logic differences from `cafe_kr.txt` are limited to strings and EN-specific values.
    - Save final summary and any remaining TODOs in this artifact.

## Known High-Risk Areas

- `Global.totalScore` initialization and high-score display/comparison.
- Mode count expansion and new high-score slots.
- `Global.ITEM_NAME`: preserve the existing EN block; do not use line/chunk structure as a diff key.
- Version string, workshop code, and `ow-restaurant.com/en` path.
- Practice-mode menu strings and workshop-code announcements.
- New Cafe-only systems such as ice maker, cooling gun, and mode additions.
- Any `Custom String` with placeholders or nested `Custom String` arguments.
