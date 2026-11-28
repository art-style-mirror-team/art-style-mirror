# Test Results — #8 `detect_type` (2026-11-25)

## 빌드 상태

성공. Python 3.11, 새 의존성 없음. 수집/임포트 오류 없음.

## 테스트 실행

실행 환경: `.venv\Scripts\python -m pytest` (Windows, 가짜 끼우기 autouse).

| 명령 | 결과 | exit |
| --- | --- | --- |
| `pytest -q` (전체) | **34 passed, 2 skipped** in ~8.6s | 0 |
| `pytest tests/test_classify.py tests/test_smoke.py -q` (범위) | 19 passed, 2 skipped | 0 |

- skipped 2개 = `tests/test_smoke.py`의 `@pytest.mark.model` 테스트(실제 CLIP 필요, 기본/CI 건너뜀). `--run-model`로만 실행.
- 신규 통과 테스트: `test_detect_type_returns_valid_literal`, `test_detect_type_deterministic`, `test_detect_type_matches_prompt_class`, `test_detect_type_scale_invariant`.
- `tests/test_smoke.py::test_classify_formats`는 수정 없이 통과(계약 형식 유지).

## 실패 상세

없음.

## 스타일

- `ruff format --check .` → 26 files already formatted.
- `ruff check .` → All checks passed.

## 커버리지

커버리지 하한 없음(팀/프로젝트 규칙). 측정 생략.

## Target Verification Matrix (최종)

| Target ID | Expected | Actual | Evidence | Owning Stage | Verdict |
| --- | --- | --- | --- | --- | --- |
| NFR1 | pytest 전체 통과(가짜만) | 34 passed, 2 skipped, exit 0 | `pytest -q` | build-and-test | Met |
| NFR2 | smoke 수정 없이 통과 | test_smoke 15 passed, 2 skipped | `pytest tests/test_smoke.py -q` | build-and-test | Met |
| NFR3 | 같은 CLIP 모델 | `data.embed_text`/`embed_image` 동일 모델 경유 | `modules/classify.py` 검토 | build-and-test | Met |
| NFR4 | ruff 통과 | format OK, check OK | `ruff format --check .` / `ruff check .` | build-and-test | Met |
| CI-before-merge | express 비적용 | — | — | n/a | N/A |

모든 적용 대상 Verdict = Met (CI-before-merge는 N/A). 실패·Unverified 없음.
