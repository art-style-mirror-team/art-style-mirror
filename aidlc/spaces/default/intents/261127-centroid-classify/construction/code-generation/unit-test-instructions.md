# 단위 테스트 안내 — #10 `_centroid_logits()`

## 프레임워크·설정

- pytest (설정은 `pyproject.toml`). `tests/conftest.py`가 모델 함수 `data.embed_image`를
  `tests/fakes.py`의 가짜로 자동으로 바꿔 끼운다. 이번 변경은 모델을 쓰지 않으므로
  `@pytest.mark.model` 없이 기본 실행으로 돈다.
- `_centroid_logits`는 `classify.load_index`를 monkeypatch한 작은 가짜 색인으로 테스트한다.
  `_centroids()`가 `@lru_cache(maxsize=1)`이므로 각 테스트 안에서 `classify._centroids.cache_clear()`를
  monkeypatch 직후와 테스트 끝(정리)에 호출한다.

## 이 이슈(#10) 테스트 실행 명령 (unit-scoped)

```
.venv\Scripts\python -m pytest tests/test_classify.py
```

(macOS/Linux: `.venv/bin/python -m pytest tests/test_classify.py`)

이 명령은 이 이슈의 동작 테스트 파일만 돈다. 전체 스위트(`pytest`)는 Build and Test 단계에서
돌려 `tests/test_smoke.py`를 포함한 기존 테스트가 모두 녹색인지 확인한다.

## 커버리지 목표

- 프로젝트에 라인 커버리지 하한 없음(team.md). 조건은 `pytest` 전체 통과다.
- Minimal 전략: 요구사항(FR1~FR3)당 동작 테스트 1개 이상, happy-path 포함. 총 6개 예정.

## 목·스텁 안내

- 외부 모델 로드 없음. 색인은 `monkeypatch.setattr(classify, "load_index", lambda: idx)`로 주입한다.
- 가짜 색인 `meta`는 계약대로 6개 열(`id, artist, style, genre, path, split`)을 모두 둔다
  (`tests/test_classify.py`의 기존 `_index` 헬퍼 관례를 따른다).

## 테스트 데이터

- 임베딩은 축이 뚜렷한 작은 단위벡터로 만들어 "가장 가까운 중심점 = 최대 z"를 결정적으로 검사한다.
- 학습셋 전용 검사는 같은 이름에 `split`만 다른 행(train/val)을 넣어, 비학습 행이 중심점을
  바꾸지 못하는지 확인한다.
