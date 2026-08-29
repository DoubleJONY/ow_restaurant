# en_deluxe 정적 검증 보고서

## 산출물 기준선

| 파일 | 바이트(LF UTF-8) | SHA-256 |
|---|---:|---|
| `kr_deluxe.ow` | 382,918 | `F226B32978003BFDC505A5176D18DE10DAD7F880A521462A0797255C084A37A4` |
| `en_deluxe.ow` | 383,681 | `935AA105EE0803AE54D39BBFF433FB94F124FB955529A6BD6FCE6BCC65E21F1E` |

현재 작업 트리의 `kr_deluxe.ow`에 수동 추가되어 있던 CAFE/GC 튜토리얼용 `Global.currentCustomer` 대입도 KR 생성기에 반영했다. 따라서 KR 생성기 `--check` 결과와 현재 파일의 해시가 일치하며, EN 생성기도 이 최신 기준선을 사용한다.

## 구조

- rule 57개
- global 128개
- subroutine 40개
- 로케일 대입부와 `Custom String` literal을 마스킹한 최종 EN 구조 해시:
  `5FB7564207CBDED9F4896A9A4B1F075C5C54C14C6B536E02369144C56BF31D32`
- 최종 EN은 연습모드 아이템 생성 HUD, Sandevistan 동작, 구형 외부 Workshop 안내 제거 등 승인된 릴리즈 코드 override 15건을 포함하므로 KR 구조 해시와 의도적으로 다르다.
- 승인된 이름/점수/STAGE_CODE 대입 manifest 해시:
  `40F199B5B5839A1BDF888F27CB0F11BEA094B5D3EB5C7BCCDF2F31B298E2B0D2`
- 최대 rule: `Dummy: Spawn`, 37,065 bytes
- rule 제한 검증값: 100,352 bytes

## 로케일 데이터

| 에디션 | ITEM_NAME | STAGE_NAME | UPGRADE_NAME | KR/EN 인덱스 검증 테이블 |
|---|---:|---:|---:|---:|
| ORG | 476 | 12 | 10 | 15 |
| CAFE | 399 | 12 | 10 | 17 |
| GC | 464 | 12 | 10 | 15 |

- 모든 영문 `ITEM_NAME`은 KR과 동일한 `build_mapping()`으로 remap했다.
- ORG 20=`Freeze Gun`, CAFE 19=`Food Box`, GC 19=`Food Box`, GC 20=`Freeze Gun` donor를 삽입했다.
- ITEM_NAME 직렬화 왕복 결과가 원 배열과 일치한다.
- ITEM_NAME용 단일 `Custom String` 최대 길이는 세 에디션 모두 85자로 제한값 90자 이하다.

## totalScore

- ORG: `Practice`, 5506/4082 `SizzlingGunz`, 4555/7759 `Carrion`, 마지막 `None`
- CAFE: `Practice` + `None` 5행
- GC: 원본 4행을 읽고 `None` 2행을 추가해 6행으로 확장
- 최종 18행을 `Global.stageMode[0] * 6` 위치에서 6행 slice한다.
- 대입 위치는 에디션/모드 선택 완료 뒤이며 `Global.difficulty`보다 앞이다.

## STAGE_CODE 허용 차이

- ORG mode 1: `[7] 4→1`, `[9] 1→4`, `[10] 4→1`, `[12] 1→4`, `[13] 4→1`, `[14] 1→4`
- CAFE: 차이 없음
- GC mode 2: `[10] 8→6`
- GC의 동적 mode 3과 Deluxe mode 4·5는 KR Deluxe 구조를 유지한다.

## 문자열 검증

- 최종 전체 `Custom String`: 1,702회
- 자동·수동 번역 적용: 332회
- 현재 `en_deluxe.ow`에서 확정한 수동 출력 override: 60회
- 미해결 문자열: 0회
- placeholder multiset 불일치: 0회
- 색상 markup 불일치: 0회
- 미허용 한글: 0회
- 허용 예외: 작성자 인증키 `변기클라우드`, 기존 영문판 크레딧의 `변기클라우드`/`한국어`/`日本語`
- 한국판 괄호 `〔 〕`, `/ko` 레시피 URL, `Eqiup Item` 오타는 최종 출력에 남지 않는다.
- 기존 EN 튜토리얼의 `Soy Sauce` 오역은 ITEM_NAME 의미에 맞춰 `Sweet Soy Sauce`로 수정했다.

현재 OW에 수동 확정된 칼·도구·신발 설명, 에디션명, 고객 밈 문구, HUD 공백과 마침표 정리는
`scripts/en_deluxe/output_overrides.tsv`에 rule/ordinal 및 기존 생성값과 함께 고정했다. 빌더는 기존 생성값이
달라지면 stale override 오류를 내며, `--check`는 실제 `en_deluxe.ow`와 생성 결과의 바이트 불일치도 실패 처리한다.

릴리즈 직전 수동 코드 변경은 `scripts/en_deluxe/release_code_overrides.jsonl`에 기존/최종 코드 조각 15건으로 고정했다.
여기에는 `Suspicious Drinks`의 `Sandevistan` 개명, 강화된 시간 감속과 칼 내구도 복구, 연습 아이템 생성 HUD,
연습 테마 3개 제한, 구형 외부 Workshop 안내 제거가 포함된다.

공식 영문 문장은 어순상 placeholder 순서를 바꿀 수 있으므로 순서가 아닌 multiset을 검증한다. 예를 들어 예약 메시지는 `{1}` 테이블과 `{2}` 손님 정보를 영어 어순에 맞게 재배치한다.

## Element 예산

- EN은 KR보다 `Custom String(` 호출이 156개, `Array(` 호출이 10개 많다. 주된 원인은 긴 영문 ITEM_NAME 직렬화다.
- 참고용 이전 KR 실측값은 31,925 / 32,768이다.
- 최종 EN Workshop import 성공. 실측 element 수는 **32,716 / 32,768**이며 52개 여유가 있다.

## 실행 결과

```text
python -B scripts\kr_deluxe\build_kr_deluxe.py --check
rules=57 bytes=382918 sha256=F226B32978003BFDC505A5176D18DE10DAD7F880A521462A0797255C084A37A4

python -B scripts\en_deluxe\build_en_deluxe.py --check
rules=57 bytes=383681 sha256=935AA105EE0803AE54D39BBFF433FB94F124FB955529A6BD6FCE6BCC65E21F1E unresolved=0
```

`--check`는 `en_deluxe.ow`와 보고서 파일을 변경하지 않으며 반복 실행 결과가 동일하다.
