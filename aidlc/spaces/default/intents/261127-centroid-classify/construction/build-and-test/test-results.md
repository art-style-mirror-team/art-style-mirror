# Test Results — #10 중심점 방식 판정

실행 환경: Windows 11, Python 3.11.9, pytest 9.2.0. 인터프리터 `.venv\Scripts\python`.

## 빌드 / 정적 검사

| 명령 | 결과 |
|------|------|
| `.venv\Scripts\python -m ruff format --check .` | `27 files already formatted` (통과) |
| `.venv\Scripts\python -m ruff check .` | `All checks passed!` (통과) |

## 테스트

전체 스위트를 한 번 실행했다(이 이슈의 단위 명령 `pytest tests/test_classify.py`는 전체 실행에
포함되므로 중복 실행하지 않음).

- 명령: `.venv\Scripts\python -m pytest`
- 요약: `119 passed, 5 skipped in 27.87s`

| 구분 | 수 |
|------|----|
| 통과(passed) | 119 |
| 건너뜀(skipped) | 5 |
| 실패(failed) | 0 |
| 오류(errored) | 0 |

- `tests/test_classify.py`: 14 passed (기존 8 + #10 신규 6).
- 건너뜀 5개는 `@pytest.mark.model`(실제 CLIP 로드) 테스트로, 기본 실행·CI에서 설계상 건너뛴다
  (`pytest --run-model`로만 실행). 실패가 아니다.

## 실패 상세

- 없음.

## 커버리지

- 프로젝트에 라인 커버리지 하한 없음(team.md). 커버리지 도구를 돌리지 않았고 하한 대상도 없다.

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|-----------|--------|----------|--------|----------|--------------|---------|
| NFR2-pytest | requirements.md NFR2 / project.md Testing Posture | `pytest` 전체 통과, `test_smoke.py` 불변 | 119 passed, 5 skipped, 0 failed | `pytest` 출력 | build-and-test | Met |
| NFR3-ruff | requirements.md NFR3 / project.md Code Style | `ruff format --check`·`ruff check` 통과 | 둘 다 통과 | ruff 출력 | build-and-test | Met |
| NFR1-contract | requirements.md NFR1 | `contracts/interfaces.md`·`predict_clip()` 불변 | 변경 없음 | git diff (두 대상 변경 없음) | build-and-test | Met |
| CI-pr | project.md Testing Posture | GitHub Actions CI가 PR마다 동일 검사 | N/A | — | — | N/A (이 플랜은 CI Pipeline 단계를 돌리지 않음; GitHub CI는 PR 생성 시 동작) |

적용되는 측정 대상(NFR1~3)은 모두 `Met`. `Pending` 행 없음.
