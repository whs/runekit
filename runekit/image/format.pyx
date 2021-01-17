from cpython.mem cimport PyMem_Malloc, PyMem_Free

cdef struct ImageRGBA:
    unsigned char r
    unsigned char g
    unsigned char b
    unsigned char a

def image_to_bgra(image):
    ptr = dict(image.im.unsafe_ptrs)['image32']
    cdef size_t ptr_int = <size_t> ptr
    cdef ImageRGBA **image32 = <ImageRGBA**> ptr_int

    cdef unsigned long width = image.width
    cdef unsigned long height = image.height

    cdef size_t size = width * height * 4
    cdef unsigned char *buf = <unsigned char*> PyMem_Malloc(size)

    cdef size_t index, x, y
    cdef unsigned char r, g, b, a

    with nogil:
        for x in range(width):
            for y in range(height):
                index = ((y * width) + x) * 4
                r = image32[y][x].r
                g = image32[y][x].g
                b = image32[y][x].b
                a = image32[y][x].a

                buf[index] = b
                buf[index+1] = g
                buf[index+2] = r
                buf[index+3] = a

    try:
        return buf[:size]
    finally:
        PyMem_Free(buf)
