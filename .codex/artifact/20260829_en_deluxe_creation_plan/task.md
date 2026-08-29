# en_deluxe 제작 작업

## 목표

완성된 `kr_deluxe.ow`의 코드 구조와 개선된 데이터 초기화 방식을 그대로 사용하여 ORG, CAFE, GC 영문 통합판 `en_deluxe.ow`를 만든다.

한국어·영어 개별판은 번역과 로케일 데이터의 읽기 전용 원본으로 사용한다. 게임 로직과 숫자 데이터는 `kr_deluxe.ow`를 기준으로 하며, 구형 영문판의 코드 구조를 통합판에 역이식하지 않는다.

## 확정 원칙

- 결과물은 `en_deluxe.ow` 하나다.
- 코드 뼈대, 통합 아이템 인덱스, 직렬화, 에디션 분기와 서브루틴 구조는 `kr_deluxe.ow`를 따른다.
- `en.ow`, `cafe_en.ow`, `gc_en.ow`에서는 영문 문자열과 명시적으로 허용된 로케일 데이터만 가져온다.
- `gc_en.ow`는 구조적 소스가 아니라 GC 영문 이름 사전으로 사용한다.
- `Global.totalScore`는 세 영문판의 값을 사용하고, GC에 없는 5·6번째 모드는 `Array(0, Custom String("None"))`으로 채운다.
- `ITEM_NAME`, `STAGE_NAME`, `UPGRADE_NAME`은 에디션별 영문 원본에서 가져온다.
- 숫자 조리표, 레시피, 메뉴, 드랍 목록과 런타임 설정은 KR Deluxe 데이터를 유지한다.
- `STAGE_CODE`는 Deluxe의 최신 구조를 유지하면서 같은 구조로 비교 가능한 영문판 순서 차이만 반영한다.
- 구조용 `Custom String` 토큰은 번역하지 않는다.
- 기존 영문판에 없는 Deluxe 신규 사용자 문구는 별도 수동 번역표로 작성한다.
- placeholder, 줄바꿈, 중첩 인수 구조를 바꾸는 전역 문자열 치환은 하지 않는다.
- 원본 6개 파일과 `kr_deluxe.ow`는 수정하지 않는다.

## 작업 체크리스트

### 1. 기준선과 생성 구조

- [x] 현재 `kr_deluxe.ow`와 KR Deluxe 생성기 일치 확인
- [ ] `totalScore` 보완 후 KR Deluxe Workshop element 수 재측정 기록
- [x] `scripts/en_deluxe` 및 `build/en_deluxe` 생성 구조 준비
- [x] `en_deluxe.ow`를 KR Deluxe 산출물에서 결정론적으로 생성하도록 구성

### 2. 영문 데이터 추출

- [x] ORG/CAFE/GC의 `ITEM_NAME` 추출 및 원본 아이템 수 검증
- [x] KR Deluxe와 동일한 공통 아이템 인덱스 매핑 적용
- [x] 보존식 박스와 냉각총의 영문 donor 레코드 삽입
- [x] 에디션별 `STAGE_NAME` 12개와 `UPGRADE_NAME` 10개 추출
- [x] 영문 `totalScore` 18행 구성
- [x] 영문판의 URL, 코드, 크레딧과 로케일 메타데이터 목록화

### 3. STAGE_CODE

- [x] ORG의 영문 순서 차이 6개 leaf를 manifest에 기록하고 적용
- [x] CAFE가 KR과 동일함을 재검증
- [x] GC 공통 구간의 `[2][10][0]` 차이를 기록하고 적용
- [x] GC 모드 3의 Deluxe 동적 구조와 모드 4·5 유지
- [x] 허용된 경로 외 `STAGE_CODE` 변경이 없음을 검증

### 4. Custom String 번역

- [x] `kr_deluxe.ow`의 모든 `Custom String` 문맥 인벤토리 생성
- [x] 사용자 표시 문자열과 구조용 문자열 분류
- [x] ORG 공통 문구를 `en.ow`에서 문맥 매칭
- [x] CAFE 전용 문구를 `cafe_en.ow`에서 문맥 매칭
- [x] GC 전용 문구를 `gc_en.ow`에서 문맥 매칭
- [x] 과거 cafe 영문 overlay artifact를 보조 매핑으로 적용
- [x] Deluxe 신규 문구 수동 번역표 작성 및 적용
- [x] 중복 원문이 문맥별로 다른 번역을 요구하는 경우 개별 키로 보존
- [x] 현재 `en_deluxe.ow`의 후속 수동 번역 60건을 출력 override로 역반영
- [x] `--check`가 실제 OW와 생성 결과의 불일치를 실패 처리하도록 보강
- [x] 미해결 사용자 표시 문자열 0건 달성

### 5. 정적 검증

- [x] rule/global/subroutine 수가 KR Deluxe와 동일
- [x] 로케일 허용 영역을 마스킹한 KR/EN 구조 비교 0-diff
- [x] `totalScore` 18행 정확성 및 KR 점수 유입 0건
- [x] `ITEM_NAME` 최종 수 ORG 476 / CAFE 399 / GC 464
- [x] `STAGE_NAME` 12개, `UPGRADE_NAME` 10개씩
- [x] 모든 `Custom String` placeholder 및 인수 구조 일치
- [x] 미허용 한글 사용자 문구 0건
- [x] 구조용 직렬화 payload 왕복 검증
- [x] 생성기 반복 실행 SHA-256 일치
- [x] `git diff --check` 통과

### 6. Workshop 검증

- [x] `en_deluxe.ow` Workshop import 성공
- [x] 최종 element 수 `32,716 / 32,768` 기록
- [x] 사용자 최종 릴리즈 판정

추후 코드 변경 시 ORG/CAFE/GC 부팅·모드 선택, 에디션별 이름 배열, 점수 HUD, ORG 보존식 박스,
CAFE 제빙기/냉각총 및 GC 기본 경로를 다시 회귀 확인한다.

## 완료 조건

- `en_deluxe.ow`가 KR Deluxe 통합 구조를 기반으로 하며, 승인된 EN 릴리즈 코드 override만 추가로 가진다.
- 사용자에게 표시되는 문구는 의도적으로 허용한 고유명사 외에 모두 영어다.
- 영문 데이터 차이는 기록된 `totalScore`, 이름 배열, `STAGE_CODE` 허용 경로와 로케일 메타데이터에 한정된다.
- 생성기와 검증 보고서가 최종 파일을 재현한다.
- Workshop element 상한 32,768 안에서 import된다.
