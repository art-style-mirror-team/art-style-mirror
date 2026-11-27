# Unit Test Instructions — #22 해석 문장 템플릿

## 테스트 프레임워크와 설정

- pytest 사용(버전은 `requirements.txt`에 고정). 설정은 `pyproject.toml`과 `tests/conftest.py`에 이미 있으며 새 설정은 추가하지 않는다.
- `tests/conftest.py`가 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다. 이번 테스트는 모델 함수를 부르지 않고 `render_card()`에 `result` dict를 직접 넘긴다.

## 이 작업의 테스트 실행 명령

변경 전 기준선과 변경 후에 같은 명령을 쓴다(Windows, 저장소 루트).

```
.venv\Scripts\python -m pytest -q tests/test_explain.py tests/test_smoke.py
```

macOS/Linux: `.venv/bin/python -m pytest -q tests/test_explain.py tests/test_smoke.py`

`tests/test_smoke.py`는 계약 형식 검사라 함께 돌리며 수정하지 않는다.

## 추가할 테스트 (`tests/test_explain.py`)

| # | 테스트 | 요구사항 |
| --- | --- | --- |
| 1 | `LEVEL_TEXT`가 9칸(`photo/painting/sketch` × `높음/보통/낮음`)을 모두 가지고, 비어 있지 않으며, 서로 다르다 | FR1.1, NFR5 |
| 2 | 9개 조합 매개변수화: `render_card()` 문장에 그 칸 문구와 `input_type`별 제목이 들어 있다 | FR1.1, FR1.2, FR2.3 |
| 3 | 9개 조합 문장이 모두 서로 다르다. "높음"에도 해설 문구가 붙는다 | FR1.1, FR1.2 |
| 4 | "낮음"은 Top 3 번호 목록 없이 두 관점 줄을 보여주고, `gray=True`면 줄 이름이 "선(OpenCV)"이다 | FR1.3, FR2.4 |
| 5 | 계약 밖 `input_type="unknown"`, `level="?"`에서도 예외 없이 `(str, Figure)`를 돌려주고 기본 문구를 쓴다 | FR1.4 |
| 6 | `gray=True`이고 CLIP 1위와 OpenCV 1위가 다르면, 세 입력 유형 모두 엇갈림 문장에 "색"이 없다 | FR2.1 |
| 7 | `gray=False`이면 엇갈림 문장에 "색감·선"이 있다 | FR2.2 |
| 8 | 키워드 문장에 키워드가 순서대로 있고 점수 문자열(예: "0.71")이 없으며, 마지막 키워드에 맞는 조사가 붙는다 | FR3.1, FR3.3 |
| 9 | 키워드가 빈 목록이면 키워드 줄이 없고 예외가 없다 | FR3.2 |
| 10 | `_josa()` 매개변수화: 받침 있음/없음 × 이/가, 은/는, 과/와, 을/를, 그리고 영문 끝 글자 대체 규칙 | FR4.1, FR4.3 |
| 11 | 카드 문장에 `이(가)` 같은 병기형이 없고, 대조 문장이 "밝기, 대비가 …"처럼 조사를 맞춘다 | FR4.2, FR5.2 |
| 12 | 기존 요소 유지: Top 3 %, 닮은 화풍, 비슷한 명화, 상세 수치 줄, `DISCLAIMER`가 있고, 같은 `result`를 두 번 넣으면 같은 문장이 나온다 | FR5.1, NFR3 |

NFR1(계약 유지)은 `tests/test_smoke.py`가 수정 없이 통과하는 것으로 확인한다. NFR4(Ruff)는 Build and Test에서 `ruff format --check`와 `ruff check`로 확인한다.

## 예상 커버리지

- 커버리지 하한은 없다(team.md Testing Posture). 프로젝트 전체 `pytest` 통과가 조건이며, Build and Test가 전체 테스트로 확인한다.
- 이번 변경에서 `render_card()`의 분기(등급 3, `gray` 2, 엇갈림 있음/없음, 키워드 있음/없음)와 `_josa()`의 분기(한글 받침 있음/없음, 한글 아님)를 모두 지나게 한다.

## 모킹과 테스트 데이터

- 모킹 없음. `_card_result(input_type, level, gray, keywords=..., clip_first=..., cv_first=...)` 같은 도우미로 계약(`contracts/interfaces.md`) 형식의 `result` dict를 만든다.
  - `top3`, `styles_top3`, `p_clip_top`, `p_cv_top`, `confidence`(5개 키), `keywords`, `similar`, `features`(수치 10개 + `palette`), `top1_profile`, `comparison`
- 화가 이름은 `modules/data.py`의 스텁 화가처럼 영문 이름을 쓰고, 키워드는 `"두꺼운 붓 자국"`, `"부드러운 빛"`처럼 받침 있음/없음이 섞인 한국어 명사구를 쓴다.
- 레이더 `Figure`는 matplotlib `Figure` 객체라 pyplot 상태를 남기지 않는다. 별도 정리는 하지 않는다.
