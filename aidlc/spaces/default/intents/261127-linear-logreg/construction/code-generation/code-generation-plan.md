# Code Generation 계획 — #11 선형 분류기(로지스틱 회귀)

## Summary

- Builds: `modules/classify.py`에 `LINEAR_PATH` 상수와 비공개 함수 4개(`_fit_linear`/`_save_linear`/`_load_linear`/`_linear_logits`)를 추가하고 `tests/test_classify.py`에 동작 테스트를 더한다.
- Touches: `modules/classify.py`, `tests/test_classify.py` (이 두 파일만).
- Tests: `tests/test_classify.py`에 `# --- #11 logreg` 절로 9개 동작 테스트(학습셋 한정·z 최대·라운드트립·반환 모양·1차원 ValueError·0장·파일 없음·softmax=predict_proba·재저장 C 반영).

## 리뷰 반영 (revision)

리뷰에서 두 가지 변경을 요청받아 반영한다:
- **(R1)** `_linear_logits`의 이진 분류 처리를 `np.column_stack([-z, z])` → `np.column_stack([np.zeros_like(z), z])`로
  바꿔 `softmax(z)`가 `model.predict_proba`와 정확히 일치하게 한다(`sigmoid(z) = p`). 2클래스 가짜 색인에서
  `softmax(z)`와 `predict_proba`가 같은지(`np.allclose`) 테스트를 추가한다.
- **(R2)** `_save_linear` 끝에서 `_load_linear.cache_clear()`를 호출해 같은 경로 재저장이 반영되게 한다.
  `tmp_path`에 `C=1.0` 모델 저장·로드 후 같은 경로에 `C=0.1` 모델을 저장하면 다시 로드한 `C`가 `0.1`인지
  테스트를 추가한다.

## 테스트 순서 계약 (custom)

팀 규칙: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의
동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다. → 구현 함수와 그 동작 테스트를 같은
변경으로 작성하고, 끝에 `pytest` 전체(스모크 포함)가 통과함을 확인한다. layer-local TDD로
바꾸지 않는다.

## 구현 단계

- [x] **Step 1. 러너 확인** — 기존 `pytest`가 도는지 확인하고 단위 범위 명령을 기록한다
  (`unit-test-instructions.md` 참조). `tests/test_smoke.py`가 그대로 통과하는 기준선.
- [x] **Step 2. 상수·import 추가 (`modules/classify.py`)** — 파일 상단에 `import joblib`를 추가하고
  (scikit-learn 1.9.1의 의존성으로 이미 설치됨), 기존 `CALIBRATION_PATH`와 같은 방식으로
  `LINEAR_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "linear.pkl"` 상수를 둔다.
  (FR1.1)
- [x] **Step 3. `_fit_linear(by, C=1.0)` 구현** — `load_index()`의 학습셋(`split=="train"`)만으로
  `sklearn.linear_model.LogisticRegression(C=C, max_iter=1000, random_state=0)`을 학습한다.
  입력 임베딩은 기존 `_l2_normalize`로 정규화. 라벨은 `meta.loc[train, by]`에서 읽어 클래스 수·이름을
  하드코딩하지 않는다. 모델 객체 하나를 돌려준다. (FR2.1~FR2.5)
- [x] **Step 4. `_save_linear(models, path=LINEAR_PATH)` 구현** —
  `{"artist": models["artist"], "style": models["style"], "C": {...}, "sklearn_version": sklearn.__version__}`
  형태 dict를 `joblib.dump`로 저장. 상위 폴더가 없으면 만든다(`path.parent.mkdir(parents=True, exist_ok=True)`).
  **(R2)** 저장 끝에서 `_load_linear.cache_clear()`를 호출한다. (FR3.1~FR3.2)
- [x] **Step 5. `_load_linear(path=LINEAR_PATH)` 구현** — `@lru_cache(maxsize=1)`로 감싸고,
  파일이 없으면 경로를 포함한 알기 쉬운 `FileNotFoundError`를 던진다(`#11` 학습·저장 안내 메시지).
  `joblib.load`로 dict를 읽어 돌려준다. 테스트에서 `_load_linear.cache_clear()` 가능. (FR4.1~FR4.3)
- [x] **Step 6. `_linear_logits(E, by, model=None)` 구현** — `model`이 없으면 `_load_linear()[by]`.
  `E`가 2차원이 아니면 `ValueError`. `n==0`이면 `(list(model.classes_), np.zeros((0, len(model.classes_)), np.float32))`.
  그 외에는 `_l2_normalize(E)` 뒤 `z = model.decision_function(E)`를 구하고
  `(list(model.classes_), z (n, 이름 수))`를 돌려준다. 이름 목록은 `model.classes_`의 정렬 순서로,
  #9 `_knn_logits`·#10 `_centroid_logits`와 동일한 모양. **(R1)** 이진 분류 시(`z.ndim == 1`)는
  `np.column_stack([np.zeros_like(z), z])`로 쌓아 `softmax(z)`가 `predict_proba`와 일치하게 한다. (FR5.1~FR5.5, NFR2)
- [x] **Step 7. 동작 테스트 작성 (`tests/test_classify.py`)** — 파일 끝에 `# --- #11 logreg` 절 추가.
  작은 가짜 색인(train/val 섞인 2클래스)을 `classify.load_index`에 `monkeypatch`, 저장은 `tmp_path`.
  검사: (a) 학습셋만 사용, (b) 학습 데이터 쪽 치우친 입력의 그 이름 z가 최대, (c) 저장→로드 후 z 동일,
  (d) 반환 모양 `(이름 목록, (n, 이름 수))`, (e) 1차원 입력 `ValueError`, (f) 0장 입력,
  (g) 파일 없음 `FileNotFoundError`, **(h, R1)** `softmax(z)`가 `model.predict_proba`와 같음(`np.allclose`),
  **(i, R2)** 같은 경로에 `C=1.0`→`C=0.1` 재저장 후 다시 로드한 `C`가 `0.1`. 각 테스트는
  `classify._load_linear.cache_clear()`로 캐시 비움. `tests/test_smoke.py`는 건드리지 않는다. (FR6.1~FR6.4)
- [x] **Step 8. 린트·전체 테스트** — `ruff format .`과 `ruff check --fix .` 실행 후
  `pytest` 전체(스모크 포함)가 통과함을 확인한다(실제 실행 결과만 기록). (NFR3, NFR4)
- [x] **Step 9. 문서·추적** — `code-summary.md`와 `traceability.json`을 작성한다.

## 범위 밖 (이번에 하지 않음)

- `artifacts/linear.pkl` 실제 생성·커밋, 노트북(`notebooks/eval.ipynb`) — #9 머지 후 별도 커밋.
- `contracts/interfaces.md`·`predict_clip()` 변경, `tests/test_smoke.py`·`requirements.txt` 변경.
- 온도·가중치·등급 경계값, 정확도/ECE 수치.

## 추적 (단계 → 요구)

| 단계 | 요구 ID |
| --- | --- |
| Step 2 | FR1.1 |
| Step 3 | FR2.1~FR2.5 |
| Step 4 | FR3.1~FR3.2 |
| Step 5 | FR4.1~FR4.3 |
| Step 6 | FR5.1~FR5.5, NFR2 |
| Step 7 | FR6.1~FR6.4, NFR1 |
| Step 8 | NFR3, NFR4 |

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
