# Build Instructions — #8 `detect_type`

Python 3.11 프로젝트(컴파일/번들 없음). "빌드"는 의존성 설치 + 임포트/수집 확인이다.

## 의존성 설치

```
py -3.11 -m venv .venv            # 최초 1회 (Windows). macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

이 변경은 새 의존성을 추가하지 않는다(기존 numpy·pytest·ruff로 충분).

## 환경 설정

- 별도 env 변수·로컬 서비스 불필요.
- 기본/CI 테스트는 모델을 내려받지 않는다. `tests/conftest.py`가 `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`을 세팅하고 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼운다.

## 빌드 검증

```
.venv\Scripts\python -m pytest --collect-only -q      # 수집 오류(임포트 오류) 확인
```

## 스타일 검사(빌드 게이트)

```
.venv\Scripts\python -m ruff format --check .
.venv\Scripts\python -m ruff check .
```

## 자주 겪는 문제

- `ModuleNotFoundError`: 가상환경 활성화 여부와 `pip install -r requirements.txt` 확인.
- 모델을 내려받으려다 멈춤: `model` 표시 없는 테스트인데 `data.embed_*`를 모듈 경유로 부르지 않아 가짜가 안 끼워진 경우. `detect_type`은 `data.embed_text(...)`로 부른다.
