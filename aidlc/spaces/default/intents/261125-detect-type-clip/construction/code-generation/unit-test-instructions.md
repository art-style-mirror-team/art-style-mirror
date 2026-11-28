# 테스트 실행 명령 (#8 `detect_type`)

러너는 이미 구성되어 있다(`tests/conftest.py`, `pyproject.toml`). 새 러너 준비는 없고 기존 명령으로 갈음한다.

## 이 이슈 범위 테스트

```
.venv\Scripts\python -m pytest tests/test_classify.py tests/test_smoke.py -q
```

(fallback: `python -m pytest tests/test_classify.py tests/test_smoke.py -q`)

## 전체 스위트 (Step 4에서 1회)

```
.venv\Scripts\python -m pytest -q
```

(fallback: `python -m pytest -q`)

## 메모

- `model` 표시 테스트는 기본 실행/CI에서 건너뛴다. 실제 모델까지 돌리려면 `--run-model`.
- `model` 표시가 없는 테스트는 `tests/conftest.py`의 autouse fixture가 `modules.data`의 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다. 그래서 `detect_type`은 `data.embed_text`를 **모듈 경유**로 불러야 한다.
- 검증 결과(2026-11-25): `pytest tests/test_smoke.py -q` → 15 passed, 2 skipped.
