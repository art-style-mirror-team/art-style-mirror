"""화가 프로필 사전 계산 (담당: 심현준, C) — #19 구현.

출력: artifacts/profiles.json  ({artist: {feature: [mean, std]}})
학습셋(split == "train")으로만 계산한다. 명화에는 화이트밸런스를 적용하지 않는다.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.data import display_name  # noqa: E402
from modules.features import (  # noqa: E402
    LONG_SIDE,
    NUMERIC_FEATURES,
    extract_features,
    is_grayscale,
)

META_PATH = ROOT / "artifacts" / "meta.csv"
PROFILES_PATH = ROOT / "artifacts" / "profiles.json"


def _resize_long_side(img: np.ndarray, long_side: int = LONG_SIDE) -> np.ndarray:
    """명화용 전처리: 화이트밸런스 없이 RGB uint8 변환 및 긴 변 512px 크기 맞춤만 수행한다."""
    arr = np.asarray(img)
    if arr.ndim == 2:
        arr = np.stack([arr] * 3, axis=-1)
    elif arr.ndim == 3 and arr.shape[2] == 4:
        arr = arr[:, :, :3]
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError("이미지는 RGB (H, W, 3) 형태여야 합니다.")

    arr = np.ascontiguousarray(arr.astype(np.uint8, copy=False))
    h, w = arr.shape[:2]
    scale = long_side / max(h, w)
    if scale != 1.0:
        interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_CUBIC
        arr = cv2.resize(
            arr, (max(1, round(w * scale)), max(1, round(h * scale))), interpolation=interp
        )
    return arr


def _load_rgb_image(image_path: Path) -> np.ndarray:
    """한글/공백 경로를 포함해 이미지 파일을 RGB uint8 배열로 읽는다."""
    buf = np.fromfile(image_path, dtype=np.uint8)
    bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(f"이미지를 읽을 수 없습니다: {image_path}")
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def compute_profiles(
    samples: Iterable[tuple[str, np.ndarray]],
) -> dict[str, dict[str, list[float]]]:
    """(artist, rgb_img) 쌍들을 받아 {artist: {feature: [mean, std]}}를 계산한다."""
    grouped: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    for artist, img in samples:
        name = display_name(artist.strip())
        resized = _resize_long_side(img)
        gray = is_grayscale(resized)
        feats = extract_features(resized, gray=gray)
        for feat in NUMERIC_FEATURES:
            grouped[name][feat].append(float(feats[feat]))

    profiles: dict[str, dict[str, list[float]]] = {}
    for artist in sorted(grouped):
        profiles[artist] = {}
        for feat in NUMERIC_FEATURES:
            vals = np.asarray(grouped[artist][feat], dtype=np.float64)
            profiles[artist][feat] = [float(np.mean(vals)), float(np.std(vals))]
    return profiles


def _iter_train_samples(meta_path: Path) -> Iterable[tuple[str, np.ndarray]]:
    """meta.csv에서 split == 'train' 행만 순회하며 (artist, rgb_img)를 반환한다."""
    if not meta_path.exists():
        raise FileNotFoundError(
            f"메타데이터 파일이 없습니다: {meta_path}\n"
            "먼저 A 파트(scripts/build_index.py)로 artifacts/meta.csv를 생성하거나 공유받아 주세요."
        )

    with meta_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("split", "").strip() != "train":
                continue
            artist = display_name(row["artist"].strip())
            raw_path = Path(row["path"].strip())
            img_path = raw_path if raw_path.is_absolute() else (ROOT / raw_path)
            yield artist, _load_rgb_image(img_path)


def build_profiles(
    meta_path: Path = META_PATH,
    output_path: Path = PROFILES_PATH,
) -> dict[str, dict[str, list[float]]]:
    """학습셋 기준으로 화가별 프로필을 계산해 JSON으로 저장한다."""
    profiles = compute_profiles(_iter_train_samples(meta_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profiles, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return profiles


def main() -> None:
    parser = argparse.ArgumentParser(description="학습셋 기준 화가별 색·선 프로필 생성")
    parser.add_argument("--meta", type=Path, default=META_PATH, help="입력 meta.csv 경로")
    parser.add_argument("--out", type=Path, default=PROFILES_PATH, help="출력 profiles.json 경로")
    args = parser.parse_args()

    profiles = build_profiles(meta_path=args.meta, output_path=args.out)
    print(f"저장 완료: {args.out} (화가 {len(profiles)}명)")


if __name__ == "__main__":
    main()