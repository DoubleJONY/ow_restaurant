# gc_kr.txt Change Summary

Date: 2026-05-31

## Summary

Ported the cafe follow-up/system patch set to `gc_kr.txt` while keeping Cook International data arrays and utility-item indexes.

## Main Changes

- Updated visible version strings from `v260212` to `v260531`.
- Expanded mode handling to six modes:
  - practice
  - casual dining
  - fine dining
  - star bistro
  - mastercook challenge
  - head chef challenge
- Added the newer 19-table routing model and customer support for Jetpack Cat, Reinhardt, and Junker Queen.
- Added missing shared subroutines:
  - `gameSummaryTP`
  - `validateServe`
  - `changeHero`
  - `stageFail`
- Replaced repeated stage-fail handling with the shared `stageFail` subroutine.
- Added Jetpack Cat double-jump exclusion.
- Added practice-mode customer injection logic for Jetpack Cat and Mauga/Roadhog/Reinhardt.
- Updated direct serving, serve-fail, call-customer, serving-ball, scoreboard, and merchant flow to the newer shared behavior.
- Kept `ADDITIONAL_MATERIAL_LIST` LifeWeaver-driven only; no stage-specific additional-material spawning was added.

## Cook International Adjustments

- Preserved `gc_kr.txt` food/menu/fridge/hazard/weaver/additional-material data.
- Preserved Cook International utility IDs:
  - perks: `8, 9, 11, 12, 15, 16, 17`
  - foot perks: `10, 13, 14`
  - tips/money: `18`
- Removed cafe-only tool/perk `351` from generated-item pools.
- Changed copied cafe UI text back to Cook International:
  - `레스토랑 - 쿡제요리`
  - `튀김기`, `솥`, `그릴`, `팬`

## Verification

- Confirmed no duplicate `rule("...")` names remain.
- Confirmed no `v260212` remains.
- Confirmed no cafe-only `제빙기`, `냉각총`, `ICE_NEEDED`, `ICE_RESULT`, `MELT_LIST`, or `hintText` references remain.
- Confirmed `351` remains only in Cook International food/data arrays, not as a generated perk/tool.
