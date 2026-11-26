# Developer Scan — #9 kNN 투표 판정 (focused)

## Developer Code Scan Results

### Scan Coverage
- **Analyzed deeply**:
  - `modules/classify.py` — 판정·융합(B), 이번 intent의 수정 대상
  - `tests/test_classify.py` — `similar_works()` 동작 테스트(#13), 이번 intent가 끝에 "# --- #9 kNN" 절을 덧붙일 파일
  - `contracts/interfaces.md` — 변경 불가 함수 계약(B·A 표면)
  - `modules/data.py` — `classify`가 소비하는 `load_index()` 계약(이웃을 찾는 색인)
- **Skimmed only**:
  - 저장소의 나머지(`app.py`, `modules/features.py`, `modules/explain.py`, `scripts/`, `tests/test_smoke.py`, `notebooks/eval.ipynb`, `docs/`, `.github/`, `requirements.txt`)는 이번 run에서 다시 읽지 않고 기존 CodeKB 스토어(STALE, 2026-11-19 full scan)의 기록으로만 맥락을 참고했다
- **Left out**:
  - 의존성 `.venv/`, 캐시 `__pycache__/`, `.pytest_cache/`
  - AI-DLC 설치물 `.claude/`, `aidlc/`, `.aidlc-version` 및 `.gitignore`/`AGENTS.md`의 AI-DLC 구역
  - 사전 계산 산출물 자리 `artifacts/`, `samples/`(비어 있음, `.gitkeep`만)

### Packages Found
- `modules` — 애플리케이션 패키지 — Python — A·B·C·D 4개 모듈(이번 focus는 B `classify`, A `data`)
- `tests` — 테스트 — Python — `test_classify.py`(동작, #13)·`test_smoke.py`(형식)·`conftest.py`

### Build System
- **Type**: pip + `requirements.txt`(전부 `==` 고정), `pyproject.toml`에 Ruff 설정(focus 밖, 스토어 참고)
- **Config Files**: `requirements.txt`, `pyproject.toml`
- **Build Dependencies**: `classify` → `data`(`from modules.data import load_index`, `classify.py:16`)

### APIs Discovered
- 모듈 함수 계약(HTTP/DB 없음) — `contracts/interfaces.md` — B 4개(`detect_type`, `predict_clip`, `similar_works`, `fuse`), A 4개(`embed_image`, `embed_text`, `load_index`, `clip_keywords`)
- `classify` 계약 밖 공개 보조: `load_calibration()`, 상수 `NEAR_DUPLICATE`(테스트가 참조)

### Frameworks & Libraries
- numpy — 2.4.6 — 임베딩 배열·코사인·softmax(`classify`, `data`)
- pandas — 3.1.1 — 색인 메타 DataFrame(`data.load_index`, `classify`가 `.iloc`로 읽음)

### Test Coverage
- **Test Directories**: `tests/`
- **Test Frameworks**: pytest 9.2.0
- **Coverage Config**: 없음(커버리지 하한 없음, project.md)
- 모델 함수는 `tests/conftest.py`가 `tests/fakes.py`의 가짜로 자동 치환(`@pytest.mark.model`·`--run-model`로 실제 실행). `test_classify.py`는 `monkeypatch`로 `classify.load_index`에 작은 가짜 색인을 끼워 검사한다

### Code Quality Indicators
- **Linting**: Ruff(`pyproject.toml`, line-length 100) — focus 밖, 스토어 참고
- **CI/CD**: `.github/workflows/ci.yml`(PR마다 `pytest`) — focus 밖
- **Documentation**: 모든 공개 함수에 한국어 docstring + 반환 형식·스텁 여부. `classify`·`data`는 모듈 docstring 규약을 따름

### Technical Debt Signals
- `classify.py`에 남은 스텁: `detect_type` `TODO(#8)`, `predict_clip` `TODO(#9–#12)`, `fuse` `TODO(#15)`. (`similar_works`는 #13에서 실제 구현 완료 — 더 이상 스텁 아님)
- `classify._centroids()`·`similar_works()`가 `data.load_index()`에 의존(B→A import). 계약을 지키는 한 A 내부 변경은 B에 영향 없음
- `load_index()["meta"]`의 DataFrame 인덱스가 0..N-1이라는 보장이 없음 → 위치 기준 `.iloc`로만 읽어야 함(라벨 `.at`/`.loc`는 깨짐)

## Handoff Summary
- **Intent-relevant finding**: 이번 #9가 추가할 비공개 함수 `_knn_logits(E, k, by)`·`_topk_accuracy(z, names, labels, ks)`는 현재 `classify.py`에 없다(신규). 재사용할 자원이 이미 있다: (1) `_l2_normalize(v)`(`classify.py:37`)는 1D·2D 모두 정규화하고 영벡터를 1e-12로 눌러 안전하며 입력을 복사한다 — kNN 코사인 계산에 그대로 쓸 수 있다. (2) 학습셋 선택 패턴 `(meta["split"] == "train").to_numpy()`가 `_centroids()`(`classify.py:52`)에 이미 있다 — kNN 이웃도 학습셋에서만 찾아야 하므로 같은 패턴을 따른다. (3) 화가·화풍 목록은 `sorted(meta.loc[train, col].unique())`로 색인에서 읽고 숫자로 고정하지 않는다(`classify.py:53`). (4) 위치 기준 읽기: `similar_works()`가 `meta.iloc[row]`로 읽고(`classify.py:98`) `tests/test_classify.py::test_similar_works_reads_by_position_not_label`가 인덱스 `[10,20,30]` 색인으로 이를 검증한다 — kNN도 라벨 인덱스가 아니라 emb 행 위치로 라벨을 읽어야 한다.
- **Risks / follow-up**: `predict_clip()`은 이번에 바꾸지 않는다(#12 결정, state Project). `contracts/interfaces.md`(B 4개 공개 함수 시그니처)와 `tests/test_smoke.py`는 변경 불가. 새 함수는 비공개(`_` 접두)라 공개 계약을 건드리지 않는다. 동점은 이름순으로 결정적이어야 하고, 투표 0인 이름도 `z = log(투표 + 작은 값)`로 유한값을 가져야 한다(state 요구). 이웃은 학습셋만 사용(테스트셋 사용 금지, project.md Forbidden). 동작 테스트는 `test_classify.py` 끝 "# --- #9 kNN" 절에 작은 가짜 색인 monkeypatch로 추가한다.
