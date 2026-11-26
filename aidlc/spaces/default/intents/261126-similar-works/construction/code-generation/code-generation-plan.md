# Code Generation 계획 — #13 `similar_works()` 실제 색인 검색

## Summary

- Builds: `modules/classify.py`의 `similar_works()`를 실제 색인 기준 코사인 유사도 검색으로 정리(계약 불변)
- Touches: `modules/classify.py`, `tests/test_classify.py`(신규)
- Tests: pytest 단위 테스트 8개 — FR1(코사인 정렬)·FR2(0.95 제외)·FR3(네이티브 타입)·FR4(k=0/k>후보/동점) + meta 비표준 인덱스

## Testing Contract (요약)

- 방법론: custom — 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며,
  이 이슈의 동작 테스트는 구현과 함께 `tests/test_classify.py`에 작성해 같은 변경에서 실행한다.
- 전략: Minimal — 요구사항당 테스트 1개 + 컴포넌트 happy-path 하한.
- 러너: 기존 pytest(이미 구성됨). 새 러너 부트스트랩 불필요(brownfield). 아래 명령으로 먼저 실행 확인.
- 커버리지 하한 없음(팀 규칙). `pytest` 전체 통과가 조건이다.

## 구현 단계 (요구사항 추적 포함)

- [ ] **Step 1 — 러너 확인**: `unit-test-instructions.md`의 정확한 명령으로 현재 테스트가
  돌아가는지 먼저 확인한다(brownfield, 테스트 우선 단계 전 선행). → NFR2
- [ ] **Step 2 — `_l2_normalize` 헬퍼 추가** (`modules/classify.py`): 1D/2D 모두 처리하는
  L2 정규화 헬퍼. 영벡터는 `max(norm, 1e-12)`로 안전 처리. → FR1.1, AS-2
- [ ] **Step 3 — `similar_works()` 본문 교체** (`modules/classify.py`, 함수 이름·인자·반환 형식 불변):
  - 입력 `emb`와 색인 `load_index()["emb"]`를 각각 L2 정규화 후 내적(코사인). → FR1.1
  - 검색 범위는 색인 전체(split으로 거르지 않음). → FR1.2
  - `np.argsort(-scores, kind="stable")`로 유사도 내림차순 + 색인 행 오름차순(동점 결정적). → FR1.3, FR4.3
  - 유사도 ≥ `NEAR_DUPLICATE`(0.95)는 건너뜀. → FR2.1
  - `k <= 0`이면 `[]` 반환, 남은 후보가 k보다 적으면 전부 반환(예외 없음). → FR4.1, FR4.2
  - 각 원소 `{"id","artist","style","path","score"}`, `id/artist/style/path`→`str`, `score`→`float`. → FR3.1, FR3.2
  - 색인 `emb`는 읽기 전용이므로 정규화는 새 배열로 만든다(원본 비변경).
- [ ] **Step 4 — 동작 테스트 작성** (`tests/test_classify.py`, 신규): FR1~FR4 각각 검증(아래 7개).
  `tests/test_smoke.py`는 수정하지 않는다. → NFR2
- [ ] **Step 5 — 전체 테스트 실행**: `tests/test_classify.py` 통과 + `pytest` 전체 통과(특히
  `test_smoke.py::test_similar_works_excludes_itself`, `test_classify_formats` 유지). → NFR1, NFR2
- [ ] **Step 6 — 포매팅/린트**: `ruff format .`, `ruff check --fix .` 통과(line-length 100). → C3
- [x] **Step 7 — 리뷰 반영: 위치 기준 읽기** (`modules/classify.py`): `similar_works()`에서 결과 값을
  `meta.at[row, ...]`(라벨 인덱스) 대신 `meta.iloc[row]`(위치 기준)로 읽는다. 계약은 "meta 행 순서 =
  emb 행 순서"만 보장하고 DataFrame 인덱스가 0..N-1이라는 보장은 없기 때문. `_l2_normalize`는 유지. → FR1.2, FR3.1
- [x] **Step 8 — 리뷰 반영: 비표준 인덱스 테스트** (`tests/test_classify.py`): DataFrame 인덱스가
  0..N-1이 아닌 meta(예: 인덱스 `[10, 20, 30]`)에서도 `emb` 행 위치에 맞는 값을 돌려주는지 검사하는
  테스트 1개 추가(총 8개). → FR3.1
- [x] **Step 9 — 재검증**: `pytest tests/test_classify.py -q`(8 passed) + `pytest -q` 전체 통과,
  `ruff format .`·`ruff check --fix .` 재실행. → NFR2, C3

## 테스트 파일 단계

- [ ] `tests/test_classify.py` (신규): 8개 단위 테스트
- [ ] 테스트 구성: 기존 pytest/`conftest.py`/`tests/fakes.py` 그대로 사용(추가 설정 없음)

## 범위 밖 / 비변경

- `tests/test_smoke.py`, `contracts/interfaces.md`, 다른 `modules/` 파일은 건드리지 않는다.
- 성능 최적화(벡터화/ANN)는 범위 밖(현재 색인 규모에서 선형 스캔으로 충분).

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
