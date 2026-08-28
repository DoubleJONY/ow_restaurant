# kr_deluxe 정적 검증 보고서

## 파일 무결성

| 파일 | SHA-256 |
|---|---|
| `ko.ow` | `01AEFCE72D0250EFAEEDE44646759D977E832A134BA6F9EBED554BC58848E982` |
| `cafe_kr.ow` | `34378CEE5E2C5ECF836B44AE319A7A97EBB0FF92819D6BEB468149520C6C5BE9` |
| `gc_kr.ow` | `BA87EABCB98CB76CB1EF77BACE46C6DC8497CF3D0F16970A3A9EF7AFD865D290` |
| `kr_deluxe.ow` | `54C6784A4F1255EA500467C066C50B4E196CAF227471F47ADDD4ED3B350DB439` |

## 데이터 수치

| 에디션 | item 수 | RAW 행 | 최대 RAW operand | 최대 RAW result |
|---|---:|---:|---:|---:|
| ORG | 476 | 306 | 475 | 472 |
| CAFE | 399 | 255 | 398 | 397 |
| GC | 464 | 282 | 463 | 460 |

RAW 좌/우 operand와 result는 원본 행 순서로 왕복 검증했으며 모든 코드는 base-1000 범위 안이다.

## 구조 검증

- global variable ID: 정확히 `0..127`, ID 100 = `ICE_NEEDED`, ID 105 = `ICE_RESULT`, ID 126 = `DELUXE_DATA`
- subroutine ID: 정확히 `0..38`
- rule 수: 56
- 실제 edition init rule: 9
- CAFE ICE assignment: `Global.ICE_NEEDED`, `Global.ICE_RESULT` 각각 1회
- ORG MELT assignment: `DELUXE_DATA[0]` 1회
- 삭제한 `itemPrevPosition`, `itemNormal` 선언·대입·참조: 0회
- 폐기된 컨테이너 슬롯 `DELUXE_DATA[3]` 이상: 0회
- legacy `Global.MELT_LIST`: 0회
- 공통 MIX/KNIFE/PERK/upgrade/difficulty 초기화: 각각 dispatcher 1사본
- 생성된 per-item 47개 테이블, 숫자 lookup 1,339칸, 메뉴 계열 13개 테이블 재파싱 왕복 검사 통과
- 생성된 table용 `Custom String` 942개: 최대 85자, 90자 초과 0개
- `createItemData` assignment: 33곳, 세 번째 필드의 구 장비 코드 잔존 0곳
- Workshop `If/Else/While/For/End` 중첩: 57개 rule 전체 검사 통과
  - `ko.ow` 원본부터 actions 끝을 암시적 `End`로 사용하는 `Player: Reload button` 1곳은 동일 구조 보존 확인
- CAFE 설비명: 월드 라벨·상태 HUD·강화 상점 모두 `오븐`, 나머지 에디션은 `그릴`로 분기 확인
  - 월드 라벨은 `Visible To and String`으로 문자열 재평가 활성화
- 선택 HUD 표시명: `오리지널` / `카페` / `쿡제요리`, 실제 ORG/CAFE/GC 데이터 순서와 일치
- 버전 문자열: `v260828`
- `git diff --check`: 오류 없음

## 보존한 원본 데이터 차이

공통 코드와 의미는 통일했지만 에디션 원본의 처리 요구치는 임의로 평준화하지 않았다.

- code 8 `FRYING_NEEDED`: ORG 5, CAFE/GC 10
- code 6 `PAN_NEEDED`: ORG 99, CAFE/GC 10

두 항목 모두 해당 result가 0인 원본 도구 레코드이며, 에디션별 원본 동작 보존을 우선했다.

## 크기·Elements 현황

| 파일 | GitHub blob 크기 |
|---|---:|
| `ko.ow` | 282,679 bytes (282.679 KB / 276.054 KiB) |
| `kr_deluxe.ow` | 390,969 bytes (390.969 KB / 381.806 KiB) |
| `n3_kr.ow` | 254,809 bytes (254.809 KB / 248.837 KiB) |

- 위 파일들이 모두 98KB보다 크므로 98KB는 전체 파일 제한이 아니다.
- 현재 판단 기준은 전체 최대 32,768 elements와 개별 rule의 약 98KB 제한이다.
- 큰 데이터 초기화 rule은 에디션별·단계별 서브루틴으로 분할한다.
- `ko.ow` 혼합 배열 변환 전후 인게임 실측은 약 28,800 → 27,700대이며, 1,000개 이상 절감됐다.
- `kr_deluxe.ow` 및 N3 추가 후 element 수는 아직 인게임에서 측정하지 않았다.

## 자동 산출물

- `build/kr_deluxe/generated_data_init_rules.ow`
- `build/kr_deluxe/data_validation.json`
- `build/kr_deluxe/item_index_mapping.tsv`
- `build/kr_deluxe/runtime_item_sites.tsv`
- `build/kr_deluxe/assembled_validation.json`

## 미실행 검증

- Overwatch Workshop import
- `kr_deluxe.ow`의 전체 element 수와 개별 rule 직렬화 크기 확인
- ORG/CAFE/GC 인게임 회귀 플레이
