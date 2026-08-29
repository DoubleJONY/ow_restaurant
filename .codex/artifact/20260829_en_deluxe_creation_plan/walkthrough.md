# en_deluxe 제작 내역

## 결과

`kr_deluxe.ow`의 최신 통합 로직을 그대로 유지하는 `en_deluxe.ow`를 생성했다. 영문 개별판은 코드 베이스로 복사하지 않고, 로케일 문자열과 승인된 데이터만 읽는 생성기를 추가했다.

## 구현

- `scripts/en_deluxe/build_en_deluxe.py`
  - 최신 KR Deluxe 생성 결과를 기준으로 사용
  - 세 KR/EN 원본의 per-item 숫자 테이블 일치 검증
  - 영문 ITEM/STAGE/UPGRADE 이름 추출, 공통 인덱스 remap 및 재직렬화
  - 세 영문판의 `totalScore` 추출과 18행 slice 구성
  - ORG/GC의 승인된 STAGE_CODE leaf만 patch
  - 동일 구조 문맥 번역, 기존 Cafe overlay 보조 매핑, 수동 번역 overlay
  - 미번역·placeholder·색상 markup·구조 fingerprint 검증
- `scripts/en_deluxe/manual_translations.tsv`
  - Deluxe 신규 에디션 선택 UI
  - Knife/Perk/Foot 설명
  - 통합 패치노트와 URL
  - 구조가 바뀌어 자동 문맥 매칭이 불가능한 튜토리얼/레시피
  - `Equip Item` 오타 수정 등 명시 override
- `scripts/en_deluxe/output_overrides.tsv`
  - 현재 `en_deluxe.ow`에서 수동 확정한 60개 문자열을 rule/ordinal 기준으로 고정
  - 칼·도구·신발 설명, 고객 밈, 에디션명, HUD 공백 및 문장부호 변경을 재생성 시 보존
  - 기반 생성 문구가 바뀌면 조용히 덮어쓰지 않고 stale override 오류로 중단
- `scripts/en_deluxe/release_code_overrides.jsonl`
  - 최종 릴리즈 OW에서 수동 확정한 코드 및 구조 변경 15건 보존
  - 이전 생성 조각이 정확히 한 번 일치할 때만 적용하여 예상 밖의 코드에 잘못 덮어쓰지 않음
- `scripts/kr_deluxe/build_kr_deluxe.py`
  - 현재 `kr_deluxe.ow`의 CAFE/GC 튜토리얼 `currentCustomer` 초기화 한 줄을 생성기에 동기화

## 번역 정책

- 공통 런타임 용어와 모드명은 기본적으로 `en.ow`를 canonical로 사용했다.
- 에디션명은 `Assorted Sashimi Rice Bowl!`, `Cafe & Dessert`, `World Cuisine`으로 통일했다.
- 신규 영문 Workshop code가 없으므로 상단 메타데이터에는 기존 ORG 영문 코드 `HTNZ3`를 임시 유지했다.
- `Eqiup Item`은 `Equip Item`으로 수정했다.
- `썬 파 + 간장 소스`는 ITEM_NAME 의미에 맞춰 `Sliced Green Onion + Sweet Soy Sauce`로 번역해 기존 EN의 `Soy Sauce` 오역을 수정했다.
- 작성자 인증 비교용 `Custom String("변기클라우드")`는 로직 보존을 위해 번역하지 않았다.
- 같은 rule 안의 문자열 수만 같은 경우에는 자동 대응하지 않는다. 실제로 만두/버거 도움말 순서가 KR/EN에서 달라 잘못 대응될 수 있어, 구조가 완전히 같은 문맥만 자동 적용하고 나머지는 수동표로 고정했다.

## 생성 보고서

- `build/en_deluxe/translation_inventory.tsv`: 전체 1,706개 위치와 번역 출처
- `build/en_deluxe/resolved_translation_map.tsv`: 번역된 332개 위치
- `build/en_deluxe/unresolved_strings.tsv`: 헤더만 존재하며 미해결 0건
- `build/en_deluxe/stage_code_delta.tsv`: 허용된 7개 leaf 차이
- `build/en_deluxe/validation.json`: 데이터 수, 구조 해시, 문자열 검증 및 산출물 해시

## 최종 릴리즈

사용자가 최종 `en_deluxe.ow`의 Workshop import와 릴리즈를 완료했다. 실측 element 수는
`32,716 / 32,768`이며 52개 여유가 있다. 현재 OW는 생성기, 번역 override 및 릴리즈 코드 override에서 완전히 재현된다.
