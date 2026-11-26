# Developer Code Scan — 261126-similar-works (#13)

> FOCUSED 스캔. 이번 변경 영역(`modules/classify.py`의 `similar_works()`)만 깊게 읽고,
> 그것이 직접 기대는 부분(`modules/data.py`의 `load_index`, `contracts/interfaces.md`의
> `similar_works` 계약)은 문서화에 필요한 만큼만 훑었다. `pytest`·빌드·앱은 실행하지 않았다.

## Developer Code Scan Results

### Scan Coverage

- **Analyzed deeply**:
  - `modules/classify.py`
- **Skimmed only**:
  - `modules/data.py` — `load_index()` 반환 형식(`{"emb": (N,512), "meta": DataFrame[id, artist, style, genre, path, split]}`)과 가짜 색인 생성 경로만 확인(`similar_works`의 입력 출처)
  - `contracts/interfaces.md` — `similar_works(emb, k=3) -> list[dict]` 계약(길이 ≤ k, score 내림차순, 유사도 0.95 이상 제외) 확인
  - 디렉터리 수준만 보고 이번 런에서 다시 읽지 않은 손수 작성 소스(이전 전체 스캔 산출물로만 덮임, 이번 런에서 재검증 안 함): `app.py`, `modules/features.py`, `modules/explain.py`, `scripts/`, `tests/`, `notebooks/`, `docs/`, `.github/`, `README.md`, `requirements.txt`
- **Left out** ("What to Skip" 규칙으로 열지 않음):
  - `.venv/`, `__pycache__/`, `.pytest_cache/`, `.git/`
  - AI-DLC 설치물: `.claude/`, `aidlc/`, `.aidlc-version`
  - `.gitignore`가 무시하는 데이터·대용량: `/data/`, `samples/disagree/`, `*.pt`

### Packages Found

- `modules` (`modules/classify.py`) — Service(판정·융합) — Python — B Unit(홍예원). 이번 깊은 분석 대상은 이 파일뿐.

### Build System

- **Type**: pip + `requirements.txt` (전부 `==` 고정, lock·`pyproject.toml` 없음) — 이번 런에서 재확인 안 함(이전 스캔 기록 유지)
- **Config Files**: `requirements.txt` (skimmed)
- **Build Dependencies**: `modules.classify` → `modules.data` (`from modules.data import load_index`, `classify.py:16`)

### APIs Discovered

- 모듈 함수 계약 — `modules/classify.py` — 공개 함수 4개(`detect_type`, `predict_clip`, `similar_works`, `fuse`) + 공개 보조 `load_calibration`, 상수 `NEAR_DUPLICATE`·`LOGIT_SCALE`. HTTP/REST/DB API 없음.

### Frameworks & Libraries

- numpy — 2.4.6 (기존 기록) — 배열·코사인 유사도 계산 (`classify.py` 유일 외부 import)
- (그 외 라이브러리 버전은 이번 런에서 재확인하지 않음 — `technology-stack.md`의 이전 기록 유지)

### Test Coverage

- **Test Directories**: `tests/` (이번 런에서 열지 않음)
- **Test Frameworks**: pytest (기존 기록)
- **Coverage Config**: absent (기존 기록, 재확인 안 함)

### Code Quality Indicators

- **Linting**: 설정 없음(기존 기록). `classify.py`에 `# noqa` 억제 없음.
- **CI/CD**: `.github/workflows/ci.yml` (기존 기록, 이번 런에서 열지 않음)
- **Documentation**: 모듈 docstring + 모든 공개 함수에 반환 형식·스텁 여부 docstring. `classify.py` 품질 good.

### Technical Debt Signals

- `modules/classify.py:71` `# TODO(#13): 스텁 — #13 실제 색인 기준 검색 (담당 B)` — 이번 인텐트가 해소할 대상. 현재 `similar_works()`는 가짜 색인(`load_index()["emb"]`) 전체에 대해 `emb @ emb.T` 코사인을 계산하고 `NEAR_DUPLICATE = 0.95` 이상을 자기 자신으로 보고 제외한 뒤 상위 k를 돌려준다.
- `classify.py:16`의 `from modules.data import load_index`는 AGENTS.md 테스트 규약(모델 함수는 `data.foo(...)`처럼 모듈 경유 호출)과 다른 import 형태다. `load_index`는 모델 함수가 아니라 영향은 제한적이나, B→A Unit 간 import로 남아 있다(기존 `dependencies.md` 설계 주의점).
- `classify.load_calibration()`은 `calibration.json` JSON 파싱 오류를 그대로 올린다(조용한 실패 아님).

## Handoff Summary

- **Intent-relevant finding**: `similar_works(emb, k=3)` (`classify.py:69-85`)는 이미 실제 코사인 유사도 검색의 형태를 갖추고 있다. `load_index()["emb"]`(N×512, 각 행 L2 정규화)와 질의 임베딩의 내적으로 점수를 만들고, `np.argsort(-scores)`로 내림차순 정렬한 뒤 `scores[i] < NEAR_DUPLICATE(0.95)` 조건으로 자기 자신(동일 작품)을 거르고 상위 k개를 `[{"id","artist","style","path","score"}]`로 반환한다. #13 작업은 "가짜 색인 전체 선형 검색"을 실제 색인 기반 검색으로 바꾸는 것이며, 계약(`contracts/interfaces.md`)과 반환 형식은 그대로 유지해야 한다.
- **Risks / follow-up**:
  - 계약 불변: `similar_works`의 이름·인자(`emb`, `k=3`)·반환 키 5개·정렬·0.95 제외 규칙은 `contracts/interfaces.md` 기준이라 바꾸지 않는다.
  - 입력 임베딩과 색인 임베딩은 같은 CLIP 모델 버전이어야 하며, 둘 다 L2 정규화 전제(코사인 = 내적)여야 한다.
  - `load_index()` 반환 형식에 기대므로 A(`modules/data.py`) 계약이 깨지면 B가 영향을 받는다(B→A import).
