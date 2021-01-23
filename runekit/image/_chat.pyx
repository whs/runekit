from ._utils cimport image_to_ptr, unblend, ImageRGBA, RGB

cdef struct Rectangle:
    int x
    int y
    int width
    int height

def get_chat_color(image, tuple box_, list colors):
    cdef Rectangle box = Rectangle(box_[0], box_[1], box_[2], box_[3])

    cdef float best_score = -1.0
    cdef RGB best = RGB(0, 0, 0)
    cdef ImageRGBA **data = image_to_ptr(image)

    cdef double score
    cdef ImageRGBA i1, i2
    cdef (unsigned char, unsigned char) pixel1, pixel2
    cdef int x, y
    cdef RGB color

    for color in colors:
        score = 0.0
        for y in range(box.y, box.y + box.height):
            for x in range(box.x, box.x + box.width):
                if x < 0 or x + 1 >= box.height:
                    continue
                if y < 0 or y + 1 >= box.width:
                    continue
                i1 = data[y][x]
                i2 = data[y + 1][x + 1]
                pixel1 = unblend(i1.r, i1.g, i1.b, color.r, color.g, color.b)

                pixel2 = unblend(i2.r, i2.g, i2.b, color.r, color.g, color.b)
                score += (pixel1[0] / 255 * pixel1[1] / 255) * (pixel2[0] / 255 * (255.0 - pixel2[1]) / 255)

        if score > best_score:
            best_score = score
            best = color

    return (best.r, best.g, best.b)














