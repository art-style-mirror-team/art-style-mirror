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


def _parallel_line_image(angle_degrees: float = 0, size: int = 256) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    angle = np.deg2rad(angle_degrees)
    direction = np.array([np.cos(angle), np.sin(angle)])
    normal = np.array([-direction[1], direction[0]])
    center = np.array([(size - 1) / 2, (size - 1) / 2])
    for offset in range(-size // 2, size // 2 + 1, 24):
        start = np.rint(center + offset * normal - size * direction).astype(int)
        end = np.rint(center + offset * normal + size * direction).astype(int)
        cv2.line(image, tuple(start), tuple(end), (255, 255, 255), 2)
    return image


def _multi_direction_segments_image(size: int = 256) -> np.ndarray:
    image = np.zeros((size, size, 3), dtype=np.uint8)
    angles = (0, 45, 90, 135)
    length = 20
    for row, y in enumerate(range(24, size - 16, 32)):
        for col, x in enumerate(range(24, size - 16, 32)):
            angle = np.deg2rad(angles[(row + col) % len(angles)])
            delta = np.array([np.cos(angle), np.sin(angle)]) * (length / 2)
            start = np.rint([x, y] - delta).astype(int)
            end = np.rint([x, y] + delta).astype(int)
            cv2.line(image, tuple(start), tuple(end), (255, 255, 255), 2)
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


def test_direction_is_high_for_parallel_lines():
    result = features.extract_features(_parallel_line_image())

    assert result["direction"] >= 0.8


def test_direction_is_lower_for_lines_in_multiple_directions():
    parallel = features.extract_features(_parallel_line_image())
    varied = features.extract_features(_multi_direction_segments_image())

    assert varied["direction"] < parallel["direction"] - 0.3


def test_direction_is_continuous_across_horizontal_angle_boundary():
    positive = features.extract_features(_parallel_line_image(angle_degrees=3))
    negative = features.extract_features(_parallel_line_image(angle_degrees=-3))

    assert abs(positive["direction"] - negative["direction"]) < 0.05


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
