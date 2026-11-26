# Code Summary — #13 `similar_works()` 실제 색인 검색

## 변경·생성 파일

- **수정** `modules/classify.py`
  - `_l2_normalize(v)` 헬퍼 추가: 마지막 축 L2 정규화, 1D(질의 `(512,)`)·2D(색인 `(N,512)`) 모두 처리,
    영벡터는 `np.maximum(norm, 1e-12)`로 안전 처리, 새 배열 반환(읽기 전용 색인 `emb` 비변경).
  - `similar_works(emb, k=3)` 본문 교체(이름·시그니처·반환 형식 불변):
    입력과 색인 `emb`를 각각 L2 정규화 → 내적(코사인) → 색인 전체에서 검색(`split` 미필터) →
    `np.argsort(-scores, kind="stable")`(내림차순 + 색인 행 오름차순 동점 처리) →
    `score >= 0.95`(`NEAR_DUPLICATE`) 제외 → `k`개 수집. `k <= 0`이면 `[]`.
    각 원소는 `str`(id/artist/style/path)·`float`(score)로 변환.
    - **리뷰 반영**: 값을 `meta.at[row, ...]`(라벨 인덱스)가 아니라 `meta.iloc[row]`(위치 기준)로
      읽는다. 계약은 "meta 행 순서 = emb 행 순서"(위치)만 보장하고 DataFrame 인덱스가 0..N-1이라는
      보장은 없기 때문. `_l2_normalize`는 변경 없음.
- **생성** `tests/test_classify.py` — 동작 테스트 8개(아래).

`tests/test_smoke.py`, `tests/conftest.py`, `tests/fakes.py`, `contracts/interfaces.md`,
다른 `modules/` 파일은 수정하지 않았다.

## 핵심 구현 결정

- 미리 slice하지 않고 "루프 후 k개까지 수집"으로 구현 → `>=0.95` 제외와 "후보가 k보다 적음"이
  인덱스 오류 없이 자연히 처리됨(FR4.1·FR4.2).
- 동점 결정성(FR4.3)은 `kind="stable"` 안정 정렬로 색인 행 오름차순을 2차 키로 보장.
- 색인 `emb`는 읽기 전용이라 정규화는 새 배열로 만들어 원본을 건드리지 않음.

## 테스트 커버리지

`tests/test_classify.py` 8개:
1. FR1 — 색인 전체 코사인 + 내림차순(brute-force로 최상위 확인)
2. FR2 — 0.95 이상(자기 자신/근접 중복) 제외
3. FR3.1 — 결과가 계약의 5개 키를 정확히 가짐
4. FR3.2 — 네이티브 타입(`type(...) is str`/`is float`, numpy 누수 검출)
5. FR4.1 — `k=0`, `k=-1` → `[]`
6. FR4.2 — k가 후보 수보다 클 때 남은 후보 전부 반환(2행 가짜 색인)
7. FR4.3 — 동점 시 색인 행 오름차순(3행 가짜 색인, 같은 코사인 A→B)
8. FR3.1 — meta의 DataFrame 인덱스가 0..N-1이 아닐 때(`[10,20,30]`)도 emb 행 위치 기준으로
   읽힘(`meta.iloc` 확인; 리뷰 반영)

## 실행한 검증 (실제 결과)

- `python -m pytest tests/test_classify.py -q` → **8 passed** (약 0.90s)
- `python -m pytest -q` (전체) → **38 passed, 2 skipped** (약 10.72s).
  2 skipped는 `@pytest.mark.model` 실제 모델 테스트(기본 실행에서 건너뜀).
  `test_smoke.py::test_similar_works_excludes_itself`, `test_classify_formats`는 실제 구현에서도 그대로 통과.
- `ruff format .` → 26 files unchanged. `ruff check --fix .` → All checks passed.
- (리뷰 전 1차 빌드 결과는 test_classify.py 7 passed / 전체 37 passed, 2 skipped였고, 위 수치는
  `meta.iloc` 반영 + 테스트 1개 추가 후의 최종 결과다.)

## 실행했으나 이 단계에서 돌리지 않은 테스트

- `@pytest.mark.model` 실제 모델 테스트 2개: 기본 pytest·CI가 건너뛰는 설계. `pytest --run-model`로만
  실행되며 이 변경 범위 밖이라 돌리지 않았다.

## 계획 대비 편차

- 없음. 계획의 Step 1~6을 그대로 수행.
