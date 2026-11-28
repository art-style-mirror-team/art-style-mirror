# Code Generation 계획 — #8 `detect_type()` CLIP zero-shot

## Summary

- Builds: `modules/classify.py`의 `detect_type(img_emb)`를 CLIP zero-shot(영어 문장 앙상블·클래스 프로토타입 평균·코사인 argmax)으로 구현
- Touches: `modules/classify.py`(detect_type 본문 + `TYPE_PROMPTS` 상수), 신규 `tests/test_classify.py`
- Tests: 가짜 기반 동작 테스트 4개(유효 리터럴·결정성·프롬프트 클래스 매칭·스케일 불변)

## Testing Contract (적용)

- Methodology: **custom** (team). Ordering: `tests/test_smoke.py`의 계약 형식 검사는 먼저 있고 그대로 통과해야 하며, 이 이슈의 동작 테스트는 구현과 **같은 PR**에 작성해 함께 실행한다.
- Strategy: Minimal. 커버리지 하한 없음 — `pytest` 전체 통과가 조건.
- 테스트 러너는 이미 구성됨(`tests/conftest.py`, `pyproject.toml`). 러너 준비 단계는 기존 명령 확인으로 갈음한다.

## 구현 설계 (무엇을 만드는가)

`detect_type(img_emb)`는 이미지가 아니라 **CLIP 이미지 임베딩**(`np.ndarray`, 보통 (512,) L2 정규화)을 받는다(계약 FR1.1·고정).

1. 모듈 상수 `TYPE_PROMPTS: dict[str, list[str]]` — `"photo"`/`"painting"`/`"sketch"`별 **영어** 문장 앙상블(유형당 여러 문장). (FR1.2·FR1.3, Q1=영어)
2. 각 유형의 문장을 `data.embed_text(...)`로 임베딩한다. 반드시 `modules.data`를 **모듈 경유**로 부른다(`from modules.data import embed_text` 금지). (FR1.3·FR2.1 — 가짜 끼우기 작동)
3. 유형별 문장 임베딩을 **평균**해 유형당 프로토타입 벡터 1개를 만들고 L2 재정규화한다. (FR1.4, Q2=프로토타입 평균)
4. 입력 `img_emb`를 L2 정규화한 뒤 각 프로토타입과의 **코사인 유사도가 최대**인 유형을 반환한다 → `"photo"`/`"painting"`/`"sketch"` 중 하나. (FR1.2·FR1.4)
5. 입력이 list 등으로 와도 `np.asarray(..., dtype=float32)`로 받아 결정적으로 동작한다(동일 입력 → 동일 결과). (FR1.5)
6. 프롬프트 임베딩은 매 호출 재계산하지 않도록 캐시해도 되지만, 가짜 끼우기가 깨지지 않게 **모듈 경유 호출은 유지**한다(캐시는 결과 불변 범위에서만). (FR1.5)

새로 만드는 모델 함수는 없다 — 기존 `data.embed_text`만 쓰므로 `tests/fakes.py` 수정 불필요(FR2.2). 데이터 모델 요소 추가 없음(⇒ `## Assumptions` 없음).

## 단계 (체크박스)

- [ ] **Step 1 — 러너 확인.** 기존 테스트 명령이 도는지 확인하고 `unit-test-instructions.md`에 정확한 명령을 기록한다. 코드 변경 없음.
- [ ] **Step 2 — `detect_type` 구현 (business logic).** `modules/classify.py`에 `TYPE_PROMPTS` 상수를 추가하고 `detect_type`의 `TODO(#8)` 스텁을 위 설계대로 교체한다. 다른 함수·파일은 건드리지 않는다. (FR1.1–1.5, FR2.1, NFR3, NFR4)
- [ ] **Step 3 — 동작 테스트 작성 (same PR).** 신규 `tests/test_classify.py`에 가짜 기반 테스트 4개를 작성한다 (아래 Tests). (FR3.1·FR3.2)
- [ ] **Step 4 — 테스트 실행.** `pytest` 전체를 돌려 `tests/test_smoke.py::test_classify_formats`가 수정 없이 그대로 통과하고 신규 테스트도 통과함을 확인한다. (NFR1·NFR2)
- [ ] **Step 5 — 스타일.** `ruff format .`과 `ruff check --fix .`를 돌려 통과시킨다. (NFR4)
- [ ] **Step 6 — 산출물 기록.** `code-summary.md`와 `traceability.json`을 쓴다.

## Tests (Step 3 상세, 모두 가짜 기반 · `@pytest.mark.model` 없음)

- `test_detect_type_returns_valid_literal` — autouse 가짜로 만든 `img_emb`에 대해 반환이 `{"photo","painting","sketch"}` 중 하나. (happy path, FR1.2)
- `test_detect_type_deterministic` — 같은 `img_emb`로 두 번 호출 시 같은 결과. (edge: 결정성, FR1.5)
- `test_detect_type_matches_prompt_class` — `data.embed_text`를 "문장이 속한 클래스의 기저 벡터"를 돌려주는 스텁으로 monkeypatch하고, 각 클래스의 기저 벡터를 `img_emb`로 넣으면 그 클래스가 나오는지. `classify.TYPE_PROMPTS`로 매핑. (핵심 정확성, FR1.3·FR1.4)
- `test_detect_type_scale_invariant` — 같은 방향·다른 크기의 `img_emb`가 같은 유형으로 분류되는지(코사인 기반). (edge: 정규화, FR1.4)

## Story-to-code 추적

| 단계 | 구현 대상 | 요구사항 |
| --- | --- | --- |
| Step 2 | `TYPE_PROMPTS`, `detect_type` 본문 | FR1.1–1.5, FR2.1, NFR3, NFR4 |
| Step 3 | `tests/test_classify.py` 4개 | FR3.1, FR3.2 |
| Step 4 | 전체 `pytest` | NFR1, NFR2 |
| Step 5 | ruff | NFR4 |

제약: `contracts/interfaces.md` 변경 불가(C1), Unit B 범위만 수정(C2), 작은 커밋(C3). Out of scope: `predict_clip`/`similar_works`/`fuse`, 실제 모델 테스트(`@pytest.mark.model`), app 통합.

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
