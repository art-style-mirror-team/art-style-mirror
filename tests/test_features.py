import numpy as np

from modules import features


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
