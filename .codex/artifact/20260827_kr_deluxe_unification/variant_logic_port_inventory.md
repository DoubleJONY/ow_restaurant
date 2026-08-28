# 에디션 전용 로직 포팅 인벤토리

> 상태 메모(2026-08-29): ORG/CAFE/GC 3종 포팅은 `v260829`로 완료했다. N3 관련 항목은 조사 기록만 보존하며 이번 릴리즈 범위 밖이다. 아래 초기 `DELUXE_DATA` 슬롯 설명은 후속 구현에서 변경됐으므로 최종 레이아웃은 `release_v260829.md`를 따른다.

## 조사 범위

`kr_deluxe.ow`를 직접 수정하지 않고 다음 원본에서 에디션 전용 동작과 참조 지점을 조사했다.

- CAFE: `cafe_kr.ow`
- GC: `gc_kr.ow`
- N3 물 생성 원본: `n3_kr.ow`

최종 공통 item-perk ordinal은 다음을 전제로 한다.

| ordinal | 기능 | 활성 에디션 |
|---:|---|---|
| 6 | 서빙볼 | 전체 |
| 7 | 보존식 박스 | ORG |
| 8 | 냉각총 | CAFE |

에디션 값과 공통 전용 설정은 `DELUXE_DATA` 컨테이너에 저장한다. write-only 글로벌 ID 100/105를 회수한 뒤 CAFE 배열은 `Global.ICE_NEEDED`, `Global.ICE_RESULT`로 분리했다. `DELUXE_DATA[0]`은 에디션, `[2]`는 활성 드랍, `[3]`은 에디션 전용 코드/설정 슬롯을 뜻한다.

## CAFE 제빙기와 냉각총

### 원본 참조 지점

| 기능 | `cafe_kr.ow` 기준 위치 | 이식 내용 |
|---|---:|---|
| ICE 글로벌 선언 | 123, 126 | write-only ID 100/105를 `ICE_NEEDED`/`ICE_RESULT`로 재사용 |
| 제빙기 표지 | 725 | CAFE 플레이어에게만 표시 |
| 우측 상태 HUD | 799 | CAFE에서만 `튀김&제빙`, 나머지는 `튀김` |
| stageMode 시작 도구 | 883-884 | 기존 `351`을 공통 냉각총 코드 `20`으로 바꾸고 CAFE 데이터에서만 사용 |
| 냉각총 secondary-fire | 1683-1709 | ordinal `7`을 `8`로 변경하고 CAFE 조건 추가 |
| 음식 복제 제외 목록 | 1762-1763 | 도구 전체 공통 범위 `1..20`을 제외 |
| 업그레이드 상점 표시 | 2018 | CAFE에서만 `튀김기&제빙기` |
| ICE_NEEDED 데이터 | 2872-2901 | remap 후 `Global.ICE_NEEDED`에 저장; CAFE init에서만 생성 |
| ICE_RESULT 데이터 | 2903-2927 | remap 후 `Global.ICE_RESULT`에 저장; CAFE init에서만 생성 |
| PERK_LIST | 3140 | 공통 9개 목록으로 교체 |
| UPGRADE_NAME | 3143-3144 | CAFE 데이터만 `튀김기&제빙기 강화` 유지 |
| 연습모드 도구 풀 | 3980 | 활성 드랍 풀 사용; 직접 `1..17,351` 사용 금지 |
| 일반 도구 가중치 풀 | 4197 | 활성 드랍 풀 사용; `351`은 새 코드 `20` |
| Perk HUD | 4036-4062 | 9개 ordinal에 맞춰 아이콘, 내구도, 키 배열 확장 |
| 제빙기 조리 구역 | 4694-4713 | CAFE 조건 안에서만 ICE 배열 조회 |

`cafe_kr.ow`에서 냉각총 코드 `351`의 로직 참조는 위 시작 도구, 복제 제외, PERK_LIST, 연습/업그레이드 드랍 풀에 집중되어 있다. 데이터 배열 내부의 `351`은 별도의 item-index 변환기가 처리한다.

### 제빙기 물리 구역

CAFE 제빙기 좌표는 다음과 같다.

```text
표지: Vector(226.649, 3, 159.387)
처리 구역 A: Vector(226.617, 2, 159.497), 반경 0.550
처리 구역 B: Vector(226.617, 2.748, 159.497), 반경 0.550
```

원본은 `itemCooking`의 팬 처리 다음 `Else If`에서 다음 동작을 한다.

1. `itemStatus = 5`
2. 진행도를 `Global.fryingPower`만큼 증가
3. `ICE_NEEDED[itemCode]` 이상이면 `ICE_RESULT[itemCode]`로 변환
4. 진행도 초기화, 효과 재생, 위쪽 속도 추가, 마지막 조작자를 cooker에 추가

`fryingPower` 업그레이드를 제빙기와 공유하는 것이 원본 의도다. 통합본에서는 반드시 먼저 CAFE 여부를 분기한 뒤 `ICE_NEEDED`, `ICE_RESULT`를 조회해야 한다. ORG/GC에는 ICE 배열이 할당되지 않으므로 다음처럼 ICE 표현식이 비CAFE 경로에서 실행될 수 없는 중첩 구조를 사용한다.

```ow
Else If(Global.DELUXE_DATA[0] == 1);
    If(제빙기 거리 조건);
        ...
        If(Global.itemProgress[Global.cookingIndex]
                >= Global.ICE_NEEDED[Global.itemCode[Global.cookingIndex]]);
            Global.itemCode[Global.cookingIndex]
                = Global.ICE_RESULT[Global.itemCode[Global.cookingIndex]];
            ...
        End;
    End;
End;
```

### 냉각총 secondary-fire

현재 CAFE 원본의 ordinal `7` 분기를 새 ordinal `8`로 옮긴다. 분기 조건은 `edition == CAFE && itemPerk == 8`이어야 한다. 대상 아이템의 처리 방식은 제빙기와 같지만 진행도 증가는 기본 `1`, Super Drink 상태 `6`에서는 `10`이다. 발사당 내구도 `1`을 소모하며 `destroyPerk`를 호출한다.

ICE 배열 접근은 CAFE 분기 안에만 둔다. `Event Player.controlingIndex == -1`일 때 `itemPosition[-1]`에 효과를 재생하는 원본 동작은 마지막 배열 원소를 잘못 참조할 가능성이 있으므로, 포팅 시 대상 존재 확인 뒤 대상 위치 효과를 재생하는 편이 안전하다. 이는 원본 동작 보존과 별개의 결함 수정이므로 구현 diff에 명시한다.

### 공통 Perk HUD

9개 ordinal의 권장 배열은 다음 의미 순서다.

```text
아이콘: Roadhog, Ana, Ashe, Sigma, Baptiste, Torbjorn, Wrecking Ball, Domina, Mei
내구도 숨김: True, True, False, False, False, False, True, True, False
키: Ultimate, Ultimate, Ultimate, Secondary, Ultimate, Secondary, Ultimate, Ultimate, Secondary
```

즉, ko 원본의 Domina/Wrecking Ball 위치를 교환하고 마지막에 Mei를 추가한다. 서빙볼은 ordinal `6`, 보존식 박스는 `7`, 냉각총은 `8`이다.

## CAFE 최소 이식 단위 재검토

### 필요한 규칙의 전체 폐쇄 집합

CAFE ICE/냉각총을 동작시키기 위해 새 standalone rule을 만들 필요는 없다. 다음 기존 규칙의 action 일부만 수정하면 된다.

| 규칙 | 최소 변경 단위 | edition gate 위치 |
|---|---|---|
| `Global: Setting` | 제빙기 In-World Text 한 action, 상태 HUD 문자열, CAFE 시작 아이템 배열 | 제빙기 텍스트 생성 전. 반드시 에디션 확정 후 실행 |
| `Player: Secondary fire button` | 토치 분기 뒤에 냉각총 `Else If` 하나 추가 | `edition == CAFE && itemPerk == 8`을 분기 조건에 둠 |
| `Player: Ultimate button` | 음식 복제 제외 목록과 box/serving ordinal 수정 | box 동작만 ORG gate; serving은 공통. ICE 접근 없음 |
| `Dummy: Spawn` | 무료 아이템 랜덤 풀 교체 | 이미 선택된 에디션의 active pool 사용 |
| `drop tips` | Ramattra 랜덤 풀 교체 | 이미 선택된 에디션의 active pool 사용 |
| `Host Player: Set Permission` | 연습모드 전체 장비 순환 목록 교체 | CAFE 목록에는 20 포함, 19 제외 |
| `Global subroutine: Data init`의 CAFE 사본 | ICE_NEEDED와 ICE_RESULT action 두 개 | dispatcher가 CAFE init만 호출하므로 내부 gate 불필요 |
| `Global subroutine: Data init2`의 CAFE 사본 | PERK_LIST, UPGRADE_NAME 및 관련 데이터 | dispatcher gate로 충분 |
| `Global subroutine: Perk Hud` | action의 3개 ordinal 배열을 9칸으로 교체 | 별도 gate 불필요; equipped item ordinal로 선택 |
| `Global subroutine: Purchase Upgrade` | 도구 가중치 풀 교체 | 에디션별 weighted pool 사용 |
| `Global subroutine: Item cooking` | 팬 분기 뒤에 제빙기 `Else If` 하나 추가 | 제빙기 거리 조건과 같은 `Else If`에 `edition == CAFE` 추가 |

`Player: Control item`, `createItem`, `destroyItem`, `destroyPerk`, `itemPhysics`, `despawnItem`에는 CAFE ICE 기능을 위해 새 action을 넣을 필요가 없다.

### 삽입 단위 A: 제빙기 표지

`Global: Setting`에서 팬 표지 다음, 싱크대 표지 전에 다음 action을 넣는다.

```ow
If(Global.DELUXE_DATA[0] == 1);
    Create In-World Text(
        Players Within Radius(Vector(226.649, 2, 159.387), 10, Team 1, Off),
        Custom String("제빙기"),
        Vector(226.649, 3, 159.387),
        3,
        Do Not Clip,
        Visible To,
        Color(Blue),
        Default Visibility
    );
End;
```

이 action은 에디션 확정 전에 실행하면 CAFE에서도 생성되지 않는다. 따라서 `Global: Setting`의 UI 생성부를 에디션 선택 뒤로 옮기거나, 위 action만 에디션 확정 직후 실행해야 한다.

### 삽입 단위 B: 냉각총 secondary-fire

`Player: Secondary fire button`의 토치 `itemPerk == 5` 분기 바로 뒤, 최종 `End` 전에 CAFE 원본 `1683..1709`를 다음 조건으로 넣는다.

```ow
Else If(Global.DELUXE_DATA[0] == 1 && Event Player.itemPerk == 8);
    Play Effect(All Players(All Teams), Bad Pickup Effect, Color(Sky Blue),
        Eye Position(Event Player) + Facing Direction Of(Event Player) * 3, 1);
    Play Effect(All Players(All Teams), Brigitte Whip Shot Heal Area Sound, Null,
        Eye Position(Event Player) + Facing Direction Of(Event Player) * 3, 100);
    If(Event Player.controlingIndex != -1);
        Play Effect(All Players(All Teams), Bad Pickup Effect, Color(Sky Blue),
            Global.itemPosition[Event Player.controlingIndex], 1);
        If(Global.itemStatus[Event Player.controlingIndex] == 5);
            Global.itemProgress[Event Player.controlingIndex]
                += Global.superDrink == 6 ? 10 : 1;
        Else;
            Global.itemStatus[Event Player.controlingIndex] = 5;
            Global.itemProgress[Event Player.controlingIndex]
                = Global.superDrink == 6 ? 10 : 1;
        End;
        If(Global.itemProgress[Event Player.controlingIndex]
                >= Global.ICE_NEEDED[Global.itemCode[Event Player.controlingIndex]]);
            Global.itemCode[Event Player.controlingIndex]
                = Global.ICE_RESULT[Global.itemCode[Event Player.controlingIndex]];
            Global.itemProgress[Event Player.controlingIndex] = Null;
            Play Effect(All Players(All Teams), Brigitte Repair Pack Armor Sound, Null,
                Global.itemPosition[Event Player.controlingIndex], 50);
            Play Effect(All Players(All Teams), Good Explosion, Color(Sky Blue),
                Global.itemPosition[Event Player.controlingIndex], 0.500);
            Global.itemVelocity[Event Player.controlingIndex]
                += Direction From Angles(False, Random Integer(False, 360)) * 0.005
                + Vector(False, 0.075, False);
            Modify Global Variable At Index(itemCooker, Event Player.controlingIndex,
                Append To Array, Global.itemLastControl[Event Player.controlingIndex]);
        End;
    End;
    Event Player.controlingIndex = -1;
    Event Player.itemPerkDurability -= 1;
    Call Subroutine(destroyPerk);
    Wait(0.300, Ignore Condition);
```

원본은 대상 유무 확인 전에 `itemPosition[controlingIndex]` 효과를 재생한다. 위 최소 이식안은 마지막 아이템을 잘못 참조할 수 있는 `-1` 인덱스 효과만 대상 확인 안으로 옮긴다. 변환·내구도·대기 값은 원본과 같다.

### 삽입 단위 C: 제빙기 조리 구역

`Global subroutine: Item cooking`에서 팬 처리 `Else If` 블록 뒤, station chain의 마지막 `End` 전에 다음 한 블록을 넣는다. edition gate와 거리 조건은 같은 `Else If`에 둘 수 있다. ICE 배열 표현식은 action 내부에서만 평가된다.

```ow
Else If(Global.DELUXE_DATA[0] == 1 && (
        Distance Between(Global.itemPosition[Global.cookingIndex],
            Vector(226.617, 2, 159.497)) < 0.550
        || Distance Between(Global.itemPosition[Global.cookingIndex],
            Vector(226.617, 2.748, 159.497)) < 0.550));
    Play Effect(All Players(All Teams), Brigitte Repair Pack Impact Sound, Null,
        Vector(226.617, 2.748, 159.497), 50);
    Play Effect(All Players(All Teams), Good Explosion, Color(Sky Blue),
        Global.itemPosition[Global.cookingIndex], True);
    Global.itemDespawn[Global.cookingIndex] = Null;
    If(Global.itemStatus[Global.cookingIndex] == 5);
        Global.itemProgress[Global.cookingIndex] += Global.fryingPower;
    Else;
        Global.itemStatus[Global.cookingIndex] = 5;
        Global.itemProgress[Global.cookingIndex] = Global.fryingPower;
    End;
    If(Global.itemProgress[Global.cookingIndex]
            >= Global.ICE_NEEDED[Global.itemCode[Global.cookingIndex]]);
        Global.itemCode[Global.cookingIndex]
            = Global.ICE_RESULT[Global.itemCode[Global.cookingIndex]];
        Global.itemProgress[Global.cookingIndex] = Null;
        Play Effect(All Players(All Teams), Brigitte Repair Pack Armor Sound, Null,
            Vector(226.617, 2.748, 159.497), 50);
        Play Effect(All Players(All Teams), Good Explosion, Color(Aqua),
            Global.itemPosition[Global.cookingIndex], 0.500);
        Global.itemVelocity[Global.cookingIndex]
            += Direction From Angles(False, Random Integer(False, 360)) * 0.005
            + Vector(False, 0.075, False);
        Modify Global Variable At Index(itemCooker, Global.cookingIndex,
            Append To Array, Global.itemLastControl[Global.cookingIndex]);
    End;
```

### 삽입 단위 D: Perk HUD 전체 action 교체

기존 8칸 배열을 다음 9칸 의미로 교체한다.

```text
icon = [Roadhog A2, Ana Ult, Ashe A2, Sigma A1, Baptiste Ult,
        Torbjorn Ult, Wrecking Ball A1, Domina Ult, Mei A1]
hide durability = [T,T,F,F,F,F,T,T,F]
input = [Ult,Ult,Ult,Secondary,Ult,Secondary,Ult,Ult,Secondary]
```

HUD의 아이템 이름과 색상 조회는 기존처럼 `PERK_LIST[0][itemPerk]`를 사용한다. 최종 `PERK_LIST[0]`은 `Array(8, 9, 11, 12, 15, 16, 17, 19, 20)`이어야 한다.

교체 가능한 전체 rule은 다음과 같다.

```ow
rule("Global subroutine: Perk Hud")
{
    event
    {
        Subroutine;
        perkHud;
    }

    actions
    {
        Abort If(Event Player.itemPerk == -1);
        Create HUD Text(Event Player,
            Array(
                Ability Icon String(Hero(Roadhog), Button(Ability 2)),
                Ability Icon String(Hero(Ana), Button(Ultimate)),
                Ability Icon String(Hero(Ashe), Button(Ability 2)),
                Ability Icon String(Hero(Sigma), Button(Ability 1)),
                Ability Icon String(Hero(Baptiste), Button(Ultimate)),
                Ability Icon String(Hero(Torbjörn), Button(Ultimate)),
                Ability Icon String(Hero(Wrecking Ball), Button(Ability 1)),
                Ability Icon String(Hero(Domina), Button(Ultimate)),
                Ability Icon String(Hero(Mei), Button(Ability 1))
            )[Event Player.itemPerk],
            Custom String("{1}{0}",
                Array(True, True, False, False, False, False, True, True, False)
                    [Event Player.itemPerk]
                    ? Custom String("")
                    : Custom String("-{0}%", Round To Integer(
                        Event Player.itemPerkDurability, Up)),
                Evaluate Once(Global.ITEM_NAME[
                    Global.PERK_LIST[False][Event Player.itemPerk]])),
            Custom String("〔{0}〕",
                Array(
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Secondary Fire)),
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Secondary Fire)),
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Ultimate)),
                    Input Binding String(Button(Secondary Fire))
                )[Event Player.itemPerk]),
            Right,
            2,
            Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]],
            Global.ITEM_COLOR[Global.PERK_LIST[False][Event Player.itemPerk]],
            Color(White),
            String and Color,
            Default Visibility);
        Event Player.itemPerkText = Last Text ID;
    }
}
```

### CAFE 하드코드 변환표

| 원본 | 최종 | 문맥 |
|---|---|---|
| itemCode `351` | `20` | 냉각총 |
| itemPerk `7` | `8` | secondary-fire 냉각총 분기만 해당 |
| itemStatus `5` | 유지 | ICE 진행 상태 |
| 시작 배열 `Array(Null,351,351,3,351,16)` | `Array(Null,20,20,3,20,16)` | stageMode별 두 번째 시작 아이템 |
| 복제 제외 `Array(1..18,351)` | `Array(1..20)` | 보존식 박스와 냉각총 모두 복제 금지 |
| 연습 전체 장비 `Array(1..17,351)` | `Array(1..17,20)` | `$100` 18과 비활성 box 19는 넣지 않음 |
| 일반 weighted pool의 `351,351` | `20,20` | 냉각총 가중치 2 유지 |

CAFE item-index 변환은 `old19 물 -> new398`, `old20 얼음 -> new351`, `old351 냉각총 -> new20`, `new19 보존식 박스` 삽입이다. 따라서 `ICE_NEEDED`와 `ICE_RESULT`도 단순히 `351`만 치환하지 않고 외부 인덱스 전체를 이동해야 한다. `ICE_RESULT`의 결과 itemCode도 CAFE 매핑으로 재귀 변환한다. 새 보존식 박스 슬롯은 CAFE에서 비활성이므로 neutral ICE 레코드를 사용한다.

### 직접 하드코드가 아니지만 반드시 분기할 랜덤 경로

공통 `PERK_LIST`에 19와 20이 모두 들어가면 다음 원본 표현은 비활성 도구도 드랍한다.

```ow
Random Value In Array(Global.PERK_LIST[Random Integer(0, 1)])
```

적어도 `Dummy: Spawn`의 무료 아이템과 `drop tips`의 Ramattra 보상에서 선택 에디션의 active item-perk pool을 사용해야 한다. CAFE active item-perk pool은 `Array(8,9,11,12,15,16,17,20)`이다. 도구/신발 50:50 선택을 유지하려면 도구 pool만 active pool로 바꾸고 신발은 기존 `PERK_LIST[1]`을 사용한다.

`Purchase Upgrade`의 pool은 확률 보존을 위해 별도의 weighted 배열을 사용해야 한다. 단순 active pool로 대체하면 원본 가중치가 사라진다.

## N3 싱크대 물 생성 조사 결과

### 범위 정정

싱크대 근처에서 Primary Fire로 물 아이템을 생성하는 기능은 GC가 아니라 N3 전용이다. `gc_kr.ow`에는 물 item 레코드, 물 recipe, 해당 Primary Fire 분기가 없으며 공통 배수 로직만 있다.

`n3_kr.ow`에는 다음 구현이 함께 존재한다.

| 기능 | 위치 |
|---|---:|
| `sinkcode` 글로벌 선언 | 123 |
| 물 표지·Aqua Sphere 효과 | 378-380 |
| Primary Fire 물 생성 분기 | 734-738 |
| `ITEM_NAME[19] = 물` | 3529-3532 |
| `sinkcode = Array(19)` | 4074 |

따라서 물 생성 분기만 현재 GC 데이터에 복사하지 않는다. N3를 네 번째 Deluxe 에디션으로 추가할 때 N3의 물 item·recipe·런타임을 같은 매핑 단위로 이식한다. 현재 단계에서는 조사 결과만 유지하고 구현은 WIP이다.

### 용량 대응

약 98KB 제한은 전체 `.ow` 파일이 아니라 개별 rule 기준으로 관리한다. N3용 `dataInit_n3_1`, `dataInit_n3_2`, `dataInit_n3_3`처럼 큰 초기화를 서브루틴으로 나누면 해당 위험은 줄일 수 있다. 단, 전체 32,768 element 예산은 별도이므로 실제 import 수치 확인 전에는 4종 통합 가능성을 확정하지 않는다.

## 검증 항목

- ORG/GC 경로에서 `ICE_NEEDED`, `ICE_RESULT` 접근 0회
- 냉각총은 CAFE에서만 secondary-fire가 작동하고 ordinal은 `8`
- 보존식 박스는 ORG에서만 작동하고 ordinal은 `7`
- 서빙볼은 전 에디션에서 ordinal `6`
- CAFE 제빙기 이외 위치에서는 `itemStatus = 5`가 설정되지 않음
- CAFE의 튀김 업그레이드가 제빙기 속도에도 적용됨
- 비CAFE 화면에 제빙기 표지와 제빙 관련 문구가 노출되지 않음
- 현재 GC에 N3 물 코드를 임의로 삽입하지 않음
- N3 통합 시 Primary Fire 생성과 Interact 배수가 독립적으로 정상 동작
