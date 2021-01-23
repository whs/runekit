from PIL.Image import new as image_new
from libc.math cimport sqrt, fabs
from ._utils cimport ImageRGBA

cpdef (unsigned char, unsigned char) unblend(int r, int g, int b, int R, int G, int B) nogil:
    cdef double m = sqrt(r * r + g * g + b * b)
    cdef double n = sqrt(R * R + G * G + B * B)

    cdef double x = (r * R + g * G + b * B) / n
    cdef double y = sqrt(max(0.0, m * m - x * x))

    cdef int r1 = int(max(0.0, (63.75 - y) * 4))
    cdef int r2 = int(x / n * 255)

    if r2 > 255:
        r1 = max(0, r1 - r2 + 255)
        r2 = 255

    return r1, r2

cdef ImageRGBA** image_to_ptr(image):
    ptr = dict(image.im.unsafe_ptrs)['image32']
    cdef size_t ptr_int = <size_t> ptr
    return <ImageRGBA**> ptr_int

def rgb(unsigned char r, unsigned char g, unsigned char b):
    return RGB(r, g,b)

cpdef int can_blend(int rm, int gm, int bm, int r1, int g1, int b1, int p) nogil:
    """
    Determine whether color [rgb]m can be a result of a blend with color [rgb]1 that is p (0-1) of the mix
    :param rm: resulting color
    :param r1: first color of the mix (the other color is unknown)
    :param p: the portion of the [rgb]1 in the mix (0-1)
    :return: the number that the second color has to lie outside of the possible color ranges
    """
    cdef int m = min(50, p/(1-p))
    cdef int r = rm + (rm - r1) * m
    cdef int g = gm + (gm - g1) * m
    cdef int b = bm + (bm - b1) * m
    return max(-r, -g, -b, r - 255, g - 255, b - 255)

def unblend_known_background(img, bg_img, bint shadow, unsigned char r, unsigned char g, unsigned char b):
    if bg_img:
        assert img.width == bg_img.width and img.height == bg_img.height

    out_img = image_new('RGBA', (img.width, img.height), None)

    cdef ImageRGBA **outptr = image_to_ptr(out_img)
    cdef ImageRGBA **imgptr = image_to_ptr(img)
    cdef ImageRGBA **bgptr = image_to_ptr(bg_img)
    cdef int width = img.width
    cdef int height = img.height

    cdef int x, y
    cdef (double, double, double) col
    cdef double m
    cdef unsigned char red

    with nogil:
        for y in range(height):
            for x in range(width):
                pixel = imgptr[y][x]
                bg_pixel = bgptr[y][x]

                col = decompose2col(pixel.r, pixel.g, pixel.b, r, g, b, bg_pixel.r, bg_pixel.g, bg_pixel.b)

                if shadow:
                    m = 1 - col[1] - fabs(col[2])
                    red = <unsigned char> (m * 255)
                    outptr[y][x].r = red
                    outptr[y][x].g = <unsigned char> (col[0] / m * 255.0)
                    outptr[y][x].b = red
                else:
                    red = <unsigned char> (col[0] * 255)
                    outptr[y][x].r = red
                    outptr[y][x].g = red
                    outptr[y][x].b = red

                outptr[y][x].a = 255

    return out_img

cdef inline (double, double, double) decompose2col(double rp, double gp, double bp, double r1, double g1, double b1, double r2, double g2, double b2) nogil:
    cdef double r3 = g1 * b2 - g2 * b1
    cdef double g3 = b1 * r2 - b2 * r1
    cdef double b3 = r1 * g2 - r2 * g1

    cdef double norm = 255.0 / sqrt(r3 * r3 + g3 * g3 + b3 * b3)
    r3 *= norm
    g3 *= norm
    b3 *= norm

    return decompose3col(rp, gp, bp, r1, g1, b1, r2, g2, b2, r3, g3, b3)

cdef inline (double, double, double) decompose3col(double rp, double gp, double bp, double r1, double g1, double b1, double r2, double g2, double b2, double r3, double g3, double b3) nogil:
    cdef double A = g2 * b3 - b2 * g3
    cdef double B = g3 * b1 - b3 * g1
    cdef double C = g1 * b2 - b1 * g2

    cdef double D = b2 * r3 - r2 * b3
    cdef double E = b3 * r1 - r3 * b1
    cdef double F = b1 * r2 - r1 * b2

    cdef double G = r2 * g3 - g2 * r3
    cdef double H = r3 * g1 - g3 * r1
    cdef double I = r1 * g2 - g1 * r2

    cdef double det = r1 * A + g1 * D + b1 * G

    cdef double x = (A * rp + D * gp + G * bp) / det
    cdef double y = (B * rp + E * gp + H * bp) / det
    cdef double z = (C * rp + F * gp + I * bp) / det

    return x, y, z

