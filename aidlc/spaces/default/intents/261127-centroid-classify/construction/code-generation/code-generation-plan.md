# Code Generation 계획 — #10 `_centroid_logits()` 추가

## Summary

- Builds: `modules/classify.py`에 비공개 함수 `_centroid_logits(E, by, scale=LOGIT_SCALE)` 추가 (중심점 방식 판정 로짓)
- Touches: `modules/classify.py`, `tests/test_classify.py`
- Tests: `tests/test_classify.py` 끝 `# --- #10 centroid` 절에 pytest 동작 테스트 6개 (학습셋 전용·최대 z·scale 배율·1차원·0장·scale 예외)

## 방식 (Testing Contract)

- 방법론: **custom**. 순서: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과한다.
  이 이슈의 동작 테스트는 구현과 **함께** 작성해 같은 PR에서 실행한다(레이어별 TDD로 바꾸지 않는다).
- 전략: Minimal (요구사항 1개당 테스트 1개, 컴포넌트당 happy-path 하한). 기존 스위트는 녹색 유지.

## 단계

- [x] **Step 1 — 테스트 러너 확인 (runner ready).** 기존 pytest 설정(`pyproject.toml`,
  `tests/conftest.py`가 `data.embed_image`를 가짜로 바꿔 끼움)을 확인한다. 이 이슈의 단위 테스트
  실행 명령을 `unit-test-instructions.md`에 기록한다. 새 러너·설정·의존성은 추가하지 않는다.

- [x] **Step 2 — `_centroid_logits()` 구현 + 동작 테스트 (함께).** → FR1, FR2, FR3
  - `modules/classify.py`에 `_centroid_logits(E, by, scale=LOGIT_SCALE)` 추가 (비공개, 한국어 docstring).
    - `_centroids()[by]`의 `(names, cents)`를 그대로 쓴다(중심점 재계산 없음). [FR1.1]
    - `E = np.asarray(E, dtype=np.float32)`; `E.ndim == 1`이면 알기 쉬운 `ValueError`. [FR2.1]
    - `scale <= 0`이면 `ValueError`. [FR2.3]
    - `En = _l2_normalize(E)`; `z = scale * (En @ cents.T)`. 0장이면 `(0, 이름 수)` 모양 유지. [FR1.2, FR2.2]
    - 반환 `(names, z)`, `names`는 `_centroids()`의 정렬된 목록 그대로, `z` shape `(n, 이름 수)`. [FR1.3]
  - `tests/test_classify.py` 끝에 `# --- #10 centroid` 절로 테스트 추가(아래 Step 3). 같은 PR·같은 변경.

- [x] **Step 3 — 동작 테스트 작성.** → FR3
  - 작은 가짜 색인을 `classify.load_index`에 monkeypatch. 각 테스트 전후 `classify._centroids.cache_clear()`. [FR3.1]
  - 학습셋(`split=="train"`)만 중심점에 쓰이는지 검사(비학습 행을 섞으면 결과가 달라짐). [FR3.2]
  - 어떤 중심점에 가장 가까운 입력일 때 그 이름이 `z` 최댓값인지. [FR3.3]
  - `scale` 선형 배율(2배 → z 2배). [FR3.4]
  - 1차원·0장·`scale<=0` 예외/반환. [FR3.5]

- [x] **Step 4 — 검증과 스타일.** → NFR2, NFR3
  - 단위 테스트 실행(`unit-test-instructions.md`의 명령)으로 녹색 확인.
  - `ruff format .`, `ruff check --fix .` 실행.
  - `tests/test_smoke.py`·`contracts/interfaces.md`·`predict_clip()`은 건드리지 않는다. [NFR1, NFR2]

- [ ] **Step 5 — 문서·추적.** `code-summary.md`에 변경 파일·결정·테스트 결과 기록, `traceability.json` 작성.

## 비고

- 데이터 분할: 중심점은 학습셋으로만(기존 `_centroids()`가 이미 `split=="train"`만 사용). [NFR4]
- `_centroid_logits()`를 `predict_clip()`에 실제 연결하는 일은 이번 범위 밖(#12).
- 새로운 데이터 모델 요소를 추가하지 않는다(`Adds:` 없음).

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
