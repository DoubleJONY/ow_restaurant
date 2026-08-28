# kr_deluxe 통합 사전 작업

## 목표

`ko.ow`를 기반으로 한 단일 결과물 `kr_deluxe.ow`에 ORG, CAFE, GC 세 에디션의 데이터와 필요한 전용 로직을 통합한다.

게임 시작 시 방장이 에디션 하나를 선택하고, 단일 `dataInit` 디스패처가 선택된 에디션의 1/2/3 데이터를 순서대로 로드한다. 원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow`는 수정하지 않는다.

## 확정 결정

- 실행 결과물은 `kr_deluxe.ow` 하나이며, 재생성 일치를 위해 생성 스크립트와 build 산출물도 함께 갱신한다.
- `kr_deluxe.ow`는 `ko.ow` 기반의 통합 결과물이며 생성 스크립트로 결정론적으로 재생성한다.
- 최초 에디션 선택은 아이템 데이터 초기화보다 먼저 완료한다. 연습모드의 에디션 메뉴에서는 stage 5 진입 전 선택 에디션을 바꾸고 `dataInit`을 다시 호출할 수 있다.
- 기존 최상위 `dataInit`, `dataInit2`, `dataInit3`는 하나의 `dataInit` 디스패처로 병합한다.
- 에디션별 실제 데이터는 다음 9개 서브루틴으로 분리한다.
  - `dataInit_org1`, `dataInit_org2`, `dataInit_org3`
  - `dataInit_cafe1`, `dataInit_cafe2`, `dataInit_cafe3`
  - `dataInit_gc1`, `dataInit_gc2`, `dataInit_gc3`
- 세 데이터 세트의 공통 아이템 코드는 `0..20`으로 통일한다.
- 코드 `19`는 보존식 박스, 코드 `20`은 냉각총이다.
- 보존식 박스는 ORG에서만 드랍·활성화한다.
- 냉각총과 제빙기는 CAFE에서만 드랍·노출·활성화한다.
- GC에서는 보존식 박스와 냉각총을 드랍하거나 활성화하지 않는다.
- 두 도구의 ITEM 데이터 레코드는 세 에디션의 데이터에 모두 존재한다.
- `ICE_NEEDED`는 CAFE 초기화에만 포함한다.
- `ICE_RESULT`는 에디션별 전용 배열 슬롯으로 재사용한다. ORG에서는 MELT 목록, CAFE에서는 제빙 결과 매핑을 할당하고 GC에서는 할당하지 않는다.
- MELT 디스폰 판정은 기존 ORG 조건을 유지한 채 `DELUXE_DATA[0]` 대신 `ICE_RESULT`를 조회한다.
- 싱크대 물 생성은 GC 기능이 아니라 N3 전용 기능이다. 현재 3종 Deluxe에는 넣지 않고, N3를 네 번째 에디션으로 통합할 때 함께 이식한다.
- 장비 판별용 전체 `PERK_LIST`와 실제 랜덤 드랍용 활성 목록을 분리한다.
- stage 인덱스, HUD와 `CUSTOMER_LIST` 구조는 `ko`를 공통 규격으로 유지한다. 기존 CAFE/GC stage 0 우회와 `setHint`의 비ORG Abort는 즉시 제거하고, `setHint`에 에디션 분기를 추가하되 CAFE/GC 본문은 비워둔다. 실제 CAFE/GC 튜토리얼 콘텐츠는 후속 작업에서 해당 빈 분기에 추가한다.

## 범위

- 공통 아이템 인덱스 설계 및 세 데이터 세트 변환
- `RAW_MIX`/`RAW_RESULT`, 결과 테이블, 메뉴, 하드코딩 itemCode 변환
- 방장 에디션 선택과 3단 초기화 디스패처
- ORG/CAFE/GC 전용 기능 조건 분기
- 에디션별 시작 아이템·상점·랜덤 드랍 목록 분기
- Workshop element 제한 및 글로벌 변수 제한 대응
- 자동 의미 동치 검증과 에디션별 런타임 회귀 검증
- 구현 및 검증 결과의 후속 artifact 기록

## 이번 artifact 상태

- [x] 목표와 단일 산출물 구조 확정
- [x] 공통 코드 `0..20` 확정
- [x] 파일별 최소 이동 매핑 확정
- [x] 9개 에디션 데이터 초기화와 단일 `dataInit` 디스패처 구조 확정
- [x] 전용 기능 활성 조건 확정
- [x] CAFE 전용 ICE 배열 정책 확정
- [x] 드랍 목록 분리 원칙 확정
- [x] 튜토리얼 후속 범위 확정
- [x] 변환 도구 및 매핑 매니페스트 작성
- [x] `kr_deluxe.ow` 핵심 통합 구현
- [x] 데이터/RAW/런타임 하드코드 정적 검증
- [x] GC 싱크대 물 생성 항목 제외(N3 전용 기능으로 범위 정정)
- [x] `dataInit3`의 ORG판 `CUSTOMER_LIST`를 공용 서브루틴으로 분리(튜토리얼 항목과 ko 인덱스/HUD 유지, 예상 순절감 약 1,650~1,750 elements)
- [x] MELT 목록을 ORG의 `ICE_RESULT`로 이동하고 `DELUXE_DATA[0]` 제거
- [x] CAFE/GC stage 0 우회와 `setHint` 비ORG Abort 제거, `setHint`에 ORG/CAFE/GC 분기 추가(CAFE/GC 본문은 빈 상태)
- [ ] CAFE/GC의 빈 `setHint` 분기에 실제 튜토리얼 콘텐츠 추가(후속 작업)
- [x] 연습모드 stage 5 에디션 선택 시 `dataInit` 세트 재로딩
- [ ] N3 네 번째 에디션 통합 가능성 검토(Elements 실제 측정 전까지 WIP, 이번 작업에서는 미이식)
- [ ] Workshop import 및 런타임 검증

## 구현 재개 결과 (2026-08-28)

- 에디션 선택을 기존 `selectMode`에 통합하고, 선택 확정 시 선택 에디션의 init을 다시 실행하도록 정리했다.
- 최상위 `dataInit`, `dataInit2`, `dataInit3`를 단일 `dataInit` 디스패처로 병합하고 실제 9개 에디션 init을 유지했다.
- 공통 칼·도구·돈 코드를 `0..20`으로 통일했다.
- ORG 476개, CAFE 399개, GC 464개 item table을 생성했다.
- RAW 조합 306/255/282행을 새 코드로 변환하고 문자열 기반 Mapped Array로 압축했다.
- 공통 phase2/phase3 문장을 단일 디스패처 또는 공용 고객 초기화로 끌어올려 세 사본의 중복 element를 제거했다.
- write-only 글로벌 ID 100/105의 사용처를 제거하고 `ICE_NEEDED`/`ICE_RESULT`로 재사용했다. `ICE_NEEDED`는 CAFE만, `ICE_RESULT`는 ORG MELT와 CAFE 제빙 결과가 에디션별로 사용한다.
- `DELUXE_DATA`는 `[1]` 활성 드랍, `[2]` 런타임 설정만 사용하며 `[0]` 대입·조회는 제거했다.
- ORG 보존식 박스, CAFE 제빙기·냉각총, 에디션별 드랍/시작/연습/업그레이드 pool 분기를 적용했다.
- cafe/gc의 stage 0 건너뛰기와 비ORG `setHint` 중단을 제거했다. `setHint`에 ORG/CAFE/GC 분기를 만들고 CAFE/GC는 빈 본문으로 두어 ko 기준 stage 인덱스/HUD를 공통화했다.
- 원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow` SHA-256이 작업 전 기준과 동일함을 확인했다.
- 상세 결과와 재현 명령은 `walkthrough.md`, 검증 수치는 `validation_report.md`에 기록했다.

## 후속 최적화 적용 결과 (2026-08-28)

- ORG판 `CUSTOMER_LIST` 한 사본을 공용 `dataInit_customerCommon`으로 이동하고 에디션별 init3의 세 사본을 제거했다.
- 생성기는 공용 고객 Rule을 포함한 10개 Rule을 만들며, ORG 원본과 정규화 표현식이 일치하는지 왕복 검증한다.
- 데이터 생성기와 전체 조립기는 LF/CRLF 입력을 내부 CRLF로 정규화하며, 전체 조립 결과와 검증 산출물을 결정론적으로 재생성한다.
- 원본의 scalar `Global.stageMode`가 생성 산출물에 남지 않도록 init3 생성 시 `Global.stageMode[1]`로 변환한다.
- ORG MELT 24개 목록은 `ICE_RESULT`에 할당하고 MELT 조회 다섯 곳의 ORG 조건을 유지했다.
- CAFE 제빙기·냉각총의 `ICE_RESULT` 인덱싱 두 곳은 기존 CAFE 조건 안에 유지했다.
- 외부 Workshop 도구와 인게임 런타임 검증은 요청에 따라 실행하지 않았다.

## 범위 최신화 (2026-08-28)

- `gc_en`의 독립 최신화는 하지 않는다. 기존 영문판은 향후 English Deluxe가 대체하며, 그때 필요한 아이템·현지화 배열만 가져온다.
- N3의 싱크대 물 생성은 향후 4종 Deluxe 후보 범위다. 개별 rule 약 98KB 제한은 init을 서브루틴으로 나누어 대응한다.
- 전체 Workshop 예산은 파일 바이트가 아니라 element 수로 관리한다. `ko.ow`의 혼합 배열 압축 전후 실측은 약 28,800개에서 27,700개대로, 1,000개 이상 절감된 것으로 기록한다.

## 수동 변경 동기화 (2026-08-28)

- 현재 `kr_deluxe.ow`의 수동 변경분을 `build_kr_deluxe.py`와 `build_deluxe_data.py`에 역반영했다.
- 에디션 선택 전 초기화를 지연하고, 선택 확정 및 연습모드 에디션 전환 시에만 단일 `dataInit`을 호출한다.
- 선택 HUD 5개 생성·ID 저장·삭제 순서, 에디션 표시명, 제작자/난이도 문구, 제빙기 라벨 재평가, 월드 에디션 라벨을 생성기에 고정했다.
- 연습모드 stage 5 메뉴는 내부 3개 에디션 전환과 외부 2개 코드 표시를 함께 지원하며, CAFE/GC의 연습 `STAGE_CODE` 슬롯도 6개로 맞췄다.
- 난이도 상승 시 에디션별 phase3만 다시 불러도 공통 고객/난이도 값이 빠지지 않도록 `dataInit_customerCommon`에 공통 scalar를 모으고 두 경로에서 호출한다.
- 후속 수동 변경으로 `storageData`를 String Split 기반 Mapped Array로 압축했다.
- 연습모드 에디션 전환 처리를 `otherMenu`, 공통 메뉴 재구성을 `menuInit` 서브루틴으로 분리했다.
- 에디션 전환 시 기존 아이템·솥·보관함 데이터를 초기화하고, `pot0`/`pot1` 재시작 전 종료 가드를 적용했다.
- 최신 조립 결과는 57 rules, 40 subroutines, 382,877 bytes이며 생성기 출력과 `kr_deluxe.ow`가 0-diff다.
- 최신 Workshop import 실측은 32,746 / 32,768 elements이며 남은 예산은 22 elements다.

## 고객·Deluxe 설정 직렬화 (2026-08-29)

- `STAGE_CODE` 직렬화는 랜덤 배열의 평가 순서와 절감 대비 복잡도를 고려해 이번 범위에서 보류했다.
- 공용 `CUSTOMER_LIST`의 고정 고객 행을 모드별 숫자 토큰 문자열로 직렬화했다.
- 고정 고객 행은 `RAW_MIX`를 `For Global Variable` 카운터로 재사용해 한 단계씩 복원하며, 21개 Hero 팔레트에서 실제 Hero 객체를 조회한다.
- 랜덤 Hero를 포함한 3개 행은 디코딩 후 원본 표현식으로 행 전체를 다시 대입해 기존 무작위 동작을 보존한다.
- `dataInit_org3`, `dataInit_cafe3`, `dataInit_gc3`의 `DELUXE_DATA[1]`, `[2]`를 문자열로 직렬화했다.
- phase2 조합표 생성 후 수명이 끝난 `RAW_RESULT`는 `DELUXE_DATA[2]` 복원 카운터로 사용한 뒤 `0..20` 문자열 lookup으로 바꾸고, `RAW_MIX`는 `[2]` 복원 결과 임시 배열과 `CUSTOMER_LIST` 복원 카운터로 재사용한다.
- `DELUXE_DATA[2]`의 `Null`은 토큰 `N`으로 저장하고 복원 루프에서 다시 `Null`로 변환한다.
- 기존 수동 결정인 `otherMenu`의 솥 정지·냉장고 목록 초기화와 `pot0`/`pot1` 시작 가드 제거를 전체 조립기에 동기화했다.
- 버전 문자열은 `v260829`로 갱신했다.
