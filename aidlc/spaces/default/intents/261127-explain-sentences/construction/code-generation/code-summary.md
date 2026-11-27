# Code Summary — #22 해석 문장 템플릿

## 바뀐 파일

| 파일 | 내용 |
| --- | --- |
| `modules/explain.py` | `LEVEL_NOTE`를 9칸 `LEVEL_TEXT[(input_type, level)]`로 바꿨다. `DEFAULT_INTRO`·`DEFAULT_TYPE`·`DEFAULT_LEVEL`·`LOW_TAIL`·`KEYWORD_TAIL` 상수와 `_josa()`·`_level_text()` 도우미를 추가했다. `render_card()`는 9칸 문구를 쓰고, `gray`에 따라 색 표현을 정하며, 키워드를 점수 없이 문장으로 쓰고, 대조 문장의 조사를 맞춘다. 모듈 docstring도 고쳤다. |
| `tests/test_explain.py` | 파일 docstring을 고치고, `_card_result()` 도우미와 해석 문장 동작 테스트 13개 함수(매개변수화 포함 약 50케이스)를 추가했다. 기존 `compare()`·레이더 테스트는 그대로다. |

`contracts/interfaces.md`, `app.py`, `tests/test_smoke.py`와 다른 Unit의 파일은 바꾸지 않았다.

## 주요 결정

- 계약 밖 값(FR1.4):
  - `input_type`이 세 값이 아니면 제목은 "이 이미지는"으로 쓰고 문구는 `painting` 줄을 쓴다.
  - `level`이 세 값이 아니면 등급은 받은 값 그대로 보여주고, 문구는 `보통` 칸을 쓰며 Top 3를 보여준다.
  - 이 처리는 모두 `_level_text()` 한 곳에서 한다.
- `_josa()`:
  - 끝 글자가 한글 음절(가~힣)이면 `(코드 - 0xAC00) % 28`로 받침을 판단한다.
  - 끝 글자가 한글이 아니거나 빈 문자열이면 받침 없는 조사를 쓴다(요구사항 가정 A2).
- `gray`는 `result.get("gray", False)`로 읽는다. 계약상 이 키는 항상 있다.
- 화가 이름은 영문이라 이름 바로 뒤에 조사를 붙이지 않는다. 예: "{top1}인 이유", "{top1} 평균에".

## 테스트 결과 (실제 실행)

| 명령 | 변경 전 | 변경 후 |
| --- | --- | --- |
| `.venv\Scripts\python -m pytest -q tests/test_explain.py tests/test_smoke.py` | 32 passed, 2 skipped | 82 passed, 2 skipped |
| `.venv\Scripts\python -m pytest -q` (전체) | — | 98 passed, 2 skipped |
| `ruff format --check modules/explain.py tests/test_explain.py` | — | 2 files already formatted |
| `ruff check modules/explain.py tests/test_explain.py` | — | All checks passed |

건너뛴 2개는 실제 모델이 필요한 기존 `@pytest.mark.model` 테스트다. 기본 실행과 CI에서는 원래 건너뛴다.

## 이 단계에서 실행하지 않은 테스트

- `@pytest.mark.model` 테스트 2개: 실제 CLIP 모델을 내려받아야 해서 실행하지 않았다(`pytest --run-model` 필요). 이번 변경과 관련이 없다.
- CI(`.github/workflows/ci.yml`)는 PR을 올리면 돈다. 이 단계에서는 로컬 실행만 했다.

## 계획과 다른 점

- 테스트 함수가 계획보다 1개 많다(12개 → 13개). `test_no_disagreement_line_when_views_agree`를 추가해 엇갈림 문장이 없는 분기도 테스트했다(unit-test-instructions의 "엇갈림 있음/없음 분기").

## 남은 우려

- `gray=True`일 때 엇갈림 문장과 "낮음" 줄 이름에서는 색 표현을 뺐다. 그래도 다음 두 곳에는 "색"이 나올 수 있다.
  - 키워드 문장: A의 출력이며, 예를 들어 "선명한 원색".
  - 대조 문장의 색 특징 이름: `app.analyze`가 어떤 특징을 넘기느냐에 달려 있다.
- FR2.1의 판정 기준은 엇갈림 문장이다. 위 두 곳은 #25 통합(`gray`와 `input_type` 처리)에서 함께 정할 일로 남긴다.
- `feat/37-ui-design`이 `LEVEL_NOTE`를 쓰고 있으면, 머지할 때 `LEVEL_TEXT`나 `_level_text()`로 바꿔야 한다.
