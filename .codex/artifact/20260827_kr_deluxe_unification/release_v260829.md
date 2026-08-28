# kr_deluxe v260829 릴리즈 기록

## 상태

- 완료일: 2026-08-29
- 상태: 릴리즈 완료
- 결과물: `kr_deluxe.ow`
- 통합 에디션: ORG / CAFE / GC
- 기준 커밋: `711eb32` (`260829`)

## 최종 구성

- 공통 아이템 코드 `0..20`을 사용하며 코드 19는 보존식 박스, 코드 20은 냉각총이다.
- `Global.stageMode[0]`은 에디션, `[1]`은 게임 모드다.
- 단일 `dataInit` 디스패처가 선택 에디션의 `dataInit_*1/2/3`을 호출한다.
- ORG 보존식 박스/MELT, CAFE 제빙기/냉각총 로직은 에디션 조건으로 분기한다.
- `CUSTOMER_LIST`, `DELUXE_DATA[1]`, `DELUXE_DATA[2]`는 문자열 직렬화 후 런타임에 복원한다.
- `ICE_NEEDED`, `ICE_RESULT`는 CAFE 데이터에서만 초기화한다.
- 에디션별 최고점/기록 보유자 배열은 ORG·CAFE·GC 원본값 6행씩을 연속 배치하고, 최초 에디션 선택 후 `Array Slice(..., Global.stageMode[0] * 6, 6)`로 선택한다.
- 생성 스크립트가 현재 `kr_deluxe.ow`를 결정론적으로 재현한다.

## 최종 검증값

- `python scripts/kr_deluxe/build_deluxe_data.py --check`: 통과
- `python scripts/kr_deluxe/build_kr_deluxe.py --check`: 통과
- 구성: 57 rules / 128 globals / 40 subroutines
- 조립기 출력: 382,844 bytes
- 조립기 및 현재 파일 SHA-256: `554F171B0504E2D3746AD83129D516A75AE7BE817017DD3BCFE994E530D547FC`
- 버전 문자열: `v260829`

## Element 기록

- 고객·Deluxe 설정 직렬화 후, 최고점 분기 패치 전 Workshop 클라이언트 실측: **31,925 / 32,768**
- 당시 남은 element 예산: **843**
- 직렬화 전 실측 32,746 / 32,768 대비 821 elements 감소한 값이다.
- 에디션별 `totalScore` 분기 패치 후의 현재 element 수는 아직 재측정하지 않았다.

## 릴리즈 범위에서 제외한 항목

- CAFE/GC용 신규 튜토리얼 콘텐츠 작성
- N3 네 번째 에디션과 싱크대 물 생성 로직 통합
- `STAGE_CODE` 추가 직렬화
- 인게임 전체 회귀 플레이

위 항목은 `kr_deluxe.ow` 3종 통합 릴리즈의 미완성 항목이 아니라 별도 후속 범위다.
