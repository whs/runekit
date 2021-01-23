from cpython.mem cimport PyMem_Malloc, PyMem_Free
from ._font cimport CharInfo
from ._utils cimport image_to_ptr, ImageRGBA

cdef class FontDefinition:
    cdef CharInfo *chars
    cdef size_t chars_len
    cdef readonly int width
    cdef readonly int height
    cdef readonly int space_width
    cdef readonly bint shadow
    cdef readonly int base_y

    cdef readonly int min_rating
    cdef readonly int max_spaces

    def __dealloc__(self):
        for i in range(self.chars_len):
            PyMem_Free(self.chars[i].pixels)

        PyMem_Free(self.chars)

cpdef FontDefinition generate_font(image, str chars, str seconds, bonuses, int base_y, int space_width, int threshold, bint shadow):
    cdef int chars_len = len(chars)
    cdef FontDefinition out = FontDefinition()
    cdef CharInfo *cinfo = <CharInfo*> PyMem_Malloc(sizeof(CharInfo) * chars_len)
    cdef ImageRGBA **raw = image_to_ptr(image)

    cdef int width = image.width
    cdef int height = image.height
    cdef int min_y = image.height - 1
    cdef int max_y = 0
    cdef int ds = -1
    cdef int i, dx, cur_char, letter_width, x, y
    cdef Py_UNICODE letter
    cdef CharInfo *chr

    threshold *= 255

    for dx in range(width):
        if ds == -1:
            i = height - 1
            if raw[i][dx].r == 255 and raw[i][dx].a == 255:
                ds = dx

            continue

        letter = chars[cur_char]
        letter_width = ds - dx
        cinfo[cur_char] = CharInfo(
            width=letter_width,
            chr=letter,
            bonus=0,
            secondary=letter in seconds,
        )
        if bonuses and letter in bonuses:
            cinfo[cur_char].bonus = bonuses[letter]

        cur_char += 1
        out.width = max(out.width, letter_width)

        for y in range(height - 1):
            for x in range(letter_width):
                if raw[y][x + ds].r >= threshold:
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)

        ds = -1

    out.height = max_y + 1 - min_y
    out.base_y = base_y - min_y

    for a in range(chars_len):
        chr = &cinfo[a]
        # TODO

    return out
