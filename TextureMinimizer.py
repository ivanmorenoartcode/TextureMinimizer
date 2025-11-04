#!/usr/bin/env python3

import sys, os, unreal
import TGAHelpers
import DownscaleMethods

def reimport_file(source, destination):
    asset = unreal.EditorAssetLibrary.load_asset(destination)
    if not asset:
        print("Asset not found:", destination)
    else:
        # Create an import task
        task = unreal.AssetImportTask()
        task.filename = source
        task.destination_path = os.path.dirname(destination)  # keep in same folder
        task.destination_name = os.path.basename(destination)  # same asset name
        task.replace_existing = True    # important: overwrite the existing asset
        task.automated = True
        task.save = True

        # Import
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        asset_tools.import_asset_tasks([task])

        print("Reimported existing asset with new source file:", source)
    
def duplicate_game_asset(asset_to_duplicate):
    asset = unreal.EditorAssetLibrary.load_asset(asset_to_duplicate)
    if not asset:
        raise Exception("Asset not found:", asset_to_duplicate)

    # Compute desired new asset path
    desired_new_path = asset_to_duplicate + "_minimized"  # "/Game/Textures/aa_minimized"

    # Use Unreal to generate a unique asset name if it already exists
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    unique_name, unique_path = asset_tools.create_unique_asset_name(desired_new_path, "_1")
    # Duplicate the asset
    duplicated_asset = unreal.EditorAssetLibrary.duplicate_asset(asset_to_duplicate, unique_name)
    if not duplicated_asset:
        raise Exception("Failed to duplicate asset")

    return unique_name

def get_unique_minimized_path(base_path: str) -> str:
    """
    Given a base file path (without extension),
    returns a unique path ending with '_minimized.tga' or '_minimized_X.tga' if duplicates exist.
    """
    directory = os.path.dirname(base_path)
    filename = os.path.basename(base_path)
    name, _ = os.path.splitext(filename)

    # First candidate
    candidate = os.path.join(directory, f"{name}_minimized.tga")

    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{name}_minimized_{counter}.tga")
        counter += 1

    return candidate

def main():
    asset_path = sys.argv[2]
    in_path = sys.argv[1]
    base, ext = os.path.splitext(in_path)
    out_path = base + ".tga"
    if sys.argv[4] == "F":
        out_path = get_unique_minimized_path(base)

    w, h, bpp, has_alpha, data = TGAHelpers.read_tga(in_path)
    print(f"Read {in_path}: {w}×{h}, {bpp}-bit, alpha={has_alpha}")

    # Map the new argument to a divisor
    div_arg = int(sys.argv[5])  # your new unused argv
    divisor = 2 ** (div_arg + 1)  # 0 -> 2, 1 -> 4, 2 -> 8, 3 -> 16

    method = int(sys.argv[6])
    if method == 0:
        new_w, new_h, new_data = DownscaleMethods.nearest_downscale(w, h, bpp, has_alpha, data, divisor)
    elif method == 1:
        new_w, new_h, new_data = DownscaleMethods.bilinear_downscale(w, h, bpp, has_alpha, data, divisor)
    elif method == 2:
        new_w, new_h, new_data = DownscaleMethods.bicubic_downscale(w, h, bpp, has_alpha, data, divisor)
    elif method == 3:
        new_w, new_h, new_data = DownscaleMethods.lanczos_downscale(w, h, bpp, has_alpha, data, divisor)
    elif method == 4:
        new_w, new_h, new_data = DownscaleMethods.area_downscale(w, h, bpp, has_alpha, data, divisor)
    else:
        raise ValueError("Invalid method")

    TGAHelpers.write_tga(out_path, new_w, new_h, bpp, has_alpha, new_data)
    print(f"Saved {out_path}: {new_w}×{new_h}")

    if sys.argv[3] == "T":
        reimport_file(out_path, asset_path)
    else:
        duplicated_asset_path = duplicate_game_asset(asset_path)
        reimport_file(out_path, duplicated_asset_path)

if __name__ == "__main__":
    main()
