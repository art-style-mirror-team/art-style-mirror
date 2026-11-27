# Developer Code Scan — art-style-mirror (#11 선형 분류기)

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - modules/classify.py
  - tests/test_classify.py
- **Skimmed only**:
  - modules/data.py (`load_index()` 반환 형식·`ARTIST_STYLE`/`ARTISTS` 상수, `_l2`·캐시 흐름만 확인)
  - contracts/interfaces.md (B절 `classify.py` 함수 계약 4개 확인)
  - tests/fakes.py (`FAKES` 끼워넣기 대상과 모델 함수 경유 호출 규칙 확인)
- **Left out** (code-analysis-guide.md "What to Skip" 기준, 열지 않음):
  - .venv/ (의존성)
  - __pycache__/, .pytest_cache/, .ruff_cache/ (캐시)
  - .claude/, aidlc/, .aidlc/ 및 AGENTS.md·.gitignore의 AI-DLC 마킹 구역 (AI-DLC 설치물)
  - /data/, samples/disagree/, *.pt, .gradio/ (.gitignore 무시 대상)
  - app.py, modules/{data,features,explain}.py, scripts/, notebooks/, docs/, .github/, tests/{conftest,test_smoke,test_explain,test_features}.py — 이번 집중 스캔 범위 밖(기존 저장소 prose 보존, shallow)

### Packages Found
- modules.classify — Service(판정·융합) — Python — B Unit(홍예원). 입력 유형 판별·CLIP 관점 확률·비슷한 명화 검색·두 관점 합치기·`calibration.json` 로드
- tests.classify (tests/test_classify.py) — Test — Python — `similar_works()` 동작 테스트(#13)

### Build System
- **Type**: pip + requirements.txt (전부 `==` 고정), pyproject.toml은 도구 설정만
- **Config Files**: requirements.txt, pyproject.toml (이번 스캔에서 다시 열지 않음; technology-stack.md 기준 유지)
- **Build Dependencies**: modules.classify → modules.data(`load_index`) 한 건. 그 외 classify는 numpy와 표준 라이브러리(json, functools, pathlib)만

### APIs Discovered
- 모듈 함수 계약(B) — contracts/interfaces.md — 4개: `detect_type`, `predict_clip`, `similar_works`, `fuse`
- classify.py 공개 보조(계약 밖) — `load_calibration() -> dict`, 상수 `NEAR_DUPLICATE=0.95`, `LOGIT_SCALE=20.0`, `DEFAULT_CALIBRATION`, `CALIBRATION_PATH`
- HTTP/REST/DB API 없음 (프로젝트 전체 동일, api-documentation.md 기준 유지)

### Frameworks & Libraries
- numpy — (technology-stack.md 고정 버전) — 배열·확률·코사인 계산. classify.py가 직접 import하는 유일한 서드파티
- (classify.py는 현재 scikit-learn/joblib을 import하지 않음 — #11에서 추가 예정)

### Test Coverage
- **Test Directories**: tests/
- **Test Frameworks**: pytest (tests/fakes.py의 가짜 모델을 conftest가 끼움 — 이번엔 conftest 미열람)
- **Coverage Config**: 부재 (측정 도구·설정 없음, code-quality-assessment.md 기준 유지)

### Code Quality Indicators
- **Linting**: Ruff (pyproject.toml, line-length 100). classify.py·test_classify.py에 `# noqa` 없음
- **CI/CD**: .github/workflows/ci.yml (이번 스캔 미열람, 기준 유지)
- **Documentation**: classify.py 모듈 docstring + 모든 공개 함수에 반환 형식·스텁 여부 docstring. `similar_works`·`_l2_normalize`는 경계 동작까지 상세

### Technical Debt Signals
- classify.py 스텁 4곳: `detect_type` `TODO(#8)`, `predict_clip` `TODO(#9–#12)`, `fuse` `TODO(#15)` (docstring의 `(스텁: …)` 표기). `similar_works`만 실제 구현(#13)
- B → A 직접 import(`from modules.data import load_index`)는 "Unit은 서로 의존하지 않는다" 팀 결정과 코드 수준에서 어긋남(기존 저장소에 기록된 설계 주의점, dependencies.md). 단, classify는 모델 함수가 아닌 `load_index`를 import하므로 `tests/fakes.py` 끼워넣기 규칙(모듈 경유 호출) 대상은 아님 — 테스트는 `classify.load_index`를 monkeypatch함
- predict_clip·fuse·detect_type 전용 동작 테스트 없음: test_classify.py는 `similar_works`만 검사(8개 함수)

## Handoff Summary
- **Intent-relevant finding**: 이번 집중 스캔 시점(브랜치 feat/11-logreg, commit cd3a97f)의 modules/classify.py에는 #11이 추가하려는 `LINEAR_PATH` 상수와 `_fit_linear`/`_save_linear`/`_load_linear`/`_linear_logits` 비공개 함수가 **아직 없다**. 또한 #9 `_knn_logits`·#10 `_centroid_logits`도 코드에 없다 — CLIP 관점 확률은 현재 `_centroids()`(학습셋 중심점, `@lru_cache(maxsize=1)`)와 `predict_clip()`(`LOGIT_SCALE * (cents @ emb)` → `_softmax(·, T_clip)`)로만 계산된다(classify.py:46-75). #11의 `_linear_logits(E, by, model=None)`가 맞춰야 할 반환 모양의 현존 선례는 `similar_works`가 아니라 계약·state에 적힌 `(이름 목록, z (n, 이름 수))`이며, 현재 코드에서 이름 목록·정규화의 참고 지점은 `_centroids()`의 `names = sorted(meta.loc[train, col].unique())`와 `_l2_normalize()`(classify.py:37-56)다. 학습셋 한정 규칙은 `_centroids()`가 `meta["split"] == "train"`으로 이미 적용하고 있어 `_fit_linear`가 그대로 따르면 된다.
- **Risks / follow-up**: (1) 기존 저장소는 STALE이고 직전 집중 스캔(#22)은 modules/explain.py·app.py 등 D 영역 7개 파일만 깊게 봤다. 이번 run은 classify 영역만 깊게 봤으므로 D·A·C 영역 prose는 보존하고 그 analyzed.paths는 shallow로 강등한다. (2) tests/test_classify.py는 `classify.load_index`를 직접 monkeypatch하므로 #11 테스트도 같은 방식(작은 가짜 색인 주입 + tmp_path 저장)을 따라야 하며 `tests/fakes.py`의 `FAKES`는 모델 함수(embed_*)만 다룬다 — logreg 학습/저장은 모델 함수가 아니라 `FAKES` 추가 불필요. (3) test_classify.py는 `index["meta"].at[7, ...]`를 쓰는 곳이 있으나(FR2) 이는 가짜 색인이 0..N-1 인덱스를 가질 때만 유효 — 구현부 `similar_works`는 위치 기준(`.iloc`)을 쓴다(의도적 대비, MEMORY.md의 load_index 위치 기준 계약).
