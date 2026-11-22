"""C — 색·선 분석 (담당: 심현준).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 결과를 돌려준다.
preprocess_input()은 크기 맞추기만 하고, is_grayscale()은 실제 판정을 한다.
extract_features()는 색 특징을 계산하고 선 특징은 결정적인 가짜 값을 만든다.
load_profiles()는 결정적인 가짜 값을 만든다.
predict_cv()는 plan.md 6.1의 z값 거리 → 확률 식을 그대로 쓴다.
실제 구현(#16~#20)에서 함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from modules.data import ARTISTS

LONG_SIDE = 512
EPS = 0.01
COLOR_FEATURES = ["brightness", "contrast", "saturation", "warmth", "color_diversity"]
LINE_FEATURES = ["edge_density", "direction", "straight_ratio", "roughness", "stroke_length"]
NUMERIC_FEATURES = COLOR_FEATURES + LINE_FEATURES  # "palette"는 수치 비교에서 뺀다
PALETTE_SIZE = 5
PALETTE_SAMPLE_SIZE = 10_000


def _seed(*parts: bytes | str) -> int:
    h = hashlib.sha1()
    for p in parts:
        h.update(p.encode("utf-8") if isinstance(p, str) else p)
    return int.from_bytes(h.digest()[:8], "little")


def preprocess_input(img: np.ndarray) -> np.ndarray:
    """사용자 입력 전용 전처리. RGB uint8, 긴 변 512px. (스텁: 크기 맞추기만, 종이 자르기·화이트밸런스는 #16)"""
    # TODO(#16): 스텁 — #16 종이 영역 자르기·화이트밸런스 (담당 C)
    img = np.asarray(img)
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("이미지는 RGB (H, W, 3) 형태여야 합니다.")
    img = np.ascontiguousarray(img.astype(np.uint8, copy=False))
    h, w = img.shape[:2]
    scale = LONG_SIDE / max(h, w)
    if scale != 1.0:
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        img = cv2.resize(
            img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp
        )
    return img


def is_grayscale(img: np.ndarray) -> bool:
    """흑백(스케치) 여부: 채널 간 차이의 평균이 작으면 흑백으로 본다."""
    x = np.asarray(img, dtype=np.int16)
    if x.ndim == 2:
        return True
    spread = x.max(axis=2) - x.min(axis=2)
    return float(spread.mean()) < 8.0


def extract_features(img: np.ndarray, gray: bool = False) -> dict:
    """색 6종(palette 포함)·선 5종 특징. 수치는 0~1, direction은 각도(0~180), palette는 [[r, g, b] × 5].
    색 특징은 실제 계산하고 선 특징은 Issue #18 구현 전까지 결정적인 스텁 값을 쓴다."""
    rgb = np.asarray(img, dtype=np.uint8)
    if rgb.ndim == 2:
        rgb = np.repeat(rgb[:, :, None], 3, axis=2)

    gray_pixels = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray_float = gray_pixels.astype(np.float32)
    brightness = float(gray_float.mean() / 255.0)
    contrast = float(np.clip(gray_float.std() / 127.5, 0.0, 1.0))

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = float(hsv[:, :, 1].mean() / 255.0)
    warmth = float((rgb[:, :, 0].mean() - rgb[:, :, 2].mean()) / 510.0 + 0.5)

    palette_img = cv2.cvtColor(gray_pixels, cv2.COLOR_GRAY2RGB) if gray else rgb
    palette, color_diversity = _palette_and_diversity(palette_img)
    if gray:
        saturation = 0.0
        warmth = 0.5
        color_diversity = 0.0

    rng = np.random.default_rng(_seed(np.asarray(img).tobytes(), str(gray)))
    feats = {f: float(rng.uniform(0.1, 0.9)) for f in NUMERIC_FEATURES}
    feats["direction"] = float(rng.uniform(0, 180))
    feats.update(
        {
            "brightness": brightness,
            "contrast": contrast,
            "saturation": saturation,
            "warmth": warmth,
            "color_diversity": color_diversity,
            "palette": palette,
        }
    )
    return feats


def _palette_and_diversity(img: np.ndarray) -> tuple[list[list[int]], float]:
    lab_img = cv2.cvtColor(img.astype(np.float32) / 255.0, cv2.COLOR_RGB2LAB)
    pixels = lab_img.reshape(-1, 3)
    if len(pixels) > PALETTE_SAMPLE_SIZE:
        indices = np.linspace(0, len(pixels) - 1, PALETTE_SAMPLE_SIZE, dtype=int)
        sample = pixels[indices]
    else:
        sample = pixels

    unique_colors, unique_counts = np.unique(sample, axis=0, return_counts=True)
    if len(unique_colors) <= PALETTE_SIZE:
        centers = unique_colors
        counts = unique_counts
    else:
        model = MiniBatchKMeans(
            n_clusters=PALETTE_SIZE,
            random_state=0,
            n_init=3,
            batch_size=1024,
        )
        labels = model.fit_predict(sample)
        centers = model.cluster_centers_
        counts = np.bincount(labels, minlength=PALETTE_SIZE)

    order = np.argsort(-counts, kind="stable")
    order = order[counts[order] > 0]
    centers = centers[order]
    counts = counts[order]

    rgb_centers = cv2.cvtColor(
        centers.astype(np.float32).reshape(-1, 1, 3), cv2.COLOR_LAB2RGB
    ).reshape(-1, 3)
    palette = np.rint(np.clip(rgb_centers, 0.0, 1.0) * 255).astype(np.uint8).tolist()
    palette.extend([palette[0].copy() for _ in range(PALETTE_SIZE - len(palette))])

    proportions = counts / counts.sum()
    entropy = -float(np.sum(proportions * np.log(proportions)))
    diversity = entropy / np.log(PALETTE_SIZE)
    return palette, float(np.clip(diversity, 0.0, 1.0))


@lru_cache(maxsize=1)
def _profiles() -> dict:
    rng = np.random.default_rng(_seed("profiles"))
    out = {}
    for artist in ARTISTS:
        prof = {}
        for f in NUMERIC_FEATURES:
            if f == "direction":
                prof[f] = (float(rng.uniform(20, 160)), float(rng.uniform(15, 40)))
            else:
                prof[f] = (float(rng.uniform(0.2, 0.8)), float(rng.uniform(0.1, 0.25)))
        out[artist] = prof
    return out


def load_profiles() -> dict:
    """{artist: {feature: (mean, std)}}. 실제 구현은 학습셋으로만 계산한다. (스텁: 가짜 프로필)"""
    # TODO(#19): 스텁 — #19 artifacts/profiles.json 로드, 학습셋 기준 (담당 C)
    return {a: dict(p) for a, p in _profiles().items()}


def predict_cv(features: dict, gray: bool = False) -> dict:
    """OpenCV 관점 확률. {artist: prob}, 합 1.
    z(a,f) = (x_f − μ) / max(σ, ε), D_a = mean_f z², p ∝ exp(−D_a / 2T). 스케치는 선 특징만 쓴다.
    (스텁: T = 1, 피셔 점수 거르기는 #20)"""
    # TODO(#20): 스텁 — #20 피셔 점수로 약한 특징 제외, #14 온도 T 적용 (담당 C)
    T = 1.0
    used = LINE_FEATURES if gray else NUMERIC_FEATURES
    profiles = load_profiles()
    names = list(profiles)
    D = np.array(
        [
            np.mean(
                [
                    ((features[f] - profiles[a][f][0]) / max(profiles[a][f][1], EPS)) ** 2
                    for f in used
                ]
            )
            for a in names
        ]
    )
    logits = -D / (2 * T)
    e = np.exp(logits - logits.max())
    p = e / e.sum()
    return {a: float(v) for a, v in zip(names, p)}
