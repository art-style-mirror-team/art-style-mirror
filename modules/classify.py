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

from modules.data import load_index

CALIBRATION_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "calibration.json"
# calibration.json이 없을 때 쓰는 기본값 (plan.md 9.5 플랜 B: T = 1, 가중합 w = 0.8)
DEFAULT_CALIBRATION = {"T_clip": 1.0, "T_cv": 1.0, "w": 0.8, "method": "weighted_sum"}
LOGIT_SCALE = 20.0  # 코사인 유사도 → 점수 배율 (스텁용)
NEAR_DUPLICATE = 0.95  # similar_works()에서 이 값 이상은 같은 작품으로 보고 제외


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
    """입력 유형 판별. "photo" | "painting" | "sketch". (스텁: 임베딩 앞 3개 값 중 최댓값)"""
    # TODO(#8): 스텁 — #8 CLIP zero-shot 유형 판별 (담당 B)
    return ("photo", "painting", "sketch")[int(np.argmax(np.asarray(img_emb)[:3]))]


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
