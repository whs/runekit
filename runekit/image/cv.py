from typing import Tuple, List

import numpy as np
import cv2

_debug_save_images = False


def find_subimages(image: np.ndarray, subimage: np.ndarray) -> List[Tuple[int, int]]:
    """
    Detect BGRA subimage in BGRA image with the following limitations

    * Image transparency is not supported (alpha channel is removed)
    * Subimage semi-translucency is not supported
    """
    mask = subimage[:, :, 3]
    image_bgr = image[:, :, :3]
    subimage_bgr = subimage[:, :, :3]
    matched = cv2.matchTemplate(image_bgr, subimage_bgr, cv2.TM_SQDIFF, mask=mask)

    # allow up to 30 pixel per pixel
    threshold = (30 ** 2) * subimage.shape[0] * subimage.shape[1]
    loc = np.where((matched < threshold) & (matched != np.inf))
    out = []
    for pos in zip(*loc[::-1]):
        out.append(pos)

    if _debug_save_images:
        from runekit.image.np_utils import np_save_image
        import hashlib

        cv2.normalize(matched, matched, 0, 0xFF, cv2.NORM_MINMAX)
        matched = matched.astype("uint8")
        image_bgr = image_bgr.copy()

        subimg_hash = hashlib.blake2b(subimage.data, digest_size=8).hexdigest()

        for pos in out:
            cv2.rectangle(
                matched,
                pos,
                (pos[0] + subimage.shape[1], pos[1] + subimage.shape[0]),
                0,
                2,
            )
            cv2.rectangle(
                image_bgr,
                pos,
                (pos[0] + subimage.shape[1], pos[1] + subimage.shape[0]),
                (0, 255, 0),
                2,
            )

        np_save_image(image_bgr, f"/tmp/debug-image-{subimg_hash}.png")
        np_save_image(subimage_bgr, f"/tmp/debug-subimage-{subimg_hash}.png")
        np_save_image(mask, f"/tmp/debug-mask-{subimg_hash}.png")
        np_save_image(matched, f"/tmp/debug-result-{subimg_hash}.png")

    return out
