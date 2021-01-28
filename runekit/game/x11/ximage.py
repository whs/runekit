import sysv_ipc
from PIL import ImageOps, Image


def zpixmap_shm_to_image(
    shm: sysv_ipc.SharedMemory, size: int, width: int, height: int
) -> Image:
    out = Image.frombytes(
        "RGBA",
        (width, height),
        shm.read(size),
        "raw",
    )
    b, g, r, a = out.split()
    a = ImageOps.invert(a)
    return Image.merge("RGBA", (r, g, b, a))
