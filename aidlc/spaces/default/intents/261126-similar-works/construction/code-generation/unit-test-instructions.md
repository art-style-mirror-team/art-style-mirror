# 단위 테스트 지침 — #13 `similar_works()`

## 테스트 프레임워크 / 구성

- 기존 pytest를 그대로 쓴다. 추가 설정 없음.
- `tests/conftest.py`가 `@pytest.mark.model`이 없는 테스트에서 모델 함수(`data.embed_image` 등)를
  `tests/fakes.py`의 가짜로 자동 교체한다. `load_index()`는 가짜가 아니라 실제(스텁) 색인을 쓴다
  (24명 × 20점 = 480행, L2 정규화된 결정적 `emb`).
- 모델 함수는 반드시 모듈을 통해 부른다(`data.embed_image(...)`). 이 이슈는 새 모델 함수를
  추가하지 않으므로 `FAKES`에 추가할 항목은 없다.

## 이 작업의 테스트 실행 방법 (unit-scoped)

이 이슈의 동작 테스트만 실행하는 정확한 명령 (Windows PowerShell):

```
.venv\Scripts\python -m pytest tests/test_classify.py -q
```

(venv를 이미 활성화했다면 `python -m pytest tests/test_classify.py -q`)

이 명령은 테스트 우선 단계 전에도 그대로 실행 가능해야 한다(기존 러너 재사용).

## 전체 회귀 (Build and Test가 확인)

```
.venv\Scripts\python -m pytest -q
```

`tests/test_smoke.py`는 `similar_works`를 이미 검사하므로 전체 통과가 유지되어야 한다
(`test_similar_works_excludes_itself`, `test_classify_formats`). 이 파일은 수정하지 않는다.

## 커버리지 목표

- 커버리지 하한 없음(팀 규칙). 조건은 `pytest` 전체 통과다. 이 작업은 임계값을 설정하지 않는다.

## 작성할 테스트 (Minimal: 요구사항당 1개 + happy-path)

1. `test_similar_works_sorted_by_cosine` — 무작위 입력에서 score가 내림차순이고 모두 < 0.95. (FR1)
2. `test_similar_works_excludes_self` — 색인 자기 임베딩을 넣으면 그 행이 제외되고 모든 score < 0.95. (FR2)
3. `test_similar_works_native_types` — `id/artist/style/path`는 `str`, `score`는 파이썬 `float`
   (numpy/pandas 스칼라 아님). 키 집합도 계약과 일치. (FR3)
4. `test_similar_works_k_zero` — `k=0`이면 `[]`. (FR4.1)
5. `test_similar_works_k_larger_than_candidates` — 아주 큰 k면 예외 없이 0.95 미만 후보 전부 반환. (FR4.2)
6. `test_similar_works_deterministic` — 같은 입력을 두 번 호출하면 동일한 결과. (FR4.3)
7. `test_similar_works_ties_break_by_index_order` — `load_index`를 작은 가짜 색인으로 바꿔
   동점(같은 코사인 < 0.95) 시 색인 행 순서(낮은 인덱스)가 먼저 옴을 검증. (FR4.3)
8. `test_similar_works_reads_by_position_not_label` — DataFrame 인덱스가 0..N-1이 아닌 meta
   (예: 인덱스 `[10, 20, 30]`)를 `monkeypatch`로 주입해, 결과 값이 `emb` 행 위치에 맞게 읽히는지
   검증(`meta.iloc` 사용 확인, `.at` 라벨 인덱스였다면 KeyError/오매칭). (FR3.1)

## 모킹/스터빙·테스트 데이터

- 1~6번은 실제(스텁) `load_index()`와 가짜 `embed_image`를 쓴다.
- 7번은 `monkeypatch.setattr(classify, "load_index", ...)`로 3행짜리 통제된 색인을 주입해
  동점을 재현한다(실제 색인은 float 동점이 거의 없어 결정성만으로는 2차 키를 증명하기 어렵기 때문).
