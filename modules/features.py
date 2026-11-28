"""C — 이미지 전처리와 색·선 특징 분석 (담당: 심현준).

입력 이미지의 흑백 여부를 판정하고, 색·선 특징을 추출해 OpenCV 분석에 제공한다.
"""

from __future__ import annotations

import hashlib
import json
import logging
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from sklearn.cluster import MiniBatchKMeans

from modules.data import ARTISTS

log = logging.getLogger(__name__)
PROFILES_PATH = Path(__file__).resolve().parents[1] / "artifacts" / "profiles.json"

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
        np.array([0, 0, 120], dtype=np.uint8),
        np.array([180, 90, 255], dtype=np.uint8),
    )
    kernel_size = max(3, min(31, min(h, w) // 40 | 1))
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    image_area = h * w
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if not (4 <= len(polygon) <= 8 and cv2.isContourConvex(polygon)):
            continue

        x, y, box_w, box_h = cv2.boundingRect(polygon)
        box_area = box_w * box_h
        if box_area < image_area * 0.3 or box_area > image_area * 0.98:
            continue
        if box_w < w * 0.5 or box_h < h * 0.5:
            continue
        if x < 2 or y < 2 or x + box_w > w - 2 or y + box_h > h - 2:
            continue
        if cv2.contourArea(contour) / box_area < 0.75:
            continue

        trim_x = min(round(box_w * 0.01), (box_w - 1) // 2)
        trim_y = min(round(box_h * 0.01), (box_h - 1) // 2)
        return (
            x + trim_x,
            y + trim_y,
            box_w - 2 * trim_x,
            box_h - 2 * trim_y,
        )
    return None


def _sketch_gains(img: np.ndarray) -> np.ndarray | None:
    """Return lighting gains only when balancing leaves a neutral line drawing."""
    h, w = img.shape[:2]
    scale = LONG_SIDE / max(h, w)
    small = (
        img
        if scale >= 1
        else cv2.resize(
            img,
            (max(1, round(w * scale)), max(1, round(h * scale))),
            interpolation=cv2.INTER_AREA,
        )
    )
    f = cv2.GaussianBlur(small, (5, 5), 0).astype(np.float32)
    lum = f.mean(axis=2)
    light = np.median(f[lum >= np.percentile(lum, 50)], axis=0)
    if light.min() < 40:
        return None

    gains = light.max() / light
    if gains.max() > 1.8:
        return None

    balanced = f * gains
    spread = balanced.max(axis=2) - balanced.min(axis=2)
    valid = lum > 50
    color_fraction = np.count_nonzero((spread > 20) & valid) / max(1, np.count_nonzero(valid))
    if color_fraction > 0.02:
        return None

    gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
    if np.count_nonzero(cv2.Canny(gray, 30, 100)) / gray.size < 0.002:
        return None
    return gains


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
    gains = _sketch_gains(img)
    if gains is not None:
        balanced = np.clip(img.astype(np.float32) * gains, 0, 255).astype(np.uint8)
        gray = cv2.cvtColor(balanced, cv2.COLOR_RGB2GRAY)
        img = np.repeat(gray[:, :, None], 3, axis=2)

    h, w = img.shape[:2]
    scale = LONG_SIDE / max(h, w)
    if scale != 1.0:
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        img = cv2.resize(
            img, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp
        )
    return np.ascontiguousarray(img)


def is_grayscale(img: np.ndarray) -> bool:
    """채널 차이의 평균이 8 미만이면 흑백으로 본다."""
    x = np.asarray(img, dtype=np.int16)
    if x.ndim == 2:
        return True
    spread = x.max(axis=2) - x.min(axis=2)
    return float(spread.mean()) < 8.0


def extract_features(img: np.ndarray, gray: bool = False) -> dict:
    """색 6종(palette 포함)·선 5종 특징. direction은 방향 일관성 (0~1)이다."""
    rgb = np.asarray(img, dtype=np.uint8)
    if rgb.ndim == 2:
        rgb = np.repeat(rgb[:, :, None], 3, axis=2)

    gray_img = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    gray_float = gray_img.astype(np.float32)
    brightness = float(gray_float.mean() / 255.0)
    contrast = float(np.clip(gray_float.std() / 127.5, 0.0, 1.0))

    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = float(hsv[:, :, 1].mean() / 255.0)
    warmth = float((rgb[:, :, 0].mean() - rgb[:, :, 2].mean()) / 510.0 + 0.5)

    palette_img = cv2.cvtColor(gray_img, cv2.COLOR_GRAY2RGB) if gray else rgb
    palette, color_diversity = _palette_and_diversity(palette_img)
    if gray:
        saturation = 0.0
        warmth = 0.5
        color_diversity = 0.0

    feats = {
        "brightness": brightness,
        "contrast": contrast,
        "saturation": saturation,
        "warmth": warmth,
        "color_diversity": color_diversity,
        "palette": palette,
    }

    blurred = cv2.GaussianBlur(gray_img, (5, 5), sigmaX=1)
    edges = cv2.Canny(blurred, 50, 150)
    edge_count = int(cv2.countNonZero(edges))
    pixel_count = int(edges.shape[0] * edges.shape[1])

    if edge_count == 0 or pixel_count == 0:
        feats.update(
            edge_density=0.0,
            direction=0.0,
            straight_ratio=0.0,
            roughness=0.0,
            stroke_length=0.0,
        )
    else:
        feats["edge_density"] = float(np.clip(edge_count / pixel_count, 0.0, 1.0))

        gx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
        edge_mask = edges > 0
        edge_gx = gx[edge_mask]
        edge_gy = gy[edge_mask]
        magnitudes = np.hypot(edge_gx, edge_gy)
        magnitude_sum = float(magnitudes.sum())
        if magnitude_sum > 0.0:
            tangent = np.mod(np.arctan2(edge_gy, edge_gx) + np.pi / 2, np.pi)
            cos_mean = float(np.sum(magnitudes * np.cos(2 * tangent)) / magnitude_sum)
            sin_mean = float(np.sum(magnitudes * np.sin(2 * tangent)) / magnitude_sum)
            feats["direction"] = float(np.clip(np.hypot(cos_mean, sin_mean), 0.0, 1.0))
        else:
            feats["direction"] = 0.0

        long_side = max(edges.shape)
        segments = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=max(10, round(0.03 * long_side)),
            minLineLength=max(10, round(0.05 * long_side)),
            maxLineGap=max(2, round(0.01 * long_side)),
        )
        straight_mask = np.zeros_like(edges)
        if segments is not None:
            for segment in segments.reshape(-1, 4):
                x1, y1, x2, y2 = (int(value) for value in segment)
                cv2.line(straight_mask, (x1, y1), (x2, y2), 255, 1, cv2.LINE_8)
        straight_count = int(cv2.countNonZero(cv2.bitwise_and(straight_mask, edges)))
        feats["straight_ratio"] = float(np.clip(straight_count / edge_count, 0.0, 1.0))

        skeleton = np.zeros_like(edges)
        current = edges.copy()
        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
        while cv2.countNonZero(current) > 0:
            eroded = cv2.erode(current, kernel)
            opened = cv2.dilate(eroded, kernel)
            residue = cv2.subtract(current, opened)
            skeleton = cv2.bitwise_or(skeleton, residue)
            current = eroded
        component_count, _, stats, _ = cv2.connectedComponentsWithStats(skeleton, connectivity=8)
        component_lengths = stats[1:component_count, cv2.CC_STAT_AREA]
        component_lengths = component_lengths[component_lengths >= 3]
        if component_lengths.size:
            diagonal = float(np.hypot(*edges.shape))
            feats["stroke_length"] = float(np.clip(component_lengths.mean() / diagonal, 0.0, 1.0))
        else:
            feats["stroke_length"] = 0.0

        laplacian = cv2.Laplacian(blurred, cv2.CV_32F)
        roughness_energy = float(np.mean(np.abs(laplacian))) / 255.0
        feats["roughness"] = float(
            np.clip(roughness_energy / (roughness_energy + 0.1), 0.0, 1.0)
            if roughness_energy > 0.0
            else 0.0
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
def _fallback_profiles() -> dict:
    """profiles.json이 아직 생성되지 않은 환경을 위한 결정적 기본 프로필."""
    rng = np.random.default_rng(_seed("profiles"))
    out = {}
    for artist in ARTISTS:
        prof = {}
        for f in NUMERIC_FEATURES:
            prof[f] = (float(rng.uniform(0.2, 0.8)), float(rng.uniform(0.1, 0.25)))
        out[artist] = prof
    return out


@lru_cache(maxsize=4)
def _cached_profiles(
    path: str, stamp: tuple[int, int]
) -> dict[str, dict[str, tuple[float, float]]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        artist: {feat: (float(vals[0]), float(vals[1])) for feat, vals in feats.items()}
        for artist, feats in raw.items()
    }


def load_profiles(path: str | Path | None = None) -> dict:
    """{artist: {feature: (mean, std)}}. 학습셋으로 계산된 artifacts/profiles.json을 로드한다."""
    target = Path(PROFILES_PATH if path is None else path)
    if not target.exists():
        if target.resolve() == PROFILES_PATH.resolve():
            log.warning(
                "profiles.json이 없어 기본 폴백 프로필을 사용합니다. build_profiles.py를 실행하세요."
            )
            return {a: dict(p) for a, p in _fallback_profiles().items()}
        raise FileNotFoundError(f"프로필 파일을 찾을 수 없습니다: {target}")

    stat = target.stat()
    loaded = _cached_profiles(str(target.resolve()), (stat.st_mtime_ns, stat.st_size))
    return {a: dict(p) for a, p in loaded.items()}


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
