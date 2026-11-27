## Developer Code Scan Results

집중 스캔(focused), 깊이 Minimal, intent `centroid-classify`(#10), 브랜치 `feat/10-centroid`, 커밋 `c8f7a3e8e25e9324c7833470833e7e0925221763`. 기존 CodeKB 저장소 판정은 STALE이다. 이 스캔은 #10이 건드릴 영역(`modules/classify.py`의 CLIP 중심점 로짓 계산 경로)만 깊게 읽었다. 프로젝트의 테스트·빌드·앱은 실행하지 않았다.

### Scan Coverage
- **Analyzed deeply**:
  - `modules/classify.py`
  - `tests/test_classify.py`
- **Skimmed only**:
  - `contracts/interfaces.md` (B 계약 확인용 문맥)
  - `modules/data.py` (`load_index()` 반환 형식 확인용 문맥)
  - `modules/features.py`, `modules/explain.py`, `app.py` (B 계약 경계 확인용 문맥)
- **Left out** (code-analysis-guide.md "What to Skip"):
  - `.venv/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/` (의존성·캐시)
  - `.claude/`, `aidlc/`, `.aidlc-version` (AI-DLC 설치물)
  - `artifacts/`, `samples/` (비어 있는 자리, `.gitkeep`만)

### Packages Found
- `modules` — Python 패키지(앱 로직) — Python 3.11 — 이번 스캔은 그중 `classify.py`(Unit B) 하나만 깊게 봄
- `tests` — pytest 테스트 — Python 3.11 — 이번 스캔은 `test_classify.py`(Unit B 동작 테스트)만 깊게 봄

### Build System
- **Type**: pip + `requirements.txt`(전부 `==` 고정), `pyproject.toml`은 도구 설정(Ruff·pytest)만. 패키지로 배포하지 않음
- **Config Files**: `requirements.txt`, `pyproject.toml`(이번 스캔에서 다시 열지 않음)
- **Build Dependencies**: `modules/classify.py` → `modules/data.py`(`load_index`), `numpy`, 표준 `json`·`pathlib`·`functools`

### APIs Discovered
- HTTP/REST/DB API 없음. `classify.py`가 노출하는 표면은 `contracts/interfaces.md`가 정한 모듈 함수 계약 4개(`detect_type`, `predict_clip`, `similar_works`, `fuse`) + 계약 밖 공개 보조 `load_calibration()`·상수 `NEAR_DUPLICATE`

### Frameworks & Libraries
- numpy — (버전은 `technology-stack.md`) — 배열·코사인·softmax 계산 (`classify.py` 직접 import)
- pandas — — `load_index()`의 `meta` DataFrame을 `classify.py`가 소비(직접 import 아님, `data.py` 경유)
- pytest — — `tests/test_classify.py` 실행 프레임워크

### Test Coverage
- **Test Directories**: `tests/`
- **Test Frameworks**: pytest (`@pytest.mark.model` 마커, `conftest.py`가 모델 함수를 `fakes.py`로 교체)
- **Coverage Config**: 없음(커버리지 측정 도구·설정 없음)

### Code Quality Indicators
- **Linting**: Ruff (`pyproject.toml`: py311, line-length 100, 기본 규칙 + import 정렬 `I`). `classify.py`·`test_classify.py`에 `# noqa` 없음
- **CI/CD**: `.github/workflows/ci.yml`(ruff + pytest). 이번 스캔에서 열지 않음
- **Documentation**: 모듈 docstring + 모든 공개 함수 docstring(반환 형식·스텁 여부). `_l2_normalize`·`similar_works`·`_centroids` docstring 충실, 한국어

### Technical Debt Signals
- `classify.py`에 스텁 `TODO` 3곳: `detect_type`(`TODO(#8)`), `predict_clip`(`TODO(#9–#12)`), `fuse`(`TODO(#15)`). `similar_works`는 #13에서 실제 구현됨
- Unit 간 import: `from modules.data import load_index`(B→A). 팀 결정 "Unit은 서로 의존하지 않는다"와 코드 수준에서 어긋남(계약 경유라 계약 유지 시 영향 없음)
- 중심점 로짓 계산이 `predict_clip` 안에 인라인(`LOGIT_SCALE * (cents @ emb)`)이고 재사용 가능한 비공개 함수로 분리돼 있지 않음 — #10이 다룰 지점
- `test_classify.py`는 `similar_works`만 검사하고 `predict_clip`·`_centroids`·중심점 로짓 경로의 동작 테스트가 없음 — #10이 채울 틈

## Handoff Summary
- **Intent-relevant finding**: #10이 추가하려는 비공개 함수 `_centroid_logits()`는 현재 코드에 **아직 없다**. 지금 중심점 로짓 계산은 두 곳에 나뉘어 있다 — (1) `_centroids()`(`classify.py:46-56`, `@lru_cache(maxsize=1)`)가 학습셋(`split == "train"`)만으로 `artist`·`style` 중심점을 만들고 행 단위 L2 정규화한 `(names, cents)`를 돌려주고, (2) `predict_clip()`(`classify.py:65-75`)이 `_softmax(LOGIT_SCALE * (cents @ emb), T)`로 로짓을 인라인 계산한다. `LOGIT_SCALE = 20.0`(코사인→점수 배율), 온도 `T = load_calibration()["T_clip"]`. #10은 이 인라인 로짓 계산(`LOGIT_SCALE * (cents @ emb)`)을 비공개 `_centroid_logits()`로 빼고 `tests/test_classify.py`에 그 동작 테스트를 같은 PR로 추가하는 작업으로 보인다. 입력 `emb`는 L2 정규화 가정(`predict_clip`은 `_l2_normalize`를 호출하지 않음 — 정규화된 임베딩을 전제)인 점에 주의.
- **Risks / follow-up**:
  - 계약 고정: `predict_clip(emb) -> dict`와 `contracts/interfaces.md`는 바꾸지 않는다. `_centroid_logits()`는 비공개 보조이므로 계약 표면이 아니며 `predict_clip` 반환 형식(`{"artists": {...}, "styles": {...}}`, 각 합 1)을 그대로 유지해야 한다.
  - 팀 테스트 방식(custom): 계약 형식 검사(`tests/test_smoke.py`)는 그대로 통과해야 하고, 동작 테스트는 구현과 같은 PR에 넣는다. 모델 함수가 아닌 `load_index`는 테스트에서 `monkeypatch.setattr(classify, "load_index", ...)`로 작은 색인을 끼우는 기존 패턴(`test_classify.py:86-132`)을 따르는 것이 자연스럽다.
  - `_centroids()`가 `@lru_cache(maxsize=1)`라 테스트 간 상태가 남는다. 작은 색인을 monkeypatch하는 테스트는 캐시 초기화(`_centroids.cache_clear()`)를 고려해야 한다.
  - `MEMORY.md`의 위치 기준 계약(meta는 emb와 행 위치만 일치, `.iloc` 사용)은 `similar_works`에 이미 반영됨. `_centroids()`는 `meta[col]` 불리언 마스크로 접근하므로 라벨/위치 문제와 무관.
