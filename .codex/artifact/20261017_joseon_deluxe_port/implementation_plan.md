# Joseon Deluxe port plan

Date: 2026-10-17 (Asia/Seoul)
Status: initial port implemented on 2026-10-17; two-edition amendment implemented on 2026-10-31; game import/play tests pending.

## Current amendment (2026-10-31)

2026-11-01 superseding request: remove the deferred third edition's arrays and
all three GC init rules from the runtime, along with unused subroutine declarations.
Do not renumber retained identifiers or remove shared data. Historical snapshots
remain archival only. References below to retaining GC data are historical.

Only editions 0 (New Branch 3) and 1 (New Cafe) are selectable. This supersedes
the original requirement below to keep edition 2 selectable. Retain all three
GC init rules/data for later work, but remove their dispatcher/difficulty-up
calls. Startup cycles modulo 2. Practice Other Menu cycles four entries:
N3, Cafe, SPXXM external reference, 8MAAN external reference. Internal dispatch
accepts 0..1 and external link arrays use indexes 2..3. Keep all six game modes,
both active edition data sets, shared water 21, site-only tutorials, scores,
and the 2026-10-31 HUD/shop fixes unchanged.

## Objective and authoritative inputs

Create root `Joseon_deluxe.ow` as a copy of current `kr_deluxe.ow`.
Keep Deluxe's shared runtime and replace edition-specific food data and its
dependent references. Do not replace the current KR/EN/JP Deluxe files.

| Role | Input | Policy |
| --- | --- | --- |
| Runtime baseline | `kr_deluxe.ow` | Current shared logic, mode structure and common items |
| Edition 0 food data | `n3_kr.ow` | Existing root version v260827; do not use the older attached message.txt |
| Edition 1 food data | `deprecated/nc_kr.ow` | Explicitly selected new Cafe source, v260613, STRAX |
| Edition 2 placeholder | Existing third edition in kr_deluxe.ow | Retain structure and values except recipe contents |

The user explicitly selected nc_kr.ow for this new port. This is an exception to
the general prohibition on using deprecated files as generation inputs. It is a
one-time data migration into a new root source, not a builder workflow. Once
created, Joseon_deluxe.ow becomes its own authoritative source.

## Confirmed constraints

- Edition indexes: 0 = New Branch 3, 1 = New Cafe, 2 = unfinished placeholder.
- Use GC as the behavioral integration example for New Branch 3 and Cafe as the
  example for New Cafe. Copying their theme IDs, food IDs or old recipes is not
  part of this correspondence.
- Keep Deluxe's six game modes, shared customers, roles, scoring, physics,
  persistence and tool implementation unless data integration requires a change.
- Both implemented editions use the simple GC-style recipe-site tutorial.
  Do not copy Classic's detailed hints, forced tutorial orders or customer waves.
- New Branch 3 must not supply, sell, drop or activate the preservation box,
  even though it occupies Classic's edition index 0.
- Keep common preservation-box slot 19 for stable shared item ordinals.
- Keep Cafe freezing, oven and cooling-gun behavior through Deluxe's Cafe branch.
- Supply common water item 21 from the sink in all three editions, without a waterCode variable or edition condition.
- Edition 2 remains selectable. Add no selection block, unfinished warning,
  fallback edition or special handling just because its recipes are empty.
- No commit or push is included in the implementation request by implication.

## Phase 1: baseline and inventories

1. Record current HEAD, source hashes and the initial working-tree status.
2. Preserve immutable input snapshots under this artifact before editing runtime.
3. Inventory all item tables, recipe tables, menu tables and data initializers.
4. Inventory hardcoded item IDs and edition conditions throughout the runtime,
   including sources outside the obvious data initialization rules.
5. Do not run retired historical builders or use stale generated metadata.

## Phase 2: explicit item mappings

Retain Deluxe's common item layout: 0 = burnt food, 1..7 = knives, 8..18 =
shared drinks/tools/boots/money, 19 = preservation box, 20 = cooling gun.
User amendment: 21 is shared water in all three edition data layouts. Sink
supply is enabled in all three editions without a waterCode variable. New Branch 3 rice is
514 and boiled water is 515; New Cafe boiled water is 521. The placeholder's
former item 21 (gochujang) is retained at 464. See item_mapping.tsv.

- New Branch 3 already shares 0..18. Move old 19 (water) to common 21,
  old 20 (boiled water) to 515 and old 21 (rice) to 514; add box/gun records.
- New Cafe already shares 0..18. Move old 19 (cooling gun) to common 20,
  old 20 (water) to common 21 and old 21 (boiled water) to 521; add box slot 19.
- Destination slots were chosen after parsing the full input tables.
  Unaffected IDs remain stable; historic Cafe mappings were not reused.
- Record forward and inverse mappings, source names and final names.
- Preserve item-table keys and result-code values separately. Recursively map
  multiple-output arrays and additional-material arrays.
- Rebuild encoded RAW_MIX pairs as M(left) * 1000 + M(right), and map each
  RAW_RESULT value without reordering, deduplicating or changing pair direction.
- Do not remap times, scores, colors, theme IDs, mode IDs, itemStatus,
  tool ordinals, sentinel values or arbitrary numeric literals as item IDs.
- Preserve boolean indexing optimizations; never blanket-replace [2] or other
  indexes. Distinguish False sentinels from the burnt-food item code by context.

## Phase 3: edition data

Port ITEM_NAME, ITEM_COLOR, ITEM_SCORE and the cutting, impact, pot, pan,
grilling, frying and freezing tables, including thresholds and result arrays.
Port RAW_MIX/RAW_RESULT, MENU_LIST, HAZARD_MENU_LIST, WEAVER_MENU_LIST,
FRIDGE_LIST, ADDITIONAL_MATERIAL_LIST and STAGE_NAME with consistent mappings.

- New Branch 3 has 12 themes; New Cafe has 14. Update theme ranges, random
  selection, fusion combinations and mode-specific STAGE_CODE accordingly.
- Use source theme identity and ordering while adapting to Deluxe's mode
  structure. New Branch 3's older mode layout must not replace the six-mode runtime.
- Keep common customer progression and difficulty behavior from current Deluxe.
- Reset edition-local data on every initialization and practice edition switch
  so ICE, recipes, menus and extra materials cannot leak across editions.
- Build all lookup arrays with ranges large enough for the final mapped IDs.

## Phase 4: runtime-dependent references

- Add water label/effect and the Primary Fire source branch, keeping role and
  item-count limits. Keep the existing independent sink-disposal interaction.
- Generate common water code 21 directly; no edition-specific water variable is needed.
- Audit DELUXE_DATA start items, active tool pool, weighted purchase pool,
  practice equipment, merchant stock, free gifts and Ramattra rewards.
- New Branch 3 uses GC-like active equipment without box or cooling gun.
- Cafe permits its cooling gun at itemPerk ordinal 8 and excludes the box.
- Audit every edition-0 condition: box activation, box food generation and the
  hardcoded theme-to-box-food array must not run for New Branch 3.
- Review Classic-specific theme-11 additional-material supply, reservation
  supply and despawn treatment. Retarget by the new actual tables, not index 11
  alone. Preserve New Branch 3 and Cafe special-order ingredient availability.
- Audit copy-spell exclusions, equipment detection and drop/restore paths.
- Keep edition 2's existing common settings and runtime flow unchanged.

## Phase 5: tutorial, identity and scores

- Use recipe-site guidance only for New Branch 3 and New Cafe, following the
  GC example. Preserve their normal currentMenu/loadingMenu and refill behavior.
- Inspect all callers of setHint, including practice entry, so no Classic
  tutorial IDs or Classic-only customer overrides remain reachable.
- Align title, selection menu, edition author text, equipment labels, stage
  names, scoreboard, practice other-menu links and update text.
- Do not claim the new combined map has an existing standalone workshop code.
  Use a neutral undecided label until a combined code is supplied.
- New-map score records start at 0 / none; do not inherit Classic/Cafe/GC records
  as records for the new game. Preserve the score storage layout.
- Set new runtime version strings to the actual implementation date vYYMMDD.
  Leave the legacy input snapshot's version and bytes unchanged.

## Phase 6: unfinished third edition

Retain edition index 2, its dispatcher, mode values, item definitions, theme/menu
structure, customer configuration and common equipment records.

- Empty RAW_MIX and RAW_RESULT and explicitly reset derived mixing arrays.
- Clear food recipe conversion results for cutting, impact, pot, pan,
  grilling, frying and freezing where applicable, using neutral values at
  existing indexes rather than shifting table positions.
- Retain non-recipe settings, thresholds and item metadata; preserve any truly
  common equipment records. Do not empty the shared customer's initialization.
- Do not clear MENU_LIST/FRIDGE_LIST/STAGE_CODE merely to make this placeholder
  appear playable. Its playability is intentionally outside acceptance.
- No selection guard or unfinished-edition runtime exception is to be added.

## Phase 7: verification and delivery

- Verify input copies byte-for-byte and preserve their original versions.
- Compare each mapped source record with its destination through inverse mapping.
- Verify recipe pair/result alignment, valid indexes and multiple-output shapes.
- Trace each implemented edition and mode from STAGE_CODE through orders,
  fridge supply, additional materials, water supply and reachable recipes.
- Verify site-only tutorial on/off and practice paths preserve normal menus;
  record displayed stage numbers separately from zero-based indexes.
- Verify no New Branch 3 box acquisition/use and Cafe-only cooling gun behavior.
- Review practice edition switches for stale tables and apparatus visibility.
- Confirm edition 2 recipe values are empty without selection restrictions.
- Run python -B scripts/check_ow_syntax.py "*.ow" and git diff --check.
- Inspect string segment lengths, initialization order and lookup ranges.
- Report Workshop import, element budget and in-game tests as pending unless
  actually measured. Static syntax checks do not establish runtime correctness.
- Deliver a scoped change summary, mapping inventory and validation report.

## Current progress

New Cafe was copied verbatim from the supplied message-2.txt to deprecated/nc_kr.ow.
Joseon_deluxe.ow now contains both remapped editions, common water code 21,
site-only tutorials and a selectable third edition with recipe outputs cleared.
Source comparison, structural checks, recipe reachability and syntax checks
passed; validation_report.md distinguishes these from pending game tests.
No commit or push was performed.
