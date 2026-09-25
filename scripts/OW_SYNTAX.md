# 독립 Workshop 문법 검사

Python 3.10 이상이면 추가 패키지나 빌더 실행 없이 사용합니다. 입력은 UTF-8/BOM `.ow` 파일이며 읽기만 합니다. 새로운 파일을 추가해도 검사기 소스나 파일 목록을 수정할 필요가 없습니다.

```powershell
python scripts/check_ow_syntax.py kr_deluxe.ow
python scripts/check_ow_syntax.py "*.ow"
python scripts/check_ow_syntax.py "**/*.ow"
python scripts/check_ow_syntax.py deprecated
python -m unittest discover -s tests -v
```

여러 경로를 함께 지정할 수 있고 디렉터리는 재귀 검색합니다. glob은 따옴표로 감쌉니다. 오류는 `파일:줄:열`로 출력하며 실패 또는 일치하는 파일이 없는 입력은 종료 코드 1, 성공은 0입니다. 파일마다 첫 문법 오류를 보고하고 다른 파일은 계속 검사합니다.

`.github/workflows/ow-syntax.yml`의 **OW syntax / syntax** 잡은 push/PR에서 현재 원본인 루트의 모든 `.ow`를 검사합니다. Actions의 수동 실행에서는 파일·디렉터리·glob 경로를 지정할 수 있습니다. 이전 버전까지 검사하려면 `**/*.ow` 또는 `deprecated`를 지정합니다. 빌더는 폐기되었으며 번역 매핑이나 생성 결과 일치 검사는 요구하지 않습니다. 게임 데이터와 번역도 `.ow`를 직접 수정하고, `reference/`의 자료는 참고용으로만 사용합니다.

검사 범위:

- `variables`, `subroutines`, `rule` 및 event/conditions/actions 구획
- 선언 형식과 같은 스코프의 중복 인덱스·이름
- 문자열, 주석, 괄호, 함수 호출의 인자 구분, 수식·삼항식, 세미콜론
- 비활성 규칙/액션과 한국어·일본어 문자열

이는 **영문 Workshop 텍스트 구문에 대한 제한된 정적 검사기**이며 공식 게임 파서는 아닙니다. 함수·이벤트·상수 이름의 유효성, 인자 개수·타입, 변수 참조, 대입 대상의 유효성, 게임 리소스 제한과 실행 동작은 검증하지 않습니다. `settings`, `extensions` 및 번역된 문법 키워드는 현재 지원하지 않으며 미지원 최상위 구획은 성공으로 넘기지 않고 실패합니다. 한국어/일본어 UI 문자열을 포함한 이 저장소 파일은 영문 문법이므로 검사할 수 있습니다.

`--strict-control-flow`를 추가하면 짝 없는 `End`/`Else`와 `Else` 뒤의 분기를 추가로 검사합니다. 이 옵션은 문법 검사와 별개인 엄격한 린트이며 기존 파일도 실패할 수 있습니다. 액션 목록 끝의 암묵적 종료는 허용합니다. 예시는 [Workshop If 문서](https://workshop.codes/wiki/articles/if)를 참고하세요. 기본 검사의 성공은 게임 내 가져오기나 플레이 테스트의 성공을 보장하지 않습니다.
