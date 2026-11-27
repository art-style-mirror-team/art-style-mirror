# Test Results — #22 해석 문장 템플릿

실행일: 2026-11-27, 브랜치 `feat/22-explain-sentences`(작업 트리), Windows, Python 3.11 `.venv`.

## 빌드

| 명령 | 종료 | 결과 |
| --- | --- | --- |
| `.venv\Scripts\python -m compileall -q modules app.py` | 0 | 성공 |

## 테스트

| 명령 | 종료 | 결과 |
| --- | --- | --- |
| `.venv\Scripts\python -m pytest -q tests/test_explain.py tests/test_smoke.py` (unit-test-instructions의 명령) | 0 | 82 passed, 2 skipped |
| `.venv\Scripts\python -m pytest -q` (전체) | 0 | 98 passed, 2 skipped, 실패 0 |

- 건너뛴 2개는 기존 `@pytest.mark.model` 테스트다. 실제 CLIP 모델이 필요해 기본 실행과 CI에서 건너뛴다. 이번 변경과 관련이 없다.
- 변경 전 기준선(Code Generation Step 1): 같은 단위 명령에서 32 passed, 2 skipped.
- 커버리지: 팀 규칙상 하한이 없고 커버리지 도구도 설정돼 있지 않아 측정하지 않았다.

## 린트·형식

| 명령 | 종료 | 결과 |
| --- | --- | --- |
| `.venv\Scripts\ruff format --check .` | 0 | 26 files already formatted |
| `.venv\Scripts\ruff check .` | 0 | All checks passed |

## 계약 파일 확인

| 명령 | 결과 |
| --- | --- |
| `git diff --quiet origin/main -- tests/test_smoke.py contracts/interfaces.md app.py` | 차이 없음 (종료 0) |

## 실패

없음.

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| TC-PYTEST-ALL | Testing Contract(team.md·project.md Testing Posture) | `pytest` 전체 통과 | 98 passed, 2 skipped, 실패 0 | `pytest -q` 출력(위 표) | build-and-test | Met |
| TC-SMOKE-UNCHANGED | Testing Contract ordering, NFR1 | `tests/test_smoke.py` 수정 없이 통과 | 수정 없음, 통과 | `git diff --quiet origin/main -- tests/test_smoke.py`, 단위 명령 | build-and-test | Met |
| TC-UNIT-SCOPED | unit-test-instructions.md | 단위 명령 통과 | 82 passed, 2 skipped | 단위 명령 출력 | build-and-test | Met |
| NFR1-CONTRACT | requirements.md NFR1 | `contracts/interfaces.md` 변경 없음, 반환 `(str, Figure)` | 변경 없음, smoke 통과 | `git diff --quiet origin/main -- contracts/interfaces.md` | build-and-test | Met |
| NFR4-RUFF | requirements.md NFR4, project.md Code Style | `ruff format --check`·`ruff check` 통과 | 둘 다 통과 | Ruff 출력(위 표) | build-and-test | Met |
| TC-CI | Testing Contract | CI에서 실행 | — | 이 계획은 CI Pipeline을 실행하지 않는다(ci-pipeline SKIP). 저장소 CI는 PR에서 돈다. | — | N/A |
| TC-COVERAGE | team.md Testing Posture | 커버리지 하한 없음 | — | 팀 규칙상 하한 없음 | — | N/A |
