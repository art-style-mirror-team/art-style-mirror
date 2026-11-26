# Code Summary — u1-knn-vote (#9 kNN 투표 방식 판정)

## 바꾼 파일 (3개, NFR3 범위 안)

1. **`modules/classify.py`** — 비공개 함수 2개를 파일 끝에 추가. 기존 공개 계약(`predict_clip`,
   `similar_works`, `fuse` 등)과 `_l2_normalize`·`load_index`는 건드리지 않았다.
   - `_knn_logits(E, k, by, eps=1e-3) -> (names, z)`
   - `_topk_accuracy(z, names, labels, ks=(1, 3)) -> dict[int, float]`
2. **`tests/test_classify.py`** — 파일 끝에 `# --- #9 kNN` 절로 동작 테스트 9개 추가. 작은
   가짜 색인(`_knn_index`)을 `classify.load_index`에 monkeypatch한다. `tests/test_smoke.py`는
   수정하지 않았다(FR3.3).
3. **`notebooks/eval.ipynb`** — 맨 아래에 `#9 kNN` 절(마크다운 1 + 코드 3)을 추가. 셀 출력은
   비웠고(`outputs: []`, `execution_count: null`), 유효한 nbformat 4.5 구조.
   **(개정 2026-11-26)** 이 개정에서는 `notebooks/eval.ipynb`의 `#9 kNN` 절만 손봤다. `classify.py`와
   `test_classify.py`는 바꾸지 않았다. 두 가지: ① 첫 코드 셀 맨 위에서 저장소 루트(`modules` 폴더의
   상위)를 `sys.path`에 넣어 `notebooks/`를 작업 위치로 실행해도 `from modules import ...`가 되게
   했다. ② "표받은 이름 수 평균"의 eps를 `1e-3`으로 하드코딩하지 않고
   `inspect.signature(classify._knn_logits).parameters["eps"].default`로 읽어 쓴다(기본값이 바뀌어도
   따라감).

`contracts/interfaces.md`, `predict_clip()`, `tests/test_smoke.py`, 다른 모듈 파일은 불변.

## 핵심 설계 결정

- **학습셋 한정·위치 기반 읽기**: 이웃은 `split=="train"` 행만 쓴다. 메타는 `meta[col].to_numpy()`로
  열을 위치 순 numpy 배열로 뽑아 읽어, 라벨 인덱스 가정을 피한다(메모리 노트·similar_works와 동일
  규칙, FR1.7).
- **이름 목록**: `sorted(np.unique(train 행의 by 값))`으로 색인에서 읽어 정한다(개수 비고정, FR1.7).
  이웃이 학습셋에서만 오므로 이름 공간도 학습셋 이름으로 둔다(`_centroids`와 일관).
- **결정적 동점 처리**: 이웃 선택은 `np.argsort(-sims, kind="stable")`로 유사도 내림차순 + 동점은
  색인 위치 앞선 이웃 먼저(FR1.8). 이름 순위 동점은 열이 이름순으로 정렬돼 있어 `_topk_accuracy`의
  안정 정렬이 이름순으로 끊는다(FR1.6).
- **clip + eps 바닥값**: `max(sim, 0)`으로 clip 후 이름별 합산, `z = log(투표 + eps)`. 투표 합이
  항상 0 이상이라 모든 z가 유한하고, 투표 0인 이름은 `log(eps)`(기본 `log(1e-3)`). 더 작은 값은
  쓰지 않는다(NFR5).
- **엣지 순서(FR1.9)**: `k<=0` 또는 빈 학습셋 → `ValueError`(n 무관, 먼저 검사) → k를 학습셋
  크기로 clamp → `n==0`이면 `(names, (0, 이름 수))` 빈 z.
- **`_topk_accuracy` 일반화(FR2.3)**: `_knn_logits`의 `(names, z)` 형식에만 의존하고 특정 `by`에
  묶이지 않아 #10·#11에서 그대로 재사용 가능. 미지 label은 오답(FR2.4), `ks` 초과는 이름 수로
  clamp(키는 원래 값 유지), 행 수≠labels·`ks<=0`은 `ValueError`(FR2.5).
- **노트북**: 검증셋(`split=="val"`)만 사용, k=5/10/20, `by="artist"`·`"style"` 둘 다 계산(비교
  기준 artist), k별 "표받은 이름 수 평균"(z > log(eps)) 표시. 첫 셀에서
  `load_index()["meta"].attrs.get("fake")` 출력 + True면 경고. 테스트셋 미사용, 출력 비움.

## 테스트 커버리지 (`# --- #9 kNN`, 9개)

- `test_knn_logits_return_shape_and_sorted_names` — 반환 형식·이름 정렬 (FR1.1/1.5/1.7)
- `test_knn_logits_uses_train_only` — 학습셋 한정 이웃 (FR1.2)
- `test_knn_logits_weighted_vote_accumulates` — 가중 투표 합산 (FR1.3/1.4)
- `test_knn_logits_clip_negative_and_eps_floor` — 음수 clip·유한·log(eps)·eps 키워드 (FR1.4/1.5/NFR5)
- `test_knn_logits_neighbor_tie_broken_by_position` — 이웃 동점 위치순 (FR1.8/NFR1)
- `test_knn_logits_edge_order` — k<=0·clamp·n==0 (FR1.9)
- `test_knn_logits_empty_train_raises_regardless_of_n` — 빈 학습셋 ValueError (FR1.9)
- `test_topk_accuracy_counts_name_order_tie_and_unknown_label` — dict 반환·이름순 동점·미지 label (FR2.2/2.4)
- `test_topk_accuracy_clamp_and_value_errors` — ks clamp·ValueError (FR2.4/2.5)

## 실행 결과 (실제)

- `ruff format .` → 26 files unchanged (최종). `ruff check .` → All checks passed.
- 유닛 명령 `.venv\Scripts\python -m pytest tests/test_classify.py` → **17 passed** (기존 8 + #9 9).
- 전체 `.venv\Scripts\python -m pytest` → **47 passed, 2 skipped**(2개는 `@pytest.mark.model`).
- 노트북 `#9 kNN` 셀을 스텁 색인으로 실행 → 오류 없음(FR4.6). 수치는 가짜 색인이라 기록하지 않음(NFR2),
  셀 출력은 비운 채 커밋.
- **(개정 2026-11-26)** 작업 위치를 `notebooks/`로 둔 채 `#9 kNN` 코드 셀 3개를 실제 실행 →
  `from modules import ...`·`inspect.signature` eps 읽기 모두 오류 없이 통과. 실행 후 셀 출력을 다시
  비웠다(`outputs: []`, `execution_count: null`, nbformat 4.5 유지). `ruff format .` → 26 files
  unchanged, `ruff check --fix .` → All checks passed, 전체 `pytest` → **47 passed, 2 skipped**(변동
  없음, 테스트 불변). 수치는 가짜 색인이라 기록하지 않음(NFR2).

## written-but-not-run / 편차

- 없음. 모든 테스트 실행·통과. 계약(custom ordering) 그대로 지킴: `tests/test_smoke.py`는 불변·green,
  #9 동작 테스트는 구현과 같은 PR에서 작성·실행. 데이터 모델 변경 없음(엔티티·테이블 추가 없음).
