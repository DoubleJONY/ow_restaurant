# kr_deluxe 통합 사전 작업

## 목표

`ko.ow`를 기반으로 한 단일 결과물 `kr_deluxe.ow`에 ORG, CAFE, GC 세 에디션의 데이터와 필요한 전용 로직을 통합한다.

게임 시작 시 방장이 에디션 하나를 선택하고, 선택된 에디션의 `dataInit` 1/2/3 데이터만 로드한다. 원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow`는 수정하지 않는다.

## 확정 결정

- 최종 수정 파일은 `kr_deluxe.ow` 하나다.
- 현재 작업 사본의 `kr_deluxe.ow`는 `ko.ow`와 바이트 단위로 동일하다.
- 에디션 선택은 아이템 데이터 초기화보다 먼저 완료하고 게임 중에는 변경하지 않는다.
- 기존 `dataInit`, `dataInit2`, `dataInit3`는 에디션 디스패처로 유지한다.
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
- `ICE_NEEDED`, `ICE_RESULT`의 실제 배열은 CAFE 초기화에만 포함한다. ORG/GC에는 빈 배열이나 길이 맞춤용 배열도 만들지 않는다.
- ORG의 `MELT_LIST`는 ORG 초기화에만 포함한다.
- GC 전용 싱크대/물 상호작용 로직은 GC에서만 활성화한다.
- 장비 판별용 전체 `PERK_LIST`와 실제 랜덤 드랍용 활성 목록을 분리한다.
- cafe/gc 전용 튜토리얼 콘텐츠는 이번 범위에 포함하지 않는다. ko의 튜토리얼 제어 로직을 공통 기반으로 유지하고 외전용 콘텐츠 연결은 후속 작업으로 남긴다.

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
- [x] 9개 데이터 초기화와 3개 디스패처 구조 확정
- [x] 전용 기능 활성 조건 확정
- [x] CAFE 전용 ICE 배열 정책 확정
- [x] 드랍 목록 분리 원칙 확정
- [x] 튜토리얼 후속 범위 확정
- [x] 변환 도구 및 매핑 매니페스트 작성
- [x] `kr_deluxe.ow` 핵심 통합 구현
- [x] 데이터/RAW/런타임 하드코드 정적 검증
- [ ] GC 싱크대 물 생성 기능 포팅(현재 `gc_kr.ow`에 원본 기능·물 아이템 레코드가 없어 보류)
- [ ] Workshop import 및 런타임 검증

## 구현 재개 결과 (2026-08-28)

- 방장 에디션 선택기와 init-ready barrier를 추가했다.
- `dataInit`, `dataInit2`, `dataInit3`를 디스패처로 바꾸고 실제 9개 에디션 init을 추가했다.
- 공통 칼·도구·돈 코드를 `0..20`으로 통일했다.
- ORG 476개, CAFE 399개, GC 464개 item table을 생성했다.
- RAW 조합 306/255/282행을 새 코드로 변환하고 문자열 기반 Mapped Array로 압축했다.
- 공통 init2/init3 문장을 디스패처로 끌어올려 세 사본의 중복 element를 제거했다.
- write-only 글로벌 ID 100/105의 사용처를 제거하고 `ICE_NEEDED`/`ICE_RESULT`로 재사용했으며, ICE 데이터는 CAFE init에서만 할당한다.
- ICE를 꺼낸 `DELUXE_DATA`의 나머지 슬롯은 `[0..4]`로 압축했다.
- ORG 보존식 박스, CAFE 제빙기·냉각총, 에디션별 드랍/시작/연습/업그레이드 pool 분기를 적용했다.
- cafe/gc의 미작성 튜토리얼은 ORG 튜토리얼 데이터를 잘못 참조하지 않도록 진입을 건너뛴다.
- 원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow` SHA-256이 작업 전 기준과 동일함을 확인했다.
- 상세 결과와 재현 명령은 `walkthrough.md`, 검증 수치는 `validation_report.md`에 기록했다.
