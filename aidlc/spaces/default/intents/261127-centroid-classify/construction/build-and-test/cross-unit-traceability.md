# Cross-Unit Traceability — #10 중심점 방식 판정

판정: **PASS** — 추적한 모든 요구사항 ID가 빌드/테스트로 커버됨. 미커버 항목 없음.

출처: `aidlc engine sensor-traceability --stage build-and-test` (`"pass": true`, `"uncovered": []`).

| ID | Covered | Owning Stage | Target 파일 |
|----|---------|--------------|-------------|
| FR1.1 | ✔ | code-generation | `modules/classify.py` |
| FR1.2 | ✔ | code-generation | `modules/classify.py` |
| FR1.3 | ✔ | code-generation | `modules/classify.py` |
| FR2.1 | ✔ | code-generation | `modules/classify.py` |
| FR2.2 | ✔ | code-generation | `modules/classify.py` |
| FR2.3 | ✔ | code-generation | `modules/classify.py` |
| FR3.1 | ✔ | code-generation | `tests/test_classify.py` |
| FR3.2 | ✔ | code-generation | `tests/test_classify.py` |
| FR3.3 | ✔ | code-generation | `tests/test_classify.py` |
| FR3.4 | ✔ | code-generation | `tests/test_classify.py` |
| FR3.5 | ✔ | code-generation | `tests/test_classify.py` |
| NFR1 | ✔ | code-generation | `modules/classify.py` (계약·predict_clip 불변) |
| NFR2 | ✔ | build-and-test | `tests/test_classify.py` + 전체 스위트 |
| NFR3 | ✔ | build-and-test | Ruff(`modules/classify.py` 등) |
| NFR4 | ✔ | code-generation | `tests/test_classify.py` (학습셋 전용 검사) |

## 미커버 요소

- 없음.
