# Build Instructions — #11 선형 분류기

순수 Python 패키지(빌드 산출물 없음). "빌드"는 린트 + 테스트 수집으로 본다.

## 사전 준비 (이미 구성됨)

```
py -3.11 -m venv .venv        # Windows. macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

## 빌드·정적 검사

```
.venv\Scripts\python -m ruff format --check .
.venv\Scripts\python -m ruff check .
```

## 전체 테스트

```
.venv\Scripts\python -m pytest
```

CI(`.github/workflows/ci.yml`)가 PR마다 `ruff (format + lint)`와 `pytest`를 같은 방식으로 돌린다.
실제 모델 테스트(`@pytest.mark.model`)는 기본 실행·CI에서 건너뛴다(`pytest --run-model`로 실제 실행).
