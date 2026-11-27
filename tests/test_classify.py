"""B — `similar_works()` 동작 테스트 (#13).

`tests/test_smoke.py`는 형식만 검사하므로, 실제 색인 기준 코사인 검색 동작을 여기서 확인한다.
모델 함수(`data.embed_image`)는 `tests/conftest.py`가 자동으로 `tests/fakes.py`의 가짜로 바꿔 끼운다.
"""

from __future__ import annotations

from contextlib import contextmanager

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


# --- #10 centroid


def _centroid_index(rows: list[tuple]) -> dict:
    """중심점 테스트용 작은 색인. rows는 (id, artist, style, split, emb_row) 튜플 목록.
    meta는 계약대로 6개 열(id, artist, style, genre, path, split)을 모두 가진다."""
    ids = [r[0] for r in rows]
    meta = pd.DataFrame(
        {
            "id": ids,
            "artist": [r[1] for r in rows],
            "style": [r[2] for r in rows],
            "genre": ["landscape"] * len(rows),
            "path": [f"data/{i}.jpg" for i in ids],
            "split": [r[3] for r in rows],
        }
    )
    emb = np.array([r[4] for r in rows], dtype=np.float32)
    return {"emb": emb, "meta": meta}


@contextmanager
def _fake_centroids(monkeypatch, idx: dict):
    """가짜 색인을 끼우고, `_centroids`가 `lru_cache`이므로 전후로 캐시를 비운다."""
    monkeypatch.setattr(classify, "load_index", lambda: idx)
    classify._centroids.cache_clear()
    try:
        yield
    finally:
        classify._centroids.cache_clear()


# FR3.2 — 중심점에는 학습셋(split=="train")만 쓰인다(비학습 행이 섞이면 결과가 달라짐)
def test_centroid_logits_uses_train_split_only(monkeypatch):
    # artist "A": train 2행([1,0,0])과 val 1행([0,1,0]). val이 섞이면 A 중심점이 [0,1,0] 쪽으로 이동.
    idx = _centroid_index(
        [
            ("a1", "A", "sA", "train", [1.0, 0.0, 0.0]),
            ("a2", "A", "sA", "train", [1.0, 0.0, 0.0]),
            ("a3", "A", "sA", "val", [0.0, 1.0, 0.0]),
            ("b1", "B", "sB", "train", [0.0, 0.0, 1.0]),
        ]
    )
    with _fake_centroids(monkeypatch, idx):
        names, z = classify._centroid_logits(np.array([[1.0, 0.0, 0.0]]), "artist", scale=1.0)
        assert names == ["A", "B"]
        # 학습셋만 쓰면 A 중심점은 [1,0,0] → [1,0,0]과 코사인 1.0. val이 섞였다면 ~0.894로 줄어든다.
        assert z[0, names.index("A")] == pytest.approx(1.0)


# FR3.3 — 어떤 중심점에 가장 가까운 입력이면 그 이름의 z가 최댓값(argmax)이다
def test_centroid_logits_nearest_centroid_has_largest_z(monkeypatch):
    idx = _centroid_index(
        [
            ("a", "A", "sA", "train", [1.0, 0.0, 0.0]),
            ("b", "B", "sB", "train", [0.0, 1.0, 0.0]),
            ("c", "C", "sC", "train", [0.0, 0.0, 1.0]),
        ]
    )
    with _fake_centroids(monkeypatch, idx):
        names, z = classify._centroid_logits(np.array([[0.9, 0.1, 0.0]]), "artist")
        assert names[int(np.argmax(z[0]))] == "A"  # A 중심점에 가장 가깝다


# FR3.4 — scale은 z에 선형으로 반영된다(2배 → z 2배)
def test_centroid_logits_scale_is_linear(monkeypatch):
    idx = _centroid_index(
        [
            ("a", "A", "sA", "train", [1.0, 0.0, 0.0]),
            ("b", "B", "sB", "train", [0.0, 1.0, 0.0]),
        ]
    )
    E = np.array([[0.8, 0.6, 0.0]])
    with _fake_centroids(monkeypatch, idx):
        _, z1 = classify._centroid_logits(E, "artist", scale=5.0)
        _, z2 = classify._centroid_logits(E, "artist", scale=10.0)
        assert z2 == pytest.approx(2.0 * z1)


# FR2.1/FR3.5 — 1차원 입력이면 ValueError
def test_centroid_logits_rejects_1d_input(monkeypatch):
    idx = _centroid_index([("a", "A", "sA", "train", [1.0, 0.0, 0.0])])
    with _fake_centroids(monkeypatch, idx), pytest.raises(ValueError):
        classify._centroid_logits(np.array([1.0, 0.0, 0.0]), "artist")


# FR2.2/FR3.5 — 0장 입력이면 예외 없이 (이름 목록, (0, 이름 수) z)를 돌려준다
def test_centroid_logits_zero_rows_returns_empty_z(monkeypatch):
    idx = _centroid_index(
        [
            ("a", "A", "sA", "train", [1.0, 0.0, 0.0]),
            ("b", "B", "sB", "train", [0.0, 1.0, 0.0]),
        ]
    )
    with _fake_centroids(monkeypatch, idx):
        names, z = classify._centroid_logits(np.zeros((0, 3), dtype=np.float32), "artist")
        assert z.shape == (0, len(names))


# FR2.3/FR3.5 — scale <= 0이면 ValueError
def test_centroid_logits_rejects_non_positive_scale(monkeypatch):
    idx = _centroid_index([("a", "A", "sA", "train", [1.0, 0.0, 0.0])])
    with _fake_centroids(monkeypatch, idx):
        E = np.array([[1.0, 0.0, 0.0]])
        with pytest.raises(ValueError):
            classify._centroid_logits(E, "artist", scale=0.0)
        with pytest.raises(ValueError):
            classify._centroid_logits(E, "artist", scale=-1.0)
