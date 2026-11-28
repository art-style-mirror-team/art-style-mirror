"""B — 판정·융합 (담당: 홍예원).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 가짜 결과를 돌려준다.
가짜 색인(load_index)의 학습셋 중심점으로 확률을 만들기 때문에 형식뿐 아니라 흐름도 실제와 비슷하다.
실제 구현(#8~#15)에서 함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import numpy as np

from modules import data
from modules.data import load_index

CALIBRATION_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "calibration.json"
# calibration.json이 없을 때 쓰는 기본값 (plan.md 9.5 플랜 B: T = 1, 가중합 w = 0.8)
DEFAULT_CALIBRATION = {"T_clip": 1.0, "T_cv": 1.0, "w": 0.8, "method": "weighted_sum"}
LOGIT_SCALE = 20.0  # 코사인 유사도 → 점수 배율 (스텁용)
NEAR_DUPLICATE = 0.95  # similar_works()에서 이 값 이상은 같은 작품으로 보고 제외

# detect_type()의 CLIP zero-shot 프롬프트. 유형별 영어 문장 앙상블(여러 변형)을
# 임베딩해 평균한 프로토타입과 입력 임베딩의 코사인 유사도로 유형을 고른다.
# CLIP이 영어 캡션으로 학습돼 프롬프트를 영어로 둔다.
# 순서는 고정한다(argmax 동률 시 앞의 유형이 뽑혀 결정적으로 동작하게).
# photo는 실제 장면으로 좁혀 종이 그림을 폰으로 찍은 입력이 끌려가지 않게 하고,
# 직접 그린 색 그림은 painting에 포함한다.
TYPE_PROMPTS: dict[str, list[str]] = {
    "photo": [
        "a photo of a real-world scene",
        "a photograph of people, objects or places",
        "a snapshot taken with a camera",
    ],
    "painting": [
        "a painting",
        "an oil painting",
        "a watercolor painting",
        "a colored drawing on paper",
    ],
    "sketch": [
        "a pencil sketch",
        "a black and white line drawing",
        "a charcoal sketch on paper",
    ],
}


def load_calibration() -> dict:
    if CALIBRATION_PATH.exists():
        return {**DEFAULT_CALIBRATION, **json.loads(CALIBRATION_PATH.read_text(encoding="utf-8"))}
    return dict(DEFAULT_CALIBRATION)


def _softmax(z: np.ndarray, T: float) -> np.ndarray:
    z = z / T
    e = np.exp(z - z.max())
    return e / e.sum()


def _l2_normalize(v: np.ndarray) -> np.ndarray:
    """마지막 축 기준 L2 정규화. 1D(질의 shape (512,))·2D(색인 shape (N, 512)) 모두 처리한다.
    영벡터는 norm을 1e-12로 눌러 나눗셈을 안전하게 하고, 원본을 바꾸지 않는 새 배열을 돌려준다
    (`load_index()["emb"]`는 읽기 전용이다)."""
    v = np.asarray(v, dtype=np.float32)
    norm = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.maximum(norm, 1e-12)


@lru_cache(maxsize=1)
def _centroids() -> dict:
    index = load_index()
    emb, meta = index["emb"], index["meta"]
    train = (meta["split"] == "train").to_numpy()
    out = {}
    for col in ("artist", "style"):
        names = sorted(meta.loc[train, col].unique())
        cents = np.stack([emb[train & (meta[col] == n).to_numpy()].mean(axis=0) for n in names])
        out[col] = (names, cents / np.linalg.norm(cents, axis=1, keepdims=True))
    return out


def detect_type(img_emb: np.ndarray) -> str:
    """입력 유형 판별. "photo" | "painting" | "sketch".

    CLIP zero-shot: `TYPE_PROMPTS`의 유형별 영어 문장을 `data.embed_text`로 임베딩해
    유형당 프로토타입(문장 임베딩 평균 후 L2 재정규화) 하나를 만들고, 입력 이미지
    임베딩(L2 정규화)과 코사인 유사도가 가장 큰 유형을 돌려준다.

    프롬프트 임베딩은 매 호출 계산한다(유형 10문장으로 작다). 그래서 테스트가
    `data.embed_text`를 가짜로 바꿔 끼워도 그대로 반영된다. 모델 함수는 반드시
    모듈 경유(`data.embed_text`)로 부른다.
    """
    types = list(TYPE_PROMPTS)  # dict는 삽입 순서 보존 → 결정적
    prototypes = np.stack(
        [
            _l2_normalize(np.asarray(data.embed_text(TYPE_PROMPTS[t]), dtype=np.float32).mean(0))
            for t in types
        ]
    )
    # 입력은 list 등으로 와도 받는다. 방향만 보므로 L2 정규화해 크기에 불변이게 한다.
    # NaN·inf가 섞인 입력은 계산 중 경고 대신 NaN 점수가 되게 한다(아래에서 처리).
    with np.errstate(invalid="ignore"):
        sims = prototypes @ _l2_normalize(img_emb)
    # NaN(입력에 NaN·inf가 섞인 경우)은 가장 낮은 점수로 보고, 모두 NaN이어도 세 값 중 하나를
    # 돌려준다(계약). argmax는 동률이면 앞의 유형을 고르므로 같은 입력에 같은 결과가 나온다.
    sims = np.nan_to_num(sims, nan=-np.inf)
    return types[int(np.argmax(sims))]


def predict_clip(emb: np.ndarray) -> dict:
    """CLIP 관점 확률. {"artists": {name: prob}, "styles": {name: prob}}, 각각 합 1, 온도 보정 적용."""
    # TODO(#9–#12): 스텁 — #9–#12, #14 판정 방식 선정과 온도 보정 (담당 B)
    T = load_calibration()["T_clip"]
    emb = np.asarray(emb, dtype=np.float32)
    result = {}
    for key, col in (("artists", "artist"), ("styles", "style")):
        names, cents = _centroids()[col]
        probs = _softmax(LOGIT_SCALE * (cents @ emb), T)
        result[key] = {n: float(p) for n, p in zip(names, probs)}
    return result


def similar_works(emb: np.ndarray, k: int = 3) -> list[dict]:
    """비슷한 명화 k점. [{"id", "artist", "style", "path", "score"}], score 내림차순, 길이 ≤ k.

    색인 전체(split으로 거르지 않음)에서 코사인 유사도로 찾는다. 입력 `emb`와 색인 임베딩을 각각
    L2 정규화한 뒤 내적으로 코사인을 구하고, 유사도 0.95(`NEAR_DUPLICATE`) 이상은 자기 자신 또는
    사실상 같은 작품으로 보고 제외한다. 동점은 색인 행 오름차순으로 끊어 결과가 결정적이다.
    `k <= 0`이면 `[]`, 남은 후보가 k보다 적으면 있는 만큼만 돌려준다.
    """
    if k <= 0:
        return []
    index = load_index()
    scores = _l2_normalize(index["emb"]) @ _l2_normalize(emb)
    meta = index["meta"]
    results: list[dict] = []
    for i in np.argsort(-scores, kind="stable"):
        if scores[i] >= NEAR_DUPLICATE:
            continue
        row = int(i)
        # 계약은 "meta 행 순서 = emb 행 순서"(위치)만 보장한다. meta의 DataFrame 인덱스가
        # 0..N-1이라는 보장은 없으므로 라벨 인덱스(.at)가 아니라 위치 기준(.iloc)으로 읽는다.
        meta_row = meta.iloc[row]
        results.append(
            {
                "id": str(meta_row["id"]),
                "artist": str(meta_row["artist"]),
                "style": str(meta_row["style"]),
                "path": str(meta_row["path"]),
                "score": float(scores[row]),
            }
        )
        if len(results) >= k:
            break
    return results


def fuse(p_clip: dict, p_cv: dict) -> list[tuple]:
    """두 관점 합치기. p_clip = predict_clip()["artists"], p_cv = predict_cv() 결과.
    [(artist, prob) × 3], 확률 내림차순. calibration.json의 w·방식을 쓴다. (스텁: 가중합만 구현)"""
    # TODO(#15): 스텁 — #15 가중합·가중곱·RRF 비교 후 calibration.json의 방식 적용 (담당 B)
    w = load_calibration()["w"]
    names = sorted(set(p_clip) | set(p_cv))
    fused = {a: w * p_clip.get(a, 0.0) + (1 - w) * p_cv.get(a, 0.0) for a in names}
    total = sum(fused.values()) or 1.0
    return sorted(((a, p / total) for a, p in fused.items()), key=lambda x: -x[1])[:3]


def _knn_logits(E: np.ndarray, k: int, by: str, eps: float = 1e-3) -> tuple[list[str], np.ndarray]:
    """kNN 가중 투표 로짓. (#9)

    학습셋(`split == "train"`) 이웃만으로, 질의 `E`와 색인 임베딩의 코사인 유사도 상위 `k`개를
    고른 뒤 `max(유사도, 0)`으로 clip해 `by`("artist"|"style") 이름별로 더한 가중 투표를 구하고,
    `z = log(투표 + eps)`를 돌려준다.

    Args:
        E: `(n, 512)` 질의 임베딩 여러 장.
        k: 이웃 수. 학습셋 크기보다 크면 학습셋 크기로 제한한다.
        by: "artist" 또는 "style". 색인 메타의 해당 열로 투표한다.
        eps: 투표 합에 더하는 바닥값(키워드 인자, 기본 1e-3). 투표가 0인 이름은 `log(eps)`가 되어
            모든 z 원소가 유한하다(NaN·-inf 없음).

    Returns:
        `(names, z)`. `names`는 학습셋에서 읽어 정렬한 이름 목록, `z`는 `(n, len(names))` 로짓.

    Raises:
        ValueError: `k <= 0`이거나 학습셋이 비어 있을 때(둘 다 `n`과 무관하게 먼저 검사한다).

    이름 순위 동점은 이름순(FR1.6), 이웃 선택 동점은 색인 행 위치가 앞선 쪽을 먼저(FR1.8,
    안정 정렬)로 끊어 결과가 결정적이다. 색인 메타는 위치 기준으로만 읽는다(라벨 인덱스 가정 금지).
    """
    index = load_index()
    emb, meta = index["emb"], index["meta"]
    # 메타는 emb와 행 위치만 일치한다. 라벨 인덱스로 읽지 않고 열을 위치 순 numpy 배열로 뽑는다.
    split = meta["split"].to_numpy()
    by_values = meta[by].to_numpy()
    train_mask = split == "train"

    # FR1.9: k·학습셋 검사를 n 처리보다 먼저 한다(학습셋이 비면 n과 무관하게 ValueError).
    if k <= 0 or not train_mask.any():
        raise ValueError("k는 1 이상이어야 하고 학습셋(split=='train')이 비어 있으면 안 됩니다.")

    names = sorted(np.unique(by_values[train_mask]).tolist())
    name_to_col = {name: col for col, name in enumerate(names)}

    k = min(k, int(train_mask.sum()))  # FR1.9: 학습셋 크기로 제한

    n = int(np.asarray(E).shape[0])
    if n == 0:  # FR1.9: 입력 0장이면 (names, (0, 이름 수)) 빈 z
        return names, np.empty((0, len(names)), dtype=np.float64)

    train_emb = _l2_normalize(emb[train_mask])  # (m, 512), 행 순서 = 원래 색인 위치 순서
    train_cols = np.array([name_to_col[v] for v in by_values[train_mask]])
    sims = _l2_normalize(E) @ train_emb.T  # (n, m) 코사인 유사도

    # 유사도 내림차순 + 동점은 위치 앞선 이웃 먼저(안정 정렬) → 상위 k개
    order = np.argsort(-sims, axis=1, kind="stable")[:, :k]
    votes = np.zeros((n, len(names)), dtype=np.float64)
    for i in range(n):
        neigh = order[i]
        np.add.at(votes[i], train_cols[neigh], np.maximum(sims[i, neigh], 0.0))
    return names, np.log(votes + eps)


def _topk_accuracy(
    z: np.ndarray,
    names: list[str],
    labels: list[str],
    ks: tuple[int, ...] = (1, 3),
) -> dict[int, float]:
    """Top-k 정확도. (#9, #10·#11 재사용)

    각 입력에 대해 `z`가 큰 상위 `k`개 이름 안에 정답 이름(`labels[i]`)이 있으면 맞힌 것으로 센다.
    `_knn_logits`의 반환 형식(`names`, `z`)에만 의존하므로 `by`나 특정 이름 집합에 묶이지 않는다.

    Args:
        z: `(n, len(names))` 로짓 행렬.
        names: `z`의 열에 대응하는 이름 목록.
        labels: 각 행의 정답 이름 리스트(길이 n). `names`에 없는 이름은 오답으로 센다(FR2.4).
        ks: 평가할 k 값들. 이름 수보다 크면 이름 수로 제한해 계산한다(FR2.4).

    Returns:
        `{k: 정확도}` 딕셔너리. 키는 원래 `ks` 값을 그대로 쓴다.

    Raises:
        ValueError: `z` 행 수와 `labels` 길이가 다르거나 `ks`에 0 이하 값이 있을 때(FR2.5).

    상위 선택의 동점은 이름순(열 위치 오름차순, FR1.6)으로 끊어 결정적이다.
    """
    z = np.asarray(z, dtype=np.float64)
    n = z.shape[0]
    if n != len(labels):
        raise ValueError("z의 행 수와 labels 길이가 같아야 합니다.")
    if any(k <= 0 for k in ks):
        raise ValueError("ks의 모든 원소는 1 이상이어야 합니다.")

    num = len(names)
    name_to_col = {name: col for col, name in enumerate(names)}
    # 유사도 큰 순, 동점은 이름순(열 위치 오름차순) → 안정 정렬
    order = np.argsort(-z, axis=1, kind="stable")
    result: dict[int, float] = {}
    for k in ks:
        kk = min(k, num)  # FR2.4: 이름 수로 제한
        topk = order[:, :kk]
        hits = 0
        for i in range(n):
            col = name_to_col.get(labels[i])  # FR2.4: 미지 이름이면 None → 오답
            if col is not None and col in topk[i]:
                hits += 1
        result[k] = hits / n if n > 0 else 0.0
    return result
