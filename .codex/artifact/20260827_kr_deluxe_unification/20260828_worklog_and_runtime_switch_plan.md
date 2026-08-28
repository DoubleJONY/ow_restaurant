# 2026-08-28 작업 기록 및 런타임 에디션 전환 계획

## 1. 오늘 확정한 구현

### 에디션·게임 모드 선택 통합

- 별도 `selectEdition` 규칙과 서브루틴을 제거했다.
- 선택 상태를 다음처럼 통합했다.
  - `Global.stageMode[0]`: 에디션 (`0` ORG / `1` CAFE / `2` GC)
  - `Global.stageMode[1]`: 게임 모드 (`0..5`)
- 기존 scalar `Global.stageMode` 참조는 모두 게임 모드인 `[1]` 참조로 전환했다.
- 에디션 HUD는 기존 모드 HUD 바로 앞에서 생성한다.
  - 에디션 HUD 우선순위 `-999`
  - 모드 HUD 우선순위 `-998`
  - 두 HUD 모두 선택값을 실시간 반영한다.
- `selectMode`가 두 입력을 함께 처리한다.
  - Ability 2: 에디션 변경
  - Reload: 게임 모드 변경
  - Ability 2 또는 Reload 입력 후 공통 Loop
  - Jump 단독 입력: 선택 확정
- 모드 선택 HUD의 초기값은 `Global.stageMode[1] = 1`로 확정했다.

### 데이터 초기화 흐름

- 월드 공통 초기화에는 기본 ORG 데이터가 먼저 로드된다.
- 방장이 선택을 확정하면 선택된 에디션 기준으로 다음을 다시 호출한다.
  1. `dataInit`
  2. `dataInit2`
  3. difficulty/storage 계산
  4. `dataInit3`
- `DELUXE_DATA`에서 에디션 값과 init-ready 값을 제거하고 `[0..2]`만 사용한다.
  - `[0]`: ORG `MELT_LIST`
  - `[1]`: 선택 에디션의 활성 item-perk 드랍 목록
  - `[2]`: 시작 아이템과 강화 풀 등 에디션 런타임 설정
- 별도 `DELUXE_DATA[3]` 동기화 장벽은 사용하지 않는 현재 흐름을 최종 기준으로 결정했다.

### ICE 데이터와 제빙기 표시

- 글로벌 ID 100/105를 각각 `ICE_NEEDED`, `ICE_RESULT`로 재사용한다.
- 기존 write-only 변수의 할당과 참조는 제거했다.
- ICE 배열은 CAFE init에서만 할당하고, 제빙·냉각총 로직은 CAFE 조건 안에서만 조회한다.
- 제빙기 라벨 블록은 팬 라벨 다음의 원래 월드 초기화 위치로 복귀했다.
- 제빙기 라벨의 `If(Global.stageMode[0] == 1)` 내용은 그대로 유지한다.
- 그릴/오븐처럼 같은 텍스트 엔티티의 문자열이 에디션에 따라 달라지는 곳은 `Visible To and String`을 유지한다.

### 생성·검증 체계

- `scripts/kr_deluxe/build_deluxe_data.py`가 세 원본의 데이터 변환과 검증을 담당한다.
- `scripts/kr_deluxe/build_kr_deluxe.py`가 현재 `kr_deluxe.ow`를 결정론적으로 재생성한다.
- 현재 수동 수정본과 빌더 출력은 바이트 단위로 일치한다.

## 2. 현재 확정 기준점

- 버전: `v260828`
- `kr_deluxe.ow`: 56 rules / 128 globals / 39 subroutines
- `createItemData` 생성 지점: 33곳
- `DELUXE_DATA` 최대 슬롯: `[2]`
- `kr_deluxe.ow` SHA-256:
  `54C6784A4F1255EA500467C066C50B4E196CAF227471F47ADDD4ED3B350DB439`

원본 파일은 변경하지 않았다.

| 파일 | SHA-256 |
|---|---|
| `ko.ow` | `01AEFCE72D0250EFAEEDE44646759D977E832A134BA6F9EBED554BC58848E982` |
| `cafe_kr.ow` | `34378CEE5E2C5ECF836B44AE319A7A97EBB0FF92819D6BEB468149520C6C5BE9` |
| `gc_kr.ow` | `BA87EABCB98CB76CB1EF77BACE46C6DC8497CF3D0F16970A3A9EF7AFD865D290` |

다음 검증이 통과한 상태다.

```powershell
python scripts/kr_deluxe/build_deluxe_data.py --check
python scripts/kr_deluxe/build_kr_deluxe.py --check
git diff --check
```

## 3. 기존 연습모드 `stage == 5` 기능

ORG 연습모드의 `stage == 5`는 통합 전 다른 워크샵을 소개하기 위한 기능이다.

- Reload로 네 개의 외부 워크샵 항목을 순환한다.
- Interact로 선택한 워크샵의 이름과 코드를 Small Message로 표시한다.
- Deluxe는 이 워크샵들을 한 파일 안에 통합하므로 기존 코드 안내 기능은 제거 대상이다.

이 자리를 런타임 에디션 선택 기능으로 재사용할 수 있는지 검토했다.

## 4. 런타임 에디션 전환 가능성

### 결론

에디션 전환은 가능하다. `dataInit`, `dataInit2`, `dataInit3`는 기존 배열을 직접 재할당하고 파생 MIX 배열을 처음부터 다시 만들기 때문에 재호출할 수 있다. 동일한 action이 다시 실행되는 것이므로 Workshop의 컴파일 element 수가 추가로 증가하지도 않는다.

다만 `stageMode[0]`을 변경하고 세 init만 호출하는 단순 구현은 안전하지 않다. 데이터와 함께 기존 런타임 상태를 정리하고 재구성해야 한다.

### 단순 재호출이 불가능한 이유

1. 공통화된 것은 칼·도구 코드 `0..20`이며 일반 음식 코드는 에디션마다 의미가 다르다.
   - 기존 바닥 아이템
   - 플레이어가 조작 중인 음식
   - 저장고 아이템
   - 솥 안의 결과 코드
   - 진행 중인 주문 코드
   를 그대로 두면 새 에디션에서 다른 음식 또는 범위 밖 코드로 해석될 수 있다.
2. `currentMenu`, `currentMenuHaz`, `currentMenuWeaver`, `currentCustomer`, `fridgeCode`는 init 결과에서 다시 파생해야 한다.
3. `upgradeList`는 에디션별 `DELUXE_DATA[2]`를 기준으로 다시 구성해야 한다.
4. 연습모드가 무효화한 `KNIFE_DECREASE`는 `dataInit2`가 원래 값으로 복구하므로 전환 후 다시 Null 배열로 만들어야 한다.
5. init1/2에는 에디션에 따라 약 1.3~1.6초의 Wait가 포함된다. 전환 중에는 입력과 아이템 처리의 경쟁을 막아야 한다.
6. 제빙기 라벨은 최초 월드 초기화 시 CAFE인 경우에만 생성된다. 런타임에 CAFE로 전환할 때는 별도의 라벨 생성 또는 재평가 설계가 필요하다.
7. 현재 practice `STAGE_CODE` 길이는 서로 다르다.
   - ORG: stage `0..5`
   - CAFE/GC: stage `0..4`
   따라서 ORG의 `stage == 5` 상태에서 CAFE/GC `dataInit3`를 호출한 뒤 그대로 배열을 조회하면 범위를 벗어난다.

## 5. 권장 전환 절차

전환은 연습 영업이 닫힌 상태(`difficulty == 4`, `isOpen == False`)에서 방장만 실행하게 한다.

1. 전환 중 재진입을 막는 상태를 설정하고 Team 1 플레이어를 잠근다.
2. 진행 중인 손님과 주문을 종료한다.
   - Team 2 customer 상태 종료
   - `tableOrderCode` 초기화
   - 주문 HUD/텍스트 정리
3. 기존 에디션의 일반 음식 상태를 제거한다.
   - 바닥 아이템 effect/text 제거
   - item 배열과 `itemCount` 초기화
   - 모든 플레이어의 `controlingIndex = -1`
   - 저장고 `storageData` 초기화
   - `potData`, `potTime` 초기화
4. 필요하면 장착 HUD를 파괴하고 전환 뒤 `knifeHud`/`perkHud`/`footHud`를 다시 생성한다.
   - 장비 코드 `0..20`은 공통이므로 장비 자체를 보존할 수 있다.
   - 이름에 `Evaluate Once`를 사용하는 HUD는 재생성이 안전하다.
5. 새 에디션 값을 `Global.stageMode[0]`에 기록한다.
6. `Call Subroutine(dataInit)`을 호출한다.
7. `Call Subroutine(dataInit2)`를 호출한다.
8. 연습모드 불변값을 재확정한다.
   - `Global.stageMode[1] = 0`
   - `Global.difficulty = 4`
9. `Call Subroutine(dataInit3)`를 호출한다.
10. 새 에디션에서 유효한 stage로 먼저 이동한다.
    - ORG 튜토리얼을 유지한다면 ORG는 `0` 또는 `1`
    - CAFE/GC는 현재 정책에 따라 `1`
11. 현재 stage 기준 런타임 배열을 재구성한다.
    - `currentCustomer`
    - `currentMenu` / `loadingMenu`
    - `currentMenuHaz` / `loadingMenuHaz`
    - `currentMenuWeaver` / `loadingMenuWeaver`
    - `fridgeCode`
12. `upgradeList`를 새 `DELUXE_DATA[2]` 기준으로 재구성한다.
13. `KNIFE_DECREASE`를 연습모드용 Null 배열로 다시 적용한다.
14. CAFE 전환 시 필요한 제빙기 라벨을 처리한다.
15. HUD와 월드 표시를 갱신하고 플레이어 잠금을 해제한다.

## 6. `stage == 5` 선택 UI 설계

기존 네 개 워크샵 이름/코드 배열은 제거하고 다음 세 항목으로 교체할 수 있다.

- 오리지널
- 카페
- 쿡제요리

Reload는 선택 인덱스를 `0..2`에서 순환하고, 방장의 Interact는 현재 에디션과 다른 항목을 확정한 뒤 위 전환 절차를 호출한다.

CAFE/GC에서도 다시 다른 에디션으로 이동하려면 다음 중 하나가 필요하다.

### 안 A: 공통 practice stage 5 예약

- 세 에디션의 practice `STAGE_CODE`와 `CUSTOMER_LIST`에 선택용 여섯 번째 슬롯을 둔다.
- 현재 stage 순환 로직을 계속 사용할 수 있다.
- 배열 구조가 동일해져 가장 단순하다.

### 안 B: stage와 분리된 선택 상태

- stage 배열에는 선택용 슬롯을 추가하지 않는다.
- 별도 상태 또는 기존 임시 값을 사용해 에디션 선택 UI를 연다.
- 데이터 배열은 덜 건드리지만 UI 진입·종료 분기가 더 복잡하다.

현재 구조에서는 안 A가 구현과 검증이 단순하다. 구현 전에 Workshop element 증가량을 비교해 최종 결정한다.

## 7. 게임 모드 전환과의 구분

위 계획은 연습모드 상태에서 `stageMode[0]` 에디션만 바꾸는 기능이다.

`stageMode[1]`을 연습모드에서 캐주얼/파인/스타/챌린지 모드로 실시간 변경하는 것은 init 재호출만으로 처리하지 않는다. 다음 항목들이 `Global: Setting`과 시작 흐름에 묶여 있기 때문이다.

- 난이도와 제한 시간
- objective와 match time
- 시작 아이템
- setup/startStage 규칙
- 점수·손님·실패 조건
- 연습모드 전용 HUD와 상호작용

게임 모드 자체를 바꾸는 기능이 필요하다면 전체 런타임 리셋을 별도로 설계하거나 매치 재시작 방식으로 처리한다.

## 8. 후속 검증 체크리스트

- [ ] ORG → CAFE → GC → ORG 순환 전환
- [ ] 전환 직전 바닥 음식·저장고·솥·조작 중 아이템이 모두 안전하게 정리되는지 확인
- [ ] 전환 후 냉장고 메뉴와 주문 결과가 새 에디션 데이터만 참조하는지 확인
- [ ] CAFE 제빙기/냉각총 및 ORG 보존식 박스 조건 확인
- [ ] GC에서 코드 19/20이 드랍 목록에 포함되지 않는지 확인
- [ ] 장착 칼·item perk·foot perk HUD 재생성 확인
- [ ] 전환 중 물리/조리/디스폰 규칙의 배열 범위 오류 확인
- [ ] 반복 전환 시 텍스트/effect entity 누적 확인
- [ ] Workshop import와 실제 element 카운트 확인

이 문서의 런타임 에디션 전환 부분은 계획만 확정한 상태이며 아직 `kr_deluxe.ow`에는 구현하지 않았다.


## 9. 검사 도구·제한·범위 최신화

### Workshop 제한

- 전체 스크립트 크기 98KB 제한으로 보지 않는다.
- 현재 GitHub blob 크기는 `ko.ow` 282,679 bytes, `kr_deluxe.ow` 390,969 bytes, `n3_kr.ow` 254,809 bytes다.
- 약 98KB 제한은 개별 rule 기준으로 관리한다. 큰 데이터 초기화는 에디션별·단계별 서브루틴으로 분할한다.
- 전체 컴파일 예산은 최대 32,768 elements로 별도 관리한다.
- `ko.ow`의 혼합 배열 압축 전후 사용자 실측은 약 28,800 → 27,700대로, 1,000개 이상 절감됐다.
- `kr_deluxe.ow`의 실제 element 수와 N3 추가 후 수치는 아직 Workshop에서 측정하지 않았다.

### 검사 도구

- 현재 클라우드 Work 환경에는 OverPy, OSTW/Deltinteger 또는 전용 Workshop 검사기가 설치되어 있지 않다.
- OverPy 온라인 데모에 현재 `ko.ow`를 넣은 시험은 `Player: Secondary fire button`의 player variable `500`을 허용하지 않아 역컴파일에 실패했다.
- 로컬 Codex 환경에서는 최신 OSTW/Deltinteger를 먼저 설치해 vanilla Workshop import·element 정보를 확인하고, OverPy CLI를 보조로 사용한다.
- 두 도구가 현재 export 문법을 처리하지 못하면 Overwatch 클라이언트 import를 문법·element 판정의 최종 기준으로 사용한다.
- 필요하면 로컬에서 전체 elements, rule별 UTF-8 직렬화 크기, 최대 rule 목록을 출력하는 읽기 전용 검사 스크립트를 추가한다.

### 범위 정정

- 싱크대 Primary Fire 물 생성은 GC가 아니라 N3 전용 기능이다.
- 현재 3종 Deluxe의 GC 누락으로 취급하지 않으며, N3를 네 번째 에디션으로 통합할 때 데이터·recipe·런타임을 함께 가져온다.
- `gc_en` 독립 마이그레이션은 하지 않는다. 향후 English Deluxe를 만들 때 필요한 아이템·현지화 배열만 가져온다.
- 이번 최신화에서는 N3 또는 잔여 마이그레이션 코드를 수정하지 않는다.


## 10. init3 공용 손님 구성 계획

### 구조

- `STAGE_CODE`는 에디션별 음식·웨이브 구성을 포함하므로 ORG/CAFE/GC/N3별 `dataInit_*3`에 둔다.
- `CUSTOMER_LIST`의 손님 유형 구성은 공용 서브루틴으로 분리한다.
- `dataInit3` 디스패처가 에디션별 init3를 실행한 다음, 공용 손님 구성 서브루틴을 조건 없이 한 번 호출한다.
- 런타임 에디션 전환 시에도 같은 호출 순서를 사용한다.

### 현재 데이터 차이

- CAFE와 GC의 `CUSTOMER_LIST`는 공백을 제외하면 완전히 동일하다.
- ORG는 첫 번째 게임 모드의 연습 배열에 `Soldier: 76 ×2` 항목 하나만 더 있다.
- 기존 ORG `stage == 5` 외부 워크샵 소개 기능을 제거·재사용하는 계획과 함께 이 슬롯을 정규화한다.
- 에디션별 `STAGE_CODE` 길이가 다르므로, 공용 목록을 확장형으로 유지할 경우 존재하지 않는 stage 인덱스가 실제로 선택되지 않게 한다.

### Elements 추정

| 항목 | 추정치 |
|---|---:|
| 현재 `CUSTOMER_LIST` 한 사본 | 약 830~880 |
| 현재 세 사본 | 약 2,500~2,650 |
| 공용 한 사본 + rule/call | 약 850~900 |
| 예상 순절감 | 약 1,650~1,750 |

이 변경을 적용하면 3종 dataInit 추정 합계는 약 11,500에서 약 9,800으로 내려간다. 전체 3종 Deluxe는 약 34,500~35,500에서 약 32,800~33,800으로 내려갈 가능성이 있어 32,768 제한에 근접하지만, 실제 import 전에는 통과를 확정하지 않는다.

N3도 같은 손님 구성을 사용한다면 N3 추가분에는 `CUSTOMER_LIST` 사본이 필요하지 않으므로 기존 N3 추가 추정치 약 4,000~4,500에서 약 3,100~3,600으로 낮아진다.
