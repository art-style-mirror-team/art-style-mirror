# Code Generation Plan — u1-knn-vote (#9 kNN 투표 방식 판정)

## Summary

- Builds: `modules/classify.py`에 비공개 함수 `_knn_logits`·`_topk_accuracy`, `tests/test_classify.py`에 `# --- #9 kNN` 동작 테스트, `notebooks/eval.ipynb`에 `#9 kNN` 검증셋 평가 셀.
- Touches: `modules/classify.py`, `tests/test_classify.py`, `notebooks/eval.ipynb` (이 3개만).
- Tests: `test_classify.py`에 #9 절 동작 테스트 8~10개(투표·동점·clip·eps·엣지·Top-k). `tests/test_smoke.py`는 불변·green 유지.

출처: `requirements.md`(FR1~FR4, NFR1~NFR5), `unit-of-work.md`. 테스트 계약: custom — 계약 형식
검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과, 각 이슈 동작 테스트는 구현과 함께 작성해 같은
PR에서 실행.

## Steps

- [ ] **Step 1 — 구조/설정 확인(변경 없음)**: 기존 프로젝트 구조 그대로. 새 설정 파일·의존성 없음
  (numpy 등 이미 설치). `contracts/interfaces.md`·`predict_clip()`·`tests/test_smoke.py` 불변
  (NFR3).
- [ ] **Step 2 — 테스트 러너 확인·명령 기록**: 기존 pytest 러너 확인, 이 유닛 전용 명령을
  `unit-test-instructions.md`에 기록(`.venv\Scripts\python -m pytest tests/test_classify.py`).
- [ ] **Step 3 — 순서(custom)**: `tests/test_smoke.py`의 계약 형식 검사는 그대로 두어 먼저 통과
  상태를 유지하고, #9 동작 테스트는 아래 구현과 함께 작성한다(layer별 TDD로 바꾸지 않음).
- [ ] **Step 4 — `_knn_logits(E, k, by, eps=1e-3)` 구현** (`modules/classify.py`) — FR1.1~FR1.9:
  학습셋(`split=="train"`) 한정 이웃, `_l2_normalize` 코사인 유사도 상위 k(동점은 색인 위치순,
  FR1.8), `max(sim,0)` clip 후 이름별 가중 투표(FR1.4), `z=log(투표+eps)` 반환
  `(이름 목록, (n, 이름 수) z)`(FR1.5), 이름 목록은 색인에서 `sorted(unique())`(FR1.7, 위치 기준
  `.iloc`), 비정상 입력 처리 순서(`k<=0`·빈 학습셋→`ValueError`, k 초과→clamp, n=0→빈 z)(FR1.9).
- [ ] **Step 5 — `_topk_accuracy(z, names, labels, ks=(1,3))` 구현** (`modules/classify.py`) —
  FR2.1~FR2.5: `labels`=정답 이름 리스트(len n), 반환 `dict {k: 정확도}`, 상위 k 동점은 이름순
  (FR1.6 규칙), 미지 이름은 오답(FR2.4), `ks`가 이름 수 초과 시 clamp(FR2.4),
  행 수≠labels 길이 또는 `ks<=0`이면 `ValueError`(FR2.5). #10·#11 재사용 가능하게 일반적으로 작성.
- [ ] **Step 6 — 동작 테스트** (`tests/test_classify.py`, `# --- #9 kNN` 절) — FR3.1~FR3.4:
  작은 가짜 색인을 `classify.load_index`에 monkeypatch, 투표·결정성·clip·eps(투표 0→`log(1e-3)`)·
  엣지(`ValueError`)·Top-k(`dict`)·미지 label 오답을 검증. `tests/test_smoke.py` 미수정(FR3.3).
- [ ] **Step 7 — 검증셋 평가 셀** (`notebooks/eval.ipynb`, `#9 kNN` 절) — FR4.1~FR4.6:
  **(개정)** 첫 코드 셀 맨 위에서 저장소 루트(`modules` 폴더의 상위)를 `sys.path`에 넣어
  `notebooks/` 폴더를 작업 위치로 실행해도 `from modules import ...`가 되게 한다(노트북을
  `notebooks/` 기준으로 실제 실행해 오류 없음을 확인).
  첫 셀에서 `load_index()["meta"].attrs.get("fake")` 출력(True면 "가짜 색인 — 수치 기록 금지"),
  화가 수는 `meta["artist"].nunique()`로 표시(FR4.3), `split=="val"`로 k=5/10/20 Top-1·Top-3를
  `by="artist"`·`by="style"` 둘 다(비교 기준 artist, FR4.1), k별 "표를 받은 이름 수 평균"도 표시
  (FR4.4). **(개정)** "표를 받은 이름 수" 계산의 eps는 `1e-3`을 직접 적지 말고
  `inspect.signature(classify._knn_logits).parameters["eps"].default`로 읽어 쓴다(기본값이 바뀌어도
  따라감). 테스트셋 미사용, 셀 출력 비움(FR4.5), 가짜 색인에서 오류 없이 실행(FR4.6).
  **코드(`modules/classify.py`)와 테스트(`tests/test_classify.py`)는 바꾸지 않는다.**
- [ ] **Step 8 — 품질 게이트**: `ruff format .`·`ruff check --fix .` 실행, `pytest` 전체 통과
  확인(NFR4). 평가 수치는 가짜 색인이면 기록하지 않음(NFR2). (개정 후 재실행)
- [ ] **Step 9 — 문서·추적성**: `code-summary.md`와 `traceability.json` 작성.

## Story-to-code traceability

| FR | Plan Step |
|---|---|
| FR1.1~FR1.9 | Step 4 |
| FR2.1~FR2.5 | Step 5 |
| FR3.1~FR3.4 | Step 6 |
| FR4.1~FR4.6 | Step 7 |
| NFR1·NFR5 | Step 4~6 (결정성·eps 테스트) |
| NFR2 | Step 7~8 |
| NFR3 | Step 1 (불변 파일) |
| NFR4 | Step 8 |

## Testing Contract

```json
{
  "version": 1,
  "methodology": "custom",
  "source": "team",
  "ordering": "계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 각 이슈의 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다.",
  "scope": "classic",
  "test_strategy": "standard",
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
    "strategy": "standard",
    "strategy_volume": [
      "Five to eight tests per component.",
      "Unit tests plus integration tests for key boundaries.",
      "Add E2E, performance, or security tests when requirements demand them."
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
  "input_sha256": "sha256:fcf6b315e8ccc4fe44c61299b7d35b85712a3ed690cee91b1f5998de4a1fd30a",
  "contract_sha256": "sha256:03c26b0c18720805e664a3c1e7c1e75363db8cdfc064f2deb39542db063bb917"
}
```
