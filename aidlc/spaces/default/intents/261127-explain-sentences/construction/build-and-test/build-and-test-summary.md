# Build and Test Summary — #22 해석 문장 템플릿

## 전체 상태

- 빌드: 성공. 문법·가져오기 확인용 `compileall`.
- 테스트: 전체 `pytest` 98 passed, 2 skipped, 실패 0. 단위 명령은 82 passed, 2 skipped.
- 린트·형식: Ruff format과 check 모두 통과.
- 사전 조건: Python 3.11 `.venv`, `pip install -r requirements.txt`. 새 의존성은 없다.

## 테스트 종류

- 단위 테스트(Minimal 전략): `tests/test_explain.py`의 해석 문장 동작 테스트 13개 함수. Code Generation에서 작성했다.
- 계약 형식 검사: `tests/test_smoke.py`. 수정하지 않았다.
- 통합·성능·보안 테스트 지침: Minimal 전략이라 만들지 않았다.
- 브라우저 동작은 이번 범위에 없다. `render_card()` 문자열을 Python에서 직접 검사한다.

## 커버리지 기대치

- 프로젝트 전체 하한은 없다(team.md). 조건은 `pytest` 전체 통과다.
- 이번 변경의 분기는 테스트로 모두 지나간다: 등급 3, `gray` 2, 엇갈림 있음/없음, 키워드 있음/없음, 조사 받침 있음/없음/한글 아님.

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
| --- | --- | --- | --- | --- | --- | --- |
| TC-PYTEST-ALL | Testing Contract | `pytest` 전체 통과 | 98 passed, 2 skipped | `test-results.md` | build-and-test | Met |
| TC-SMOKE-UNCHANGED | Testing Contract, NFR1 | smoke 수정 없이 통과 | 수정 없음, 통과 | `test-results.md` | build-and-test | Met |
| TC-UNIT-SCOPED | unit-test-instructions.md | 단위 명령 통과 | 82 passed, 2 skipped | `test-results.md` | build-and-test | Met |
| NFR1-CONTRACT | requirements.md | 계약 파일 변경 없음 | 변경 없음 | `test-results.md` | build-and-test | Met |
| NFR4-RUFF | requirements.md | Ruff 통과 | 통과 | `test-results.md` | build-and-test | Met |
| TC-CI | Testing Contract | CI 실행 | — | 이 계획은 CI Pipeline을 실행하지 않는다 | — | N/A |
| TC-COVERAGE | team.md | 하한 없음 | — | 팀 규칙상 하한 없음 | — | N/A |

## 준비 상태

- 빌드 준비: 됨
- 테스트 준비: 됨, 모든 대상 Met
- 배포 준비: 해당 없음. 이 팀은 자동 배포가 없고 로컬 실행만 한다(team.md Deployment). 머지는 PR과 리뷰를 거친다.

## 남은 일

- `gray=True`일 때 키워드 문장(A의 출력)과 대조 문장의 색 특징 이름에는 "색"이 나올 수 있다. #25 통합에서 정한다.
- `feat/37-ui-design`의 `build_view()`가 `LEVEL_NOTE`를 쓴다. #37을 머지할 때 `_level_text()`·`_josa()`로 연결해야 9칸 문구가 G안 화면에 나온다.
- 실제 모델 테스트 2개(`@pytest.mark.model`)는 실행하지 않았다. 이번 변경과 관련이 없다.
