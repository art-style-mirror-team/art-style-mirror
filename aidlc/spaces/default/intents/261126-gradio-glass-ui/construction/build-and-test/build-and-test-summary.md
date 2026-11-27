# 빌드·테스트 요약 — #37 G안 Gradio 화면

## 상태

- **빌드:** 성공. 새 의존성은 없다(Gradio 6.32.0).
- **테스트 종류:** 단위 테스트만(Minimal 전략). 추가 테스트 안내 파일(통합·성능·보안)은 만들지 않았다.
- **커버리지 기대치:** 하한 없음. 조건은 `pytest` 전체 통과다(팀 규칙).

## Target Verification Matrix

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| TC-suite-green | code-generation-plan.md `## Testing Contract` (scope_floor) | 기존 테스트 전체 통과 | 55 passed, 2 skipped (기준선 38 passed, 2 skipped) | `pytest -q` | build-and-test | Met |
| TC-smoke-unchanged | Testing Contract `ordering`, project.md Testing Posture | `tests/test_smoke.py` 수정 없이 통과 | 15 passed, 2 skipped, 파일 수정 없음 | `pytest tests/test_smoke.py -q`, `git status` | build-and-test | Met |
| TC-req-tests | Testing Contract `strategy_volume` (minimal) | 요구사항마다 검증 가능한 테스트, 컴포넌트마다 정상 경로 1개 이상 | explain 7개·app 9개 실행 통과, 커버리지 표 빠짐 없음 | `pytest tests/test_explain.py tests/test_app.py -q` (31 passed), `cross-unit-traceability.md` | build-and-test | Met |
| TC-ruff | project.md Code Style | `ruff format`·`ruff check` 통과 | 27 files already formatted, All checks passed! | `ruff format --check .`, `ruff check .` | build-and-test | Met |
| BR-first-screen | requirements.md FR1.1–FR1.3, FR1.9 | 첫 화면 요소가 실제 브라우저에서 그려짐 | 그려짐(헤드리스 Edge, 520·약 500px 폭) | `test-results.md` 브라우저 확인 | build-and-test | Met |
| BR-flow-360 | requirements.md FR1.4–FR6.6, NFR2 | 360×780에서 전체 흐름·전환·드래그·가로 스크롤 없음 | 6개 시나리오 통과, 화면 문제 4개를 고친 뒤 재실행 통과 | `test-results.md` "360×780 흐름 확인" (Playwright + Edge, 가짜 모델) | build-and-test | Met |
| BR-reduced-motion | requirements.md NFR3 | 애니메이션 줄이기에서 움직임 없이 최종 상태 | 전환 직후 최종 상태 | 같은 확인 | build-and-test | Met |

처음 승인 때 두 항목은 Unverified였다. 승인 뒤 사람의 요청으로 360×780 흐름을 자동 조작으로 확인했고, 찾은 화면 문제 4개를 `g.css`·`g.js`에서 고쳤다. 실제 휴대폰과 실제 CLIP 결과 화면은 아직 보지 않았다.

### 범위 추가 후 목표 (2026-11-27)

| Target ID | Source | Expected | Actual | Evidence | Owning Stage | Verdict |
|---|---|---|---|---|---|---|
| TC-suite-green-2 | Testing Contract `scope_floor` | 기존 테스트 전체 통과 | 71 passed, 2 skipped | `pytest -q` | build-and-test | Met |
| TC-smoke-unchanged-2 | project.md Testing Posture | `tests/test_smoke.py` 수정 없이 통과 | 수정 없음, 전체 실행에서 통과 | `git status`, `pytest -q` | build-and-test | Met |
| TC-ruff-2 | project.md Code Style | 포맷·린트 통과 | 27 files already formatted, All checks passed! | `ruff format --check .`, `ruff check .` | build-and-test | Met |
| BR-compare | requirements.md FR8, FR4.6–FR4.7, FR3.7, FR6.3 | 명화 페이지·탭이 파일 있음·없음 모두 동작 | 통과 | `test-results.md` "범위 추가 후 다시 실행" | build-and-test | Met |
| BR-history | requirements.md FR1.7, FR9, NFR6 | 저장·목록·밀어 지우기·되돌리기·모두 지우기·열기·저장소 막힘 | 통과 | 같은 곳 | build-and-test | Met |
| BR-360-2 | requirements.md NFR2, NFR3 | 360×780 가로 스크롤 없음, 애니메이션 줄이기 | 통과 | 같은 곳 | build-and-test | Met |
| BR-real-device | requirements.md NFR2 | 실제 휴대폰 터치·실제 명화 파일 | 실행 안 함 | 기기와 실제 데이터(#3·#4)가 없음 | build-and-test | Unverified |

## 준비 상태

- **빌드:** 됨.
- **테스트:** 됨. Python 테스트는 모두 통과했다.
- **배포:** 해당 없음. 자동 배포 없이 로컬 실행만 하는 팀 규칙 때문이다. 브라우저 흐름은 사람이 확인한 뒤 PR ①②③으로 올린다.

## 남은 일

- 실제 휴대폰에서 실제 CLIP 결과로 한 번 보기(카메라 권한 창, 손가락 끌기 느낌).
- PR ② `g.css`+`g.js`는 약 2286줄이라 팀 규칙(300줄)을 넘는다. 본문에 이유를 적거나 CSS·JS를 따로 낸다.
- 명화 페이지가 360×780에서 시트보다 약 14px 길어 시트 안에서 조금 스크롤된다(가로 넘침은 없음).
- PR ④ 명화 비교와 ⑤ 기록도 300줄을 넘으므로 본문에 이유를 적는다. 두 기능을 #37에 넣은 사람의 결정도 적는다.
