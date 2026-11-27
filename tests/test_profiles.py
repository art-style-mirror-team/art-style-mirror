"""#19 화가 프로필 사전 계산(build_profiles.py) 및 load_profiles() 검증."""

from __future__ import annotations

import csv
from pathlib import Path

import cv2
import numpy as np
import pytest

from modules.features import NUMERIC_FEATURES, load_profiles, predict_cv
from scripts.build_profiles import build_profiles


def _write_solid_png(
    path: Path, rgb: tuple[int, int, int], size: tuple[int, int] = (64, 64)
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    img = np.full((size[1], size[0], 3), rgb, dtype=np.uint8)
    bgr = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    ok, buf = cv2.imencode(".png", bgr)
    assert ok
    buf.tofile(path)


def test_build_and_load_profiles_uses_train_split_only(tmp_path: Path) -> None:
    img_dir = tmp_path / "imgs"
    train1 = img_dir / "gogh_1.png"
    train2 = img_dir / "gogh_2.png"
    val1 = img_dir / "gogh_val.png"
    test1 = img_dir / "gogh_test.png"

    _write_solid_png(train1, (220, 120, 40))
    _write_solid_png(train2, (200, 100, 20))
    _write_solid_png(val1, (0, 0, 255))
    _write_solid_png(test1, (0, 255, 0))

    meta_path = tmp_path / "meta.csv"
    rows = [
        {
            "id": "1",
            "artist": "vincent-van-gogh",
            "style": "Post-Impressionism",
            "genre": "landscape",
            "path": str(train1),
            "split": "train",
        },
        {
            "id": "2",
            "artist": "vincent-van-gogh",
            "style": "Post-Impressionism",
            "genre": "landscape",
            "path": str(train2),
            "split": "train",
        },
        {
            "id": "3",
            "artist": "vincent-van-gogh",
            "style": "Post-Impressionism",
            "genre": "landscape",
            "path": str(val1),
            "split": "val",
        },
        {
            "id": "4",
            "artist": "vincent-van-gogh",
            "style": "Post-Impressionism",
            "genre": "landscape",
            "path": str(test1),
            "split": "test",
        },
    ]
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "artist", "style", "genre", "path", "split"])
        writer.writeheader()
        writer.writerows(rows)

    out_path = tmp_path / "profiles.json"
    built = build_profiles(meta_path=meta_path, output_path=out_path)

    assert "Vincent van Gogh" in built
    prof_raw = built["Vincent van Gogh"]
    assert set(prof_raw.keys()) == set(NUMERIC_FEATURES)
    assert "palette" not in prof_raw
    assert prof_raw["warmth"][0] > 0.65

    loaded = load_profiles(out_path)
    assert "Vincent van Gogh" in loaded
    assert isinstance(loaded["Vincent van Gogh"]["brightness"], tuple)
    assert len(loaded["Vincent van Gogh"]["brightness"]) == 2


def test_load_profiles_missing_custom_path_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_profiles(tmp_path / "does_not_exist.json")


def test_predict_cv_works_with_loaded_profiles() -> None:
    profiles = load_profiles()
    sample_feats = {f: 0.5 for f in NUMERIC_FEATURES}
    probs = predict_cv(sample_feats, gray=False)
    assert set(probs.keys()) == set(profiles.keys())
    assert pytest.approx(sum(probs.values()), rel=1e-5) == 1.0
