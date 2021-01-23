cdef struct CharInfo:
    int width
    int height
    Py_UNICODE chr
    int bonus
    bint secondary

    unsigned char *pixels

