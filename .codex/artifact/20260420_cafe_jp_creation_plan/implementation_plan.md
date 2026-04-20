# Create `cafe_jp.txt`

Create a new Japanese cafe locale file that keeps the cafe gameplay/data model from the existing cafe variants while using Japanese UI and text conventions derived from `jp.txt`.

Execution is intentionally deferred in this artifact. This document only records the implementation plan.

## Analysis Summary

- `cafe_jp.txt` does not exist yet in the workspace.
- `jp.txt` is the current Japanese locale donor, but it is the restaurant variant, not the cafe variant.
- `cafe_en.txt` and `cafe_kr.txt` already contain the cafe-side gameplay/data model:
  - cafe item ids
  - cafe menu graph
  - cafe stage/menu/fridge relationships
  - cafe perk/knife/upgrade arrays
  - cafe-specific init content such as `ICE_NEEDED` / `ICE_RESULT`
- The cafe files also keep a structural constraint that `jp.txt` does not share:
  - long init content is split across `dataInit2_1` and `dataInit2_2`
- A 398-entry index-aligned `Global.ITEM_NAME` mapping between `cafe_kr.txt` and `cafe_en.txt` already exists in:
  - `.codex/artifact/20260420_cafe_item_name_mapping/cafe_item_name_mapping.md`
- Because the user wants cafe logic with Japanese text, `jp.txt` should be treated as a text donor, not as the structural/code base.

## Chosen Migration Policy

> [!IMPORTANT]
> This plan explicitly chooses migration option 2:
> start from `cafe_en.txt`, then transplant Japanese UI/String resources from `jp.txt`.
> `cafe_kr.txt` is used only as a cafe-side verification reference.

> [!IMPORTANT]
> `cafe_jp.txt` should preserve the cafe-side data model.
> No restaurant-only gameplay tables, item ids, path data, or menu graphs should be imported from `jp.txt`.

> [!NOTE]
> Migration option 1 is intentionally rejected for this plan.
> Using `jp.txt` as the structural base would require re-porting cafe item ids, menu/fridge graphs, split-init layout, and other cafe-only data structures into a restaurant-derived file, which is higher risk and less efficient than localizing an existing cafe file.

## User Review Required

> [!WARNING]
> Some cafe-only strings will not have an existing counterpart in `jp.txt`.
> Those strings must be newly localized into Japanese rather than copied mechanically from restaurant Japanese.

> [!WARNING]
> The highest-risk migration area is the split init layout in the cafe files.
> `dataInit2_1` and `dataInit2_2` must remain structurally intact even if most visible strings are migrated from outside the cafe files.

## Proposed Changes

### 1. Japanese `Global.ITEM_NAME` Translation Workstream

- Use the existing 398-entry cafe item-name alignment artifact as the source scaffold.
- Generate a new Japanese item-name table for the cafe index order.
- For each item index, choose the Japanese value by priority:
  - reuse wording already present in `jp.txt` when the same concept already exists there
  - translate from `cafe_en.txt` when the cafe item is new or cafe-specific
  - use `cafe_kr.txt` as a semantic cross-check when English wording is ambiguous
- Keep the final Japanese table strictly index-stable with the cafe variants:
  - same count
  - same order
  - no inserted or deleted indices
- Record translation provenance in a new execution-phase artifact, for example:
  - direct lift from `jp.txt`
  - new translation
  - manually normalized to match Japanese naming conventions
- Apply consistent Japanese naming rules during translation:
  - preserve existing `jp.txt` terminology when overlap already exists
  - keep ingredient-combination syntax consistent
  - keep parentheses and separator style consistent
  - avoid mixing multiple Japanese naming styles for similar drink/dessert categories

### 2. Japanese UI Text Inventory Before Code Edits

- Build a text inventory for user-visible strings in the chosen cafe base before creating `cafe_jp.txt`.
- Split the inventory into:
  - strings with a direct equivalent in `jp.txt`
  - cafe-only strings that require fresh Japanese translation
  - strings that should remain unchanged because they are identifiers, codes, URLs, or intentionally shared labels
- This inventory should include at least:
  - HUD text
  - in-world prompts
  - stage labels
  - difficulty/mode labels
  - reservation/order alerts
  - version/help/changelog text
  - any cafe-only station or product labels outside `Global.ITEM_NAME`

### 3. Code Migration Strategy For `cafe_jp.txt`

- Create `cafe_jp.txt` by cloning `cafe_en.txt`.
- Preserve the cafe-side logic/data arrays unless a text-only replacement is required:
  - `STAGE_CODE`
  - `STAGE_NAME` where the values are content-bearing and need Japanese localization, but not structural reordering
  - `MENU_LIST`
  - `FRIDGE_LIST`
  - `UPGRADE_CODE`
  - `KNIFE`
  - `PERK_LIST`
  - `ICE_NEEDED`
  - `ICE_RESULT`
  - item/perk indices in gameplay branches
- Preserve the existing call order and split-init layout:
  - `Call Subroutine(dataInit);`
  - `Call Subroutine(dataInit2_1);`
  - `Call Subroutine(dataInit2_2);`
- Replace user-visible strings in the cloned file through two channels:
  - direct transplantation from `jp.txt` where the English restaurant string already has a known Japanese counterpart
  - new Japanese localization for cafe-only strings that do not exist in `jp.txt`
- Inject the new Japanese `Global.ITEM_NAME` block after translation review.
- Do not use `jp.txt` as a code donor.
- Do not import restaurant-only content from `jp.txt`, including:
  - restaurant-side item ids
  - restaurant menu graphs
  - restaurant path/serve-zone data
  - restaurant-only table semantics

### 4. Source-Mapping Strategy During Migration

- Use `en.txt` and `jp.txt` as a localization bridge for shared strings:
  - find the English restaurant wording
  - locate the matching Japanese wording in `jp.txt`
  - reuse that Japanese wording in `cafe_jp.txt` when the meaning is the same
- Use `cafe_en.txt` and `cafe_kr.txt` as cafe-side meaning checks when:
  - a cafe item or prompt does not exist in restaurant files
  - a string is short enough to be ambiguous in English
  - a string touches gameplay terminology that must stay consistent with cafe arrays
- When a touched block is structurally cafe-specific but textually simple, preserve the block structure and only replace the string payload.

## Recommended Execution Order

1. Freeze the source policy:
   `cafe_en.txt` clone base, `jp.txt` text donor, `cafe_kr.txt` verification donor.
2. Generate the full Japanese `Global.ITEM_NAME` translation table and review ambiguities.
3. Build the non-item UI string inventory and classify direct-lift vs new-translation cases.
4. Copy `cafe_en.txt` to `cafe_jp.txt`.
5. Apply direct Japanese text substitutions from the `en.txt` -> `jp.txt` bridge.
6. Apply newly translated cafe-only Japanese strings, starting with `Global.ITEM_NAME`.
7. Re-check that all cafe-only data arrays and split-init structure remain intact.
8. Run static verification before any runtime testing.

## Verification Plan

### Automated / Static Checks

- Confirm item-table parity:
  - `Count Of(Global.ITEM_NAME)` matches `cafe_en.txt` and `cafe_kr.txt`
  - the Japanese table still has 398 entries
- Confirm split-init integrity:
  - `Call Subroutine(dataInit2_1);`
  - `Call Subroutine(dataInit2_2);`
  - no missing or duplicated cafe-only init tables
- Search for stale non-Japanese UI strings in `cafe_jp.txt`:
  - Korean UI remnants
  - English UI remnants
  - exceptions only where intentionally preserved
- Compare cafe-only structural arrays against the chosen cafe base to ensure there is no accidental data drift.
- Verify that the translated `Global.ITEM_NAME` table is still index-aligned with the existing cafe logic.

### Manual Verification

- Practice mode:
  - Japanese prompts display correctly
  - starter item naming matches the intended Japanese table
- Item flow:
  - item/world text uses the new Japanese item names
  - shop/perk/knife prompts remain cafe-correct
- Stage flow:
  - stage names, mode labels, and reservation alerts render in Japanese
  - no restaurant-only labels leak into cafe gameplay
- Init integrity:
  - game boot succeeds with the preserved split init structure
  - cafe-only systems such as ice handling remain intact
