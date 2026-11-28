"""화가 프로필 사전 계산 및 로드 테스트 (#19)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import cv2
import numpy as np
import pytest

from modules.data import ARTISTS, display_name
from modules.features import (
    COLOR_FEATURES,
    LINE_FEATURES,
    NUMERIC_FEATURES,
    extract_features,
    is_grayscale,
    load_profiles,
    predict_cv,
)
from scripts.build_profiles import _resize_long_side, build_profiles, compute_profiles


def _make_sample_image(seed: int, size: tuple[int, int] = (128, 160)) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = size
    base = rng.integers(30, 225, size=(h, w, 3), dtype=np.uint8)
    base[20:40, 20:140] = 240
    base[60:110, 50:70] = 20
    return base


def _make_gray_image(seed: int, size: tuple[int, int] = (128, 160)) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = size
    gray = rng.integers(40, 220, size=(h, w), dtype=np.uint8)
    gray[20:40, 20:140] = 245
    gray[60:110, 50:70] = 15
    return np.stack([gray, gray, gray], axis=-1)


def test_compute_profiles_structure_and_values() -> None:
    img1 = _make_sample_image(1)
    img2 = _make_sample_image(2)
    profiles = compute_profiles([("claude_monet", img1), ("claude_monet", img2)])

    monet = display_name("claude_monet")
    assert list(profiles.keys()) == [monet]
    assert set(profiles[monet].keys()) == set(NUMERIC_FEATURES)
    assert "palette" not in profiles[monet]

    f1 = extract_features(_resize_long_side(img1), gray=is_grayscale(_resize_long_side(img1)))
    f2 = extract_features(_resize_long_side(img2), gray=is_grayscale(_resize_long_side(img2)))
    for feat in NUMERIC_FEATURES:
        mean_val, std_val = profiles[monet][feat]
        expected = np.asarray([f1[feat], f2[feat]], dtype=np.float64)
        assert mean_val == pytest.approx(float(np.mean(expected)))
        assert std_val == pytest.approx(float(np.std(expected)))


def test_compute_profiles_excludes_grayscale_from_color_features() -> None:
    color_img = _make_sample_image(11)
    gray_img = _make_gray_image(22)

    c_resized = _resize_long_side(color_img)
    g_resized = _resize_long_side(gray_img)
    assert not is_grayscale(c_resized)
    assert is_grayscale(g_resized)

    profiles = compute_profiles([("claude_monet", color_img), ("claude_monet", gray_img)])
    monet = display_name("claude_monet")

    f_color = extract_features(c_resized, gray=False)
    f_gray = extract_features(g_resized, gray=True)

    for feat in COLOR_FEATURES:
        mean_val, _ = profiles[monet][feat]
        assert mean_val == pytest.approx(float(f_color[feat]))

    for feat in LINE_FEATURES:
        mean_val, _ = profiles[monet][feat]
        expected = float(np.mean([f_color[feat], f_gray[feat]]))
        assert mean_val == pytest.approx(expected)


def test_compute_profiles_zero_color_artist_fallback() -> None:
    color_img = _make_sample_image(31)
    gray_only_img = _make_gray_image(32)

    profiles = compute_profiles([("claude_monet", color_img), ("gustave_dore", gray_only_img)])
    monet = display_name("claude_monet")
    dore = display_name("gustave_dore")

    for feat in COLOR_FEATURES:
        assert profiles[dore][feat] == pytest.approx(profiles[monet][feat])


def test_build_profiles_filters_train_split_and_loads_roundtrip(tmp_path: Path) -> None:
    img_dir = tmp_path / "images"
    img_dir.mkdir()

    train_path = img_dir / "train_01.png"
    val_path = img_dir / "val_01.png"
    test_path = img_dir / "test_01.png"

    train_img = _make_sample_image(10)
    val_img = np.full((128, 128, 3), 255, dtype=np.uint8)
    test_img = np.zeros((128, 128, 3), dtype=np.uint8)

    cv2.imwrite(str(train_path), cv2.cvtColor(train_img, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(val_path), cv2.cvtColor(val_img, cv2.COLOR_RGB2BGR))
    cv2.imwrite(str(test_path), cv2.cvtColor(test_img, cv2.COLOR_RGB2BGR))

    meta_path = tmp_path / "meta.csv"
    with meta_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["artist", "split", "path"])
        writer.writeheader()
        writer.writerow({"artist": "vincent_van_gogh", "split": "train", "path": str(train_path)})
        writer.writerow({"artist": "vincent_van_gogh", "split": "val", "path": str(val_path)})
        writer.writerow({"artist": "vincent_van_gogh", "split": "test", "path": str(test_path)})

    out_path = tmp_path / "profiles.json"
    built = build_profiles(meta_path=meta_path, output_path=out_path, progress_every=None)
    loaded = load_profiles(out_path)

    gogh = display_name("vincent_van_gogh")
    assert list(loaded.keys()) == [gogh]
    for feat in NUMERIC_FEATURES:
        mean_val, std_val = loaded[gogh][feat]
        assert isinstance(mean_val, float)
        assert isinstance(std_val, float)
        assert std_val == pytest.approx(0.0)
        assert [mean_val, std_val] == pytest.approx(built[gogh][feat])


def test_load_profiles_fallback_when_missing() -> None:
    profiles = load_profiles()
    assert set(profiles.keys()) == set(ARTISTS)
    for artist in ARTISTS:
        assert set(profiles[artist].keys()) == set(NUMERIC_FEATURES)


def test_predict_cv_uses_loaded_profiles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    img_a = _make_sample_image(101)
    img_b = np.full((128, 128, 3), 240, dtype=np.uint8)
    profiles = compute_profiles([("claude_monet", img_a), ("pablo_picasso", img_b)])

    out_path = tmp_path / "profiles.json"
    out_path.write_text(json.dumps(profiles, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr("modules.features.PROFILES_PATH", out_path)

    query_feats = extract_features(_resize_long_side(img_a), gray=False)
    probs = predict_cv(query_feats, gray=False)
    assert set(probs.keys()) == {display_name("claude_monet"), display_name("pablo_picasso")}
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs[display_name("claude_monet")] > probs[display_name("pablo_picasso")]
