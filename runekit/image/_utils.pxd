cdef struct ImageRGBA:
    unsigned char r
    unsigned char g
    unsigned char b
    unsigned char a

cdef struct RGB:
    unsigned char r
    unsigned char g
    unsigned char b

cpdef (unsigned char, unsigned char) unblend(int r, int g, int b, int R, int G, int B) nogil
cdef ImageRGBA** image_to_ptr(image)
cpdef int can_blend(int rm, int gm, int bm, int r1, int g1, int b1, int p) nogil
# cdef (double, double, double) decompose2col(unsigned char rp, unsigned char gp, unsigned char bp, unsigned char r1, unsigned char g1, unsigned char b1, unsigned char r2, unsigned char g2, unsigned char b2) nogil
# cdef (double, double, double) decompose3col(unsigned char rp, unsigned char gp, unsigned char bp, unsigned char r1, unsigned char g1, unsigned char b1, unsigned char r2, unsigned char g2, unsigned char b2, double r3, double g3, double b3) nogil
