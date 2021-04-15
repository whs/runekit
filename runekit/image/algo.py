from typing import List

import numpy as np


def is_color_percent_gte(image: np.ndarray, color: List, percent: float) -> bool:
    """Check that the image has at least percent% of the given color"""
    black_pixels = np.count_nonzero(np.all(image[:, :, : len(color)] == color, axis=-1))
    total_pixels = image.shape[0] * image.shape[1]
    color_percent = black_pixels / total_pixels
    return color_percent >= percent
