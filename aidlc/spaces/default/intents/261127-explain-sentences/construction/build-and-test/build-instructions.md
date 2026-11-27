# Build Instructions — #22 해석 문장 템플릿

## 의존성 설치

```bash
py -3.11 -m venv .venv            # Windows. macOS/Linux: python3.11 -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

이번 변경은 새 의존성을 추가하지 않는다(`requirements.txt` 변경 없음).

## 환경 설정

- 환경변수나 비밀값은 필요 없다.
- 기본 `pytest`는 `tests/conftest.py`가 모델 함수를 `tests/fakes.py`의 가짜로 바꿔 끼우므로 모델을 내려받지 않는다.

## 빌드

Python이라 따로 컴파일하지 않는다. 문법과 가져오기 확인용으로 다음을 실행한다.

```bash
.venv\Scripts\python -m compileall -q modules app.py
```

## 빌드 확인

```bash
.venv\Scripts\ruff format --check .
.venv\Scripts\ruff check .
.venv\Scripts\python -m pytest -q
```

CI(`.github/workflows/ci.yml`)는 PR마다 같은 Ruff 검사와 `pytest`를 실행한다.

## 문제 해결

- 한글 폰트 경고: 레이더 차트는 `Malgun Gothic` 등 한글 폰트를 찾고, 없으면 기본 폰트로 그린다. 테스트는 폰트 유무와 상관없이 통과한다.
- `cv2` 가져오기 실패: `requirements.txt`로 `opencv-python`을 설치했는지 확인한다.
