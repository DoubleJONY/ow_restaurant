# kr_deluxe 통합 구현 기록

## 결과

`ko.ow` 공통 런타임을 기반으로 `kr_deluxe.ow`에 ORG/CAFE/GC 데이터를 통합했다. 방장이 게임 시작 시 에디션을 고르면 선택된 에디션의 세 init만 실행된다.

## 부트스트랩과 디스패처

- 글로벌 ID 126의 `MELT_LIST`를 `DELUXE_DATA` 컨테이너로 전환했다.
- 서브루틴 ID 30~38에는 ORG/CAFE/GC의 실제 init 9개를 할당했다.
- 별도 에디션 선택 서브루틴은 제거하고 기존 `selectMode`에 에디션 선택을 통합했다.
- 기존 ID 7/11/18의 `dataInit`/`dataInit2`/`dataInit3`는 호출 호환성을 유지하는 디스패처다.
- 선택 확정 시 선택 에디션 기준으로 init1, init2, difficulty/storage 계산, init3를 다시 실행한다.
- `Global.stageMode[0]`은 에디션, `Global.stageMode[1]`은 게임 모드다.
- write-only였던 ID 100/105는 각각 `ICE_NEEDED`, `ICE_RESULT`로 재사용한다.
- `DELUXE_DATA`는 `[0]` ORG MELT, `[1]` 활성 드랍, `[2]` 런타임 설정만 사용한다. 별도 init-ready 슬롯은 사용하지 않는다.

## 데이터 변환

- ORG: 475개 기존 item + 냉각총 donor = 476개
- CAFE: 398개 기존 item + 보존식 박스 donor = 399개
- GC: 462개 기존 item + 보존식 박스/냉각총 donor = 464개
- 결과 배열과 추가 재료 배열은 outer slot과 중첩 itemCode를 모두 재매핑했다.
- `RAW_MIX`는 각 행의 좌/우 itemCode를 기준으로 다시 계산하고 `RAW_RESULT`도 같은 행의 결과 코드를 변환했다.
- RAW 리터럴 Array의 element 비용을 줄이기 위해 좌/우 operand를 압축 문자열로 읽은 뒤 런타임에 `left * 1000 + right`로 복원한다.
- 세 에디션에 동일한 MIX adjacency 구축 루프, 칼/장비 배열, 업그레이드 가격, 공통 난이도 수치는 dispatcher에 한 번만 둔다.

## 런타임 통일

- `KNIFE = [1,6,2,3,4,5,7]`
- item perk = `[8,9,11,12,15,16,17,19,20]`
- foot perk = `[10,13,14]`
- 돈 itemCode = 18
- 서빙볼 ordinal = 6, 보존식 박스 = 7, 냉각총 = 8
- 33개 `createItemData` site를 검사하고 공통화 이전 장비 코드가 세 번째 필드에 남지 않음을 확인했다.
- 에디션별 시작 item, 연습 장비 pool, weighted upgrade pool, 무료 item/Ramattra 보상을 분기했다.

## 전용 로직

- ORG: 보존식 박스와 MELT 처리를 `edition == 0`에서만 활성화했다.
- CAFE: 제빙기 표지/조리 구역과 냉각총 secondary-fire를 `edition == 1`에서만 활성화했다.
- CAFE의 ICE 배열은 `Global.ICE_NEEDED`, `Global.ICE_RESULT`에만 생성되며 모든 조회는 CAFE 조건 안쪽에 있다. ORG/GC init은 두 배열을 할당하지 않는다.
- CAFE 원본 명칭에 맞춰 설비 월드 라벨·상태 HUD·강화 상점은 `오븐`, ORG/GC는 `그릴`로 표시한다. 월드 라벨에는 `Visible To and String`을 사용해 에디션 변수의 문자열 재평가도 허용한다.
- GC: 코드 19/20을 데이터에는 보유하지만 시작/연습/랜덤/업그레이드 드랍에서 모두 제외했다.

## 재현

```powershell
python scripts/kr_deluxe/build_deluxe_data.py --check
python scripts/kr_deluxe/build_kr_deluxe.py --check
```

출력물을 다시 생성할 때는 `--check`를 제거한다. 두 빌더 모두 원본 3파일을 수정하지 않으며 `build/kr_deluxe`와 `kr_deluxe.ow`만 생성한다.

## 남은 사항

싱크대 Primary Fire 물 생성, 물 item 레코드, 물 기반 recipe는 GC가 아니라 `n3_kr.ow`의 전용 기능이다. 현재 3종 Deluxe에서 누락된 GC 기능으로 취급하지 않는다. N3를 네 번째 에디션으로 통합할 때 N3 데이터와 함께 이식한다.

파일 전체 크기에는 98KB 제한을 적용하지 않는다. 현재 파일 크기는 `ko.ow` 282,679 bytes, `kr_deluxe.ow` 390,969 bytes, `n3_kr.ow` 254,809 bytes다. 약 98KB 제한은 개별 rule 기준으로 관리하며, 큰 init은 에디션·단계별 서브루틴으로 분할한다.

전체 element 상한은 32,768로 보고 실제 Workshop import 수치를 최종 기준으로 삼는다. 사용자가 확인한 `ko.ow` 혼합 배열 압축 전후 값은 약 28,800개에서 27,700개대로 1,000개 이상 감소했다. `kr_deluxe.ow`의 실제 element 수와 N3 추가 여유는 아직 측정하지 않아 WIP으로 남긴다.

이 클라우드 환경에는 OverPy/OSTW 전용 검사기가 설치되어 있지 않다. OverPy 온라인 데모에 현재 `ko.ow`를 넣은 시험은 player variable `500`을 허용하지 않아 역컴파일에 실패했다. 로컬 Codex에서는 최신 OSTW/Deltinteger 또는 OverPy CLI를 설치해 우선 검사하고, 둘 다 현재 문법을 처리하지 못하면 Workshop 클라이언트 import와 수동 element 확인을 기준으로 한다.
