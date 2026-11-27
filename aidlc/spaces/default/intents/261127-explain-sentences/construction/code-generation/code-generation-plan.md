# Code Generation Plan — #22 해석 문장 템플릿

## Summary

- Builds: 입력 유형 × 등급 9칸 문구표, `gray` 기준 색 표현 제거, CLIP 키워드 문장, 한국어 조사 도우미를 `render_card()`에 반영
- Touches: `modules/explain.py`, `tests/test_explain.py`
- Tests: `tests/test_explain.py`에 동작 테스트 12개 함수(매개변수화 포함 약 30케이스) 추가, 기존 `tests/test_smoke.py`는 수정 없이 통과

## 범위와 입력

- 입력: `inception/requirements-analysis/requirements.md`(FR1~FR5, NFR1~NFR5), CodeKB `aidlc/spaces/default/codekb/art-style-mirror/`(api-documentation 1장 D절, code-quality-assessment "D 영역 — #22 관점")
- 단위 없음(express, zero-Unit): 이 계획 하나로 구현한다.
- 바꾸는 파일은 `modules/explain.py`, `tests/test_explain.py` 두 개뿐이다. `contracts/interfaces.md`, `app.py`, 다른 Unit의 `modules/` 파일은 건드리지 않는다.
- 데이터 모델 변경 없음(새 객체·필드·테이블 없음).

## 9칸 문구 초안 (FR1.1, NFR5)

제목은 지금처럼 `TYPE_INTRO`를 따른다(FR2.3): 사진 "사진을 그림처럼 놓고 보면 이런 화가와 닮았어요", 그림 "이 그림은 이런 화가와 닮았어요", 스케치 "이 스케치의 선을 보면 이런 화가와 닮았어요".
등급 줄 `**신뢰 등급: {level}** — {문구}`에 들어갈 9칸 문구(`LEVEL_TEXT[(input_type, level)]`)는 다음과 같다. 흑백일 때도 쓸 수 있게 9칸 모두 색 표현을 넣지 않는다(FR2.1).

| 입력 \ 등급 | 높음 | 보통 | 낮음 |
| --- | --- | --- | --- |
| 사진 `photo` | 사진 속 장면의 분위기가 1위 화가의 그림과 뚜렷하게 닮았어요. | 사진이라 붓질은 없지만, 장면의 분위기가 위 화가들과 어느 정도 닮았어요. | 사진을 그림에 견주기 어려워 뚜렷하게 닮은 화가가 없어요. |
| 그림 `painting` | 붓질과 화면 구성이 1위 화가의 작품과 뚜렷하게 닮았어요. | 여러 화가의 특징이 섞여 있어 한 명으로 딱 잘라 말하기는 어려워요. | 학습한 화가들 중에서는 뚜렷하게 닮은 화가가 없어요. |
| 스케치 `sketch` | 선의 방향과 밀도가 1위 화가의 선과 뚜렷하게 닮았어요. | 선의 특징이 여러 화가와 조금씩 겹쳐 애매한 부분이 있어요. | 선만으로는 뚜렷하게 닮은 화가를 찾기 어려워요. |

"낮음"은 이 문구 뒤에 지금처럼 " 두 관점의 결과를 따로 보여드릴게요."를 붙이고 Top 3 대신 두 관점 줄을 보여준다(FR1.3).

계약 밖 값(FR1.4): `input_type`이 세 값이 아니면 제목은 "이 이미지는 이런 화가와 닮았어요", 문구는 `painting` 줄을 쓴다. `level`이 세 값이 아니면 표시는 받은 값 그대로, 문구는 `보통` 칸을 쓰고 Top 3를 보여준다. `TYPE_INTRO`·문구 조회를 한 도우미(`_level_text(input_type, level)`)로 모아 `KeyError`가 나지 않게 한다.

## 그 밖의 문장 (FR2, FR3, FR4, FR5)

- 관점 엇갈림(CLIP 1위 ≠ OpenCV 1위):
  - `gray=False`: "분위기는 **A**, 색감·선은 **B** 쪽에 가까워요." (지금과 같음, FR2.2)
  - `gray=True`: "분위기는 **A**, 선은 **B** 쪽에 가까워요." (FR2.1)
- "낮음" 두 관점 줄의 이름: `gray=False`면 "색·선(OpenCV)", `gray=True`면 "선(OpenCV)" (FR2.4)
- CLIP 키워드: `**CLIP이 본 특징**: 두꺼운 붓 자국, 소용돌이치는 하늘, 선명한 원색이 두드러져요.` 점수는 쓰지 않는다. 마지막 키워드에 조사 `이/가`를 붙인다. 키워드가 없으면 이 줄을 뺀다(FR3.1~FR3.3).
- 1·2위 대조: `**{top1}인 이유**: 밝기, 대비가 {top1} 평균에 더 가까워요.` 마지막 특징 이름에 `이/가`를 붙인다. 화가 이름 바로 뒤에는 조사를 두지 않는다(FR4.2, FR4.3, FR5.2).
- 조사 도우미 `_josa(word, pair)`:
  - `pair`는 `"이/가"`, `"은/는"`, `"과/와"`, `"을/를"` 중 하나다.
  - 끝 글자가 한글 음절(가~힣)이면 받침이 있을 때 앞쪽 조사, 없을 때 뒤쪽 조사를 붙인다.
  - 끝 글자가 한글이 아니면 받침 없는 조사(뒤쪽)를 붙인다(가정 A2).
  - 단어에 조사를 붙인 문자열을 돌려준다.
- 그대로 두는 것: Top 3와 %, 닮은 화풍, 비슷한 명화, 상세 수치 줄, `DISCLAIMER`, 레이더 차트(FR5.1)

## 단계

- [x] Step 1: 기존 테스트 실행기 확인과 기준선 기록. `.venv\Scripts\python -m pytest -q tests/test_explain.py tests/test_smoke.py`를 변경 전에 실행해 통과 수를 기록한다. 계약 형식 검사(`tests/test_smoke.py`)는 이미 있고 그대로 통과해야 한다(Testing Contract 순서). (NFR1)
- [x] Step 2: `modules/explain.py` 문구 상수 정리. `LEVEL_NOTE`를 9칸 `LEVEL_TEXT` 표로 바꾼다. 위 초안 문구를 넣고, 낮음 꼬리 문구, 키워드 문장 꼬리("두드러져요."), 기본값 상수를 둔다. 모듈 docstring의 1일차 스텁 설명 중 문장 부분을 #22 기준으로 고친다. (FR1.1, FR1.2, FR1.4, NFR5)
- [x] Step 3: `modules/explain.py`에 `_josa()`와 `_level_text()` 도우미를 추가한다. (FR4.1, FR4.3, FR1.4)
- [x] Step 4: `render_card()`를 고친다.
  - 제목과 등급 줄에 9칸 문구를 쓴다.
  - `result["gray"]`에 따라 엇갈림 문장과 낮음 두 관점 줄의 색 표현을 정한다.
  - 키워드를 문장으로 쓰고 점수를 뺀다. 키워드가 비면 생략한다.
  - 대조 문장의 `이(가)`를 `_josa()`로 바꾼다.
  - 반환 형식 `(str, Figure)`와 나머지 줄은 그대로 둔다. (FR1~FR5, NFR1, NFR3)
- [x] Step 5: `tests/test_explain.py`에 동작 테스트를 구현과 같은 PR로 추가한다. 계약 형식의 `result` dict를 만드는 `_card_result(...)` 도우미를 쓰고 실제 모델은 쓰지 않는다. 테스트 목록은 `unit-test-instructions.md`를 따른다. 파일 첫 줄 docstring을 `compare()`·레이더·해석 문장 테스트로 고친다. (NFR2)
- [x] Step 6: `ruff format`과 `ruff check --fix`를 두 파일에 실행한다. `tests/test_explain.py`와 `tests/test_smoke.py`를 실행해 통과를 확인한다. (NFR4, NFR1)
- [x] Step 7: 문서와 추적. `code-summary.md`에 바뀐 파일, 결정, 테스트 결과를 적는다. `traceability.json`에 FR·NFR별 구현과 테스트 파일을 적는다.

## 요구사항 → 단계

| 요구사항 | 단계 |
| --- | --- |
| FR1.1–FR1.4 | Step 2, 3, 4, 5 |
| FR2.1–FR2.4 | Step 4, 5 |
| FR3.1–FR3.3 | Step 4, 5 |
| FR4.1–FR4.3 | Step 3, 4, 5 |
| FR5.1–FR5.2 | Step 4, 5 |
| NFR1 | Step 1, 4, 6 |
| NFR2 | Step 5 |
| NFR3 | Step 4, 5 |
| NFR4 | Step 6 |
| NFR5 | Step 2 |

## 위험

- `feat/37-ui-design`도 `explain.py`의 `LEVEL_NOTE` 근처를 바꾼다. #22가 먼저 머지되면 #37 쪽에서 `git merge origin/main`으로 충돌을 푼다. 그때 #37의 `build_view()`가 `LEVEL_NOTE`를 쓰면 `LEVEL_TEXT`로 바꿔야 한다.
- 화가 이름이 영문이라 조사를 붙이지 않게 문장을 짰다. #3에서 화가 이름을 한국어로 바꾸면 `_josa()`가 그대로 처리한다.

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.",
  "scope": "express",
  "test_strategy": "minimal",
  "project_type": "brownfield",
  "applicable_notes": [
    {
      "layer": "org",
      "text": "We treat tests as a first-class deliverable in every Bolt. The specific\nmethodology (TDD, BDD, ATDD, or classic test-after) is affirmed at\npractices-discovery and recorded in `team.md` under this heading with explicit\n`Methodology` and `Ordering` fields; Code Generation resolves those fields\nindependently from coverage, tooling, and scope notes.\n\nWhen no posture has been affirmed, our default per scope is:\n- **Methodology**: test-after\n- **Ordering**: implement each applicable testable layer, then write and run\n  that layer's tests.\n- `mvp`, `enterprise`, `feature`, `infra` add an 80% line-coverage\n  floor and CI execution before merge.\n- `bugfix`, `security-patch` add a targeted regression for the specific\n  bug/vulnerability and require the existing suite to remain green.\n- `express` uses the Minimal strategy: requirement-driven unit tests (one per\n  requirement, with a happy-path floor per component); existing tests remain\n  green.\n- `poc`, `refactor`, `workshop`, `classic` add no extra new-test floor and require the\n  existing suite to remain green.\n\nThe active `Test Strategy` still applies in every scope and determines test\nvolume/types. Scope floors are additive; they never reduce or replace the\nselected strategy.\n\nBuild and Test verifies defined coverage floors and affirmed quality targets;\nthey may not be weakened to make a step pass.\n\nAffirm a stricter posture in `team.md` if the team commits to one."
    },
    {
      "layer": "team",
      "text": "- **Methodology**: custom\n- **Methodology evidence**: 인터뷰 Q1에서 B(계약 검사가 먼저 있고, 동작 테스트는 구현과 함께)를 골랐다. 1일차부터 `tests/test_smoke.py`가 스텁과 함께 있었다.\n- **Ordering**: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.\n- 커버리지 하한 없음. pytest 전체 통과가 조건이다."
    },
    {
      "layer": "project",
      "text": "- 모든 변경은 `pytest` 전체 통과가 조건이다. GitHub Actions CI(`.github/workflows/ci.yml`)가 PR마다 같은 검사를 돌린다.\n- `tests/test_smoke.py`는 인터페이스 형식 검사다. 실제 구현으로 바꿔도 그대로 통과해야 하며, 통과시키려고 검사를 약하게 고치지 않는다.\n- 실제 모델을 내려받거나 불러오는 테스트는 `@pytest.mark.model`로 표시한다. 기본 실행과 CI는 이를 건너뛰고 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다(`pytest --run-model`로 실제 실행). 모델 함수는 다른 모듈에서 `data.embed_image(...)`처럼 모듈을 통해 부르고, 새 모델 함수에는 `tests/fakes.py`의 `FAKES`에 가짜를 추가한다.\n- 정확도·ECE 같은 평가 수치는 검증셋으로 계산하고 실제 실행 결과만 기록한다. 테스트셋은 #26 최종 평가에서 한 번만 쓴다."
    }
  ],
  "obligations": {
    "strategy": "minimal",
    "strategy_volume": [
      "One verifiable test per requirement at the narrowest effective level.",
      "At least one happy-path unit test per component.",
      "Unit tests are the default; a bugfix/security scope floor may require an integration or E2E regression when that is the narrowest level that reproduces the defect."
    ],
    "scope_floor": [
      "Keep the existing test suite green.",
      "This scope adds no extra new-test floor beyond the selected test strategy."
    ],
    "combination_rule": "Apply every selected-strategy obligation and every scope-floor obligation; neither replaces the other, and a targeted scope regression may add the narrowest necessary test type beyond the strategy default."
  },
  "plan_profile": {
    "methodology": "custom",
    "runner_step": "Verify the existing test runner/configuration and record the exact unit-scoped command.",
    "runner_ready_before_first_test": true,
    "testable_layers": [
      "Data model / database behavior",
      "Repository / data access",
      "Business logic",
      "API / endpoint",
      "Frontend behavior"
    ],
    "steps": [
      "Project structure and production configuration skeleton.",
      "Verify the existing test runner/configuration and record the exact unit-scoped command.",
      "Custom ordering - 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.",
      "Implementation and tests - preserve that exact ordering; do not convert it to layer-local TDD.",
      "Environment/build configuration.",
      "Documentation and traceability."
    ]
  },
  "input_sha256": "sha256:8089a7fc2eb06341bfb02951c5e0e030276e7e8a3e38bfc6b0e7be2f1f014479",
  "contract_sha256": "sha256:2b682b6095ed36b4c0945571f932ed6e5fb3b2244f4196d20c2d023172ba3e52"
}
```
