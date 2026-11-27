# Cross-Unit Traceability — #11 선형 분류기

Unit 분할이 없는 단일 변경(express, zero-Unit)이라 교차 Unit 의존은 없다. 요구 → 테스트 매핑만 둔다.

| 요구 | 구현 | 검증 테스트 (`tests/test_classify.py`) |
| --- | --- | --- |
| FR1.1 `LINEAR_PATH` | `modules/classify.py` | (간접) import·상수 로드 |
| FR2.1 학습셋 한정 | `_fit_linear` | `test_fit_linear_uses_train_split_only` |
| FR2.2~2.5 학습·정규화·라벨 | `_fit_linear` | 위 + `test_linear_logits_biased_input_argmax` |
| FR3.1~3.2 저장 형식 | `_save_linear` | `test_linear_logits_save_load_roundtrip`, `test_save_linear_resave_updates_cache` |
| FR4.1 로드 | `_load_linear` | `test_linear_logits_save_load_roundtrip` |
| FR4.2 파일 없음 예외 | `_load_linear` | `test_load_linear_missing_file` |
| FR4.3 cache_clear | `_load_linear`/`_save_linear` | `test_save_linear_resave_updates_cache` |
| FR5.2 1차원 ValueError | `_linear_logits` | `test_linear_logits_rejects_1d` |
| FR5.3 0장 입력 | `_linear_logits` | `test_linear_logits_empty_input` |
| FR5.4 치우친 입력 argmax | `_linear_logits` | `test_linear_logits_biased_input_argmax` |
| FR5.5 반환 모양 | `_linear_logits` | `test_linear_logits_shape` |
| NFR1 결정성/라운드트립 | 전체 | `test_linear_logits_save_load_roundtrip` |
| NFR2 형식 일관성/softmax | `_linear_logits` | `test_linear_logits_softmax_matches_predict_proba` |
| NFR3 전체 테스트 통과 | 전체 | `pytest -q` → 123 passed |
| NFR4 Ruff | 전체 | `ruff format --check`·`ruff check` 통과 |
