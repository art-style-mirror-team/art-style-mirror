"""B — `similar_works()` 동작 테스트 (#13).

`tests/test_smoke.py`는 형식만 검사하므로, 실제 색인 기준 코사인 검색 동작을 여기서 확인한다.
모델 함수(`data.embed_image`)는 `tests/conftest.py`가 자동으로 `tests/fakes.py`의 가짜로 바꿔 끼운다.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from modules import classify, data


def _img() -> np.ndarray:
    """가짜 `embed_image`에 넣을 RGB uint8 이미지."""
    return np.random.default_rng(42).integers(0, 256, size=(64, 48, 3), dtype=np.uint8)


def _index(emb_rows: list[list[float]], ids: list[str]) -> dict:
    """monkeypatch용 작은 색인. meta는 계약대로 6개 열을 모두 가진다."""
    emb = np.array(emb_rows, dtype=np.float32)
    meta = pd.DataFrame(
        {
            "id": ids,
            "artist": [f"artist-{i}" for i in ids],
            "style": [f"style-{i}" for i in ids],
            "genre": ["landscape"] * len(ids),
            "path": [f"data/{i}.jpg" for i in ids],
            "split": ["train"] * len(ids),
        }
    )
    return {"emb": emb, "meta": meta}


# FR1 — 색인 전체 기준 코사인 유사도, 점수 내림차순
def test_similar_works_cosine_over_whole_index_descending():
    index = data.load_index()
    emb = data.embed_image(_img())
    works = classify.similar_works(emb, k=5)

    scores = [w["score"] for w in works]
    assert scores == sorted(scores, reverse=True)

    # split으로 거르지 않고 색인 전체에서 찾은 코사인 최댓값(0.95 미만)이 1위여야 한다.
    normalized = index["emb"] / np.linalg.norm(index["emb"], axis=1, keepdims=True)
    cos = normalized @ (emb / np.linalg.norm(emb))
    expected_top = float(cos[cos < classify.NEAR_DUPLICATE].max())
    assert works[0]["score"] == pytest.approx(expected_top, abs=1e-5)


# FR2 — 유사도 0.95 이상(자기 자신/사실상 같은 작품)은 제외
def test_similar_works_excludes_near_duplicates():
    index = data.load_index()
    works = classify.similar_works(index["emb"][7], k=3)
    assert index["meta"].at[7, "id"] not in {w["id"] for w in works}
    assert all(w["score"] < classify.NEAR_DUPLICATE for w in works)


# FR3.1 — 각 원소는 계약의 5개 키만 가진다
def test_similar_works_result_keys():
    works = classify.similar_works(data.embed_image(_img()), k=3)
    assert works
    assert all(set(w) == {"id", "artist", "style", "path", "score"} for w in works)


# FR3.2 — 네이티브 파이썬 타입(numpy 타입이 새어 나오지 않는다)
def test_similar_works_native_python_types():
    w = classify.similar_works(data.embed_image(_img()), k=3)[0]
    assert type(w["id"]) is str
    assert type(w["artist"]) is str
    assert type(w["style"]) is str
    assert type(w["path"]) is str
    assert type(w["score"]) is float


# FR4.1 — k <= 0이면 빈 리스트
def test_similar_works_k_zero_or_negative_returns_empty():
    emb = data.embed_image(_img())
    assert classify.similar_works(emb, k=0) == []
    assert classify.similar_works(emb, k=-1) == []


# FR4.2 — 남은 후보가 k보다 적으면 있는 만큼만 돌려준다(예외 없음)
def test_similar_works_k_exceeds_candidates_returns_all(monkeypatch):
    idx = _index([[0.6, 0.8, 0.0, 0.0], [0.3, float(np.sqrt(0.91)), 0.0, 0.0]], ["X", "Y"])
    monkeypatch.setattr(classify, "load_index", lambda: idx)
    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    works = classify.similar_works(query, k=50)
    assert [w["id"] for w in works] == ["X", "Y"]  # 코사인 0.6, 0.3 → 둘 다 반환


# FR4.3 — 동점은 색인 행 오름차순으로 결정적으로 끊는다
def test_similar_works_ties_broken_by_ascending_index(monkeypatch):
    s = float(np.sqrt(0.51))
    idx = _index(
        [[0.7, s, 0.0, 0.0], [0.7, 0.0, s, 0.0], [0.5, float(np.sqrt(0.75)), 0.0, 0.0]],
        ["A", "B", "C"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)
    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    works = classify.similar_works(query, k=2)
    assert [w["id"] for w in works] == ["A", "B"]  # 코사인 0.7로 동점 → 낮은 행(A)이 먼저
    assert works[0]["score"] == pytest.approx(works[1]["score"])


# FR3.1 — 계약은 "meta 행 순서 = emb 행 순서"(위치)만 보장한다. meta의 DataFrame 인덱스가
# 0..N-1이 아니어도 emb 행 위치에 맞춰 값을 읽어야 한다(라벨 인덱스 .at였다면 여기서 깨진다).
def test_similar_works_reads_by_position_not_label(monkeypatch):
    emb = np.array(
        [
            [0.9, float(np.sqrt(0.19)), 0.0, 0.0],
            [0.6, 0.8, 0.0, 0.0],
            [0.3, float(np.sqrt(0.91)), 0.0, 0.0],
        ],
        dtype=np.float32,
    )
    meta = pd.DataFrame(
        {
            "id": ["P0", "P1", "P2"],
            "artist": ["artist-P0", "artist-P1", "artist-P2"],
            "style": ["style-P0", "style-P1", "style-P2"],
            "genre": ["landscape"] * 3,
            "path": ["data/P0.jpg", "data/P1.jpg", "data/P2.jpg"],
            "split": ["train", "val", "test"],
        },
        index=[10, 20, 30],  # 일부러 0..N-1이 아닌 인덱스
    )
    monkeypatch.setattr(classify, "load_index", lambda: {"emb": emb, "meta": meta})
    query = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32)

    works = classify.similar_works(query, k=1)
    assert [w["id"] for w in works] == ["P0"]  # 코사인 0.9가 1위(행 위치 0)
    assert works[0]["artist"] == "artist-P0"
    assert works[0]["path"] == "data/P0.jpg"


# --- #11 logreg -------------------------------------------------------------
# 선형 분류기(로지스틱 회귀) `_fit_linear`/`_save_linear`/`_load_linear`/`_linear_logits`
# 동작 테스트. 형식 검사는 `tests/test_smoke.py`가 하므로 건드리지 않는다.


def _linear_index(dim: int = 8) -> dict:
    """train/val 섞인 가짜 색인. 학습셋은 class A(0번 축)·B(1번 축) 두 개,
    검증셋은 학습에 없는 class C(2번 축)로 둬서 "학습셋만 사용"을 확인할 수 있게 한다."""
    rng = np.random.default_rng(0)
    emb_rows: list[np.ndarray] = []
    artist: list[str] = []
    style: list[str] = []
    split: list[str] = []

    def add(axis: int, cls: str, sp: str, n: int) -> None:
        for _ in range(n):
            v = rng.normal(0.0, 0.03, size=dim).astype(np.float32)
            v[axis] += 1.0
            emb_rows.append(v)
            artist.append(cls)
            style.append(f"s{cls}")
            split.append(sp)

    add(0, "A", "train", 6)
    add(1, "B", "train", 6)
    add(2, "C", "val", 4)  # 학습에 없는 라벨: 클래스에 영향 주면 안 됨
    emb = np.array(emb_rows, dtype=np.float32)
    meta = pd.DataFrame(
        {
            "id": [str(i) for i in range(len(artist))],
            "artist": artist,
            "style": style,
            "genre": ["landscape"] * len(artist),
            "path": [f"data/{i}.jpg" for i in range(len(artist))],
            "split": split,
        }
    )
    return {"emb": emb, "meta": meta}


def _biased(dim: int, axis: int) -> np.ndarray:
    """특정 축 쪽으로 치우친 입력 1장 (shape (1, dim))."""
    v = np.zeros((1, dim), dtype=np.float32)
    v[0, axis] = 1.0
    return v


# FR2.1 — 학습셋(train)만으로 학습한다: val 라벨 "C"는 클래스에 들어가지 않는다
def test_fit_linear_uses_train_split_only(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)

    model = classify._fit_linear("artist")
    assert list(model.classes_) == ["A", "B"]  # "C"(val) 없음

    style_model = classify._fit_linear("style")
    assert list(style_model.classes_) == ["sA", "sB"]  # "sC"(val) 없음


# FR5.4 — 특정 클래스 쪽으로 치우친 입력은 그 이름의 z가 최대
def test_linear_logits_biased_input_argmax(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    model = classify._fit_linear("artist")

    names, z = classify._linear_logits(_biased(8, 0), "artist", model=model)
    assert names[int(np.argmax(z[0]))] == "A"  # 0번 축 → A

    names, z = classify._linear_logits(_biased(8, 1), "artist", model=model)
    assert names[int(np.argmax(z[0]))] == "B"  # 1번 축 → B


# FR3, FR4, NFR1 — 저장→로드 라운드트립 후 로짓이 동일
def test_linear_logits_save_load_roundtrip(tmp_path, monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    models = {"artist": classify._fit_linear("artist"), "style": classify._fit_linear("style")}

    path = tmp_path / "linear.pkl"
    classify._save_linear(models, path=path)
    assert path.exists()

    loaded = classify._load_linear(path)
    assert loaded["sklearn_version"] == __import__("sklearn").__version__
    assert loaded["C"] == {"artist": 1.0, "style": 1.0}

    E = _biased(8, 0)
    names_fit, z_fit = classify._linear_logits(E, "artist", model=models["artist"])
    names_load, z_load = classify._linear_logits(E, "artist", model=loaded["artist"])
    assert names_fit == names_load
    assert np.array_equal(z_fit, z_load)


# FR5.5 — 반환 모양: (이름 목록, z), z.shape == (n, 이름 수), 이름 = classes_ 정렬
def test_linear_logits_shape(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    model = classify._fit_linear("artist")

    E = np.concatenate([_biased(8, 0), _biased(8, 1)], axis=0)  # n=2
    names, z = classify._linear_logits(E, "artist", model=model)
    assert names == list(model.classes_) == ["A", "B"]
    assert isinstance(names, list)
    assert z.shape == (2, len(names))  # 이진 분류를 (n, 이름 수)로 맞춤


# FR5.2 — 1차원 입력이면 ValueError
def test_linear_logits_rejects_1d(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    model = classify._fit_linear("artist")

    with pytest.raises(ValueError):
        classify._linear_logits(np.zeros(8, dtype=np.float32), "artist", model=model)


# FR5.3 — 0장 입력이면 (이름 목록, (0, 이름 수))
def test_linear_logits_empty_input(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    model = classify._fit_linear("artist")

    names, z = classify._linear_logits(np.zeros((0, 8), dtype=np.float32), "artist", model=model)
    assert names == ["A", "B"]
    assert z.shape == (0, 2)


# FR4.2 — 없는 경로로 로드하면 알기 쉬운 FileNotFoundError
def test_load_linear_missing_file(tmp_path):
    classify._load_linear.cache_clear()
    missing = tmp_path / "does-not-exist.pkl"
    with pytest.raises(FileNotFoundError) as exc:
        classify._load_linear(missing)
    assert str(missing) in str(exc.value)  # 경로를 알려 준다


# FR5.4, NFR2 (R1) — [0, z]로 쌓은 덕에 softmax(z)가 model.predict_proba와 일치한다
def test_linear_logits_softmax_matches_predict_proba(monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    model = classify._fit_linear("artist")  # 2클래스(A, B)

    E = np.concatenate([_biased(8, 0), _biased(8, 1)], axis=0)  # n=2
    _, z = classify._linear_logits(E, "artist", model=model)
    e = np.exp(z - z.max(axis=1, keepdims=True))
    softmax = e / e.sum(axis=1, keepdims=True)
    proba = model.predict_proba(classify._l2_normalize(E))
    assert np.allclose(softmax, proba)


# FR3.1 (R2) — 같은 경로 재저장 시 cache_clear 덕에 새 C가 다시 읽힌다
def test_save_linear_resave_updates_cache(tmp_path, monkeypatch):
    classify._load_linear.cache_clear()
    monkeypatch.setattr(classify, "load_index", _linear_index)
    path = tmp_path / "linear.pkl"

    m1 = {
        "artist": classify._fit_linear("artist", C=1.0),
        "style": classify._fit_linear("style", C=1.0),
    }
    classify._save_linear(m1, path=path)
    assert classify._load_linear(path)["C"] == {"artist": 1.0, "style": 1.0}

    m2 = {
        "artist": classify._fit_linear("artist", C=0.1),
        "style": classify._fit_linear("style", C=0.1),
    }
    classify._save_linear(m2, path=path)
    assert classify._load_linear(path)["C"] == {"artist": 0.1, "style": 0.1}
