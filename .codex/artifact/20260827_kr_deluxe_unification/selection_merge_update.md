# 에디션·모드 선택 병합 기록 (2026-08-28)

> 보존 상태: 중간 구현 기록. 이후 최적화와 수동 동기화까지 반영한 최종 결과는 `release_v260829.md`와 `validation_report.md`를 따른다.

이 문서는 기존 `bootstrap_dispatch_plan.md`의 별도 `selectEdition` 설계를 대체한다.

## 최종 선택 상태

- `Global.stageMode[0]`: 에디션 (`0` ORG / `1` CAFE / `2` GC)
- `Global.stageMode[1]`: 게임 모드 (`0..5`)
- 선택 HUD 진입 시 기본 게임 모드는 `stageMode[1] = 1`로 시작한다.
- 기존 scalar `Global.stageMode` 참조는 모두 `[1]` 참조로 전환했다.
- `Global.DELUXE_DATA`에는 에디션 선택값을 저장하지 않는다.

## HUD와 입력 흐름

- 앞쪽의 별도 에디션 HUD와 `selectEdition` 서브루틴/규칙을 제거했다.
- 기존 모드 선택 HUD 바로 앞에 에디션 HUD를 생성한다.
  - 에디션 HUD 우선순위: `-999`
  - 모드 HUD 우선순위: `-998`
  - 에디션 HUD는 `String and Color` 재평가를 사용한다.
- `selectMode`가 두 선택을 함께 처리한다.
  - `Ability 2`: `stageMode[0]`을 3개 에디션 사이에서 순환하고 Loop
  - `Reload`: `stageMode[1]`을 6개 모드 사이에서 순환하고 Loop
  - `Jump`: 선택 확정
- Ability 2 또는 Reload가 감지되면 각 키에 대응하는 값을 변경하고, 공통 Loop로 선택 대기를 다시 시작한다.
- Jump 단독 입력은 현재 에디션과 모드를 확정한다.

## 초기화 순서

에디션 HUD가 월드/HUD 공통 초기화 뒤에 있으므로, 초기에는 `stageMode = Array(0, 0)`으로 ORG 데이터를 한 번 로드한다. 방장이 선택을 확정하면 다음 순서로 선택 에디션 데이터를 다시 로드한다.

1. `Call Subroutine(dataInit)`
2. `Call Subroutine(dataInit2)`
3. 선택 모드 기준 difficulty/storage 계산
4. `Call Subroutine(dataInit3)`

선택 전에 만들어지는 에디션 의존 텍스트는 실시간 재평가되도록 구성했다.

- 그릴/오븐 문자열: `Visible To and String`
- 제빙기 라벨: 팬 라벨 다음의 원래 월드 초기화 위치에서 CAFE 조건 블록을 그대로 유지
- 우측 상태 HUD: `Visible To and String`

## DELUXE_DATA 압축 레이아웃

에디션 값을 `stageMode[0]`으로 옮긴 뒤 컨테이너를 `[0..2]`로 다시 압축했다. 별도 init-ready 슬롯은 사용하지 않는다.

- `[0]`: ORG `MELT_LIST`
- `[1]`: 선택 에디션의 활성 item-perk 드랍 목록
- `[2]`: 선택 에디션의 시작 아이템/강화 풀 등 런타임 설정

CAFE 전용 `ICE_NEEDED`/`ICE_RESULT`는 별도 글로벌 ID 100/105를 계속 사용한다.

## 자동 검증 결과

- `kr_deluxe.ow`: 56 rules, 128 globals, 39 subroutines
- `selectEdition` 및 `Host Player: Select Deluxe Edition`: 0건
- scalar `Global.stageMode`: 배열 초기화 1건만 허용, 나머지는 `[0]`/`[1]`
- `DELUXE_DATA` 최대 슬롯: `[2]`
- 최종 SHA-256: `54C6784A4F1255EA500467C066C50B4E196CAF227471F47ADDD4ED3B350DB439`
- `build_deluxe_data.py --check`: 통과
- `build_kr_deluxe.py --check`: 통과
- `git diff --check`: 통과
- 원본 `ko.ow`, `cafe_kr.ow`, `gc_kr.ow`: 기존 SHA-256 유지

Overwatch Workshop import와 실제 입력/HUD 동작 확인은 후속 수동 검증으로 남는다.

2026-08-28의 전체 작업 내역과 연습모드 런타임 에디션 전환 후속 계획은 `20260828_worklog_and_runtime_switch_plan.md`에 기록했다.
