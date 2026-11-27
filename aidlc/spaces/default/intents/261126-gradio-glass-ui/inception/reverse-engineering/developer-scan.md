# Developer Code Scan — #37 Gradio 글래스 UI (집중 스캔)

- 저장소: `art-style-mirror` (워크스페이스 루트), 스냅숏 커밋 `45ad17b677f1f652672b78a77ede58f516094030`
- 범위: 집중 스캔(focused), 깊이 Minimal. 기존 codekb 판정은 STALE
- 프로젝트의 테스트·빌드·앱은 실행하지 않았다. 아래 내용은 파일을 읽어서 얻은 것이다.

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - `app.py`
  - `modules/explain.py`
  - `tests/test_smoke.py`
  - `tests/test_explain.py`
  - `contracts/interfaces.md`
  - `requirements.txt`
- **Skimmed only**:
  - `modules/data.py`, `modules/classify.py`, `modules/features.py` (시그니처·상수·`similar_works`·`_build_index`·`direction` 값 범위만)
  - `tests/conftest.py`, `tests/fakes.py`, `tests/test_classify.py`, `tests/test_features.py` (개수·역할만)
  - `pyproject.toml`, `.github/workflows/ci.yml`, `.github/` 파일 목록, `.gitignore`
  - `docs/notes/D.md` (D 역할 노트: `direction` 의미 변경 합의, #37 상태)
  - 저장소 루트 폴더 목록(`static/` 폴더는 아직 없음)
- **Left out**:
  - `.venv/`
  - `__pycache__/`
  - `.pytest_cache/`
  - `.ruff_cache/`
  - `.claude/`, `aidlc/` (AI-DLC 설치물·작업 공간), `.aidlc-version`, `.gitignore`의 AI-DLC 구역
  - `.git/`

### Packages Found
- `app` — 진입점 모듈 — Python — Gradio Blocks 화면(`build_demo`), 버튼 핸들러(`run`), 파이프라인 조립(`analyze`)
- `modules.explain` — 라이브러리 모듈 — Python — 신뢰 등급(`assess_confidence`), 1·2위 대조(`compare`), 결과 카드·레이더(`render_card`, `_radar`), 한국어 문구 상수
- `modules.data` / `modules.classify` / `modules.features` — 라이브러리 모듈 — Python — A·B·C Unit(훑어보기만, 상세는 기존 codekb)
- `tests` — pytest 테스트 — Python — 계약 형식 검사(`test_smoke.py`)와 D 동작 테스트(`test_explain.py`)

### Build System
- **Type**: pip + `requirements.txt`(전부 `==` 고정). 패키지 배포 없음
- **Config Files**: `requirements.txt`, `pyproject.toml`(Ruff·pytest 설정만), `.github/workflows/ci.yml`
- **Build Dependencies**: `app` → `modules.{classify,data,explain,features}`; `modules.explain` → 다른 `modules` import 없음; `tests/test_smoke.py` → `app`, 모든 `modules`; `tests/test_explain.py` → `modules.explain`(함수 안에서 `app`, `modules.features`도 import)

### APIs Discovered
- 모듈 함수 계약 — `contracts/interfaces.md` — 16개 함수(A 4, B 4, C 5, D 3) + `result` dict 11개 키 + 1일차 해석 확인 사항 3개
- D 공개 함수 — `modules/explain.py` — 3개(`assess_confidence`, `compare`, `render_card`) + 공개 상수 `EPS`, `GAP_TOL`, 등급 경계 6개, `FEATURE_KO`, `TYPE_INTRO`, `LEVEL_NOTE`, `DISCLAIMER`
- 앱 함수 — `app.py` — 3개(`analyze`, `run`, `build_demo`) + 모듈 변수 `demo`
- Gradio 화면 — `app.build_demo()` — 입력 1(`gr.Image`), 버튼 1, 출력 3(`gr.Markdown`, `gr.Plot`, `gr.JSON`), 이벤트 1(`button.click(run, ...)`)

### Frameworks & Libraries
- gradio — 6.32.0 — 웹 UI (`gr.Blocks`, `gr.Row`, `gr.Column`, `gr.Image`, `gr.Button`, `gr.Markdown`, `gr.Plot`, `gr.Accordion`, `gr.JSON`, `gr.Error`)
- matplotlib — 3.11.2 — 레이더 차트 `Figure`(pyplot 미사용, `Figure` 직접 생성), 한글 글꼴 탐색(`font_manager`)
- scipy — 1.17.1 — `jensenshannon`(JSD)
- numpy — 2.4.6 — 배열·각도 계산
- pytest — 9.2.0 — 테스트
- ruff — 0.17.6 — 포매터·린터(CI `ruff` 작업과 같은 버전)
- 그 밖에 pandas 3.1.1, scikit-learn 1.9.1, opencv-python-headless 5.1.0.95, torch 2.15.0, transformers 5.23.0, datasets 5.2.0 (이번 범위의 D 파일은 import하지 않음)

### Test Coverage
- **Test Directories**: `tests/`
- **Test Frameworks**: pytest 9.2.0. `conftest.py`가 루트를 `sys.path`에 넣고, `@pytest.mark.model`이 없는 테스트에서 `data.embed_image`·`data.embed_text`를 `tests/fakes.py`의 가짜로 바꿔 끼운다
- **Coverage Config**: absent
- `tests/test_smoke.py`: 테스트 함수 15개(매개변수 포함 17개 케이스), 그중 2개는 `model` 표시라 기본 실행에서 건너뜀
- `tests/test_explain.py`: 테스트 함수 13개(14개 케이스). `compare()` 동작 11개 + `app.analyze`의 스케치 색 특징 제외 1개(2케이스) + 빈 입력 1개

### Code Quality Indicators
- **Linting**: Ruff — `pyproject.toml`(py311, line-length 100, `extend-select = ["I"]`, `.claude`·`aidlc` 제외). CSS·JS 파일은 Ruff 대상이 아니다
- **CI/CD**: `.github/workflows/ci.yml` — `ruff (format + lint)` 작업과 `pytest (Python 3.11)` 작업
- **Documentation**: 모든 공개 함수에 한국어 docstring. `compare()` docstring이 경계 동작(비수치·NaN 건너뜀, 동점 이름 순, 미등록 화가 `KeyError`)을 자세히 적음. `render_card()`·`_radar()`는 docstring이 짧음

### Technical Debt Signals
- `modules/explain.py:22-24` 등급 경계값 6개는 임시값(#24에서 검증셋으로 확정)
- `modules/explain.py:171-173` `_radar_value()`는 `direction`을 0~180 각도로 보고 `/180` 한다. 현재 head의 `features.py:88`도 0~180 가짜 값을 만든다. 그러나 `docs/notes/D.md`에는 `direction`을 0~1 "선 방향 일관성"으로 바꾸기로 합의(PR #44·#46, 아직 이 커밋에 없음)했다고 적혀 있다. `FEATURE_KO["direction"] = "선 방향"`도 바뀔 예정
- `modules/explain.py:177` `_radar()`는 `isinstance(features.get(f), (int, float))`로 축을 고른다. `np.float32` 값은 빠진다(`compare()`의 `_finite_number`와 기준이 다름). 지금 스텁은 Python `float`를 돌려주므로 영향 없음
- `app.py`의 레이더는 `result["features"]` 전체(11개 키)로 그리므로, 스케치(`gray=True`)에서도 색 축이 그려진다. 대조(`compare`)는 선 특징만 쓴다(`app.py:43`) — 화면에서 두 기준이 다르게 보일 수 있음
- `app.py:41` 2위가 없으면 `top2 = top1`로 대조(빈 목록). `render_card`는 `top2 = None` 처리 — 두 곳의 처리 방식이 다름(동작상 문제는 없음)
- 렌더링 테스트 빈틈: `render_card()`는 `DISCLAIMER` 포함과 `Figure` 타입만, `build_demo()`는 `None`이 아님만 검사한다. 화면 구조·문구·레이더 축은 테스트가 없다
- 로깅 없음. 오류는 `gr.Error`(빈 입력), `KeyError`(`compare`의 미등록 화가, `app.py:61`의 `profiles[top1]`)로만 드러난다

## Handoff Summary
- **Intent-relevant finding**:
  - 새 UI가 그대로 지켜야 하는 외부 형식은 테스트로 고정돼 있다: `app.analyze(img)`가 11개 키 `result` dict를 돌려주고(`app.py:49-62`, `tests/test_explain.py:125-133`의 `result["gray"] is gray_input`, `"saturation" in result["features"]`), `app.run(img)`가 `(text, fig, detail)` 3개를 돌려주며 `detail["similar_works"]`에 `path`가 없어야 한다(`app.py:65-78`, `tests/test_smoke.py:186-188`), `explain.render_card(result)`가 `(str, Figure)`이고 문자열에 `DISCLAIMER`가 있어야 한다(`tests/test_smoke.py:173-179`), `app.build_demo()`가 `None`이 아니어야 한다(`tests/test_smoke.py:182-183`). 화면 구조 자체는 테스트가 없어 자유롭게 바꿀 수 있다.
  - G안 화면(결과·레이더·화풍 페이지)에 쓸 "현재 데이터"는 모두 `result`에 있다: `top3`, `styles_top3`, `p_clip_top`·`p_cv_top`, `confidence`(`level`, `margin`, `entropy`, `jsd`, `max_sim`), `keywords`, `similar`(`id`, `artist`, `style`, `score`; `path`는 스텁의 가짜 경로 `data/wikiart/...jpg`라 실제 이미지가 없음 — `modules/data.py:142`), `features`(수치 10개 + `palette` 5색 `[[r,g,b]]`), `top1_profile`, `comparison`.
  - 지금 화면(`app.py:81-98`)은 2열 `gr.Row` + 접힌 `gr.Accordion` 한 장짜리이며 `css`·`js`·`head`·정적 파일을 쓰지 않는다. `static/` 폴더는 아직 없다.
- **Risks / follow-up**:
  - `contracts/interfaces.md`는 바꾸지 않는다. `render_card()`·`analyze()`·`run()`의 반환 형식을 유지하고, G안에 필요한 추가 출력은 `run()`을 바꾸지 말고 새 핸들러·새 보조 함수(`explain.py` 안의 계약 밖 함수)로 만든다.
  - 업무 규칙을 화면에서도 지켜야 한다: 최종 순위는 `result["top3"]`(=`fuse()`)만 쓰고, 등급 "낮음"이면 Top 3 대신 CLIP·OpenCV 결과를 따로 보여 주고, 두 관점 1위가 다르면 숨기지 않고 보여 주고, `DISCLAIMER`는 항상 보여 준다(`modules/explain.py:219-264`).
  - Gradio 6.32.0에서 `css`·`js`·`head`를 넣는 위치(`gr.Blocks(...)` 인자인지 `launch(...)` 인자인지)와 `static/` 파일을 내보내는 방법(`gr.set_static_paths`, `launch(allowed_paths=...)` 등)은 설치된 버전 문서로 확인해야 한다(이번 스캔은 `.venv/`를 열지 않았고 실행도 하지 않았다). `launch()` 쪽에 넣으면 `tests/test_smoke.py`의 `build_demo()`와 `gradio app.py` 자동 재시작 경로에는 CSS·JS가 실리지 않는다는 점을 고려해야 한다.
  - `demo = build_demo()`가 import 시점에 실행된다(`app.py:102`). 정적 파일을 읽는다면 `Path(__file__)` 기준 경로를 쓰고, 파일이 없을 때도 테스트가 깨지지 않게 해야 한다.
  - `direction`의 의미(0~180 각도 → 0~1 일관성)와 레이더 라벨이 PR #44·#46으로 바뀔 예정이다. 새 UI가 `direction` 범위나 라벨 문구를 따로 하드코딩하면 그 PR과 충돌한다 — `FEATURE_KO`·`_radar_value()`를 한 곳의 기준으로 쓴다.
  - 서버 바인딩은 `127.0.0.1`로 유지한다(`app.py:105`). 사용자 입력은 계약상 `preprocess_input()`을 거쳐야 하므로, 카메라 입력을 추가해도 `analyze()` 경로를 그대로 탄다.
  - 팀 규칙상 PR은 파일 1~3개·변경 300줄 이내인데, 이 intent는 `app.py`, `modules/explain.py`, `static/g.css`, `static/g.js`(+테스트) 4개 이상을 바꾼다. 커밋·PR 나누기를 요구사항 단계에서 정해야 한다.
