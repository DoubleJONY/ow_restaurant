# 참고 자료

2026-09-25부터 루트 `.ow`를 실행 코드와 게임 데이터의 유일한 원본으로 관리합니다. 이 폴더는 전환 전 자료의 보관소이며 빌드 입력이나 최신 데이터베이스가 아닙니다. 이동한 자료의 내용은 원본 그대로 보존했습니다.

| 경로 | 용도 | 기존 위치 |
| --- | --- | --- |
| `legacy-builder-inputs/en_deluxe/` | 과거 영문 번역과 코드 교체 내역 조회 | `scripts/en_deluxe/`의 TSV·JSONL |
| `legacy-builder-inputs/jp_deluxe/` | 과거 일본어 아이템명·번역 제안·번역과 코드 교체 내역 조회 | `scripts/jp_deluxe/`의 TSV·JSONL |
| `legacy-build-reports/kr_deluxe/` | 아이템 인덱스 매핑·사용 위치와 과거 검증 결과 조회 | `build/kr_deluxe/`의 TSV·JSON |
| `legacy-build-reports/en_deluxe/`, `legacy-build-reports/jp_deluxe/` | 과거 번역 대응·문자열 목록·검증 결과 조회 | `build/en_deluxe/`, `build/jp_deluxe/` |
| [아이템 이름 Excel](overwatch_restaurant_deluxe_item_names.xlsx) | 아이템 이름 비교 참고 | 루트의 같은 이름 파일 |

파일명의 `overrides`, `translations`, `validation`은 이전 역할을 나타냅니다. 교체 내역을 현재 `.ow`에 자동 적용하지 않으며, 과거 검증 보고서는 현재 파일의 통과 증거가 아닙니다. 인덱스·문자열 순번·규칙 위치도 현재 `.ow`와 대조한 뒤 참고합니다. 참고 자료를 함께 갱신할 의무는 없습니다.

현재 값을 확인할 때는 해당 언어 `.ow`의 선언과 실제 대입·참조를 추적합니다. `ITEM_NAME`, 레시피 테이블, `STAGE_CODE`, `MENU_LIST`, `FRIDGE_LIST` 등은 현재 파일에 있는 값을 기준으로 해석하고 언어 간 의도적 차이를 유지합니다.

`scripts/*_deluxe/`의 Python 빌더 6개와 캐시, `build/kr_deluxe/generated_data_init_rules.ow` 중복 생성물은 제거했습니다. 옛 구현은 Git 이력에서 조회합니다. `../deprecated/`의 이전 버전과 `../.codex/artifact/`의 작업 기록은 비교 참고용으로 유지하며, 그 안의 스크립트나 재생성 절차는 현재 작업 흐름에 사용하지 않습니다.
