# kr_deluxe 단일 파일 통합 계획

> 상태 메모(2026-08-28): 이 문서는 최초 3종 통합 설계 기록이다. 현재 구현 기준은 `20260828_worklog_and_runtime_switch_plan.md`와 `validation_report.md`를 우선한다. 아래의 GC 싱크대/물 항목은 N3 전용 기능으로 판명되어 현재 3종 Deluxe 범위에서 폐기됐다. N3를 네 번째 에디션으로 검토할 때 별도 재설계한다.

## 1. 기본 원칙

`kr_deluxe.ow`는 ko 로직을 공통 런타임으로 사용한다. ORG, CAFE, GC 데이터는 동시에 글로벌 배열에 보관하지 않고, 시작 시 방장이 선택한 한 에디션의 데이터만 동일한 글로벌 변수에 로드한다.

일반 음식 코드는 에디션마다 다른 의미를 가질 수 있다. 한 게임에서는 에디션을 변경하지 않으므로 충돌하지 않는다. 공통 런타임에서 직접 참조하는 칼·도구·돈 코드 `0..20`만 완전히 통일한다.

원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow`는 읽기 전용 기준 자료로 사용한다.

## 2. 시작 흐름 재구성

현재 `Global: Setting`은 번역용 `Global.tx` 초기화 직후 `dataInit`, `dataInit2`를 호출한다. 이 호출보다 먼저 에디션을 확정해야 한다.

새 순서는 다음과 같다.

1. 공통 Workshop 설정과 `Global.tx` 초기화
2. 방장용 에디션 선택 HUD 표시
3. ORG/CAFE/GC 순환 및 확정
4. 선택값 잠금
5. `Call Subroutine(dataInit)`
6. `Call Subroutine(dataInit2)`
7. 기존 공통 좌표·아이템 런타임·HUD 초기화 계속
8. 기존 `selectMode`로 stageMode 선택
9. `Call Subroutine(dataInit3)`
10. 게임 시작

에디션은 게임 중 변경할 수 없다. 재선택은 Workshop 재시작으로만 허용한다.

## 3. 서브루틴 구성

기존 호출 안정성을 위해 `dataInit`, `dataInit2`, `dataInit3` 이름과 ID는 유지하고 조건 디스패처로 바꾼다.

```text
dataInit  -> dataInit_org1  / dataInit_cafe1 / dataInit_gc1
dataInit2 -> dataInit_org2  / dataInit_cafe2 / dataInit_gc2
dataInit3 -> dataInit_org3  / dataInit_cafe3 / dataInit_gc3
```

`dataInit3`는 난이도 상승이나 스테이지 재구성 경로에서도 다시 호출되므로 모든 호출부를 개별 수정하지 않고 디스패처가 항상 같은 에디션을 선택하게 한다.

## 4. 글로벌 변수 제한 대응

ko 기반 파일은 글로벌 변수 ID `0..127`을 모두 선언하지만, ID 100 `itemPrevPosition`과 ID 105 `itemNormal`은 대입만 있고 읽기가 없는 write-only 변수였다. 두 대입을 제거하고 ID 100/105를 각각 `ICE_NEEDED`/`ICE_RESULT`로 재사용한다.

기존 `MELT_LIST` 슬롯은 `DELUXE_DATA` 컨테이너로 확장해 사용하고 있으나, 후속 최적화에서는 MELT 목록을 `ICE_RESULT`와 에디션별로 재사용하고 `DELUXE_DATA[0]`을 폐기한다.

```text
Global.stageMode[0] = edition: 0 ORG / 1 CAFE / 2 GC
Global.stageMode[1] = game mode: 0..5
DELUXE_DATA[1] = 선택 에디션의 활성 item perk 드랍 목록
DELUXE_DATA[2] = 선택 에디션의 런타임 설정
Global.ICE_NEEDED = CAFE 전용 냉각 요구치
Global.ICE_RESULT = ORG MELT 목록 / CAFE 냉각 결과
```

- 에디션 값은 `stageMode[0]`에 저장한다.
- ORG init은 `ICE_RESULT`에 24개 MELT 음식 목록을 할당한다.
- CAFE init1은 `ICE_NEEDED`와 냉각 결과용 `ICE_RESULT`를 할당한다.
- GC는 두 배열을 할당하지 않는다.
- 각 에디션 init3가 `DELUXE_DATA[1]`, `[2]`를 설정한다.
- 별도 init-ready 슬롯은 사용하지 않는다.

MELT 조회 다섯 곳은 기존 `stageMode[0] == 0` 조건 안에서 `Array Contains(Global.ICE_RESULT, ...)`를 사용한다. 제빙기와 냉각총의 `ICE_NEEDED`/결과 인덱싱은 이미 `stageMode[0] == 1` 조건 안에 있으므로 배열 형태가 에디션마다 달라도 교차 접근하지 않는다.

## 5. 데이터 변환 방식

### 5.1 슬롯만 이동하는 테이블

```text
ITEM_NAME
ITEM_COLOR
ITEM_SCORE
CUTTING_NEEDED
GRILLING_NEEDED
FRYING_NEEDED
POT_TIME
PAN_NEEDED
CAFE ICE_NEEDED
```

```text
newTable[M(oldIndex)] = oldTable[oldIndex]
```

### 5.2 슬롯과 내부 itemCode를 모두 변환하는 테이블

```text
CUTTING_RESULT
GRILLING_RESULT
FRYING_RESULT
POT_RESULT
PAN_RESULT
IMPACT_RESULT
ADDITIONAL_MATERIAL_LIST
CAFE ICE_RESULT
```

```text
newTable[M(oldIndex)] = recursivelyMapItemCodes(oldTable[oldIndex])
```

중첩 `Array(a, b)`는 배열 모양과 원소 순서를 유지한다. indexed patch는 좌변 슬롯과 우변 itemCode를 모두 변환한다.

### 5.3 itemCode 값 목록

다음은 목록 순서를 보존하고 itemCode 값만 변환한다.

```text
MENU_LIST
HAZARD_MENU_LIST
FRIDGE_LIST
WEAVER_MENU_LIST
ORG MELT_LIST
KNIFE
PERK_LIST
시작 아이템
상점/업그레이드/연습 드랍 목록
튜토리얼 loadingMenu
createItemData[2] 리터럴 및 선택 배열
```

`STAGE_CODE`, `CUSTOMER_LIST`, 좌표, 점수, upgrade opcode는 itemCode가 아니므로 문맥 매니페스트 없이 숫자를 변경하지 않는다.

### 5.4 문자열 압축

현재 적용된 `Custom String` + `String Split` + `Mapped Array` 방식을 유지한다.

- 기존 문자열을 논리 배열로 복원한다.
- 매핑과 중첩 결과 변환을 적용한다.
- 각 문자열 조각을 약 90자 이하로 다시 생성한다.
- placeholder와 indexed patch를 이용해 혼합 배열의 런타임 형태를 보존한다.

## 6. 선택된 데이터만 로드

### ORG

- 최종 ITEM 길이 476
- 보존식 박스와 기존 `420..431` 보존식 결과 아이템 유지
- 냉각총은 ITEM 데이터 레코드만 존재
- MELT_LIST 할당
- ICE 배열 미할당

### CAFE

- 최종 ITEM 길이 399
- 냉각총과 보존식 박스 ITEM 데이터 레코드 존재
- ICE_NEEDED/ICE_RESULT 실제 데이터 할당
- MELT_LIST 미할당
- 보존식 박스 전용 결과 아이템은 추가하지 않음

### GC

- 최종 ITEM 길이 464
- 보존식 박스와 냉각총 ITEM 데이터 레코드 존재
- MELT_LIST와 ICE 배열 모두 미할당
- GC 자체 음식·레시피·메뉴 데이터만 로드

비활성 도구의 ITEM 레코드는 이름, 색, 점수와 중립적인 처리값을 가지지만 정상 드랍 목록에는 포함되지 않는다.

## 7. 공통 로직과 에디션 전용 로직

### 공통

- ko의 최신 일반 런타임 로직을 기준으로 사용
- 칼, 공통 perk, 서빙볼, `$100`, 조리, 주문, 서빙, 저장소
- `KNIFE`와 `PERK_LIST` ordinal 통일

### ORG 전용

```text
edition == ORG && itemPerk == 7
```

- 보존식 박스 사용
- stage별 `420..431` 아이템 생성
- MELT_LIST 기반 despawn 처리

### CAFE 전용

```text
edition == CAFE && itemPerk == 8
```

- 냉각총 secondary-fire 로직
- itemStatus 5 냉각 처리
- ICE_NEEDED/ICE_RESULT 조회
- 제빙기 위치, 표시, 상호작용, 효과

모든 ICE 조회는 CAFE 조건 안쪽에서만 실행한다.

### GC 전용

```text
edition == GC
```

- 싱크대 근처 안내 HUD
- 싱크대/물 아이템 상호작용
- GC 데이터에서 매핑된 물 itemCode 사용
- 관련 좌표·효과·제거 경로

## 8. 드랍과 노출 분기

전체 `PERK_LIST`는 장비 판별용으로 고정하고, 실제 무작위 지급은 `DELUXE_DATA[2]`의 활성 목록을 사용한다.

다음 경로를 전부 전환한다.

- 시작 아이템 3개
- 무료 아이템 NPC
- `Random Value In Array(Global.PERK_LIST...)`
- Ramattra 팁/보상
- 일반·가중치 업그레이드 풀
- 연습모드 상점
- 초기 상점 전시 및 재생성
- 도구 복제 제외 목록

도구 복제 제외 목록은 공통 코드 `1..20`을 기준으로 통일한다.

## 9. 연습모드와 튜토리얼 경계

- 연습모드의 stage 인덱스, HUD 문구와 상태 머신은 `ko`를 전 에디션의 공통 규격으로 사용한다.
- `stage == 0`은 모든 에디션에서 튜토리얼 자리로 유지하며 CAFE/GC라고 인덱스를 당기거나 별도 HUD 분기를 만들지 않는다.
- ORG판 `CUSTOMER_LIST`의 추가 `Array(Hero(Soldier: 76), Hero(Soldier: 76))` 항목은 이 공통 튜토리얼 인덱스를 유지하기 위한 정상 항목이다.
- CAFE와 GC의 현재 목록이 한 항목 짧은 이유는 튜토리얼 콘텐츠가 아직 이식되지 않았기 때문이며, 의도적으로 사용하지 않는 슬롯이 아니다.
- 현재 코드의 비ORG 시작 시 `stage = 1` 강제, 모드 순환 시 `stage 0` 건너뛰기, 튜토리얼 서브루틴의 비ORG `Abort`는 미이식 기간의 임시 우회로 분류한다.
- CAFE/GC 튜토리얼을 추가할 때 위 임시 분기를 함께 제거하고, 선택 에디션의 `MENU_LIST`, `STAGE_CODE`, `FRIDGE_LIST`에 맞는 튜토리얼 데이터만 연결한다.
- 최종 구조에는 튜토리얼 진입 여부를 결정하는 에디션 분기를 두지 않는다.

## 10. 구현 순서와 게이트

### Phase A: 매니페스트와 변환기

- semantic item catalog 작성
- 세 파일의 old-to-new 매핑과 역매핑 작성
- itemCode-bearing field 스키마 작성
- 하드코딩 site 목록 작성
- 원본 데이터와 RAW 의미 스냅숏 생성

### Phase B: 데이터 후보 생성

- 9개 init 서브루틴을 임시 후보로 생성
- 각 에디션 데이터를 독립 로드한 것으로 간주해 의미 동치 검사
- 원본 ITEM/조리/메뉴/레시피 의미와 비교

### Phase C: element feasibility

조건 분기는 실행만 막고 소스 element는 줄이지 않으므로, 3종 데이터 삽입 직후 Workshop import를 먼저 확인한다.

제한 초과 시:

- 완전히 동일한 공통 배열을 디스패처 공통부로 이동
- 공통 KNIFE/PERK/upgrade 설정 재사용
- Custom String 분할 재최적화
- 반복 indexed patch 생성 구조 공통화

### Phase D: 선택기와 디스패처

- 방장 전용 에디션 선택 HUD
- 선택값 잠금
- 기존 3개 init 디스패처
- 선택 에디션 표시

### Phase E: 전용 기능 포팅

- ORG 보존식 박스와 MELT
- CAFE 제빙기, 냉각총, ICE
- N3 싱크대와 물은 향후 네 번째 에디션 범위로 제외
- 활성 드랍과 상점 분기

### Phase F: 검증과 정리

- 정적 검증
- Workshop import
- 세 에디션 회귀 테스트
- 임시 진단 규칙 제거
- artifact 결과 문서 갱신

## 11. 검증 조건

### 정적

- 수정 파일은 `kr_deluxe.ow` 하나
- 원본 세 파일 변경 0건
- 공통 코드 `0..20`의 이름과 역할 일치
- ITEM 길이 ORG 476 / CAFE 399 / GC 464
- 모든 기존 아이템 레코드의 의미 보존
- RAW 행 수 ORG 306 / CAFE 255 / GC 282
- RAW decoded tuple의 전후 의미 일치
- 미분류 itemCode 문맥 0건
- `STAGE_CODE` 및 upgrade opcode 오변환 0건
- ORG init의 `ICE_NEEDED` 할당 0건 및 `ICE_RESULT` MELT 목록 일치
- CAFE init의 `ICE_NEEDED`/`ICE_RESULT` 냉각 매핑 일치
- GC init의 `ICE_NEEDED`/`ICE_RESULT` 할당 0건
- `DELUXE_DATA[0]` 대입·조회 0건
- 비활성 도구의 활성 드랍 목록 포함 0건

### 런타임 공통

- 방장만 에디션 선택 가능
- 선택 전 item data 접근 없음
- 선택된 init1/2/3만 실행
- stage 전환 후 dataInit3도 같은 에디션 유지
- 게임 도중 에디션 변경 불가
- 7종 칼, 공통 perk, 서빙볼, `$100` 정상
- 조리·혼합·메뉴·주문·서빙·저장소 정상

### ORG

- 보존식 박스 코드 19 드랍·장착·사용
- 냉각총 코드 20 미드랍 및 비활성
- 보존식 결과와 MELT 정상
- 기존 ko 튜토리얼 정상

### CAFE

- 냉각총 코드 20 드랍·장착·사용
- 보존식 박스 코드 19 미드랍 및 비활성
- 제빙기만 표시
- ICE_NEEDED/ICE_RESULT와 itemStatus 5 처리 정상
- 비CAFE 경로에서는 ICE 접근 없음

### GC

- 코드 19/20 모두 미드랍 및 비활성
- 싱크대 UI와 물 상호작용 정상
- GC 고유 메뉴와 레시피 유지

## 12. 완료 산출물

- 수정된 `kr_deluxe.ow`
- 실제 적용된 mapping TSV
- itemCode site 매니페스트
- 세 에디션 데이터 의미 비교 보고서
- RAW 레시피 비교 보고서
- Workshop element/import 결과
- 에디션별 런타임 체크리스트
- 최종 walkthrough와 알려진 후속 작업 목록


## 13. init3 손님 구성 공용화 추가 계획 (2026-08-28)

- 에디션별 `STAGE_CODE`는 메뉴·웨이브 구성이 다르므로 각 `dataInit_*3`에 유지한다.
- 손님 유형 구성인 `CUSTOMER_LIST`는 공용 데이터로 분리한다.
- 새 공용 서브루틴(가칭 `dataInit_customerCommon`)은 에디션 분기 없이 `CUSTOMER_LIST`를 한 번만 할당한다.
- `dataInit3` 디스패처는 선택 에디션의 `dataInit_org3/cafe3/gc3`를 호출한 뒤 공용 손님 구성 서브루틴을 한 번 호출한다.
- 현재 CAFE와 GC의 `CUSTOMER_LIST`는 동일하고, ORG에는 튜토리얼 인덱스를 위한 `Array(Hero(Soldier: 76), Hero(Soldier: 76))` 한 항목이 더 있다.
- 공통 런타임이 `ko.ow` 기준이므로 이 항목을 포함한 ORG판 `CUSTOMER_LIST`를 공용 기준으로 사용한다.
- CAFE/GC에서 이 항목을 사용하지 않는 별도 분기를 만들지 않는다. 현재 튜토리얼 미이식 상태는 후속 콘텐츠 추가로 해결하고, stage 인덱스와 HUD는 처음부터 `ko` 규격을 유지한다.
- 현재 `dataInit3`의 나머지 대입인 `STAGE_CODE`, `DELUXE_DATA[1]`, `DELUXE_DATA[2]`는 모두 에디션별 값이므로 각 init3에 유지한다.
- `FRIDGE_LIST`, `MENU_LIST`, `HAZARD_MENU_LIST`, `WEAVER_MENU_LIST`, `STAGE_NAME`, `UPGRADE_NAME`은 현재 구조에서 init3가 아니라 init2에 있으며 세 에디션 값이 모두 다르므로 공용화하지 않는다.
- 예상 절감량은 중복 `CUSTOMER_LIST` 두 사본 제거 기준 약 1,650~1,750 elements이며, 공용 rule과 호출 action 비용을 반영한 순절감 추정치다.
