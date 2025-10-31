import struct

# === READ TGA ===
def read_tga(path):
    with open(path, "rb") as f:
        header = f.read(18)
        (
            id_len,
            color_map_type,
            image_type,
            cmap_start, cmap_len, cmap_depth,
            x_origin, y_origin,
            width, height,
            pixel_depth,
            image_desc
        ) = struct.unpack("<BBBHHBHHHHBB", header)

        if image_type not in (2, 3, 10, 11):
            raise ValueError(f"Unsupported TGA type {image_type}. Supported: 2, 3, 10, 11")

        has_alpha = pixel_depth == 32 or (image_desc & 0x0F) > 0
        origin_top = (image_desc & 0x20) != 0
        bytes_per_pixel = pixel_depth // 8

        if id_len:
            f.seek(id_len, 1)

        img_data = bytearray()
        pixel_count = width * height

        def read_rle_data(bytes_per_pixel):
            data = bytearray()
            while len(data) < pixel_count * bytes_per_pixel:
                packet_header = ord(f.read(1))
                count = (packet_header & 0x7F) + 1
                if packet_header & 0x80:
                    pixel = f.read(bytes_per_pixel)
                    data.extend(pixel * count)
                else:
                    data.extend(f.read(count * bytes_per_pixel))
            return data

        if image_type == 2:
            img_data = bytearray(f.read(width * height * bytes_per_pixel))
        elif image_type == 10:
            img_data = read_rle_data(bytes_per_pixel)
        elif image_type == 3:
            gray_data = bytearray(f.read(width * height))
            img_data = bytearray()
            for g in gray_data:
                img_data.extend((g, g, g))
            bytes_per_pixel = 3
            has_alpha = False
        elif image_type == 11:
            gray_data = read_rle_data(1)
            img_data = bytearray()
            for g in gray_data:
                img_data.extend((g, g, g))
            bytes_per_pixel = 3
            has_alpha = False

    row_bytes = width * bytes_per_pixel
    if not origin_top:
        rows = [img_data[y * row_bytes:(y + 1) * row_bytes] for y in range(height)]
        rows.reverse()
        img_data = bytearray().join(rows)

    bpp = bytes_per_pixel * 8
    return width, height, bpp, has_alpha, img_data

# Mapping channels and bpp to Unreal Source Format
UE_SOURCE_MAP = {
    (1, 8, False): "TSF_G8",
    (3, 24, False): "TSF_BGRE8",
    (4, 32, True): "TSF_BGRA8",
}

def read_tga_header(path):
    with open(path, "rb") as f:
        header = f.read(18)
        (
            id_len,
            color_map_type,
            image_type,
            cmap_start, cmap_len, cmap_depth,
            x_origin, y_origin,
            width, height,
            pixel_depth,
            image_desc
        ) = struct.unpack("<BBBHHBHHHHBB", header)

        if image_type not in (2, 3, 10, 11):  # uncompressed or RLE, RGB or grayscale
            raise ValueError(f"Unsupported TGA type {image_type}")

        has_alpha = pixel_depth == 32 or (image_desc & 0x0F) > 0
        channels = pixel_depth // 8

        is_rle = image_type in (10, 11)

        return width, height, channels, has_alpha, pixel_depth, is_rle

# === WRITE TGA ===
def write_tga(path, w, h, bpp, has_alpha, data):
    image_type = 2
    image_desc = (8 if has_alpha else 0) | 0x20
    header = struct.pack(
        "<BBBHHBHHHHBB",
        0, 0, image_type,
        0, 0, 0,
        0, 0,
        w, h,
        bpp,
        image_desc
    )
    with open(path, "wb") as f:
        f.write(header)
        f.write(data)