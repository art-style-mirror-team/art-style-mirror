# 개발자 코드 스캔 — art-style-mirror

- 스캔 범위: 저장소 전체(`./`), 첫 스캔(NO_STORE), 깊이 Standard
- 기준 커밋: `b481de72629367d78716a04480687bcbf4882ec5` (작업 트리에 추적되지 않은 `aidlc/spaces/default/intents/`만 있음 — AI-DLC 기록, 스캔 대상 아님)
- 프로젝트의 테스트·빌드·프로그램은 실행하지 않았다. 아래 내용은 모두 파일을 읽어서 얻은 것이다.

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - `app.py`
  - `modules/__init__.py`
  - `modules/data.py`
  - `modules/classify.py`
  - `modules/features.py`
  - `modules/explain.py`
  - `scripts/build_index.py`
  - `scripts/build_profiles.py`
  - `tests/conftest.py`
  - `tests/test_smoke.py`
  - `contracts/interfaces.md`
  - `requirements.txt`
  - `.github/workflows/ci.yml`
  - `.github/pull_request_template.md`
  - `.github/ISSUE_TEMPLATE/contract-change.yml`
  - `docs/plan.md`
  - `README.md`
  - `AGENTS.md` (프로젝트가 쓴 부분 전체 — AI-DLC 표시 구역 없음)
  - `CLAUDE.md`
  - `notebooks/eval.ipynb`
  - `.gitattributes`
  - `.gitignore` (프로젝트 부분: Python 템플릿 + `# --- art-style-mirror` 구역. `# BEGIN AI-DLC:gitignore` 구역은 제외)
- **Skimmed only**:
  - `docs/aidlc-guide.md` (팀이 쓴 AI-DLC 사용 안내. 제목 구조만 확인 — 제품 코드와 무관)
  - `LICENSE` (MIT, 첫 줄만 확인)
  - `artifacts/`, `samples/` (`.gitkeep`만 있음)
- **Left out**:
  - `.venv/` (의존성 폴더, `.gitignore` 대상)
  - `__pycache__/`, `modules/__pycache__/`, `tests/__pycache__/` (바이트코드 캐시)
  - `.pytest_cache/` (도구 캐시)
  - `.git/`
  - AI-DLC 설치물: `.claude/`, `aidlc/`, `.aidlc-version`, `.gitignore`의 AI-DLC 구역 (브리프 지시에 따라 문서화하지 않음)

### Packages Found
- `modules` — Python 패키지 — Python 3.11 — 4개 Unit의 함수 모듈(`data`, `classify`, `features`, `explain`). `__init__.py`는 docstring 한 줄뿐, 재내보내기 없음
- `app.py` — 진입 스크립트 — Python — Gradio 화면과 파이프라인 조립(`analyze()`, `run()`, `build_demo()`)
- `scripts/` — 일회성 사전 계산 스크립트(패키지 아님, `__init__.py` 없음) — Python — `build_index.py`(#3·#4), `build_profiles.py`(#19). 둘 다 `raise NotImplementedError`
- `tests/` — pytest 테스트 — Python — `conftest.py`(저장소 루트를 `sys.path`에 추가), `test_smoke.py`(계약 형식 + 전체 파이프라인)
- `notebooks/eval.ipynb` — Jupyter 노트북 — 마크다운 셀 1개뿐(B의 #12·#14·#15·#26 계획)
- `contracts/interfaces.md` — 문서 — 함수 이름·입출력 형식의 변경 불가 기준

### Build System
- **Type**: 빌드 단계 없음. `pip install -r requirements.txt`로 의존성만 설치하고 `python app.py`로 실행. `pyproject.toml`·`setup.py`·`setup.cfg` 없음(패키지로 배포하지 않음)
- **Config Files**: `requirements.txt`(버전 고정 11개), `.github/workflows/ci.yml`, `.gitattributes`(LF 고정), `.gitignore`
- **Build Dependencies**:
  - `app` → `modules.classify`, `modules.data`, `modules.explain`, `modules.features`
  - `modules.classify` → `modules.data` (`load_index`) — `classify.py:15`
  - `modules.features` → `modules.data` (`ARTISTS`) — `features.py:17`
  - `modules.data` → (내부 의존 없음)
  - `modules.explain` → (내부 의존 없음)
  - `tests.test_smoke` → `app`, `modules.*`
  - 순환 import 없음

### APIs Discovered
- 내부 Python 함수 API — `contracts/interfaces.md` 기준 — 16개 공개 함수 (A 4, B 4, C 5, D 3) + `result` dict 키 11개
  - A `modules/data.py`: `embed_image`, `embed_text`, `load_index`, `clip_keywords`
  - B `modules/classify.py`: `detect_type`, `predict_clip`, `similar_works`, `fuse` (+ 계약 밖 보조 `load_calibration`)
  - C `modules/features.py`: `preprocess_input`, `is_grayscale`, `extract_features`, `load_profiles`, `predict_cv`
  - D `modules/explain.py`: `assess_confidence`, `compare`, `render_card` (+ 상수 `DISCLAIMER`)
  - 통합 `app.py`: `analyze(img) -> dict`, `run(img) -> (str, Figure, dict)`, `build_demo() -> gr.Blocks`
- 사용자 UI — Gradio Blocks — 로컬 `127.0.0.1:7860`, 입력 1(이미지), 출력 3(Markdown 카드, Plot 레이더, JSON 상세), 버튼 1(`분석하기`)
- 파일 계약(아직 생성 안 됨) — `artifacts/embeddings.npy`, `artifacts/meta.csv`(A), `artifacts/profiles.json`(C), `artifacts/calibration.json`(B, `classify.CALIBRATION_PATH`에서 읽음), `artifacts/linear.pkl`(B, plan.md)
- HTTP/REST/DB API 없음

### Frameworks & Libraries
- numpy — 2.4.6 — 배열·임베딩 연산 (모든 모듈)
- pandas — 3.1.1 — `load_index()["meta"]` DataFrame (`data`, `classify`)
- scipy — 1.17.1 — `scipy.spatial.distance.jensenshannon` (`explain`)
- scikit-learn — 1.9.1 — 선형 분류기 예정(#11). 현재 코드에서 import 안 함
- matplotlib — 3.11.2 — 레이더 차트 `Figure`, 한글 글꼴 탐색 (`explain`)
- opencv-python-headless — 5.1.0.95 — `cv2.resize` (`features.preprocess_input`)
- torch — 2.15.0 — CLIP 실행 예정(#5). 현재 import 안 함. CI는 CPU판을 먼저 설치
- transformers — 5.23.0 — CLIP 예정(#4·#5). 현재 import 안 함
- datasets — 5.2.0 — WikiArt 로드 예정(#3). 현재 import 안 함
- gradio — 6.32.0 — 웹 UI (`app`)
- pytest — 9.2.0 — 테스트
- 표준 라이브러리: `hashlib`, `functools.lru_cache`, `json`, `pathlib`, `math`

### Test Coverage
- **Test Directories**: `tests/`
- **Test Frameworks**: pytest 9.2.0 (fixture `color_img` 300×400 컬러, `sketch_img` 700×500 흑백 3채널, `parametrize` 사용)
- **Coverage Config**: absent (`pytest-cov`·`.coveragerc`·`pyproject.toml` 없음). 테스트 함수 16개(parametrize 포함 실행 케이스 18개)가 16개 계약 함수 모두와 `app.analyze`·`app.run`·`app.build_demo`를 호출한다

### Code Quality Indicators
- **Linting**: 없음. 린터·포매터 설정 파일 없음(`.ruff_cache/`가 `.gitignore`에 있을 뿐). CI에 린트 단계 없음
- **CI/CD**: `.github/workflows/ci.yml` — PR·`main` push·수동 실행 시 Ubuntu, Python 3.11, CPU torch 선설치 후 `pip install -r requirements.txt`, `pytest -q`. `permissions: contents: read`, 동시 실행 취소, 20분 제한. 배포 단계 없음
- **Documentation**: README(실행법, 팀원, 데이터 출처·비상업 조건), `docs/plan.md`(계획 432줄), `contracts/interfaces.md`, 모든 모듈·함수에 한국어 docstring(스텁 여부와 담당 이슈 명시), PR 템플릿(검증 결과·AI 판단 이유 3줄·체크리스트), 계약 변경 이슈 템플릿

### Technical Debt Signals
- 의도된 1일차 스텁(`TODO(#n)`): `data.embed_image`/`embed_text`(#5), `load_index`(#3·#4), `clip_keywords`(#7), `classify.detect_type`(#8), `predict_clip`(#9–#12·#14), `similar_works`(#13), `fuse`(#15, 가중합만), `features.preprocess_input`(#16, 크기 맞추기만), `extract_features`(#17·#18), `load_profiles`(#19), `predict_cv`(#20·#14). 스텁은 입력 해시로 만든 결정적 가짜 값을 돌려준다 — 화면의 값은 의미 없음(README도 명시)
- `scripts/build_index.py`, `scripts/build_profiles.py`는 `NotImplementedError`만 던진다
- `explain.py:20-21` 등급 경계값 6개는 임시값(#24에서 검증셋으로 확정)
- `features.predict_cv`는 `T = 1.0` 하드코딩(`features.py:105`). 계약은 "온도 보정 적용"이고 `T_cv`는 B 쪽 `classify.DEFAULT_CALIBRATION`/`calibration.json`에 있다 — C가 이 값을 어떻게 읽을지 정해지지 않음
- Unit 간 코드 import: `classify` → `data.load_index`, `features` → `data.ARTISTS`. 파일 소유는 분리돼 있지만 실행 시 B·C가 A에 기대고 있다
- 화가 이름 일관성 가정: `app.analyze`의 `profiles[top1]`(`app.py:57`)은 `fuse()`가 돌려준 이름이 `load_profiles()` 키에 있어야 한다. 지금은 모두 `data.ARTISTS`에서 나와서 맞지만, 실제 구현에서 `meta.csv`의 `artist` 값과 `profiles.json` 키가 다르면 `KeyError`
- `features.preprocess_input`는 float 입력을 범위 확인 없이 `astype(np.uint8)`로 바꾼다(`features.py:44`) — Gradio 입력(uint8)에서는 문제 없음
- `data.embed_text`는 계약(`list[str]`)보다 넓게 `str`도 받는다(`data.py:95`) — 계약 위반은 아님
- 커버리지 측정·린터 없음. org 기본값의 `mvp` 80% 커버리지 하한은 이 intent의 scope(`classic`)에는 적용되지 않음
- 문서 차이: `docs/plan.md` 5장·10.1은 `aidlc.settings.json`을 언급하지만 저장소에 없음. plan.md 5장 트리에는 `.github/workflows/ci.yml`이 빠져 있음
- 로깅 없음. 오류는 `ValueError`(`data._check_image`, `features.preprocess_input`)와 `gr.Error`(`app.run`, 이미지 없음)로만 알린다

## Handoff Summary
- **Intent-relevant finding**: 저장소는 이미 끝까지 도는 walking skeleton이다. `app.analyze()`(`app.py:14-59`)가 `preprocess_input → is_grayscale → embed_image → detect_type/clip_keywords/predict_clip/similar_works → extract_features → predict_cv → fuse → assess_confidence → load_profiles/compare`를 호출해 `contracts/interfaces.md`의 `result` 11개 키를 만들고, `render_card()`가 Markdown과 레이더 Figure를 돌려준다. A·B·C 함수는 `TODO(#n)` 스텁, D(`explain.py`)는 plan.md 6.3 식을 실제로 계산하되 경계값만 임시다. `tests/test_smoke.py`가 16개 계약 함수의 형식과 전체 파이프라인(컬러·스케치)을 검사한다.
- **Risks / follow-up**:
  - `contracts/interfaces.md`는 변경 불가 — 어떤 산출물도 다른 계약을 만들면 안 된다
  - Unit 독립성은 "파일 소유" 수준이다. 코드는 B→A(`load_index`), C→A(`ARTISTS`) import가 있다. Units Generation은 이 실행 시 의존을 계약 경유 의존으로 기록하거나 해소 방법을 정해야 한다(코드 수정 없이)
  - `T_cv`의 저장 위치(`calibration.json`, B 소유)와 C의 `predict_cv` 사이 연결이 미정
  - 화가 이름 키가 A(`meta.csv`)·B(`predict_clip`)·C(`profiles.json`) 사이에서 같아야 한다는 암묵 계약
  - 데이터 분할 규칙(프로필·분류기=train, T·w·등급=val, test=#26 한 번)과 화이트밸런스는 사용자 입력에만 — 코드 주석·docstring에 반영돼 있음
  - 정확도·ECE 수치는 아직 하나도 없다. 스텁 출력은 결과로 쓰면 안 된다
