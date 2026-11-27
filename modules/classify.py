"""B — 판정·융합 (담당: 홍예원).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 가짜 결과를 돌려준다.
가짜 색인(load_index)의 학습셋 중심점으로 확률을 만들기 때문에 형식뿐 아니라 흐름도 실제와 비슷하다.
실제 구현(#8~#15)에서 함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.linear_model import LogisticRegression

from modules.data import load_index

CALIBRATION_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "calibration.json"
# #11 선형 분류기(로지스틱 회귀) 저장 위치. CALIBRATION_PATH와 같은 방식.
LINEAR_PATH = Path(__file__).resolve().parent.parent / "artifacts" / "linear.pkl"
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


def _fit_linear(by: str, C: float = 1.0) -> LogisticRegression:
    """학습셋만으로 `by`(="artist" 또는 "style") 라벨을 맞히는 로지스틱 회귀를 학습한다. (#11)

    `load_index()`에서 `split=="train"`인 행만 쓰고, 입력 임베딩은 기존 `_l2_normalize`로
    정규화한다. 라벨은 `meta`에서 그대로 읽어 클래스 수·이름을 하드코딩하지 않는다. 학습셋 추출은
    `meta`의 라벨 인덱스가 아니라 위치(불리언 마스크)로 `emb`를 걸러 행 순서를 맞춘다(`_centroids`와 같은 방식).
    학습된 모델 객체 하나를 돌려준다.
    """
    index = load_index()
    emb, meta = index["emb"], index["meta"]
    train = (meta["split"] == "train").to_numpy()
    X = _l2_normalize(emb[train])
    y = meta.loc[train, by].to_numpy()
    model = LogisticRegression(C=C, max_iter=1000, random_state=0)
    model.fit(X, y)
    return model


def _save_linear(models: dict, path: Path = LINEAR_PATH) -> None:
    """학습된 모델 dict를 joblib로 저장한다. (#11)

    `models`는 `{"artist": LogisticRegression, "style": LogisticRegression}` 꼴이다. 각 모델의 `C`와
    학습에 쓴 scikit-learn 버전을 함께 적어, 로드 쪽에서 재현 조건을 확인할 수 있게 한다.
    상위 폴더가 없으면 만든다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "artist": models["artist"],
        "style": models["style"],
        "C": {"artist": models["artist"].C, "style": models["style"].C},
        "sklearn_version": sklearn.__version__,
    }
    joblib.dump(payload, path)
    # 같은 경로에 다시 저장하면 캐시된 옛 모델이 아니라 새 모델이 읽히도록 캐시를 비운다. (#11)
    _load_linear.cache_clear()


@lru_cache(maxsize=1)
def _load_linear(path: Path = LINEAR_PATH) -> dict:
    """저장된 선형 분류기 dict를 읽어 돌려준다. (#11)

    파일이 없으면 어떻게 학습·저장하는지 힌트를 담은 `FileNotFoundError`를 던진다. `@lru_cache`라
    테스트에서는 `_load_linear.cache_clear()`로 캐시를 비운다.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"선형 분류기 파일이 없습니다: {path}\n"
            '`_fit_linear("artist")`·`_fit_linear("style")`로 학습한 뒤 '
            "`_save_linear({'artist': ..., 'style': ...})`로 저장하세요 (#11)."
        )
    return joblib.load(path)


def _linear_logits(
    E: np.ndarray, by: str, model: LogisticRegression | None = None
) -> tuple[list, np.ndarray]:
    """선형 분류기의 로짓. `(이름 목록, z)`를 돌려주며 `z.shape == (n, 이름 수)`. (#11)

    이름 목록은 `model.classes_`(정렬 순서)로, #9 `_knn_logits`·#10 `_centroid_logits`와 같은 모양이다.
    `model`이 없으면 저장된 모델(`_load_linear()[by]`)을 쓴다. `E`가 2차원이 아니면 `ValueError`.
    0장 입력이면 `(이름 목록, (0, 이름 수) 영배열)`. 그 외에는 `_l2_normalize(E)` 뒤
    `decision_function`을 쓴다. 이진 분류 시 sklearn은 `(n,)`을 주므로 `classes_` 순서에 맞춰 `(n, 2)`로 맞춘다.
    """
    if model is None:
        model = _load_linear()[by]
    E = np.asarray(E, dtype=np.float32)
    if E.ndim != 2:
        raise ValueError(f"E는 2차원 (n, 512)이어야 합니다. 받은 차원: {E.ndim}")
    names = list(model.classes_)
    if E.shape[0] == 0:
        return names, np.zeros((0, len(names)), dtype=np.float32)
    z = model.decision_function(_l2_normalize(E))
    if z.ndim == 1:
        # 이진 분류 시 decision_function은 (n,)을 준다. 양수는 classes_[1] 쪽이므로
        # column 0 = classes_[0], column 1 = classes_[1] 점수로 쌓아 (n, 2)로 맞춘다.
        # [0, z]로 쌓으면 softmax(z) = [sigmoid(-z), sigmoid(z)]가 되어 model.predict_proba와 일치한다.
        z = np.column_stack([np.zeros_like(z), z])
    return names, z
