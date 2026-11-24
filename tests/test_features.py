from __future__ import annotations

import numpy as np
import pytest

from modules import features


def test_preprocess_and_grayscale():
    color_img = np.random.default_rng(0).integers(0, 256, size=(300, 400, 3), dtype=np.uint8)
    gray = np.random.default_rng(1).integers(150, 256, size=(700, 500), dtype=np.uint8)
    sketch_img = np.stack([gray, gray, gray], axis=-1)

    out = features.preprocess_input(color_img)

    assert out.dtype == np.uint8 and out.ndim == 3 and out.shape[2] == 3
    assert max(out.shape[:2]) == 512
    assert not features.is_grayscale(out)
    assert features.is_grayscale(features.preprocess_input(sketch_img))


def test_preprocess_crops_paper_and_neutralizes_white_balance():
    img = np.full((240, 320, 3), [25, 35, 45], dtype=np.uint8)
    img[30:210, 50:270] = [230, 210, 190]
    img[70:170, 90:230] = [120, 45, 20]
    original = img.copy()

    out = features.preprocess_input(img)

    assert out.shape[1] == 512
    assert out.shape[0] / out.shape[1] == pytest.approx(180 / 220, abs=0.01)
    corner = out[10, 10].astype(int)
    assert corner.min() > 200
    assert corner.max() - corner.min() <= 2
    assert np.array_equal(img, original)


def test_preprocess_without_paper_keeps_image_bounds():
    img = np.full((300, 400, 3), [100, 10, 120], dtype=np.uint8)

    out = features.preprocess_input(img)

    assert out.shape == (384, 512, 3)
    assert np.array_equal(out[0, 0], [100, 10, 120])


def test_preprocess_preserves_grayscale_after_paper_crop():
    img = np.full((240, 320), 35, dtype=np.uint8)
    img[30:210, 50:270] = 235
    img[70:170, 90:230] = 40

    out = features.preprocess_input(img)

    assert out.shape[1] == 512
    assert np.array_equal(out[:, :, 0], out[:, :, 1])
    assert np.array_equal(out[:, :, 1], out[:, :, 2])


@pytest.mark.parametrize("background", [[235, 215, 175], [240, 200, 140]])
def test_preprocess_neutralizes_full_frame_warm_sketch(background):
    img = np.full((240, 320, 3), background, dtype=np.uint8)
    img[70:75, 30:290] = 45
    img[150:155, 30:290] = 70

    out = features.preprocess_input(img)

    assert features.is_grayscale(out)


@pytest.mark.parametrize("color", [[255, 0, 0], [255, 255, 0], [0, 0, 255]])
def test_preprocess_does_not_change_saturated_non_paper_art(color):
    img = np.full((300, 400, 3), color, dtype=np.uint8)

    out = features.preprocess_input(img)

    assert np.array_equal(out, np.full_like(out, color))
