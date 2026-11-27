# Code Summary — #10 `_centroid_logits()`

## 변경 파일

- `modules/classify.py` — 비공개 함수 `_centroid_logits(E, by, scale=LOGIT_SCALE)` 추가
  (`_centroids()` 뒤, `detect_type()` 앞). 한국어 docstring. in-place 변경.
- `tests/test_classify.py` — 끝에 `# --- #10 centroid` 절 추가(헬퍼 `_centroid_index`,
  컨텍스트매니저 `_fake_centroids`, 동작 테스트 6개).

변경한 파일은 이 둘뿐이다. `tests/test_smoke.py`, `contracts/interfaces.md`, `predict_clip()`,
`modules/data.py` 등은 건드리지 않았다.

## 핵심 구현 결정

- 중심점을 새로 계산하지 않고 `_centroids()[by]`의 `(names, cents)`를 그대로 재사용한다. `cents`는
  이미 L2 정규화되어 있고 학습셋(`split=="train"`)만으로 만들어진다 → NFR4, FR1.1 충족.
- 입력 `E`를 `_l2_normalize`로 정규화한 뒤 `z = scale * (En @ cents.T)` (코사인 × 배율). 반환
  `(names, z)`, `z` shape `(n, 이름 수)` — #9 `_knn_logits`와 같은 모양 → FR1.2, FR1.3.
- 검증은 matmul 전에: `scale <= 0` → `ValueError`, `E.ndim != 2` → `ValueError`(shape 포함).
  0장 `(0, 512)`은 예외 없이 `(0, 이름 수)` z를 돌려준다 → FR2.1~FR2.3.

## 계획과의 편차

- **1차원 거부를 `ndim == 1` 대신 `ndim != 2`로 구현.** 1차원 입력은 그대로 `ValueError`이므로
  FR2.1을 그대로 만족하며, 3차원 이상도 함께 막는 상위집합이라 더 방어적이다. 동작 차이 없음.
- 그 외 편차 없음.

## 테스트 커버리지

- 신규 테스트 6개(FR3.2 학습셋 전용 / FR3.3 최근접=최대 z / FR3.4 scale 선형 /
  FR2.1·1D / FR2.2·0장 / FR2.3·scale 예외). `_centroids`가 `lru_cache`이므로 각 테스트에서
  monkeypatch 직후와 끝에 `classify._centroids.cache_clear()` 호출(FR3.1).
- 실행: `.venv\Scripts\python -m pytest tests/test_classify.py` → **14 passed in 4.16s**
  (기존 8 + 신규 6). 전부 통과.
- `ruff format .` → 변경 없음. `ruff check --fix .` → import 정렬 1건 자동 수정 후 통과.
  검사를 약화하거나 끈 곳 없음.

## 이 단계에서 실행하지 않은 테스트

- 전체 스위트(`pytest`, `tests/test_smoke.py` 포함)는 Build and Test 단계에서 실행해
  기존 테스트가 모두 녹색인지 확인한다(NFR2). 이 단계에서는 unit-scoped 명령만 돌렸다.
