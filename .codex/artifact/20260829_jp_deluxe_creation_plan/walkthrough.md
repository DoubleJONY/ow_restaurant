# JP Deluxe ITEM_NAME translation-table walkthrough

The authoritative editable table is `scripts/jp_deluxe/item_name_translations.tsv`.

Each row contains an edition, its current Deluxe runtime item index, and the corresponding Korean, English, and Japanese names. Korean and English names now come directly from the current `kr_deluxe.ow` and `en_deluxe.ow` edition init1 rules. The standalone edition files are no longer index authorities.

The first conservative fill pass reuses exact ORG names automatically. Reviewed near-equivalents and translations limited to basic nouns, established loanwords, and language-neutral names are stored semantically in `scripts/jp_deluxe/item_name_seed_translations.tsv`. Existing Japanese work is migrated by `(edition, kr, en)` so Deluxe index changes cannot attach it to the wrong item.

Code 9 is fixed to `싼데비슷한 드링크 / Sandevistan / 怪しいスタンド`. Any Japanese table or seed value containing `豚` is rejected; use `ポーク` terminology instead.

Run this read-only check before using the table for `jp_deluxe.ow` work:

```powershell
python -B scripts\jp_deluxe\build_item_name_table.py --check
```

Running the script without `--check` refreshes source-backed columns and current Deluxe indexes. Existing Japanese translations are preserved by semantic identity rather than numeric index.

## Reviewing the remaining names

All 574 formerly blank Japanese cells were reviewed in `scripts/jp_deluxe/item_name_translation_proposals.tsv` and integrated into the authoritative table. The proposal file remains as an audit record; no OW file was modified during this step.

The proposal follows these review rules:

- Japanese dishes use familiar local names where the recipe identity is clear, including `鉄火丼`, `うな丼`, `うな玉丼`, and `卵かけご飯`.
- Korean and other non-Japanese dishes use either an established Japanese loanword or a clear ingredient-based description.
- CAFE code 246 preserves the staged `オ・レ` wordplay for the cookie-and-cream intermediate.
- State terms reuse the existing Japanese vocabulary, such as `薄切り`, `捌いた`, `潰した`, `ゆで`, `焼いた`, and `炒めた`.
- `豚` is forbidden; pork names use `ポーク` or an established dish name that does not contain the character.

Check that the recorded proposals remain applied with:

```powershell
python -B scripts\jp_deluxe\build_item_name_proposals.py --check
```

## Building JP Deluxe

`scripts/jp_deluxe/build_jp_deluxe.py` starts from the current byte-verified `kr_deluxe.ow`; it never uses the old `jp.ow` as a code base. The legacy JP file supplies only reviewed ORG translations, ORG localization deltas, totalScore history, and established layout choices.

The JP overlay sources are:

- `item_name_translations.tsv`: all 1,339 edition-local ITEM_NAME rows
- `localized_tables.tsv`: new CAFE/GC STAGE_NAME and UPGRADE_NAME rows
- `manual_translations.tsv`: reviewed Deluxe-only and corrected context translations
- `legacy_context_remap.tsv`: explicit old-to-new rule positions when Deluxe additions shifted ordinals
- `output_overrides.tsv`: final JSON-literal overrides; currently empty and prohibited from touching data/control literals

Safe commands:

```powershell
# Reports only; does not touch jp_deluxe.ow
python -B scripts\jp_deluxe\build_jp_deluxe.py --report

# Read-only byte comparison
python -B scripts\jp_deluxe\build_jp_deluxe.py --check

# Normal generation; refuses divergent existing OW files
python -B scripts\jp_deluxe\build_jp_deluxe.py

# Use only after reviewing or reverse-syncing manual target drift
python -B scripts\jp_deluxe\build_jp_deluxe.py --force-write
```

The current generated target is `392634` bytes with SHA-256 `F61A149B20FF9F7451DCFDD8B287185817CB96555E665EB3D6556C9874E66758`. Static validation reports are stored in `build/jp_deluxe/`.

Three inherited JP strings that were actual semantic or grammar errors are deliberately corrected in the manual context table:

- `ホストがレベル決定中です` -> `ホストがモードを選択中です`
- `〔{0}〕 でを押してスタート` -> `〔{0}〕を押してスタート`
- the malformed `むんげ（潰す）動作...` controller hint -> a natural `材料を潰す動作...` instruction

Empty high-score holders use the approved `None` wording in all three editions, and the approved JP Deluxe public/update code is `4ND1P`. Workshop import, runtime coverage, profanity-filter acceptance, and element count must be recorded after client testing.
