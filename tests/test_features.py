from __future__ import annotations

import cv2
import numpy as np
import pytest

from modules import features


def _sketch_image(
    light: tuple[int, int, int] = (235, 215, 175), shape: tuple[int, int] = (240, 320)
) -> np.ndarray:
    height, width = shape
    img = np.empty((height, width, 3), dtype=np.uint8)
    img[:] = light
    line = tuple(np.rint(np.array(light) * 0.3).astype(np.uint8).tolist())
    for y in range(20, height, max(24, height // 7)):
        cv2.line(img, (10, y), (width - 10, min(height - 1, y + 20)), line, 2)
    cv2.ellipse(img, (width // 2, height // 2), (width // 4, height // 4), 0, 0, 300, line, 2)
    return img


def _add_noise(img: np.ndarray, sigma: float, seed: int) -> np.ndarray:
    noise = np.random.default_rng(seed).normal(0, sigma, img.shape)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


@pytest.mark.parametrize("light", [(235, 215, 175), (240, 200, 140), (225, 230, 240)])
def test_preprocess_neutralizes_full_frame_sketches(light):
    out = features.preprocess_input(_sketch_image(light))

    assert features.is_grayscale(out)


def test_preprocess_neutralizes_sketch_with_uneven_light_and_noise():
    img = _sketch_image()
    img[:, img.shape[1] // 2 :] = (img[:, img.shape[1] // 2 :].astype(np.float32) * 0.75).astype(
        np.uint8
    )

    out = features.preprocess_input(_add_noise(img, sigma=4, seed=10))

    assert features.is_grayscale(out)


def test_preprocess_neutralizes_noisy_4000px_sketch():
    img = cv2.resize(_sketch_image(shape=(512, 640)), (4000, 3200), interpolation=cv2.INTER_CUBIC)

    out = features.preprocess_input(_add_noise(img, sigma=4, seed=11))

    assert features.is_grayscale(out)


def test_preprocess_neutralizes_sketch_on_desk():
    img = np.full((280, 360, 3), (70, 55, 40), dtype=np.uint8)
    img[35:245, 45:315] = _sketch_image(shape=(210, 270))

    out = features.preprocess_input(img)

    assert features.is_grayscale(out)


def test_preprocess_keeps_grayscale_input_grayscale():
    gray = np.full((240, 320), 230, dtype=np.uint8)
    cv2.line(gray, (20, 20), (300, 220), 50, 3)

    out = features.preprocess_input(gray)

    assert features.is_grayscale(out)


def test_preprocess_crops_paper_and_neutralizes_white_balance():
    img = np.full((240, 320, 3), [25, 35, 45], dtype=np.uint8)
    img[30:210, 50:270] = [230, 210, 190]
    img[85:90, 90:230] = [69, 63, 57]
    img[130:135, 90:230] = [69, 63, 57]
    original = img.copy()

    out = features.preprocess_input(img)

    assert out.shape[1] == 512
    assert out.shape[0] / out.shape[1] == pytest.approx(180 / 220, abs=0.01)
    corner = out[10, 10].astype(int)
    assert corner.min() > 200
    assert corner.max() - corner.min() <= 2
    assert np.array_equal(img, original)


def test_preprocess_crops_low_light_paper_from_desk_background():
    img = np.full((300, 420, 3), (100, 70, 40), dtype=np.uint8)
    img[15:285, 20:400] = (145, 142, 135)
    cv2.line(img, (40, 70), (370, 220), (43, 43, 41), 3)

    out = features.preprocess_input(img)

    assert features.is_grayscale(out)


def test_preprocess_without_paper_keeps_image_bounds():
    img = np.full((300, 400, 3), [100, 10, 120], dtype=np.uint8)

    out = features.preprocess_input(img)

    assert out.shape == (384, 512, 3)
    assert np.array_equal(out[0, 0], [100, 10, 120])


@pytest.mark.parametrize(
    "color",
    [
        [100, 110, 120],
        [150, 165, 184],
        [239, 224, 169],
        [234, 200, 184],
        [255, 0, 0],
        [255, 255, 0],
    ],
)
def test_preprocess_preserves_uniform_nonpaper_colors(color):
    img = np.full((300, 400, 3), color, dtype=np.uint8)

    out = features.preprocess_input(img)

    assert np.array_equal(out, np.full_like(out, color))
    assert not features.is_grayscale(out)


def test_preprocess_preserves_grayscale_after_paper_crop():
    img = np.full((240, 320), 35, dtype=np.uint8)
    img[30:210, 50:270] = 235
    img[70:170, 90:230] = 40

    out = features.preprocess_input(img)

    assert out.shape[1] == 512
    assert np.array_equal(out[:, :, 0], out[:, :, 1])
    assert np.array_equal(out[:, :, 1], out[:, :, 2])


def _pastel_landscape(shape: tuple[int, int]) -> np.ndarray:
    height, width = shape
    img = np.empty((height, width, 3), dtype=np.uint8)
    img[: height // 3] = (230, 195, 205)
    img[height // 3 : 2 * height // 3] = (190, 220, 238)
    img[2 * height // 3 :] = (195, 225, 190)
    for x in range(width // 8, width, width // 6):
        cv2.line(img, (x, height), (x + width // 10, height // 3), (65, 60, 55), 4)
    return img


@pytest.mark.parametrize(
    "shape,uneven_light,noise",
    [((512, 512), False, 0), ((2048, 2048), False, 0), ((512, 512), True, 4)],
)
def test_preprocess_preserves_colored_pastel_landscape(shape, uneven_light, noise):
    img = _pastel_landscape(shape)
    if uneven_light:
        img[:, img.shape[1] // 2 :] = (
            img[:, img.shape[1] // 2 :].astype(np.float32) * 0.75
        ).astype(np.uint8)
    img = _add_noise(img, sigma=noise, seed=12) if noise else img
    expected = (
        img
        if max(shape) == features.LONG_SIDE
        else cv2.resize(
            img,
            (
                round(shape[1] * features.LONG_SIDE / max(shape)),
                round(shape[0] * features.LONG_SIDE / max(shape)),
            ),
            interpolation=cv2.INTER_AREA,
        )
    )

    out = features.preprocess_input(img)

    assert not features.is_grayscale(out)
    assert np.array_equal(out, expected)


@pytest.mark.parametrize("noise", [0, 3])
def test_preprocess_preserves_colored_watercolor_with_outline(noise):
    img = np.full((320, 320, 3), (250, 250, 250), dtype=np.uint8)
    cv2.circle(img, (100, 140), 65, (235, 190, 205), -1)
    cv2.circle(img, (220, 145), 65, (185, 215, 235), -1)
    cv2.ellipse(img, (160, 155), (130, 105), 0, 0, 360, (50, 45, 40), 3)
    if noise:
        img = _add_noise(img, sigma=noise, seed=13)

    out = features.preprocess_input(img)

    assert not features.is_grayscale(out)


@pytest.mark.parametrize("art", ["pens", "apple", "random"])
def test_preprocess_keeps_color_illustrations_colored(art):
    if art == "pens":
        img = np.full((300, 400, 3), (250, 250, 250), dtype=np.uint8)
        cv2.line(img, (30, 50), (360, 250), (230, 25, 35), 18)
        cv2.line(img, (30, 250), (360, 50), (20, 60, 235), 18)
    elif art == "apple":
        img = np.full((300, 400, 3), (245, 235, 215), dtype=np.uint8)
        cv2.ellipse(img, (200, 175), (85, 95), 0, 0, 360, (220, 35, 40), -1)
        cv2.line(img, (200, 85), (210, 55), (55, 100, 40), 8)
    else:
        img = np.random.default_rng(14).integers(0, 256, (300, 400, 3), dtype=np.uint8)

    out = features.preprocess_input(img)

    assert not features.is_grayscale(out)


def test_color_features_differ_between_bright_and_dark_images():
    bright = np.empty((40, 40, 3), dtype=np.uint8)
    bright[:20, :20] = [255, 200, 50]
    bright[:20, 20:] = [255, 100, 30]
    bright[20:, :20] = [220, 80, 40]
    bright[20:, 20:] = [255, 230, 100]

    dark = np.full((40, 40, 3), [20, 22, 24], dtype=np.uint8)
    dark[:4, :4] = [30, 32, 34]

    bright_features = features.extract_features(bright)
    dark_features = features.extract_features(dark)
    color_keys = ("brightness", "contrast", "saturation", "warmth", "color_diversity", "palette")

    assert all(bright_features[key] != dark_features[key] for key in color_keys)
    assert bright_features["brightness"] > dark_features["brightness"]
    assert bright_features["contrast"] > dark_features["contrast"]
    assert bright_features["saturation"] > dark_features["saturation"]
    assert bright_features["warmth"] > dark_features["warmth"]
    assert bright_features["color_diversity"] > dark_features["color_diversity"]
