# Test Results — #11 선형 분류기 (실제 실행)

실행 환경: Windows, Python 3.11 venv, scikit-learn 1.9.1, joblib 1.6.0, pytest 9.2.0.

## 정적 검사

| 명령 | 결과 |
| --- | --- |
| `ruff format --check .` | 27 files already formatted |
| `ruff check .` | All checks passed! |

## 테스트

| 범위 | 명령 | 결과 |
| --- | --- | --- |
| 이번 변경 집중 | `pytest tests/test_classify.py -q` | **17 passed** (기존 8 + #11 신규 9) |
| 전체(기준선 포함) | `pytest -q` | **123 passed, 5 skipped** |

- skip 5건은 전부 `@pytest.mark.model` 테스트로, `--run-model` 없이 건너뛴 것이다(정상).
- 회귀 없음: 변경 전 기준선(스모크 24+classify 8 통과)에서 추가된 9개 테스트가 모두 통과하고
  나머지 스위트는 그대로 그린이다.
- 정확도·ECE 같은 평가 수치는 이 범위가 아니다(검증셋 전용, #26).

## #11 신규 테스트 9개

학습셋 한정, 치우친 입력 argmax, 저장→로드 라운드트립 z 동일, 반환 모양, 1차원 `ValueError`,
0장 입력, 파일 없음 `FileNotFoundError`, softmax=predict_proba 동치(R1), 재저장 C 반영(R2).
