"""C — 이미지 전처리와 색·선 특징 분석 (담당: 심현준).

입력 이미지의 흑백 여부를 판정하고, 색·선 특징을 추출해 OpenCV 분석에 제공한다.
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


def _paper_bounds(img: np.ndarray) -> tuple[int, int, int, int] | None:
    """밝고 저채도인 종이 후보의 신뢰도 높은 바운딩 박스를 찾는다."""
    h, w = img.shape[:2]
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(
        hsv,
        np.array([0, 0, 160], dtype=np.uint8),
        np.array([180, 90, 255], dtype=np.uint8),
    )
    kernel_size = max(3, min(31, min(h, w) // 40 | 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_area = h * w
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        x, y, box_w, box_h = cv2.boundingRect(contour)
        box_area = box_w * box_h
        if box_area < image_area * 0.3 or box_area > image_area * 0.98:
            continue
        if box_w < w * 0.5 or box_h < h * 0.5:
            continue
        if x < 2 or y < 2 or x + box_w > w - 2 or y + box_h > h - 2:
            continue
        if cv2.contourArea(contour) / box_area < 0.75:
            continue

        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if 4 <= len(polygon) <= 8 and cv2.isContourConvex(polygon):
            return x, y, box_w, box_h
    return None


def _paper_sketch_candidates(
    img: np.ndarray, *, max_dark_fraction: float | None = None
) -> np.ndarray | None:
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    bright = value >= 120
    if bright.mean() < 0.6:
        return None

    lab = cv2.cvtColor(img, cv2.COLOR_RGB2LAB)
    bright_lab = lab[bright].astype(np.float32)
    if np.max(bright_lab[:, 1:3].std(axis=0)) > 10 or saturation[bright].mean() > 115:
        return None

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    background_lightness = float(np.median(bright_lab[:, 0]))
    dark = lab[:, :, 0] <= background_lightness - 35
    if max_dark_fraction is not None and dark.mean() > max_dark_fraction:
        return None
    edges = cv2.Canny(gray, 30, 100)
    edges = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8))
    dark_line_fraction = np.count_nonzero(dark & (edges > 0)) / (img.shape[0] * img.shape[1])
    if dark_line_fraction < 0.0015:
        return None
    return bright & (saturation <= 115)


def _white_balance_from_candidates(img: np.ndarray) -> np.ndarray:
    candidates = _paper_sketch_candidates(img)
    if candidates is None:
        return img

    pixels = img[candidates]
    channel_medians = np.median(pixels, axis=0).astype(np.float32)
    if np.any(channel_medians <= 0):
        return img
    gains = np.clip(channel_medians.max() / channel_medians, 0.75, 1.8)
    balanced = img.astype(np.float32) * gains
    return np.clip(balanced, 0, 255).astype(np.uint8)


def preprocess_input(img: np.ndarray) -> np.ndarray:
    """사용자 입력 전용 전처리. RGB uint8, 긴 변 512px."""
    img = np.asarray(img)
    if img.ndim == 2:
        img = np.stack([img] * 3, axis=-1)
    elif img.ndim == 3 and img.shape[2] == 4:
        img = img[:, :, :3]
    if img.ndim != 3 or img.shape[2] != 3:
        raise ValueError("이미지는 RGB (H, W, 3) 형태여야 합니다.")
    img = np.ascontiguousarray(img.astype(np.uint8, copy=False))

    paper_bounds = _paper_bounds(img)
    if paper_bounds is not None:
        x, y, w, h = paper_bounds
        img = img[y : y + h, x : x + w]
    img = _white_balance_from_candidates(img)

    h, w = img.shape[:2]
    scale = LONG_SIDE / max(h, w)
    if scale != 1.0:
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        img = cv2.resize(
            img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp
        )
    return np.ascontiguousarray(img)


def is_grayscale(img: np.ndarray) -> bool:
    """채널 차이가 작거나 균일한 종이 배경과 어두운 선이 있으면 흑백(스케치)으로 본다."""
    x = np.asarray(img, dtype=np.int16)
    if x.ndim == 2:
        return True
    spread = x.max(axis=2) - x.min(axis=2)
    return (
        float(spread.mean()) < 8.0
        or _paper_sketch_candidates(x.astype(np.uint8), max_dark_fraction=0.25) is not None
    )


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
