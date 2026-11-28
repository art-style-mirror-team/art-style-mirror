# 단위 테스트 안내 — #37 G안 Gradio 화면

## 테스트 도구

- pytest(이미 설치, `requirements.txt` 고정). 설정은 `pyproject.toml`과 `tests/conftest.py`(저장소 루트를 import 경로에 넣고, 실제 모델 함수를 `tests/fakes.py` 가짜로 바꿔 끼움).
- 새 설정 파일은 만들지 않는다.

## 이 작업의 테스트 실행 (Windows)

이 작업이 만든·바꾼 테스트만 돌린다:

```
.venv/Scripts/python -m pytest tests/test_explain.py tests/test_app.py -q
```

계약 형식 검사(그대로 통과해야 함):

```
.venv/Scripts/python -m pytest tests/test_smoke.py -q
```

코드 스타일:

```
.venv/Scripts/python -m ruff format --check app.py modules/explain.py tests/test_explain.py tests/test_app.py
.venv/Scripts/python -m ruff check app.py modules/explain.py tests/test_explain.py tests/test_app.py
```

## 순서

팀 규칙: 계약 형식 검사(`tests/test_smoke.py`)는 먼저 있고 그대로 통과해야 하며, 동작 테스트는 구현과 함께 작성해 같은 PR에서 실행한다. 고치기 전에 기준선을 한 번 기록한다(계획 Step 1).

## 테스트 범위 (Minimal)

- `tests/test_explain.py`에 `build_view()` 테스트 6개: 보통 등급 정상 경로(JSON 직렬화), 낮음 등급, 스케치 레이더 축 5개, 두 관점 1위 같음·다름, 한글 이름표 밖 화가, 레이더 값 0~1 자르기.
- 새 `tests/test_app.py`에 5개: `analyze_view` 정상 경로(단계 4개 후 결과), 업로드 폴더 밖 경로 거부, 이미지가 아닌 파일, `path` 없는 요청, `_analyze_steps`와 `analyze()` 결과 같음.
- `static/g.js`·`static/g.css`는 이 저장소에 JS 테스트 도구가 없어 자동 테스트를 쓰지 않는다. `python app.py` 후 브라우저 360×780에서 계획 Step 8의 흐름을 손으로 확인하고 결과를 `code-summary.md`에 적는다.

## 커버리지 목표

- 커버리지 하한 없음(팀 규칙). 조건은 `pytest` 전체 통과다. 전체 실행은 Build and Test가 한다.

## 가짜 값과 테스트 데이터

- 모델 함수는 `tests/conftest.py`가 가짜로 바꿔 끼운다. 새 모델 함수는 만들지 않는다.
- `build_view()` 테스트는 `app.analyze()`로 만든 `result`를 쓰고, 등급·특징 값이 필요한 경우만 dict를 복사해 값을 바꾼다.
- `analyze_view` 테스트는 `tmp_path`에 PNG를 만들고, 업로드 폴더 검사는 monkeypatch로 그 폴더를 업로드 폴더로 지정해 확인한다. 업로드 폴더 밖 경로 테스트도 `tmp_path` 안의 다른 폴더를 쓴다.

## 범위 추가 (2026-11-27): 명화 비교·기록

- 실행 명령은 위와 같다(`tests/test_explain.py tests/test_app.py`).
- `tests/test_explain.py`에 `build_view(result, works)` 테스트 6개: `works` 없음, 1위 화가 작품 제목, 낮음 등급 제목, 명화 특징 없음, 대표색 hex·`near`/`far`, `kind`·`history_name`.
- `tests/test_app.py`에 4개: 비교 명화 고르기(1위 화가 먼저·낮음이면 비슷한 순·후보 없음), `data/` 밖 경로 거부, `data/` 안 실제 PNG에서 data URL과 특징 생성, `analyze_view` 결과의 `compare`.
- 명화 파일 테스트는 `tmp_path` 안에 `data/` 폴더와 PNG를 만들고, monkeypatch로 저장소 루트(또는 데이터 폴더) 상수를 그 위치로 바꾼다. `classify.similar_works`는 monkeypatch로 정해진 후보를 돌려주게 한다.
- 기록·명화 화면(JS)은 자동 테스트 대신 계획 Step 15의 브라우저 흐름으로 확인하고 결과를 `code-summary.md`에 적는다.
