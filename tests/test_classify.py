"""B — `classify.py` 동작 테스트.

- #8 `detect_type()`: CLIP zero-shot 유형 판별
- #13 `similar_works()`: 실제 색인 기준 코사인 검색

`tests/test_smoke.py`는 형식만 검사하므로 동작은 여기서 확인한다. 모델 함수(`data.embed_image`,
`data.embed_text`)는 `tests/conftest.py`가 `tests/fakes.py`의 가짜로 바꿔 끼우므로 실제 CLIP은
내려받지 않는다(`@pytest.mark.model` 없음).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from modules import classify, data

# --- #8 detect_type() ------------------------------------------------------

TYPES = {"photo", "painting", "sketch"}


def _sample_emb() -> np.ndarray:
    """가짜 `data.embed_image`로 만든 결정적 이미지 임베딩."""
    img = np.random.default_rng(0).integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
    return data.embed_image(img)


def test_detect_type_returns_valid_literal():
    # happy path: 반환은 계약이 정한 세 리터럴 중 하나.
    assert classify.detect_type(_sample_emb()) in TYPES


def test_detect_type_deterministic():
    # 같은 입력 → 같은 결과.
    emb = _sample_emb()
    assert classify.detect_type(emb) == classify.detect_type(emb)


def test_detect_type_matches_prompt_class(monkeypatch):
    # 각 유형을 한 축(one-hot)에 몰아주는 가짜로 바꿔, 그 축 벡터를 넣으면 해당 유형이
    # 나오는지 확인한다. 핵심 정확성: 프로토타입·코사인 argmax가 제대로 작동하는가.
    classes = list(classify.TYPE_PROMPTS)

    def stub(texts):
        if isinstance(texts, str):
            texts = [texts]
        rows = []
        for text in texts:
            vec = np.zeros(512, dtype=np.float32)
            cls = next(c for c in classes if text in classify.TYPE_PROMPTS[c])
            vec[classes.index(cls)] = 1.0
            rows.append(vec)
        return np.array(rows, dtype=np.float32)

    monkeypatch.setattr(data, "embed_text", stub)

    for i, cls in enumerate(classes):
        basis = np.zeros(512, dtype=np.float32)
        basis[i] = 1.0
        assert classify.detect_type(basis) == cls


def test_detect_type_scale_invariant():
    # 방향이 같고 크기만 다른 입력은 같은 유형으로 분류된다(코사인 기반).
    emb = _sample_emb()
    assert classify.detect_type(emb) == classify.detect_type(emb * 3.0)


def test_detect_type_nan_input_returns_valid_literal():
    # NaN·inf가 섞인 입력이어도 None이 아니라 세 리터럴 중 하나를 돌려준다(계약).
    emb = np.full(512, np.nan, dtype=np.float32)
    assert classify.detect_type(emb) in TYPES
    emb = _sample_emb().copy()
    emb[0] = np.inf
    assert classify.detect_type(emb) in TYPES


# --- #13 similar_works() ---------------------------------------------------


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


# --- #9 kNN 투표 방식 판정 (_knn_logits·_topk_accuracy) ------------------------------
#
# 작은 가짜 색인을 classify.load_index에 monkeypatch해 동작을 검증한다. 모델 다운로드가 없으므로
# @pytest.mark.model은 쓰지 않는다. 임베딩은 추론을 쉽게 하려고 2차원 벡터를 쓴다(_l2_normalize는
# 차원에 무관하므로 정상 동작한다).


def _knn_index(
    emb_rows: list[list[float]], artists: list[str], styles: list[str], splits: list[str]
) -> dict:
    """#9용 작은 가짜 색인. meta는 계약의 6개 열을 모두 가지고 attrs["fake"]=True."""
    emb = np.array(emb_rows, dtype=np.float32)
    n = len(emb_rows)
    meta = pd.DataFrame(
        {
            "id": [f"w{i}" for i in range(n)],
            "artist": artists,
            "style": styles,
            "genre": ["landscape"] * n,
            "path": [f"data/w{i}.jpg" for i in range(n)],
            "split": splits,
        }
    )
    meta.attrs["fake"] = True
    return {"emb": emb, "meta": meta}


# FR1.1/FR1.5/FR1.7 — 반환 형식 (이름 목록, (n, 이름 수) z), 이름은 색인에서 읽혀 정렬됨
def test_knn_logits_return_shape_and_sorted_names(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]],
        ["Bob", "Ann", "Bob"],
        ["s1", "s0", "s1"],
        ["train", "train", "train"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)
    E = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=np.float32)

    names, z = classify._knn_logits(E, k=2, by="artist")
    assert names == ["Ann", "Bob"]  # 색인에서 읽어 정렬(개수 고정 아님)
    assert z.shape == (2, 2)
    assert np.all(np.isfinite(z))


# FR1.2 — 이웃은 학습셋에서만 찾는다(val/test 행은 투표에 포함되지 않고 이름 목록에도 없다)
def test_knn_logits_uses_train_only(monkeypatch):
    idx = _knn_index(
        [[0.6, 0.8], [1.0, 0.0], [1.0, 0.0]],
        ["Ann", "Zed", "Zed"],
        ["s0", "s1", "s1"],
        ["train", "val", "test"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    names, z = classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=1, by="artist")
    assert names == ["Ann"]  # Zed는 train이 아니므로 이름 목록에 없다
    assert z.shape == (1, 1)
    assert z[0, 0] == pytest.approx(np.log(0.6 + 1e-3), abs=1e-6)  # Ann 투표 = 코사인 0.6


# FR1.3/FR1.4 — 유사도 큰 이웃이 많은 이름의 z가 더 크다(가중 투표 합산)
def test_knn_logits_weighted_vote_accumulates(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [0.8, 0.6], [0.1, float(np.sqrt(0.99))]],
        ["Ann", "Ann", "Bob"],
        ["s0", "s0", "s1"],
        ["train", "train", "train"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    names, z = classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=3, by="artist")
    assert z[0, names.index("Ann")] > z[0, names.index("Bob")]
    assert z[0, names.index("Ann")] == pytest.approx(np.log(1.0 + 0.8 + 1e-3), abs=1e-6)


# FR1.4/FR1.5/NFR5 — 음수 유사도 clip → 모든 z 유한, 투표 0인 이름은 log(eps), eps 키워드 동작
def test_knn_logits_clip_negative_and_eps_floor(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [0.0, 1.0]],
        ["Ann", "Bob"],
        ["s0", "s1"],
        ["train", "train"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    # 질의는 Ann과 코사인 1, Bob과 코사인 0 → Bob 투표 0 → log(기본 eps 1e-3)
    names, z = classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=2, by="artist")
    assert np.all(np.isfinite(z))
    assert z[0, names.index("Bob")] == pytest.approx(np.log(1e-3), abs=1e-6)

    # 모든 이웃과 음의 코사인 → 전부 clip 0 → 모든 z = log(eps), eps 키워드가 먹힌다
    _, z_neg = classify._knn_logits(np.array([[-1.0, -1.0]], np.float32), k=2, by="artist", eps=0.5)
    assert np.allclose(z_neg, np.log(0.5))


# FR1.8/NFR1 — 이웃 선택 동점은 색인 행 위치가 앞선 쪽을 먼저(안정 정렬)
def test_knn_logits_neighbor_tie_broken_by_position(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [1.0, 0.0]],  # 두 이웃 모두 코사인 1.0으로 동점
        ["Ann", "Bob"],
        ["s0", "s1"],
        ["train", "train"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    names, z = classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=1, by="artist")
    assert z[0, names.index("Ann")] == pytest.approx(np.log(1.0 + 1e-3), abs=1e-6)  # 앞선 Ann
    assert z[0, names.index("Bob")] == pytest.approx(np.log(1e-3), abs=1e-6)  # Bob 투표 없음


# FR1.9 — 엣지 순서: k<=0 → ValueError, k 초과 → clamp, n==0 → (names, (0, 이름 수))
def test_knn_logits_edge_order(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [0.0, 1.0]],
        ["Ann", "Bob"],
        ["s0", "s1"],
        ["train", "train"],
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    with pytest.raises(ValueError):
        classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=0, by="artist")

    _, z = classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=99, by="artist")
    assert z.shape == (1, 2)  # k가 학습셋 크기 초과 → clamp, 오류 없음

    names0, z0 = classify._knn_logits(np.empty((0, 2), np.float32), k=1, by="artist")
    assert names0 == ["Ann", "Bob"]
    assert z0.shape == (0, 2)  # n==0 → 빈 z


# FR1.9 — 학습셋이 비면 n과 무관하게 ValueError(학습셋·k 검사를 n 처리보다 먼저)
def test_knn_logits_empty_train_raises_regardless_of_n(monkeypatch):
    idx = _knn_index(
        [[1.0, 0.0], [0.0, 1.0]],
        ["Ann", "Bob"],
        ["s0", "s1"],
        ["val", "test"],  # train 없음
    )
    monkeypatch.setattr(classify, "load_index", lambda: idx)

    with pytest.raises(ValueError):
        classify._knn_logits(np.array([[1.0, 0.0]], np.float32), k=1, by="artist")
    with pytest.raises(ValueError):  # 입력 0장이어도 학습셋이 비면 ValueError
        classify._knn_logits(np.empty((0, 2), np.float32), k=1, by="artist")


# FR2.2/FR2.4 — dict {k: 정확도} 반환, 상위 선택 동점은 이름순, 미지 label은 오답
def test_topk_accuracy_counts_name_order_tie_and_unknown_label():
    names = ["Ann", "Bob", "Cindy"]
    z = np.array(
        [
            [2.0, 1.0, 0.0],  # 최고 Ann
            [0.0, 1.0, 1.0],  # Bob·Cindy 동점 최고 → 이름순으로 Bob이 Top-1
            [0.0, 0.0, 2.0],  # 최고 Cindy
        ]
    )
    labels = ["Ann", "Bob", "Zed"]  # Zed는 names에 없음 → 오답(오류 아님)
    acc = classify._topk_accuracy(z, names, labels, ks=(1,))
    assert acc == {1: pytest.approx(2 / 3)}  # Ann·Bob 정답, Zed 오답


# FR2.4/FR2.5 — ks 초과 clamp, 행 수≠labels·ks<=0 → ValueError
def test_topk_accuracy_clamp_and_value_errors():
    names = ["Ann", "Bob"]
    z = np.array([[2.0, 1.0], [1.0, 2.0]])
    labels = ["Ann", "Bob"]

    acc = classify._topk_accuracy(z, names, labels, ks=(1, 5))
    assert acc[1] == pytest.approx(1.0)
    assert acc[5] == pytest.approx(1.0)  # ks=5 → 이름 수 2로 clamp, 키는 5 유지

    with pytest.raises(ValueError):  # 행 수 != labels 길이
        classify._topk_accuracy(z, names, ["Ann"], ks=(1,))
    with pytest.raises(ValueError):  # ks<=0
        classify._topk_accuracy(z, names, labels, ks=(0,))
