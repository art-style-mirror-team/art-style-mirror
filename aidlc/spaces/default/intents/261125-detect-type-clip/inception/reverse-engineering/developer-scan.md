# Developer Code Scan — detect_type() CLIP zero-shot (#8)

## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply**:
  - `modules/classify.py` (판정·융합 B, `detect_type()` 대상 포함)
  - `modules/data.py` (A, `embed_text`·`embed_image`·`load_index` 제공)
  - `modules/features.py` (C, 색·선 특징 — Unit 상호관계 파악용)
  - `modules/explain.py` (D, 신뢰도·대조·카드 — Unit 상호관계 파악용)
  - `contracts/interfaces.md` (변경 불가 함수 계약)
  - `tests/conftest.py`, `tests/fakes.py`, `tests/test_smoke.py`, `tests/test_explain.py`, `tests/test_features.py`
- **Skimmed only**:
  - `app.py` (D 통합 지점 — 이번 intent에서 수정 대상 아님)
  - `scripts/` (`build_index.py`, `build_profiles.py`)
  - `notebooks/eval.ipynb`
  - `docs/` (`plan.md`, `aidlc-guide.md`), 루트 설정(`requirements.txt`, `pyproject.toml`, `.github/`, `README.md`)
- **Left out**(스캔 지침의 "What to Skip"):
  - `.venv/`, `__pycache__/`, `.pytest_cache/` 등 캐시·의존성
  - AI-DLC 설치물 `.claude/`, `aidlc/` 워크스페이스, `.mcp.json`의 MCP 항목, `AGENTS.md`/`.gitignore`의 AI-DLC 구역
  - `.gitignore`가 무시하는 경로(원본 이미지 `/data/`, `samples/disagree/`, `*.pt` 등)

프로젝트의 테스트·빌드·앱은 실행하지 않았다. 깊이 분석은 `modules/`, `contracts/`, `tests/` 안에만 머물렀다.

### Packages Found

- `modules` — Python 패키지(파이프라인 Unit A·B·C·D) — Python — 핵심 로직
- `tests` — pytest 테스트 패키지 — Python — 계약 형식 + 동작 검사
- `contracts` — 문서 계약(`interfaces.md`) — Markdown — 함수 시그니처의 최종 기준

### Build System

- **Type**: pip + `requirements.txt`(전부 `==` 고정). `pyproject.toml`은 Ruff 설정 전용(target py311, line-length 100, 규칙 `I`); lock 파일 없음
- **Config Files**: `requirements.txt`, `pyproject.toml`(Ruff), `.github/workflows/ci.yml`
- **Build Dependencies**: 빌드 단계 없음(순수 Python). 사전 계산 산출물만 `artifacts/`로 공유 예정

### APIs Discovered

- 모듈 함수 계약 — `contracts/interfaces.md` — 16개 함수(A 4, B 4, C 5, D 3)
- HTTP/REST/DB API 없음. Gradio 로컬 화면과 `result` dict가 표면(이번 스캔에서 app.py는 훑어보기만)

### Frameworks & Libraries (깊이 분석 영역에서 실제 import 확인)

- numpy — 2.4.6 — 배열·임베딩·확률 — `modules.*`, `tests`
- pandas — 3.1.1 — 색인 메타 DataFrame — `modules.data`, `tests`
- opencv-python-headless — 5.1.0.95 — 리사이즈·색/선 특징 — `modules.features`
- scikit-learn — 1.9.1 — `MiniBatchKMeans` 팔레트 군집 — `modules.features` (**신규: 이제 실제 import됨**)
- scipy — 1.17.1 — `jensenshannon` — `modules.explain`
- matplotlib — 3.11.2 — 레이더 `Figure`·한글 글꼴 — `modules.explain`, `tests`
- pytest — 9.2.0 — 테스트 — `tests`
- torch / transformers / datasets — 2.15.0 / 5.23.0 / 5.2.0 — CLIP·WikiArt(예정) — 아직 미import

### Test Coverage

- **Test Directories**: `tests/`
- **Test Frameworks**: pytest 9.2.0
- **Coverage Config**: 없음(커버리지 측정 도구·설정 없음). 팀 규칙은 "pytest 전체 통과", 커버리지 하한 없음

테스트 구성(store 기록보다 확장됨):
- `tests/conftest.py` — 루트를 `sys.path`에 추가 + `@pytest.mark.model` 스킵 + autouse 픽스처가 `FAKES`로 모델 함수를 바꿔 끼움 + `--run-model`/`RUN_MODEL_TESTS`/`HF_HUB_OFFLINE` 처리
- `tests/fakes.py` — `fake_embed_image`, `fake_embed_text`, `FAKES` 레지스트리(`modules.data.embed_image`, `modules.data.embed_text`)
- `tests/test_smoke.py` — 16개 계약 함수 형식 + 전체 파이프라인(컬러·스케치) + Gradio 빌드 + 상세 JSON `path` 제거
- `tests/test_explain.py` — `compare()` 동작 13케이스(#21)
- `tests/test_features.py` — 색 특징 실제 계산(밝기/대비/채도/색온도/다양성/팔레트가 밝은·어두운 이미지에서 달라짐)

### Code Quality Indicators

- **Linting**: Ruff(`pyproject.toml`, line-length 100, 규칙 `I`). CI의 ruff 단계가 format+lint 검사
- **CI/CD**: `.github/workflows/ci.yml`(PR·main push → Python 3.11, CPU torch 선설치, pytest + ruff). 배포 파이프라인 없음
- **Documentation**: `README.md`, `docs/plan.md`, `contracts/interfaces.md`, 모든 공개 함수 한국어 docstring(반환 형식·스텁 여부 명시)

### Technical Debt Signals

- `classify.detect_type` 스텁(`classify.py:50-53`, `TODO(#8)`): `np.argmax(img_emb[:3])`로 유형을 정한다 — **이번 intent의 대상**
- `features.predict_cv`의 온도 `T = 1.0` 하드코딩(`features.py:169`)과 `calibration.json`의 `T_cv`(B 소유) 소유·읽기 경로 미정
- `features.extract_features`의 선 특징 5종은 아직 결정적 가짜 값(`features.py:87`, `TODO(#18)`); 색 특징은 실제 계산(#17 반영)
- `features.preprocess_input`의 종이 자르기·화이트밸런스 미구현(`features.py:35`, `TODO(#16)`)
- Unit 간 import: B→A(`classify.py:16` `load_index`), C→A(`features.py:15` `ARTISTS`) — 팀 결정("Unit 서로 비의존")과 코드 수준 어긋남
- 화가 이름 암묵 계약: `fuse()` 결과 이름이 `load_profiles()` 키에 있어야 함(`app.py`의 `profiles[top1]`)

## Handoff Summary

- **Intent-relevant finding**: `detect_type(img_emb) -> str`는 계약상 `"photo" | "painting" | "sketch"`를 돌려주는 순수 함수로, 현재 `classify.py:50-53`에서 임베딩 앞 3개 값의 argmax를 쓰는 스텁(`TODO(#8)`)이다. CLIP zero-shot 문장 앙상블로 바꾸려면 유형별 프롬프트 문장을 `data.embed_text(...)`(모듈 경유 호출 필수, `from modules.data import embed_text` 금지)로 임베딩해 `img_emb`와 코사인 비교해야 한다. `data.embed_text`는 이미 `(n,512)` L2 정규화 계약을 제공하고 `tests/fakes.py`의 `fake_embed_text`로 모델 없이 바꿔 끼워진다. 이렇게 하면 B→A 의존이 `load_index`에 더해 `embed_text`로 하나 늘어난다. 반환은 반드시 세 리터럴 중 하나여야 `tests/test_smoke.py::test_classify_formats`가 그대로 통과한다.
- **Risks / follow-up**:
  - `detect_type`이 실제 CLIP을 쓰게 되면 유형 문장 임베딩은 반드시 `data.embed_text` 모듈 경유 호출이어야 테스트 가짜 끼우기가 작동한다. 새 모델 함수를 직접 만들면 `tests/fakes.py`의 `FAKES`에 가짜를 추가해야 한다.
  - 계약 `contracts/interfaces.md`의 `detect_type` 시그니처·반환 형식은 변경 불가. 내용만 바꾼다.
  - 명화와 사용자 입력은 같은 CLIP 모델 버전을 써야 하므로 유형 판별에 쓰는 임베딩도 `data.embed_image`/`embed_text`와 같은 모델이어야 한다(모델 ID는 아직 코드에 없음, #4·#5에서 고정).
  - store는 stale(전체 `./` 스캔, 2026-11-19)이며 그 사이 `features.py`(색 특징 실제화 + sklearn import), `explain.py`(견고화), `tests/`(fakes·test_explain·test_features 추가)가 바뀌었다.
