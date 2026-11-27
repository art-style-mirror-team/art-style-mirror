# 요구사항 — #10 화가·화풍 중심점(centroid) 방식 판정

- 범위(scope): express (Minimal 깊이)
- 대상 파일: `modules/classify.py`, `tests/test_classify.py`
- 출처: GitHub 이슈 #10, 프로젝트 사양(project-description), `contracts/interfaces.md`,
  기존 코드(`modules/classify.py` `_centroids`/`_l2_normalize`/`predict_clip`,
  `tests/test_classify.py`의 #13 테스트 관례)

## 의도 분석 (Intent)

CLIP 임베딩으로 화가·화풍을 판정하는 여러 방식(#8~#15) 중 **중심점(centroid) 방식**을 독립된
비공개 함수로 분리한다. 현재 `predict_clip()`은 중심점 식을 함수 내부에 인라인으로 품고 있는데,
#10은 그 계산을 재사용·테스트 가능한 `_centroid_logits()`로 떼어낸다. 이번 이슈는 함수 추가와
동작 테스트까지만이며, `predict_clip()`을 이 함수로 바꿔 끼우는 일은 #12에서 별도로 결정한다.

## 기능 요구사항 (Functional Requirements)

### FR1 — `_centroid_logits(E, by, scale=LOGIT_SCALE)` 비공개 함수 추가 (`modules/classify.py`)
- **FR1.1** 기존 `_centroids()`(학습셋 중심점, L2 정규화됨, `@lru_cache`)를 재사용해 `by`
  축("artist" 또는 "style")의 `(이름 목록, 중심점)`을 얻는다. 중심점을 새로 계산하지 않는다.
- **FR1.2** 입력 `E`(여러 장, shape `(n, 512)`)를 `_l2_normalize`로 정규화한 뒤
  `z = scale * (E @ 중심점.T)`를 계산한다.
- **FR1.3** 반환은 `(이름 목록, z)`이며, 이름 목록은 `_centroids()`가 준 **정렬된 목록 그대로**,
  `z`의 shape는 `(n, 이름 수)`다. 이는 #9 `_knn_logits`와 같은 반환 모양이다.

### FR2 — 입력 검증과 엣지 케이스
- **FR2.1** 입력 `E`가 1차원 `(512,)`이면 알기 쉬운 메시지의 `ValueError`를 낸다.
- **FR2.2** 입력이 0장(0행 `(0, 512)`)이면 예외 없이 `(이름 목록, 0행 z)`를 돌려준다
  (`z`의 shape `(0, 이름 수)`).
- **FR2.3** `scale <= 0`이면 `ValueError`를 낸다.

### FR3 — 동작 테스트 (`tests/test_classify.py` 끝에 `# --- #10 centroid` 절로 추가)
- **FR3.1** 작은 가짜 색인을 `classify.load_index`에 monkeypatch한다. `_centroids`는
  `lru_cache`이므로 각 테스트 전후로 `classify._centroids.cache_clear()`를 호출한다.
- **FR3.2** 중심점 계산에 **학습셋(`split == "train"`)만** 쓰이는지 검사한다
  (비학습 행이 중심점에 섞이지 않음).
- **FR3.3** 어떤 축의 중심점에 가장 가까운 입력일 때, 그 중심점의 이름이 `z`에서 가장 큰 값을
  갖는지 검사한다.
- **FR3.4** `scale` 배율이 `z`에 선형으로 반영되는지 검사한다(예: `scale` 2배 → `z` 2배).
- **FR3.5** 1차원 입력·0장 입력·`scale <= 0`의 예외/반환 동작을 검사한다.

## 비기능 요구사항 (Non-Functional Requirements)

- **NFR1 — 계약·공개 API 불변**: `contracts/interfaces.md`를 바꾸지 않는다. `predict_clip()`의
  이름·입출력 형식을 이번 이슈에서 바꾸지 않는다(#12에서 결정). 합/검증 기준: `git diff`에
  해당 변경이 없음.
- **NFR2 — 테스트 통과**: `tests/test_smoke.py`를 고치지 않는다. `pytest` 전체가 통과한다
  (Windows: `.venv\Scripts\python -m pytest`).
- **NFR3 — 코드 스타일**: `ruff format .`과 `ruff check --fix .`가 통과한다
  (`pyproject.toml`: py311, line-length 100, import 정렬 `I`).
- **NFR4 — 데이터 분할 준수**: 중심점은 학습셋으로만 만든다(테스트셋/검증셋 미사용).

## 제약 (Constraints)

- 자기 Unit(B)만 수정한다: `modules/classify.py`, `tests/test_classify.py`. `modules/data.py`
  등 다른 모듈은 고치지 않는다(필요하면 이슈로 요청).
- 모델 함수는 모듈을 통해 부른다(`data.embed_image(...)`). 테스트는 `conftest.py`가 가짜로
  바꿔 끼운다.
- 노트북(`notebooks/eval.ipynb`)은 이번에 고치지 않는다(#9 머지 후 별도 커밋).
- 커밋은 작게 나누고, `main` 직접 push 금지. 브랜치 `feat/10-centroid`에서 작업한다.

## 가정 (Assumptions)

- **A1**: #9의 `_knn_logits`는 이 브랜치에 아직 머지되지 않았을 수 있다. 그 명세된 반환 모양
  `(이름 목록, z (n, 이름 수))`을 목표 규격으로 삼는다. 근거: 사양이 "#9의 _knn_logits와 같은
  모양"이라고 명시. (비차단)
- **A2**: `by`는 `_centroids()`의 축 키("artist"/"style")로 쓰여 `_centroids()[by]`를 인덱싱한다.
  근거: 현재 `_centroids()`가 두 축을 담은 dict를 반환. (비차단)

## 범위 밖 (Out of Scope)

- `predict_clip()`을 `_centroid_logits()`로 교체(#12), 온도 보정·가중 융합(`fuse`) 변경.
- #9 kNN 방식 구현, 방식 비교·선정(#12), 노트북 평가.
- CLI/UI, 색인 생성(`data.py`), OpenCV 색·선 분석.

## 미해결 질문 (Open Questions)

- 없음(차단성). `_centroid_logits()`를 실제로 `predict_clip()`에 연결할지는 #12의 결정 사항으로
  이월한다.
