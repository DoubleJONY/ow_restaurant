# JP Deluxe creation task

## ITEM_NAME translation baseline

- [x] Retire the initial table based on the old standalone edition indexes.
- [x] Extract ORG, CAFE, and GC Korean names from the current `kr_deluxe.ow` init1 rules.
- [x] Extract ORG, CAFE, and GC English names from the current `en_deluxe.ow` init1 rules.
- [x] Rebuild every row with the current Deluxe runtime item index.
- [x] Preserve prior Japanese work by `(edition, kr, en)` instead of the obsolete index.
- [x] Keep common tool/item codes `0..20` aligned across all three editions.
- [x] Add a repeatable source/table consistency check.
- [x] Reuse 172 unambiguous ORG Japanese names in CAFE and GC.
- [x] Add 15 reviewed ORG-equivalent names whose spacing or source wording differs.
- [x] Add 101 basic nouns, established loanwords, and one proper name with no meaningful translation ambiguity.
- [x] Force `싼데비슷한 드링크 / Sandevistan / 怪しいスタンド` at code 9 in every edition.
- [x] Reject the forbidden Japanese character `豚` from the table and translation seeds.
- [x] Generate a separate review proposal for all remaining 574 blank Japanese names.
- [x] Apply the JP proposal rules for Japanese dish localization, descriptive non-Japanese dishes, the `オ・レ` wordplay, and established state terms.
- [x] Validate proposal coverage, current Deluxe indexes, forbidden characters, and deterministic regeneration.
- [x] Review and approve `item_name_translation_proposals.tsv`.
- [x] Translate the remaining ORG 1, CAFE 274, and GC 299 Japanese item names.
- [x] Review shared item terminology across ORG, CAFE, and GC.
- [x] Build `jp_deluxe.ow` from the approved translation table.

## JP Deluxe static port

- [x] Use the current byte-verified `kr_deluxe.ow` as the sole runtime-code base.
- [x] Apply all 1,339 Japanese ITEM_NAME rows at current Deluxe indexes.
- [x] Add reviewed CAFE/GC STAGE_NAME and UPGRADE_NAME tables.
- [x] Reuse legacy ORG Japanese strings with explicit context remaps where the Deluxe rule layout shifted.
- [x] Preserve only the approved ORG data localization, ITEM_COLOR palette, and JP scoreboard spacing.
- [x] Carry the locale-neutral fixes already present in the released EN Deluxe output.
- [x] Generate `jp_deluxe.ow` and prove byte equality with `--check`.
- [x] Produce translation inventory, resolved map, unresolved report, and output-derived validation report.
- [x] Keep empty high-score holder wording as `None` in ORG, CAFE, and GC.
- [x] Keep the existing JP Workshop code `4ND1P` for JP Deluxe.
- [ ] Import into Workshop, run the three-edition runtime matrix, and record the final element count.

## Authoritative table

`scripts/jp_deluxe/item_name_translations.tsv`

The table uses five columns: `edition`, `item_index`, `kr`, `en`, and `jp`.
`item_index` is the actual index in each current Deluxe edition's `ITEM_NAME` array. Codes `0..20` use the shared Deluxe tool/item layout; later food indexes remain edition-specific.

Conservative initial translations that do not exactly reuse an ORG Korean name are recorded by semantic identity—not legacy index—in `scripts/jp_deluxe/item_name_seed_translations.tsv`.

## Review proposal

`scripts/jp_deluxe/item_name_translation_proposals.tsv`

This file records the 574 reviewed suggestions that were integrated into `item_name_translations.tsv`. It remains as an auditable record of the proposal pass.
