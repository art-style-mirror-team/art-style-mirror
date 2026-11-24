import cv2
import numpy as np

from modules import features

LINE_FEATURES = (
    "edge_density",
    "direction",
    "straight_ratio",
    "roughness",
    "stroke_length",
)


def _geometric_image(size: int = 256) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    for position in range(24, size, 32):
        cv2.line(image, (position, 8), (position, size - 8), (255, 255, 255), 2)
        cv2.line(image, (8, position), (size - 8, position), (255, 255, 255), 2)
    return image


def _curved_stroke_image(size: int = 256) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    for y in range(20, size - 20, 32):
        for x in range(20, size - 20, 32):
            cv2.ellipse(image, (x, y), (8, 8), 0, 20, 320, (255, 255, 255), 2)
            cv2.line(image, (x + 8, y + 8), (x + 14, y + 12), (255, 255, 255), 2)
    return image


def test_line_features_are_floats_in_unit_interval():
    result = features.extract_features(_geometric_image())

    for name in LINE_FEATURES:
        assert type(result[name]) is float
        assert 0.0 <= result[name] <= 1.0


def test_straight_ratio_separates_geometric_lines_from_curved_strokes():
    geometric = features.extract_features(_geometric_image())
    curved = features.extract_features(_curved_stroke_image())

    assert geometric["straight_ratio"] >= curved["straight_ratio"] + 0.20


def test_line_features_are_calculated_for_grayscale_sketches():
    sketch = cv2.cvtColor(_curved_stroke_image(), cv2.COLOR_RGB2GRAY)
    sketch = np.repeat(sketch[:, :, np.newaxis], 3, axis=2)

    gray_result = features.extract_features(sketch, gray=True)
    color_mode_result = features.extract_features(sketch, gray=False)

    assert all(type(gray_result[name]) is float for name in LINE_FEATURES)
    assert all(0.0 <= gray_result[name] <= 1.0 for name in LINE_FEATURES)
    assert gray_result["edge_density"] > 0.0
    assert all(gray_result[name] == color_mode_result[name] for name in LINE_FEATURES)


def test_uniform_image_returns_finite_zero_line_features():
    image = np.full((128, 128, 3), 127, dtype=np.uint8)
    result = features.extract_features(image)

    for name in LINE_FEATURES:
        assert np.isfinite(result[name])
        assert type(result[name]) is float
        assert result[name] == 0.0
