import sysv_ipc
import numpy as np
from PIL import ImageOps, Image


def zpixmap_shm_to_image(
    shm: sysv_ipc.SharedMemory, size: int, width: int, height: int
) -> np.ndarray:
    out = np.frombuffer(shm.read(size), "<B").copy()
    out.shape = (height, width, 4)
    out[:, :, 3] = 0xFF  # Convert BGRX to BGRA

    return out
