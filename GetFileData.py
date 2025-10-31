#!/usr/bin/env python3
import sys
import os
import TGAHelpers

def compute_new_size_bytes(width, height, bpp, divisor_power, is_rle):
    scale = 2 ** (divisor_power + 1)  # 0=half, 1=quarter, etc.
    new_width = max(1, width // scale)
    new_height = max(1, height // scale)

    base_bytes = new_width * new_height * bpp // 8

    if is_rle:
        # Rough estimation: RLE usually compresses 60-80% of uncompressed size
        estimated_bytes = int(base_bytes * 0.7)
    else:
        estimated_bytes = base_bytes

    return new_width, new_height, estimated_bytes

if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise Exception("Usage: script.py <tga_file_path> <divisor_power>")

    file_path = sys.argv[1]
    divisor_power = int(sys.argv[2])

    width, height, channels, has_alpha, bpp, is_rle = TGAHelpers.read_tga_header(file_path)
    file_size_bytes = os.path.getsize(file_path)

    ue_format = TGAHelpers.UE_SOURCE_MAP.get((channels, bpp, has_alpha), "TSF_BGRA8")

    new_width, new_height, new_size_bytes = compute_new_size_bytes(width, height, bpp, divisor_power, is_rle)

    # Memory saved
    saved_bytes = file_size_bytes - new_size_bytes
    percent_saved = (saved_bytes / file_size_bytes * 100) if file_size_bytes > 0 else 0

    # Format values for output (delimiter: ;)
    current_res = f"{width} x {height}"
    output = f"{current_res};{file_size_bytes};{ue_format};{saved_bytes};{percent_saved:.1f}%;{new_size_bytes}"

    print(output)
