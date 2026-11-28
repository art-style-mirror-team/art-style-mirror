# 빌드 안내 — #37 G안 Gradio 화면

## 준비

- Python 3.11, 저장소 루트에서 가상환경을 만든다(Windows: `py -3.11 -m venv .venv`, macOS/Linux: `python3.11 -m venv .venv`).
- 의존성 설치: `.venv/Scripts/python -m pip install -r requirements.txt` (Gradio 6.32.0 고정). 이 작업으로 새 패키지는 없다.
- 환경 변수: 필요 없음. `GRADIO_TEMP_DIR`을 지정하면 업로드 폴더가 그 경로가 되고, `app.py`의 업로드 경로 검사도 그 폴더를 기준으로 한다.

## 빌드

Python 앱이라 컴파일 단계가 없다. 정적 파일 `static/g.css`, `static/g.js`는 `build_demo()`가 실행될 때 읽어 화면에 싣는다. 파일이 없으면 `build_demo()`가 원인을 담은 오류를 낸다.

## 빌드 확인

```
.venv/Scripts/python -m ruff format --check .
.venv/Scripts/python -m ruff check .
.venv/Scripts/python -m pytest -q
.venv/Scripts/python app.py   # http://127.0.0.1:7860 이 200으로 응답하는지
```

## 문제 해결

- 화면이 비어 보이면 브라우저 개발자 도구 콘솔에서 `g.js` 오류를 확인한다(`js_on_load`로 실행된다).
- 카메라 미리보기는 `127.0.0.1`·HTTPS에서만 된다. 휴대폰에서 `http://192.168.x.x:7860`으로 열면 선택 창으로 대신 동작한다.
- 헤드리스 Edge로 화면을 찍을 때는 `--user-data-dir`를 따로 줘야 이미 열린 Edge와 충돌하지 않는다.

## 범위 추가 후 참고 (2026-11-27)

- 새 의존성은 없다.
- 명화 이미지는 저장소 루트의 `data/` 아래 실제 이미지 파일이 있을 때만 화면에 나온다. 지금은 데이터가 스텁이라 파일이 없고, 명화 페이지는 이름 카드로 보인다.
- 기록은 브라우저 `localStorage`(키 `g-history-v1`)에 저장된다. 지우려면 기록 화면의 "모두 지우기"를 누르거나 브라우저 사이트 데이터를 지운다.
- 앱을 다시 띄우기 전에 7860 포트에 이전 앱이 떠 있지 않은지 확인한다. 떠 있으면 예전 화면 코드가 나온다.
