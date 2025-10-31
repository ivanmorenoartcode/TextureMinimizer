import math

# === HELPER ===
def get_px(data, w, h, x, y, bpp):
    x = min(max(int(x), 0), w - 1)
    y = min(max(int(y), 0), h - 1)
    bytes_per_pixel = bpp // 8
    i = (y * w + x) * bytes_per_pixel
    b = data[i:i+bytes_per_pixel]
    if bytes_per_pixel == 3:
        return list(b) + [255]
    return list(b[:3]) + [b[3]]


# === RESAMPLING METHODS ===

def nearest_downscale(w, h, bpp, has_alpha, data, divisor):
    new_w = max(1, w // divisor)
    new_h = max(1, h // divisor)
    bytes_per_pixel = bpp // 8
    dst = bytearray(new_w * new_h * bytes_per_pixel)

    for j in range(new_h):
        for i in range(new_w):
            sx = int(i * w / new_w)
            sy = int(j * h / new_h)
            px = get_px(data, w, h, sx, sy, bpp)
            idx = (j * new_w + i) * bytes_per_pixel
            dst[idx:idx+bytes_per_pixel] = bytes(px[:3] + ([px[3]] if has_alpha else []))
    return new_w, new_h, dst


def bilinear_downscale(w, h, bpp, has_alpha, data, divisor):
    new_w = max(1, w // divisor)
    new_h = max(1, h // divisor)
    bytes_per_pixel = bpp // 8
    dst = bytearray(new_w * new_h * bytes_per_pixel)

    def lerp(a, b, t): return a + (b - a) * t

    for j in range(new_h):
        sy = (j + 0.5) * h / new_h - 0.5
        y0 = max(0, int(math.floor(sy)))
        y1 = min(h - 1, y0 + 1)
        dy = sy - y0
        for i in range(new_w):
            sx = (i + 0.5) * w / new_w - 0.5
            x0 = max(0, int(math.floor(sx)))
            x1 = min(w - 1, x0 + 1)
            dx = sx - x0

            c00 = get_px(data, w, h, x0, y0, bpp)
            c10 = get_px(data, w, h, x1, y0, bpp)
            c01 = get_px(data, w, h, x0, y1, bpp)
            c11 = get_px(data, w, h, x1, y1, bpp)

            out = [int(round(lerp(lerp(c00[k], c10[k], dx),
                                  lerp(c01[k], c11[k], dx), dy))) for k in range(4)]
            idx = (j * new_w + i) * bytes_per_pixel
            dst[idx:idx+bytes_per_pixel] = bytes(out[:3] + ([out[3]] if has_alpha else []))
    return new_w, new_h, dst


def bicubic_downscale(w, h, bpp, has_alpha, data, divisor):
    new_w = max(1, w // divisor)
    new_h = max(1, h // divisor)
    bytes_per_pixel = bpp // 8
    dst = bytearray(new_w * new_h * bytes_per_pixel)

    def cubic_weight(t):
        a = -0.5
        t = abs(t)
        if t < 1:
            return (a + 2) * t**3 - (a + 3) * t**2 + 1
        elif t < 2:
            return a * t**3 - 5*a * t**2 + 8*a * t - 4*a
        return 0

    for j in range(new_h):
        sy = (j + 0.5) * h / new_h - 0.5
        for i in range(new_w):
            sx = (i + 0.5) * w / new_w - 0.5
            acc = [0, 0, 0, 0]
            weight_sum = 0
            for yy in range(int(sy) - 1, int(sy) + 3):
                for xx in range(int(sx) - 1, int(sx) + 3):
                    wx = cubic_weight(sx - xx)
                    wy = cubic_weight(sy - yy)
                    wght = wx * wy
                    px = get_px(data, w, h, xx, yy, bpp)
                    for k in range(4):
                        acc[k] += px[k] * wght
                    weight_sum += wght
            if weight_sum != 0:
                acc = [int(round(c / weight_sum)) for c in acc]
            idx = (j * new_w + i) * bytes_per_pixel
            dst[idx:idx+bytes_per_pixel] = bytes(acc[:3] + ([acc[3]] if has_alpha else []))
    return new_w, new_h, dst


def lanczos_downscale(w, h, bpp, has_alpha, data, divisor, a=3):
    new_w = max(1, w // divisor)
    new_h = max(1, h // divisor)
    bytes_per_pixel = bpp // 8
    dst = bytearray(new_w * new_h * bytes_per_pixel)

    def sinc(x): return 1 if x == 0 else math.sin(math.pi * x) / (math.pi * x)
    def lanczos(x): return sinc(x) * sinc(x / a) if abs(x) < a else 0

    for j in range(new_h):
        sy = (j + 0.5) * h / new_h - 0.5
        for i in range(new_w):
            sx = (i + 0.5) * w / new_w - 0.5
            acc = [0, 0, 0, 0]
            weight_sum = 0
            for yy in range(int(sy - a + 1), int(sy + a)):
                for xx in range(int(sx - a + 1), int(sx + a)):
                    wght = lanczos(sx - xx) * lanczos(sy - yy)
                    px = get_px(data, w, h, xx, yy, bpp)
                    for k in range(4):
                        acc[k] += px[k] * wght
                    weight_sum += wght
            if weight_sum != 0:
                acc = [int(round(c / weight_sum)) for c in acc]
            acc = [max(0, min(255, int(round(c)))) for c in acc]  # clamp
            idx = (j * new_w + i) * bytes_per_pixel
            dst[idx:idx+bytes_per_pixel] = bytes(acc[:3] + ([acc[3]] if has_alpha else []))
    return new_w, new_h, dst


def area_downscale(w, h, bpp, has_alpha, data, divisor):
    new_w = max(1, w // divisor)
    new_h = max(1, h // divisor)
    bytes_per_pixel = bpp // 8
    dst = bytearray(new_w * new_h * bytes_per_pixel)
    area = divisor * divisor

    for j in range(new_h):
        for i in range(new_w):
            acc = [0, 0, 0, 0]
            for y in range(divisor):
                for x in range(divisor):
                    px = get_px(data, w, h, i * divisor + x, j * divisor + y, bpp)
                    for k in range(4):
                        acc[k] += px[k]
            avg = [v // area for v in acc]
            idx = (j * new_w + i) * bytes_per_pixel
            dst[idx:idx+bytes_per_pixel] = bytes(avg[:3] + ([avg[3]] if has_alpha else []))
    return new_w, new_h, dst
