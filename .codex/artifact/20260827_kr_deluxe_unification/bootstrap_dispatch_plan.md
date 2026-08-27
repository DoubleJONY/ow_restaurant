# kr_deluxe 부트스트랩·초기화 디스패처 패치 명세

## 1. 조사 기준

- 조사 파일: `kr_deluxe.ow`
- 조사 시 SHA-256: `01AEFCE72D0250EFAEEDE44646759D977E832A134BA6F9EBED554BC58848E982`
- 같은 시점의 `ko.ow`와 SHA-256이 동일하다.
- 이 문서는 부트스트랩과 디스패처의 구현 명세다. 데이터 테이블과 전용 기능 본문은 별도 변환 결과를 사용한다.

현재 초기화 호출은 다음과 같다.

```text
Global: Setting
  Global.tx 초기화
  dataInit
  dataInit2
  공통 월드 초기화
  selectMode
  dataInit3

startStage 난이도 상승 경로
  dataInit3 재호출
```

`dataInit3` 재호출은 기존 호출부를 수정하지 않고 디스패처를 통과시켜야 한다.

## 2. 슬롯 제한과 재사용

글로벌 변수 ID `0..127`이 전부 선언되어 있지만 ID 100 `itemPrevPosition`과 ID 105 `itemNormal`은 write-only였다. 두 대입을 제거하고 각각 `ICE_NEEDED`, `ICE_RESULT`로 이름을 바꿔 재사용한다.

ID 126의 `MELT_LIST`를 `DELUXE_DATA`로 이름을 바꾸고 다음 필드를 사용한다.

```text
DELUXE_DATA[0] = edition: 0 ORG / 1 CAFE / 2 GC
DELUXE_DATA[1] = ORG MELT_LIST
DELUXE_DATA[2] = 선택 에디션의 활성 item-perk 드랍 코드
DELUXE_DATA[3] = 선택 에디션 전용 추가 설정
DELUXE_DATA[4] = 공통 부트스트랩 완료 여부
Global.ICE_NEEDED = CAFE 전용 냉각 요구치
Global.ICE_RESULT = CAFE 전용 냉각 결과
```

시작 시에는 반드시 다음처럼 edition 필드만 만든다.

```ow
Global.DELUXE_DATA = Array(0);
```

ORG/GC에서 `ICE_NEEDED`, `ICE_RESULT`에 빈 배열을 할당하지 않는다. CAFE init만 실제 ICE 배열을 생성한다.

추가 임시 상태는 새 변수를 만들지 않고 기존 슬롯을 재사용한다.

- `Global.scbRank`: 에디션 및 게임 모드 선택 중 방장 플레이어
- `Global.globalText[0]`: 에디션 선택 HUD ID
- 에디션 선택이 끝나면 HUD를 삭제한다.
- 기존 게임 모드 선택기가 같은 슬롯을 다시 사용해도 충돌하지 않는다.

## 3. 서브루틴 선언

기존 ID `7`, `11`, `18`은 이름과 역할을 유지한 디스패처다.

```text
7  dataInit
11 dataInit2
18 dataInit3
```

현재 마지막 ID 29 뒤에 다음을 추가한다.

```text
30 selectEdition
31 dataInit_org1
32 dataInit_org2
33 dataInit_org3
34 dataInit_cafe1
35 dataInit_cafe2
36 dataInit_cafe3
37 dataInit_gc1
38 dataInit_gc2
39 dataInit_gc3
```

총 서브루틴 수는 40개가 된다. 글로벌 변수 슬롯은 증가하지 않는다.

## 4. Global: Setting 시작 순서

`Global.tx` 생성과 `Destroy All Dummy Bots`까지는 그대로 둔다. 그 직후의 기존 `dataInit/dataInit2` 호출 앞에 에디션 선택을 넣는다.

```ow
Global.DELUXE_DATA = Array(0);
Wait Until(Is True For Any(All Players(Team 1), Has Spawned(Current Array Element)), 99999);
Global.scbRank = Slot Of(Host Player) == -1
    ? First Of(Filtered Array(All Players(Team 1), Has Spawned(Current Array Element)))
    : Host Player;
Set Status(Global.scbRank, Null, Rooted, 9999);

Create HUD Text(
    All Players(Team 1),
    Custom String("에디션: {0}", Array(Custom String("ORG"), Custom String("CAFE"), Custom String("GC"))[
        Global.DELUXE_DATA[0]]),
    Null,
    Local Player == Global.scbRank
        ? Custom String("[{0}] 변경 / [{1}] 확정", Input Binding String(Button(Reload)), Input Binding String(Button(Jump)))
        : Custom String("방장이 에디션을 선택하는 중입니다"),
    Top,
    -1000,
    Array(Color(Orange), Color(Sky Blue), Color(Green))[Global.DELUXE_DATA[0]],
    Null,
    Color(White),
    Visible To String and Color,
    Default Visibility
);
Global.globalText[0] = Last Text ID;
Call Subroutine(selectEdition);

Call Subroutine(dataInit);
Call Subroutine(dataInit2);
```

구현 시 기존 파일의 줄바꿈 스타일에 맞춰 다시 포맷한다. 중요한 실행 순서는 다음과 같다.

1. 번역 토큰 `tx` 초기화
2. 플레이어 한 명 이상 spawn 대기
3. 실제 방장 또는 기존 방식의 fallback 플레이어 확정
4. edition 선택 및 확정
5. init1, init2 디스패치
6. 기존 공통 월드 초기화 계속
7. 기존 `selectMode`
8. init3 디스패치
9. 나머지 초기 아이템·월드 UI 구성
10. 부트스트랩 완료 플래그 설정

기존 `ALLOWED_HEROS` 앞의 spawn 대기는 중복이 되지만 즉시 통과하므로, 최초 패치에서는 그대로 두어 diff를 최소화한다.

## 5. selectEdition 본문

선택기는 `Reload`로 순환하고 `Jump`로 확정한다. 입력을 누른 채 서브루틴에 진입하거나 같은 입력이 기존 `selectMode`까지 전달되는 것을 막아야 한다.

```ow
rule("Host Player: Select Edition")
{
    event
    {
        Subroutine;
        selectEdition;
    }

    actions
    {
        Wait Until(!Is Button Held(Global.scbRank, Button(Reload))
            && !Is Button Held(Global.scbRank, Button(Jump)), 99999);
        Wait Until(Is Button Held(Global.scbRank, Button(Reload))
            || Is Button Held(Global.scbRank, Button(Jump)), 99999);
        If(Is Button Held(Global.scbRank, Button(Reload)));
            Global.DELUXE_DATA[0] = (Global.DELUXE_DATA[0] + 1) % 3;
            Loop;
        End;
        Wait Until(!Is Button Held(Global.scbRank, Button(Jump)), 99999);
        Destroy HUD Text(Global.globalText[0]);
    }
}
```

첫 번째 release 대기는 세 가지 문제를 동시에 막는다.

- spawn 시 이미 눌린 버튼으로 기본 ORG가 즉시 확정되는 문제
- Reload 한 번이 여러 번 순환하는 문제
- edition 확정 Jump가 뒤의 `selectMode`까지 남는 문제

`Global.DELUXE_DATA`를 `selectEdition` 본문에서 초기화하면 `Loop` 때마다 ORG로 되돌아가므로, 초기 `Array(0)` 할당은 호출부에만 둔다.

## 6. 플레이어 입장 흐름과 초기화 경쟁 방지

현재 `Player: Spawn`도 Jump 입력을 기다린다. 방장이 edition을 Jump로 확정하면 이 입장 흐름도 동시에 진행될 수 있다. 데이터 init은 `Wait(0.100)`을 포함하므로, 플레이어가 `loadProgress`, `knifeHud`, `perkHud`를 너무 일찍 호출하지 않도록 명시적 준비 상태가 필요하다.

`Player: Spawn`의 `Wait(2, Ignore Condition);` 뒤, `Clear Status(Event Player, Rooted);` 앞에 다음을 넣는다.

```ow
Wait Until(Global.DELUXE_DATA[4] == True, 99999);
```

`Global: Setting`의 모든 초기 아이템 생성, `Start Rule(rotatingFridge, ...)`, 패치노트 월드 텍스트 생성까지 마친 직후 rule이 끝나기 전에 다음을 넣는다.

```ow
Global.DELUXE_DATA[4] = True;
```

따라서 플레이어는 edition과 stageMode가 확정되고 init1/2/3 및 초기 월드 생성이 끝날 때까지 Rooted/Phased Out 상태를 유지한다.

## 7. init 디스패처

세 디스패처는 같은 형태를 사용한다. 예시는 init1이다.

```ow
rule("Global subroutine: Data init dispatcher")
{
    event
    {
        Subroutine;
        dataInit;
    }

    actions
    {
        If(Global.DELUXE_DATA[0] == 0);
            Call Subroutine(dataInit_org1);
        Else If(Global.DELUXE_DATA[0] == 1);
            Call Subroutine(dataInit_cafe1);
        Else;
            Call Subroutine(dataInit_gc1);
        End;
    }
}
```

`dataInit2`는 `*_org2/*_cafe2/*_gc2`, `dataInit3`는 `*_org3/*_cafe3/*_gc3`를 같은 방식으로 호출한다. edition 값은 선택기에서 `% 3`으로 고정되므로 `Else`는 GC로 사용한다.

현재 ORG 데이터 본문의 event 이름만 다음처럼 바꾼다.

```text
dataInit  -> dataInit_org1
dataInit2 -> dataInit_org2
dataInit3 -> dataInit_org3
```

본문을 먼저 복제한 후 dispatcher를 만들지 말고, ORG event를 먼저 이름 변경한 뒤 빈 dispatcher rule을 삽입해야 같은 subroutine event가 중복되는 중간 상태를 피할 수 있다.

## 8. MELT_LIST 이관

ORG `dataInit_org2`의 기존 할당은 다음처럼 바꾼다.

```text
Global.MELT_LIST = Array(...)
->
Global.DELUXE_DATA[1] = Array(...)
```

현재 런타임 참조 5곳도 모두 바꾼다.

```text
Global.MELT_LIST
->
Global.DELUXE_DATA[1]
```

그리고 각 동작은 edition이 ORG인지 함께 검사해야 한다.

```ow
Global.DELUXE_DATA[0] == 0
    && Array Contains(Global.DELUXE_DATA[1], Global.itemCode[index])
```

대상은 다음 의미 지점이다.

- 튀김기에서 itemDespawn 99 설정
- 그릴에서 itemDespawn 99 설정
- 팬에서 itemDespawn 99 설정
- despawn 효과 표시
- despawn 증가량 20 적용

CAFE/GC init은 `[1]`을 할당하지 않는다.

## 9. 기존 호출부 보존

다음 호출부는 삭제하거나 edition별 호출로 직접 치환하지 않는다.

```text
Global: Setting 초기 dataInit
Global: Setting 초기 dataInit2
Global: Setting의 selectMode 뒤 dataInit3
startStage 난이도 상승 시 dataInit3
```

특히 난이도 상승의 `dataInit3`가 dispatcher를 거치면 게임 도중에도 시작 시 선택한 edition의 stage 데이터만 다시 로드된다.

## 10. 다른 구현 단계와의 계약

- 데이터 생성기는 9개 실제 init rule만 채운다. 기존 이름 `dataInit/dataInit2/dataInit3`에는 데이터를 넣지 않는다.
- CAFE ICE 코드는 `Global.ICE_NEEDED`, `Global.ICE_RESULT`만 사용한다.
- ICE 조회를 포함한 branch 전체를 `DELUXE_DATA[0] == 1` 조건 안에 둔다.
- 활성 드랍 소스는 `DELUXE_DATA[2]`를 사용한다.
- ORG 보존식 박스는 `DELUXE_DATA[0] == 0`, CAFE 냉각총은 `== 1`, GC 물 로직은 `== 2`로 제한한다.
- edition 값은 init 본문이나 게임 도중 로직에서 다시 할당하지 않는다.
- `dataInit3`의 반복 호출은 `[0]`과 `[4]`를 변경하지 않는다.

## 11. 정적 검증

구현 직후 다음을 검사한다.

```text
Global variable 선언 ID: 0..127, 중복/추가 없음
subroutine 선언 ID: 0..39, 중복 없음
dataInit event rule: dispatcher 1개
dataInit2 event rule: dispatcher 1개
dataInit3 event rule: dispatcher 1개
각 실제 init event: 정확히 1개씩, 총 9개
Global.MELT_LIST 문자열 잔존: 0건
DELUXE_DATA 전체 할당(`=`): 시작의 Array(0) 1건만 허용
DELUXE_DATA[0] 쓰기: selectEdition 1곳만 허용
초기 dataInit 호출 시점: selectEdition 반환 뒤
부트스트랩 완료 쓰기: Global: Setting 마지막 1곳
Player: Spawn 준비 대기: Clear Status(Rooted)보다 앞
```

런타임 스모크 테스트는 다음 순서로 한다.

1. ORG/CAFE/GC 각각 Reload 순환 표시 확인
2. 방장 외 플레이어에게 확정 안내만 보이는지 확인
3. Jump를 길게 눌러도 edition과 stageMode가 동시에 확정되지 않는지 확인
4. 선택 전 init 데이터 참조 오류와 플레이어 조작 가능 상태가 없는지 확인
5. 초기 호출과 난이도 상승 재호출에서 같은 edition init3가 선택되는지 확인
6. 게임 중 edition 변경 경로가 없는지 확인
