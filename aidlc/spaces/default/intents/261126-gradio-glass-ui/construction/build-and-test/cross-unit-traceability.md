# 요구사항 커버리지 — #37 G안 Gradio 화면

**판정: 통과** — 요구사항 45개(FR 40, NFR 5)가 모두 코드나 테스트 파일에 연결돼 있고, 빠진 것이 없다. 이 작업은 Unit을 나누지 않아서 모두 code-generation 단계 하나가 만든다.

| ID | 만든 곳 |
|---|---|
| FR1.1, FR1.2, FR1.4–FR1.7 | `static/g.js` |
| FR1.3, FR1.8 | `static/g.css` |
| FR1.9 | `app.py` |
| FR2.1, FR2.3 | `static/g.js` |
| FR2.2, FR2.4 | `app.py` |
| FR2.5 | `tests/test_app.py` |
| FR3.1, FR3.3, FR3.4 | `modules/explain.py` |
| FR3.2, FR3.7 | `static/g.js` |
| FR3.5, FR3.6 | `tests/test_explain.py` |
| FR4.1, FR4.4 | `modules/explain.py` |
| FR4.2 | `tests/test_explain.py` |
| FR4.3, FR4.5 | `static/g.js` |
| FR5.1, FR5.2, FR5.5 | `static/g.js` |
| FR5.3, FR5.4 | `modules/explain.py` |
| FR6.1, FR6.2 | `static/g.css` |
| FR6.3–FR6.6 | `static/g.js` |
| FR7.1–FR7.3 | `tests/test_explain.py` |
| NFR1 | `tests/test_app.py` |
| NFR2, NFR3 | `static/g.css` |
| NFR4 | `app.py` |
| NFR5 | `tests/test_explain.py` |

- 연결이 있다는 뜻은 만든 파일이 있다는 것이다.
- FR1–FR6 중 브라우저 동작이 필요한 항목은 실제 브라우저에서 첫 화면만 확인했다. 확인 범위는 `build-and-test-summary.md`의 목표 표에 있다.

## 범위 추가 (2026-11-27)

**판정: 통과** — 새로 생기거나 바뀐 요구사항 26개(FR1.7, FR3.7, FR4.5–FR4.7, FR6.3, FR7.4, FR8.1–FR8.9, FR9.1–FR9.10, NFR4, NFR6, NFR7)가 모두 코드나 테스트에 연결돼 있다.

| ID | 만든 곳 |
|---|---|
| FR8.1, FR8.5, FR8.8, NFR4, NFR7 | `app.py` (`tests/test_app.py`로 확인) |
| FR7.4, FR8.2 | `modules/explain.py` (`tests/test_explain.py`로 확인) |
| FR1.7, FR3.7, FR4.5–FR4.7, FR6.3, FR8.3, FR8.4, FR8.6, FR8.7, FR8.9 | `static/g.js`, `static/g.css` |
| FR9.1–FR9.10, NFR6 | `static/g.js`, `static/g.css` |

- 브라우저 동작이 필요한 항목은 `test-results.md`의 브라우저 확인 6가지 경우로 확인했다.
