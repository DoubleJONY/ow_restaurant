# en_deluxe.ow 구현 계획

## 1. 기준 파일과 권한

| 역할 | 파일 | 사용 범위 |
|---|---|---|
| 코드 기준 | `kr_deluxe.ow` | 전체 코드 뼈대와 숫자 데이터 |
| ORG 영문 | `en.ow` | 공통 UI, ORG 이름, ORG 점수, ORG STAGE_CODE 순서 |
| CAFE 영문 | `cafe_en.ow` | CAFE 이름과 설비 문구, CAFE 점수 |
| GC 영문 | `gc_en.ow` | GC 이름과 점수, 비교 가능한 STAGE_CODE 차이 |
| 번역 보조 | `.codex/artifact/20260601_cafe_en_translation_overlay/` | 문맥 매핑과 기존 용어 검증 |

`ko.ow`, `cafe_kr.ow`, `gc_kr.ow`, 세 영문판과 `kr_deluxe.ow`는 읽기 전용으로 취급한다. 새 생성기와 `en_deluxe.ow`만 수정한다.

## 2. 현재 조사 결과

### Custom String 현황

| 파일 | Custom String 호출 | 고유 문자열 | 한글 포함 호출 |
|---|---:|---:|---:|
| `kr_deluxe.ow` | 1,546 | 1,072 | 459 |
| `en.ow` | 767 | 530 | 2 |
| `cafe_en.ow` | 696 | 465 | 0 |
| `gc_en.ow` | 678 | 458 | 3 |

영문판에 남은 한글은 BattleTag와 한국어판 안내처럼 의도된 고유 문자열을 포함한다. 이를 자동으로 미번역 오류로 판단하지 않고 별도 allowlist로 관리한다.

### 영어 아이템 이름 원본 수

| 에디션 | KR 원본 | EN 원본 | Deluxe 최종 |
|---|---:|---:|---:|
| ORG | 475 | 475 | 476 |
| CAFE | 398 | 398 | 399 |
| GC | 462 | 462 | 464 |

세 영문판의 `STAGE_NAME`은 각각 12개, `UPGRADE_NAME`은 각각 10개다.

## 3. 생성기 설계

### 3.1 기본 흐름

1. `build_kr_deluxe.py`의 현재 산출물을 메모리에서 생성한다.
2. 영문 소스 3개를 파싱해 로케일 데이터 모델을 만든다.
3. KR Deluxe의 숫자 데이터와 공통 인덱스 매핑을 유지한 채 영문 이름 배열을 재구축한다.
4. 문맥 기반 문자열 overlay를 적용한다.
5. 영문 `totalScore`와 승인된 `STAGE_CODE` 차이를 적용한다.
6. 검증 후 `en_deluxe.ow`와 기계 판독 보고서를 출력한다.

영문 개별판을 코드 베이스로 사용하지 않는다. 특히 구형 4모드인 `gc_en.ow`의 rule이나 init 구조를 복사하지 않는다.

### 3.2 권장 스크립트

- `scripts/en_deluxe/build_en_deluxe.py`
  - KR Deluxe 산출물 생성 호출
  - 런타임 문자열 overlay
  - `totalScore`와 STAGE_CODE locale patch
  - 최종 검증 및 출력
- `scripts/en_deluxe/build_en_deluxe_data.py`
  - 영문 `ITEM_NAME`, `STAGE_NAME`, `UPGRADE_NAME` 추출
  - 공통 아이템 인덱스 remap
  - 영문 직렬화 payload 생성과 왕복 검증

필요하면 두 기능을 한 스크립트에 합칠 수 있지만, 숫자 데이터와 일반 UI 문자열 검증은 분리해서 보고한다.

## 4. 영문 데이터 재구축

### 4.1 ITEM_NAME

영문판의 원본 위치를 한국판과 같은 에디션 내부 item code로 간주하기 전에 다음을 검증한다.

- 원본 item 수 일치
- 숫자 per-item 테이블의 구조적 일치
- 알려진 영문판 고유 차이가 이름 순서를 변경하지 않았는지 확인

검증 후 KR Deluxe의 `build_mapping()` 결과를 영문 이름에도 동일하게 적용한다.

추가 레코드:

- ORG 코드 20: `cafe_en.ow`의 냉각총 이름 donor
- CAFE 코드 19: `en.ow`의 보존식 박스 이름 donor
- GC 코드 19: `en.ow`의 보존식 박스 이름 donor
- GC 코드 20: `cafe_en.ow`의 냉각총 이름 donor

최종 배열을 기존 90자 안팎의 `Custom String` chain + `String Split` 형식으로 직렬화한다. 번역된 이름의 길이 때문에 세그먼트 수가 증가할 수 있으므로 최대 문자열 길이와 payload 왕복을 검증한다.

### 4.2 STAGE_NAME / UPGRADE_NAME

- 각 에디션 영문 원본의 배열을 사용한다.
- 배열 순서와 개수만 가져오며 주변 init 구조는 Deluxe를 유지한다.
- CAFE의 `Ice Maker`, `Oven` 등 설비 명칭은 `cafe_en.ow`의 기존 용어를 우선한다.

### 4.3 가져오지 않는 데이터

- `ITEM_COLOR`, `ITEM_SCORE`
- 모든 조리 필요치와 결과표
- `RAW_MIX`, `RAW_RESULT`
- 메뉴·냉장고·위험·Weaver 배열
- 활성 드랍과 `DELUXE_DATA`
- CAFE ICE 숫자 배열

위 값은 언어와 무관하며 KR Deluxe의 최신 통합 데이터를 그대로 사용한다.

## 5. totalScore

최종 18행은 다음 순서로 평면 배치한다.

### ORG

1. `0 / Practice`
2. `5506 / SizzlingGunz`
3. `4082 / SizzlingGunz`
4. `4555 / Carrion`
5. `7759 / Carrion`
6. `0 / None`

### CAFE

1. `0 / Practice`
2. `0 / None`
3. `0 / None`
4. `0 / None`
5. `0 / None`
6. `0 / None`

### GC

1. `0 / Practice`
2. `0 / None`
3. `0 / None`
4. `0 / None`
5. `0 / None`
6. `0 / None`

대입은 KR Deluxe와 동일하게 다음 형태를 사용한다.

```text
Global.totalScore = Array Slice(Array(<18 rows>), Global.stageMode[0] * 6, 6);
```

위치는 최초 `selectMode` 반환 뒤, `Global.difficulty` 대입 전이다. 연습모드의 에디션 전환용 `dataInit`에는 넣지 않는다.

## 6. Custom String 처리

### 6.1 문맥 키

각 `Custom String`은 다음 필드를 가진 inventory 행으로 만든다.

- rule 제목 또는 subroutine 이름
- rule 내 statement ordinal
- 호출 이름
- 인수 경로
- 원문
- placeholder 목록과 순서
- 주변 비문자열 표현식 fingerprint
- 에디션 조건
- 분류와 번역 출처

같은 한국어 원문이라도 문맥 키가 다르면 별도 항목으로 취급한다.

### 6.2 분류

| 분류 | 처리 |
|---|---|
| 공통 사용자 문구 | `en.ow` 문맥 매칭 |
| CAFE 전용 사용자 문구 | `cafe_en.ow` 문맥 매칭 |
| GC 전용 사용자 문구 | `gc_en.ow` 문맥 매칭 |
| Deluxe 신규 사용자 문구 | 수동 번역표 |
| ITEM/STAGE/UPGRADE 이름 | 데이터 재구축 경로 |
| 숫자·Hero·DELUXE payload | 번역하지 않음 |
| URL·Workshop code·버전 | locale metadata로 명시적 관리 |
| BattleTag·고유명사 | allowlist 검토 후 유지 또는 표기 결정 |

### 6.3 번역 우선순위

1. 같은 에디션 현재 영문판의 동일 문맥
2. `en.ow`의 공통 런타임 용어
3. 기존 cafe overlay의 context map
4. 기존 영문판에서 같은 placeholder 구조를 가진 확정 용어
5. Deluxe 신규 수동 번역

전역 `str.replace()` 방식의 한국어→영어 사전은 최종 적용 수단으로 사용하지 않는다.

### 6.4 신규 문구

자동 매칭되지 않는 다음 범주는 직접 번역한다.

- 에디션 선택 HUD와 입력 안내
- ORG/CAFE/GC 통합 소개
- Deluxe 로딩 및 에디션 전환 안내
- 통합판 패치노트
- 에디션 분기로 합성된 그릴/오븐·제빙기 문장

수동 번역은 `deluxe_manual_translations.tsv`에 문맥 키와 함께 기록하고 생성기가 해당 파일을 읽어 적용하도록 한다.

## 7. STAGE_CODE locale delta

### ORG

- KR/EN 모두 6모드이며 구조가 같다.
- 모드 인덱스 1에서 6개 leaf 순서가 다르다.
- 해당 모드의 영문 배열 순서를 사용한다.

### CAFE

- 6모드 전체가 현재 KR/EN 간 동일하다.
- 별도 patch를 만들지 않는다.

### GC

- `gc_en.ow`는 4모드, KR Deluxe는 6모드다.
- 구조가 같은 모드 0~2만 비교 대상으로 사용한다.
- 확인된 `[2][10][0]`의 `8 → 6` 차이를 영문 delta로 기록한다.
- 모드 3은 KR Deluxe의 최신 동적 `Append To Array` 구조를 유지한다.
- 모드 4·5는 KR Deluxe 데이터를 유지한다.

생성 후 `STAGE_CODE` 정규화 비교에서 manifest에 기록된 경로 외 차이가 있으면 실패한다.

## 8. 로케일 메타데이터

다음 문자열은 일반 자동 번역에서 제외하고 명시적으로 확정한다.

- 상단 HUD의 영문판 Workshop code
- `ow-restaurant.com/en`
- 제작자·기여자 표기
- 한국어/일본어판 코드 안내
- 버전 문자열 `v260829`

새 `en_deluxe` Workshop code가 아직 없으면 기존 영문 코드를 임시 유지하거나 code 없는 표기로 두되, 임의의 새 코드를 만들지 않는다.

## 9. Element 예산

직렬화 후, `totalScore` 보완 전 KR Deluxe 실측은 31,925 / 32,768이었다. `totalScore` 패치 후 현재 KR 수치는 아직 재측정되지 않았다.

영문 이름은 한국어보다 길어 `ITEM_NAME`의 `Custom String` 세그먼트가 증가할 수 있다. 따라서 다음 순서로 예산을 확인한다.

1. 현재 KR Deluxe 재측정
2. 영어 ITEM_NAME 직렬화 직후 생성된 Custom String 세그먼트 증감 기록
3. 전체 영문 overlay 후 Workshop import
4. 32,768 초과 시 구조용 문자열 중복과 영문 payload 패킹부터 최적화

일반 UI 번역은 기존 `Custom String`의 내용만 바꾸고 새로운 중첩 문자열을 만들지 않는다.

## 10. 자동 검증

### 구조

- KR/EN rule 수 동일
- global 128개 및 ID 동일
- subroutine 수와 ID 동일
- 모든 event/condition/action 구조 동일
- locale 허용 영역 마스킹 후 정규화 0-diff

### 데이터

- `ITEM_NAME`: 476 / 399 / 464
- `STAGE_NAME`: 에디션별 12
- `UPGRADE_NAME`: 에디션별 10
- `totalScore`: 18행 및 에디션별 slice 6행
- 영어 ITEM_NAME remap과 donor 삽입 왕복 일치
- `STAGE_CODE` 허용 delta 외 차이 0건

### 문자열

- placeholder multiset 일치(영문 어순에 따른 인덱스 순서 변경은 허용)
- 중첩 Custom String 인수 수 일치
- `\r\n` escape 유지
- 미해결 사용자 문자열 0건
- 미허용 한글 0건
- URL과 언어 경로 `/en`
- 한국판 점수 값과 기록 보유자 유입 0건

### 재현성

- 데이터 빌더 `--check`
- 전체 빌더 `--check`
- 반복 생성 SHA-256 동일
- `git diff --check`

## 11. 수동 검증

각 에디션에서 최소 다음을 확인한다.

- 최초 선택 HUD와 모드 선택 HUD
- 상단 점수/최고점 HUD
- 스테이지 시작·완료·실패 메시지
- 스테이지와 업그레이드 이름
- 아이템 이름과 장비 HUD
- ORG 보존식 박스
- CAFE 제빙기, 냉각총, Oven 표기
- GC 스테이지 순서
- 연습모드 에디션 전환 후 메뉴와 아이템 이름

## 12. 산출물

- `en_deluxe.ow`
- `scripts/en_deluxe/build_en_deluxe.py`
- 영문 데이터 빌더 또는 locale 모듈
- `build/en_deluxe/translation_inventory.tsv`
- `build/en_deluxe/resolved_translation_map.tsv`
- `build/en_deluxe/deluxe_manual_translations.tsv`
- `build/en_deluxe/unresolved_strings.tsv`
- `build/en_deluxe/stage_code_delta.tsv`
- `build/en_deluxe/validation.json`
- `.codex/artifact/20260829_en_deluxe_creation_plan/validation_report.md`
- `.codex/artifact/20260829_en_deluxe_creation_plan/walkthrough.md`

## 13. 실행 순서 요약

1. KR Deluxe 기준선과 element 재측정
2. 영문 로케일 데이터 파서 작성
3. ITEM/STAGE/UPGRADE 이름과 totalScore 구성
4. STAGE_CODE locale delta 적용
5. 전체 Custom String inventory 생성
6. 기존 영문판 문맥 자동 매칭
7. Deluxe 신규 문자열 수동 번역
8. 구조·placeholder·미번역 검증
9. `en_deluxe.ow` 생성
10. Workshop import와 에디션별 회귀 테스트
