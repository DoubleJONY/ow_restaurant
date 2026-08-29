# jp_deluxe implementation plan

## Goal

Create `jp_deluxe.ow` from the current `kr_deluxe.ow` structure, using the same deterministic overlay workflow as `en_deluxe.ow`.

- KR Deluxe remains the authority for code, canonical item indexes, serialization, edition dispatch, CAFE ice-machine/freezing logic, GC water interaction, tutorials, and all other runtime behavior.
- Current `jp.ow` is the authority for legacy ORG Japanese localization and the explicitly approved ORG gameplay-data localization listed below.
- CAFE and GC have no legacy Japanese editions. Their code and numeric data remain KR Deluxe data; only user-facing locale data is translated.
- `scripts/jp_deluxe/item_name_translations.tsv` is the authority for all ORG, CAFE, and GC `ITEM_NAME` values.

## 0. Baseline safety

1. Run a read-only byte comparison between current `kr_deluxe.ow` and `scripts/kr_deluxe/build_kr_deluxe.py` output.
2. Treat a hand-edited OW file as authoritative and reverse-sync any drift before writing.
3. Record SHA-256 fingerprints for `kr_deluxe.ow`, `jp.ow`, the ITEM_NAME table, and all JP overlay tables.
4. Start `jp_deluxe.ow` from the current KR Deluxe output, never from legacy `jp.ow`.
5. Add `scripts/jp_deluxe/build_jp_deluxe.py` with `--check` that compares the actual `jp_deluxe.ow` byte-for-byte with generated output.

## 1. Locale data tables

### ITEM_NAME

- Read all 1,339 rows from `scripts/jp_deluxe/item_name_translations.tsv`.
- Require zero blank JP cells and exact current KR/EN source identity.
- Apply counts `ORG=476`, `CAFE=399`, `GC=464` to `dataInit_org1`, `dataInit_cafe1`, and `dataInit_gc1`.
- Rebuild the serialized `Custom String` chains with safe segment lengths and round-trip validation.
- Reject `豚` in every final Japanese item name; preserve code 9 as `怪しいスタンド` in all editions.

### STAGE_NAME and UPGRADE_NAME

- ORG: extract the current Japanese values from `jp.ow`, map them to Deluxe indexes, and preserve them.
- CAFE/GC: create a reviewed JP translation table because no Japanese source editions exist.
- Keep numeric recipe and upgrade behavior from KR Deluxe; only names are localized.

### totalScore

- ORG: preserve the Japanese legacy rows from `jp.ow` (`練習モード`, `Biscuits0507`, and the existing empty rows).
- CAFE/GC: create six rows each using the Japanese practice label and empty-record policy selected during review.
- Emit the same 18-row edition slice used by KR/EN Deluxe after `stageMode[0]` is selected and before difficulty initialization.

## 2. Approved ORG Japanese gameplay-data localization

Patch the current Deluxe ORG arrays by semantic paths. Do not copy the whole legacy `dataInit` block.

### STAGE_CODE

Legacy JP differs from KO only in mode 1:

- `[1][7][0]`: `4 -> 6`
- `[1][10][0]`: `4 -> 6`
- `[1][13][0]`: `4 -> 6`

All other ORG paths and all CAFE/GC `STAGE_CODE` values remain current KR Deluxe values.

### MENU_LIST

Replace ORG stage row `[2]`:

- KR: `85,86,87,88,89,90,96`
- JP: `84,85,86,87,88,89,90,96`

This retains the Japanese fried-chicken/から揚げ menu composition.

### HAZARD_MENU_LIST

Replace ORG row `[7]` with the Japanese nine-item row:

`0,190,109,110,101,102,103,120,293`

The KR-only kimchi entries `145` and `143` are intentionally excluded.

### FRIDGE_LIST

Patch ORG `[7][1]` from `142` (kimchi) to `266` (narutomaki).

### RAW_MIX and RAW_RESULT

Patch recipes by `(ingredient A, ingredient B, result)` identity rather than copying legacy array positions. Legacy sequence order differs in 18 positions, but the semantic delta is only these three recipes:

- remove `144246 -> 247`; add `246267 -> 247`
- remove `144248 -> 249`; add `248267 -> 249`
- remove `144250 -> 251`; add `250267 -> 251`

This changes the three kimchi noodle recipes to narutomaki noodle recipes while retaining current Deluxe canonical indexes and RAW decoding.

### ITEM_COLOR

Preserve the established JP narutomaki-noodle palette by changing ORG indexes `247`, `249`, and `251` from key `C` to key `P`. The final validator compares the complete decoded palette and the unchanged mapper expression, so no other color entry or palette mapping may differ.

### Japanese scoreboard layout

Preserve the legacy JP vertical spacing for the left scoreboard column:

- cooked/cut: `2.200 -> 2.400`
- served: `2.000 -> 2.200`
- missed: `1.800 -> 2.000`

These coordinates are verified directly in the final output exactly once each.

### Tables that remain KR Deluxe data

Keep current KR values for cooking times/results, scores, knife/perk data, drop pools, CAFE/GC menu arrays, CUSTOMER_LIST, and every unlisted numeric table. Validate that no unintended locale delta enters these tables.

## 3. Japanese Custom String overlay

Use the EN Deluxe pipeline design with JP-specific sources and policies:

1. Build a rule/ordinal inventory of every KR Deluxe `Custom String`.
2. Match structurally identical ORG contexts against current `jp.ow`.
3. Reuse relevant historical JP artifacts only as secondary evidence.
4. Create `manual_translations.tsv` for Deluxe-only, CAFE-only, and GC-only strings.
5. Use the English Deluxe text as a semantic reference for new CAFE/GC strings, not as a code or placeholder authority.
6. Store final manual wording changes in `output_overrides.tsv`, keyed by rule, ordinal, source text, and approved target text.
7. Add `release_code_overrides.jsonl` only when a final JP release truly needs a structural/runtime difference; do not copy EN release overrides blindly.

Translation rules:

- Preserve placeholder multisets, color markup, icon arguments, and explicit line breaks.
- Do not translate serialization delimiters, numeric payloads, authentication keys, Workshop codes, or other structural strings.
- Use official or established Japanese Overwatch terminology where available.
- Use `ポーク` and reject `豚` across all user-facing strings, not only ITEM_NAME.
- Keep Sandevistan-related naming consistent with the final `怪しいスタンド` decision.
- Use the Japanese recipe URL `/ja` and the final JP Workshop code policy.

## 4. Static validation

- Actual `jp_deluxe.ow` equals generated output byte-for-byte.
- Rules/globals/subroutines remain `57 / 128 / 40` unless an explicitly approved change is recorded.
- ITEM_NAME counts remain `476 / 399 / 464`; STAGE_NAME is 12 and UPGRADE_NAME is 10 per edition.
- Every localized assignment round-trips through its serializer.
- ORG gameplay-data differences equal only the approved path manifest above.
- CAFE and GC numeric/menu/recipe data equal KR Deluxe.
- Unresolved user-facing Hangul is zero except explicit allowlisted authentication/credit strings.
- Placeholder and color-markup mismatches are zero.
- `豚` occurrences in user-facing Japanese strings are zero.
- No stale manual or output override remains.
- Maximum generated `Custom String` segment stays within the project safe limit.
- Repeated builds produce the same SHA-256.
- `git diff --check` passes.

## 5. Runtime and Workshop validation

Test at least:

- A non-host joining before dataInit: the default knife HUD name updates after ITEM_NAME initializes.
- Host edition/mode selection and all three edition boot paths.
- ORG Japanese chicken menu, localized STAGE_CODE sequence, narutomaki fridge item, hazard list, and three narutomaki noodle recipes.
- CAFE ice machine label/logic, Freeze Gun, item drops, and tutorial flow.
- GC sink-water interaction, item drops, and tutorial flow.
- Edition-specific totalScore display after edition selection.
- Practice mode and practice item-spawn menu.
- `怪しいスタンド` name, description, activation text, slowdown, and durability behavior.
- Save/load, knife/perk/foot HUDs, recipe URL, update-code HUD, and high-score submission text.
- Workshop import with no profanity-filter rejection.
- Final Workshop element count below `32,768`, recorded after import.

## Additional review gates

1. Approve CAFE/GC `STAGE_NAME`, `UPGRADE_NAME`, and non-ITEM_NAME translations.
2. **Approved:** keep empty `totalScore` holder wording as `None` in all three editions.
3. **Approved:** retain `4ND1P` as the JP Deluxe public and update code.
4. Confirm that all five ORG localization groups (`STAGE_CODE`, `MENU_LIST`, `HAZARD_MENU_LIST`, `FRIDGE_LIST`, RAW recipes) must be retained together.
5. Audit the remaining EN release overrides and carry over only locale-neutral fixes not already present in KR Deluxe.
6. Measure element usage early after data/string serialization and again in the Workshop client before release.

## Implemented build policy

- `--report` writes reports only and never overwrites `jp_deluxe.ow`.
- `--check` is read-only and compares the actual OW bytes with prospective output.
- A normal build refuses to overwrite a divergent OW file; `--force-write` is required after manual drift has been reviewed or reverse-synced.
- Output overrides cannot target data-init rules, authentication literals, or save/load identity wrappers.
- Final validation decodes the generated tables again and checks exact ORG deltas, unchanged CAFE/GC data, RAW mapper/base-1000 packing semantics, pinned control strings, the 128-character Custom String limit, and the `57 / 128 / 40` source shape.

The locale-neutral EN release fixes carried into JP Deluxe are the three-edition practice selector modulus, the two Sandevistan durability formulas, and removal of the obsolete external Workshop-code branch from Other Menu.
