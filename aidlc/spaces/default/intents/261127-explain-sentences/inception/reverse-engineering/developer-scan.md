# Developer Code Scan — explain-sentences (#22)

## Run Record

- Date: 2026-11-27
- Commit: f7107b399e1db543a13e93ccca3d440525e3aff2 (브랜치 `feat/22-explain-sentences`)
- 방식: 집중 스캔(focused), 깊이 Minimal. 기존 저장소 판정 STALE. 프로젝트의 테스트·빌드·앱은 실행하지 않았다.

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - modules/explain.py
  - app.py
  - contracts/interfaces.md
  - tests/test_explain.py
  - tests/test_smoke.py
  - tests/fakes.py
  - requirements.txt
- **Skimmed only**:
  - modules/data.py (`KEYWORDS`, `clip_keywords` 스텁만)
  - modules/classify.py (함수 목록과 `TODO` 표시만)
  - modules/features.py (상수 `COLOR_FEATURES`·`LINE_FEATURES`와 함수 목록만)
  - docs/plan.md (#22 행, D 역할 설명만)
  - docs/notes/D.md
  - 기존 CodeKB 9개 문서(`aidlc/spaces/default/codekb/art-style-mirror/`, 병합 입력으로만 읽음)
- **Left out**:
  - .venv/
  - __pycache__/, .pytest_cache/, .ruff_cache/
  - AI-DLC 설치물(`.claude/`, `aidlc/` 작업 공간 — 위 CodeKB 병합 입력 제외, `.aidlc-version`)

### Packages Found
- `modules` — Python 패키지(앱 내부) — Python 3.11 — A·B·C·D 4개 Unit 모듈
- `app` — 단일 스크립트 진입점 — Python — Gradio 화면 + 파이프라인 조립
- `tests` — pytest 테스트 모음 — Python — 계약 형식·동작 테스트, 가짜 모델

### Build System
- **Type**: pip + `requirements.txt`(전부 `==` 고정). 빌드 단계 없음
- **Config Files**: `requirements.txt`(깊게), `pyproject.toml`(이번에는 열지 않음, 기존 저장소 기준 Ruff·pytest 설정)
- **Build Dependencies**: `app` → `modules.{features,data,classify,explain}`. `modules.explain` → 내부 import 없음

### APIs Discovered
- 모듈 함수 계약 — `contracts/interfaces.md` D절 — 3개(`assess_confidence`, `compare`, `render_card`) + `result` dict 11개 키
- Gradio UI — `app.py` — 이벤트 1개(`button.click(run, ...)`)
- HTTP/DB API 없음

### Frameworks & Libraries
- gradio — 6.32.0 — 화면 (`app.py`)
- matplotlib — 3.11.2 — 레이더 `Figure`, 한글 글꼴 탐색 (`explain.py`)
- scipy — 1.17.1 — `jensenshannon` (`explain.py`)
- numpy — 2.4.6 — 배열·수치
- pytest — 9.2.0 — 테스트
- ruff — 0.17.6 — 포매터·린터
- (설치만, 이번 범위에서 import 확인 안 함) pandas 3.1.1, scikit-learn 1.9.1, opencv-python-headless 5.1.0.95, torch 2.15.0, transformers 5.23.0, datasets 5.2.0

### Test Coverage
- **Test Directories**: `tests/`
- **Test Frameworks**: pytest (`model` 마커, `tests/fakes.py`의 `FAKES`로 `data.embed_image`·`embed_text` 바꿔 끼움)
- **Coverage Config**: absent
- `tests/test_explain.py`: 16개 함수(17개 케이스) — `compare()` 경계 동작 12개, `app.analyze` 스케치 대조 기준 1개(파라미터 2), 레이더 `_radar()` 3개(#45). **`render_card()` 문장 동작 테스트는 없다.**
- `tests/test_smoke.py`: 15개 함수(17개 케이스, `model` 2개 기본 건너뜀). `render_card()`는 `(str, Figure)`와 `DISCLAIMER` 포함만 검사(`test_pipeline_end_to_end`, 컬러·스케치 2종)

### Code Quality Indicators
- **Linting**: Ruff (`pyproject.toml`, line-length 100, `I`), CI에서 실행
- **CI/CD**: `.github/workflows/ci.yml`(이번에는 열지 않음, 기존 저장소 기준 ruff + pytest 두 작업)
- **Documentation**: 공개 함수 모두 한국어 docstring. `render_card()` docstring은 한 줄뿐

### Technical Debt Signals
- `render_card()`의 문구 대부분이 함수 안 f-string에 하드코딩돼 있다. 상수로 빠진 것은 `TYPE_INTRO`, `LEVEL_NOTE`, `DISCLAIMER`, `FEATURE_KO`뿐 (`modules/explain.py:38-48`, `209-264`)
- 조사 미처리: `"{특징}이(가) {top1} 평균에 더 가까워요."` (`explain.py:248`)
- 입력 유형이 제목 한 줄(`TYPE_INTRO`)에만 쓰인다. 등급 문구·대조 문장·관점 엇갈림 문장은 입력 유형과 무관하게 같다. 스케치도 "분위기는 …, **색감**·선은 …" 문장이 나온다(`explain.py:239`)
- `result["gray"]`는 `render_card()`에서 쓰지 않는다
- 등급 "높음"의 `LEVEL_NOTE`는 빈 문자열이라 높음일 때 해설 문장이 없다(`explain.py:44`, `234`)
- CLIP 키워드는 문장이 아니라 `키워드(점수)` 나열이다(`explain.py:243`)
- `LEVEL_NOTE[level]`은 계약 밖 값에서 `KeyError`(계약상 세 값만 오므로 수용 가능), `TYPE_INTRO`는 `.get(..., '이 이미지는')`로 대체값이 있음 — 두 상수의 실패 방식이 다르다
- 2위 없음 처리 이중화: `app.analyze`는 `top2 = top1`, `render_card`는 `top2 = None` (`app.py:41`, `explain.py:215`)
- `tests/test_explain.py` 모듈 docstring은 "compare() 동작 테스트 (#21)"인데 레이더 테스트(#45)도 들어 있다

## Handoff Summary
- **Intent-relevant finding**: #22가 바꿀 곳은 `modules/explain.py`의 문구 상수 `TYPE_INTRO`(38-42행: `photo` "사진을 그림처럼 놓고 보면", `painting` "이 그림은", `sketch` "이 스케치의 선을 보면")·`LEVEL_NOTE`(43-47행: 높음 "", 보통 "애매한 부분이 있어요.", 낮음 "뚜렷하게 닮은 화가가 없어요.")와 `render_card()`(209-264행)다. 지금 입력 유형은 제목에만, 등급은 낮음/그 외 두 갈래 분기(218-235행)에만, CLIP 키워드는 `**CLIP 키워드**: k(0.71), …` 나열(243행)에만 쓰인다. 계약(`contracts/interfaces.md` 48행)은 `render_card(result) -> (str, Figure)`만 고정하고 문장 내용은 정하지 않는다. `result` 11개 키(50-64행)와 `level ∈ {높음, 보통, 낮음}`, `input_type ∈ {photo, painting, sketch}`가 입력이다. 3×3 문장 검사는 `app.analyze()`를 거치지 않고 계약 형식의 `result` dict를 직접 만들어 `render_card()`에 넣으면 된다(`detect_type` 스텁은 `emb[:3]` argmax라 유형을 고를 수 없음).
- **Risks / follow-up**:
  - `tests/test_smoke.py::test_pipeline_end_to_end`의 `explain.DISCLAIMER in text`와 `(str, Figure)` 반환은 그대로 지켜야 한다. `app.build_demo()`도 `explain.DISCLAIMER`를 쓴다(`app.py:86`).
  - 등급 "낮음"이면 Top 3 대신 CLIP·OpenCV 결과를 따로 보여주고, 두 관점 1위가 다르면 숨기지 않고 보여준다(project.md DECIDED, `explain.py:218-239`). 문장 개편에서도 유지해야 한다.
  - 최종 순위는 `top3`(= `fuse()`)만 쓴다. 키워드·OpenCV 문장이 순위를 바꾸면 안 된다.
  - 스케치는 대조가 선 특징만이라(`app.py:43`) 문장에 색 표현을 넣지 않는 것이 자연스럽다. `result["gray"]`와 `input_type == "sketch"`가 엇갈릴 수 있다(`docs/notes/D.md` "#25 통합 때 볼 것").
  - "선 방향 일관성"이 문장 안에서 자연스럽게 읽히는지 확인하라는 메모가 있다(`docs/notes/D.md` 81행).
  - 수정 범위는 `modules/explain.py`, `tests/test_explain.py`뿐. `app.py`·다른 Unit·계약은 바꾸지 않는다.
