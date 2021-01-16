from cpython cimport array
import array

cdef struct ImageRGBA:
    unsigned char r
    unsigned char g
    unsigned char b
    unsigned char a

cdef array.array template_array = array.array('B')

def image_to_bgra(image):
    ptr = dict(image.im.unsafe_ptrs)['image32']
    cdef size_t ptr_int = <size_t> ptr
    cdef ImageRGBA **image32 = <ImageRGBA**> ptr_int

    cdef unsigned long width = image.width
    cdef unsigned long height = image.height

    # FIXME: just use native type?
    cdef array.array buf_array = array.clone(template_array, width * height * 4, 0)
    cdef unsigned char *buf = buf_array.data.as_uchars

    cdef size_t index
    cdef unsigned char r, g, b, a

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

    return buf_array.tobytes()
