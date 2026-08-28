# kr_deluxe 정적 검증 보고서

## 파일 무결성

| 파일 | SHA-256 |
|---|---|
| `ko.ow` | `01AEFCE72D0250EFAEEDE44646759D977E832A134BA6F9EBED554BC58848E982` |
| `cafe_kr.ow` | `34378CEE5E2C5ECF836B44AE319A7A97EBB0FF92819D6BEB468149520C6C5BE9` |
| `gc_kr.ow` | `BA87EABCB98CB76CB1EF77BACE46C6DC8497CF3D0F16970A3A9EF7AFD865D290` |
| `kr_deluxe.ow` | `D346EACB4C09B0DCFA13E3A32EA546A1DCD5D339717EDE16224B8A03EE73984F` |

## 데이터 수치

| 에디션 | item 수 | RAW 행 | 최대 RAW operand | 최대 RAW result |
|---|---:|---:|---:|---:|
| ORG | 476 | 306 | 475 | 472 |
| CAFE | 399 | 255 | 398 | 397 |
| GC | 464 | 282 | 463 | 460 |

RAW 좌/우 operand와 result는 원본 행 순서로 왕복 검증했으며 모든 코드는 base-1000 범위 안이다.

## 구조 검증

- global variable ID: 정확히 `0..127`, ID 100 = `ICE_NEEDED`, ID 105 = `ICE_RESULT`, ID 126 = `DELUXE_DATA`
- subroutine ID: 정확히 `0..39`, ID 37 = `dataInit_customerCommon`, ID 38 = `menuInit`, ID 39 = `otherMenu`
- rule 수: 57
- 실제 edition init rule: 9, 공용 고객 init rule: 1
- `CUSTOMER_LIST` 대입: 공용 rule 1회, 에디션별 init3 0회
- CAFE ICE assignment: `Global.ICE_NEEDED`, `Global.ICE_RESULT` 각각 1회
- ORG MELT assignment: `Global.ICE_RESULT` 1회
- 삭제한 `itemPrevPosition`, `itemNormal` 선언·대입·참조: 0회
- `DELUXE_DATA[0]` 및 `[3]` 이상 대입·조회: 0회
- legacy `Global.MELT_LIST`: 0회
- 공통 MIX/KNIFE/PERK/upgrade 초기화: 단일 dispatcher에 각각 1사본
- 공통 고객/난이도 초기화: `dataInit_customerCommon`에 각각 1사본, 전체 초기화와 난이도 상승 경로에서 총 2회 호출
- 생성된 per-item 47개 테이블, 숫자 lookup 1,339칸, 메뉴 계열 13개 테이블 및 ORG 공용 `CUSTOMER_LIST` 재파싱 왕복 검사 통과
- 생성된 table용 `Custom String` 1,022개: 최대 85자, 90자 초과 0개
- `createItemData` assignment: 33곳, 세 번째 필드의 구 장비 코드 잔존 0곳
- 내부 `If/Else/While/For/End` 검사: 변경한 `setHint`, 단일 dataInit dispatcher, 공용 고객 rule 균형 통과
  - 원본부터 actions 끝을 암시적 `End`로 사용하는 기존 1곳은 수정 전후 동일한 잔여 스택 1개로 보존 확인
- CAFE 설비명: 월드 라벨·상태 HUD·강화 상점 모두 `오븐`, 나머지 에디션은 `그릴`로 분기 확인
  - 월드 라벨은 `Visible To and String`으로 문자열 재평가 활성화
- 선택 HUD 표시명: `모듬회밥!` / `카페 & 디저트` / `쿡제요리`, 실제 ORG/CAFE/GC 데이터 순서와 일치
- `storageData`: String Split 기반 Mapped Array 2곳, 각각 `8 × Array(False, False, False)` 구조
- 연습모드 에디션 전환: `otherMenu` 1회 호출, 공통 `menuInit` 2회 호출, 아이템·솥·보관함 초기화 포함
- `pot0`/`pot1`: 재시작 시 `potTime < 1` 종료 가드 각각 1회
- 버전 문자열: `v260828`
- 괄호·대괄호·중괄호·문자열 구분자 검사, 충돌 마커 및 행 끝 공백 검사: 오류 없음

## 보존한 원본 데이터 차이

공통 코드와 의미는 통일했지만 에디션 원본의 처리 요구치는 임의로 평준화하지 않았다.

- code 8 `FRYING_NEEDED`: ORG 5, CAFE/GC 10
- code 6 `PAN_NEEDED`: ORG 99, CAFE/GC 10

두 항목 모두 해당 result가 0인 원본 도구 레코드이며, 에디션별 원본 동작 보존을 우선했다.

## 크기·Elements 현황

| 파일 | GitHub blob 크기 |
|---|---:|
| `ko.ow` | 282,679 bytes (282.679 KB / 276.054 KiB) |
| `kr_deluxe.ow` | 382,877 bytes (382.877 KB / 373.903 KiB) |
| `n3_kr.ow` | 254,809 bytes (254.809 KB / 248.837 KiB) |

- 위 파일들이 모두 98KB보다 크므로 98KB는 전체 파일 제한이 아니다.
- 현재 판단 기준은 전체 최대 32,768 elements와 개별 rule의 약 98KB 제한이다.
- 큰 데이터 초기화 rule은 에디션별·단계별 서브루틴으로 분할한다.
- 현재 내부 UTF-8 소스 기준 최대 rule은 37,248 bytes이며 98 KiB를 넘는 rule은 0개다.
- `ko.ow` 혼합 배열 변환 전후 인게임 실측은 약 28,800 → 27,700대이며, 1,000개 이상 절감됐다.
- 이 단계의 결과물은 Workshop import에서 32,746 / 32,768 elements로 측정됐다. 최종 릴리즈 이전 기준치다.

## 자동 산출물

- `build/kr_deluxe/generated_data_init_rules.ow`
- `build/kr_deluxe/data_validation.json`
- `build/kr_deluxe/item_index_mapping.tsv`
- `build/kr_deluxe/runtime_item_sites.tsv`
- `build/kr_deluxe/assembled_validation.json`

## 2026-08-28 후속 최적화 내부 검증

- `build_deluxe_data.py`와 `build_kr_deluxe.py` Python 구문 검사 통과
- LF/CRLF 원본 입력을 동일한 CRLF 내부 표현으로 정규화하는 생성기 검사 통과
- 원본 ORG/CAFE/GC를 사용한 생성기 `--check` 통과
- 생성 Rule 10개와 `kr_deluxe.ow`의 대응 init Rule 정규화 비교 통과
- `CUSTOMER_LIST`와 공통 난이도 값 각 1사본, 공용 호출 2회, `DELUXE_DATA[0]` 0회 확인
- ORG MELT용 `ICE_RESULT` 포함 조회 5회가 모두 `stageMode[0] == 0` 조건을 유지함
- 기존 CAFE 제빙 결과 인덱싱 2회와 CAFE 에디션 조건 유지 확인
- 전체 조립기 재생성 결과: 57 rules / 128 globals / 40 subroutines, 382,877 bytes, SHA-256 `D346EACB4C09B0DCFA13E3A32EA546A1DCD5D339717EDE16224B8A03EE73984F` 일치
- CAFE/GC stage 0 우회 및 비ORG `setHint` Abort 0회 확인
- Overwatch Workshop import 성공, 당시 32,746 / 32,768 elements 확인

## 2026-08-29 고객·Deluxe 설정 직렬화 검증

- ORG 원본 `CUSTOMER_LIST` 6개 모드의 행 수와 고정 Hero 순서를 토큰 payload에 대해 왕복 비교했다.
- Hero 팔레트 21개, 원본 표현식으로 유지한 랜덤 행 3개를 확인했다.
- `CUSTOMER_LIST` 복원용 `For Global Variable(RAW_MIX, ...)` 1회와 중첩 `Mapped Array` 0회를 확인했다.
- ORG/CAFE/GC의 `DELUXE_DATA[1]` 활성 드랍 목록과 `[2]` 런타임 설정 4개 행을 원본 Python 모델과 왕복 비교했다.
- `DELUXE_DATA[2]` 복원 루프는 에디션별 1회, 총 3회이며 `Null` 토큰 복원도 비교를 통과했다.
- 데이터 생성기와 전체 조립기 Python 구문 검사 및 `--check`를 통과했다.
- 전체 조립 결과: 57 rules / 128 globals / 40 subroutines, 381,009 bytes, SHA-256 `0FD0D132E94650C9A2287EDDD2D6C2B8A7C5A1A33A584E5B2F7A31C3C160FE23`.
- 전체 조립기 출력과 `kr_deluxe.ow`가 일치하며 `git diff --check` 오류가 없다.
- 버전 문자열 `v260829` 2회, 이전 `v260828` 0회를 확인했다.
- 이 검증 직후에는 Workshop element 수를 재측정하지 않았으며, 당시에는 변경 전 실측 32,746 / 32,768을 기준으로 유지했다. 이후 최종 릴리즈 실측값은 31,925 / 32,768로 확인됐다.

## 릴리즈 후 선택 검증

아래 항목은 자동 정적 검증으로 대체하지 못하는 수동 회귀 항목이며, `v260829` 릴리즈 완료를 막는 미구현 항목으로 취급하지 않는다.

- ORG/CAFE/GC 인게임 회귀 플레이
- `otherMenu` 아이템 정리 루프의 `Global.despawnIndex` 공유 및 `itemCount` 감소 결과 확인
  - 현재 수동 구현은 항상 실행 중인 `despawnItem`과 같은 전역 인덱스를 사용하고, 비어 있는 슬롯을 포함한 모든 `itemCode` 슬롯에서 `itemCount`를 감소시킨다. 생성기에는 원문 그대로 보존했으며 별도 수정 결정이 필요하다.

## 최종 릴리즈 확인 (2026-08-29)

- `build_deluxe_data.py --check`: 통과
- `build_kr_deluxe.py --check`: 통과
- 조립기 기준: 57 rules / 128 globals / 40 subroutines
- 조립기 및 현재 파일: 382,844 bytes, SHA-256 `554F171B0504E2D3746AD83129D516A75AE7BE817017DD3BCFE994E530D547FC`
- Workshop 클라이언트 실측: 31,925 / 32,768 elements (에디션별 `totalScore` 분기 패치 직전 값, 당시 잔여 843)
- `totalScore`는 `Global: Setting`에서 `selectMode`보다 뒤, `Global.difficulty`보다 앞에 정확히 1회 대입되는 것을 조립기 검증으로 확인했다.
- 현재 패치 후 element 수는 아직 재측정하지 않았다.
- 릴리즈 상태: 완료
