# Build Instructions — #13 `similar_works()`

## 전제 / 의존성

- Python 3.11. 의존성은 `requirements.txt`에 고정(numpy, pandas, pytest, ruff 등).
- 가상환경(Windows):

```
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## 빌드

- 이 프로젝트는 컴파일/번들 단계가 없는 순수 Python 패키지다. 별도 빌드 산출물 없음.
- "빌드 검증"은 import가 깨지지 않고 테스트가 수집·실행되는 것으로 갈음한다.

## 빌드/정적 검증 명령

```
.venv\Scripts\ruff format --check .
.venv\Scripts\ruff check .
```

(개발 중에는 `ruff format .`로 정리 후 `ruff check --fix .`)

## 흔한 문제

- `@pytest.mark.model` 테스트가 모델을 내려받으려 하면 오래 걸림 → 기본 실행은 자동으로 건너뜀
  (`conftest.py`가 `HF_HUB_OFFLINE=1` 설정). 실제 모델까지 돌리려면 `pytest --run-model`.
- 모델 함수가 가짜로 바뀌지 않으면 → 다른 모듈이 `data.embed_image(...)`처럼 모듈을 통해 부르는지 확인.
