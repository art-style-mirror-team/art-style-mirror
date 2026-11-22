"""C — 색·선 분석 (담당: 심현준).

1일차 스텁: contracts/interfaces.md와 똑같은 모양의 가짜 결과를 돌려준다.
preprocess_input()은 사용자 입력의 종이 영역·화이트밸런스·크기를 처리하고,
is_grayscale()은 실제 판정을 하며 extract_features()·load_profiles()는 결정적인 가짜 값을 만든다.
predict_cv()는 plan.md 6.1의 z값 거리 → 확률 식을 그대로 쓴다.
실제 구현(#16~#20)에서 함수 이름·입출력 형식은 그대로 두고 내용만 바꾼다.
"""

from __future__ import annotations

import hashlib
from functools import lru_cache

import cv2
import numpy as np

from modules.data import ARTISTS

LONG_SIDE = 512
EPS = 0.01
COLOR_FEATURES = ["brightness", "contrast", "saturation", "warmth", "color_diversity"]
LINE_FEATURES = ["edge_density", "direction", "straight_ratio", "roughness", "stroke_length"]
NUMERIC_FEATURES = COLOR_FEATURES + LINE_FEATURES  # "palette"는 수치 비교에서 뺀다
PALETTE_SIZE = 5


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


def _white_balance_from_paper(img: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    neutral = cv2.inRange(
        hsv,
        np.array([0, 0, 180], dtype=np.uint8),
        np.array([180, 90, 255], dtype=np.uint8),
    )
    pixels = img[neutral > 0]
    min_pixels = max(16, int(img.shape[0] * img.shape[1] * 0.001))
    if pixels.shape[0] < min_pixels:
        return img

    channel_medians = np.median(pixels, axis=0).astype(np.float32)
    if np.any(channel_medians <= 0):
        return img
    gains = np.clip(channel_medians.max() / channel_medians, 0.75, 1.35)
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
        if not is_grayscale(img):
            img = _white_balance_from_paper(img)

    h, w = img.shape[:2]
    scale = LONG_SIDE / max(h, w)
    if scale != 1.0:
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        img = cv2.resize(
            img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp
        )
    return np.ascontiguousarray(img)


def is_grayscale(img: np.ndarray) -> bool:
    """흑백(스케치) 여부: 채널 간 차이의 평균이 작으면 흑백으로 본다."""
    x = np.asarray(img, dtype=np.int16)
    if x.ndim == 2:
        return True
    spread = x.max(axis=2) - x.min(axis=2)
    return float(spread.mean()) < 8.0


def extract_features(img: np.ndarray, gray: bool = False) -> dict:
    """색 6종(palette 포함)·선 5종 특징. 수치는 0~1, direction은 각도(0~180), palette는 [[r, g, b] × 5].
    (스텁: 이미지 바이트로 만든 가짜 값)"""
    # TODO(#17): 스텁 — #17 색 특징, #18 선 특징 실제 계산 (담당 C)
    rng = np.random.default_rng(_seed(np.asarray(img).tobytes(), str(gray)))
    feats = {f: float(rng.uniform(0.1, 0.9)) for f in NUMERIC_FEATURES}
    feats["direction"] = float(rng.uniform(0, 180))
    if gray:
        feats["saturation"] = 0.0
        feats["color_diversity"] = 0.0
    palette = rng.integers(0, 256, size=(PALETTE_SIZE, 3))
    if gray:
        palette = np.repeat(palette[:, :1], 3, axis=1)
    feats["palette"] = palette.tolist()
    return feats


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
