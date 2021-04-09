import array
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender.tests.test_creation_helpers import (
    create_datablock_image_from_disk,
)

import time
_Pixel = List[float]
def _get_pixel(pixels: bpy.types.Image, x:int, y:int, width:int, height:int) -> _Pixel:
    num_pixels = width * height
    i = 4 * (y * width + x)
    return list(pixels[i:i+4])

def _put_pixel(pixels: bpy.types.Image, x:int, y:int, width:int, height:int, pixel: _Pixel) -> None:
    i = 4 * (y * width + x)
    pixels[i] =   pixel[0]
    pixels[i+1] = pixel[1]
    pixels[i+2] = pixel[2]
    pixels[i+3] = pixel[3]

def make_tmp_filepath(temp_img_path:Path, frame:int, slot:int)->Path:
    """
    Temp image path are in the form of 'parent_folder/bake_image_name_slot[1-4]_001.png' etc
    """
    return Path(f"{temp_img_path.parent}", f"{temp_img_path.stem}_slot{slot}_{frame:03}.png")

def make_wiper_images(paths:List[Path]):
    """
    It is assumed all paths come in the proper format
    and share the same parent folder
    """
    assert all(path.parent == paths[0].parent for path in paths)

    try:
        master = bpy.data.images["master"]
    except KeyError:
        master = bpy.data.images.new("master", 1024, 1024, alpha=True)
        master.filepath = f"{paths[0].parent}/wiper_gradient.png"
    else:
        master.pixels[:] = [0.0] * len(master.pixels)
    master_array = array.array("f", master.pixels)
    width, height = master.size

    time_start = time.perf_counter()
    for i, path in enumerate(paths):
        loop_start = time.perf_counter()
        slot = int(path.name[path.name.find("slot")+4])
        frame = int(path.name[path.name.rfind("_")+1:path.name.rfind("_")+4])
        img = create_datablock_image_from_disk(path)
        pixels = array.array("f", (img.pixels))

        for y in range(height-1, -1, -1):
            for x in range(0, width):
                img_pixel = _get_pixel(pixels, x, y, width, height)
                if img_pixel[3] > 0:
                    #print(*img_pixel, f"@ ({x}, {y})")
                    m_pixel = _get_pixel(master_array, x, y, width, height)
                    m_pixel[slot-1] = frame/250
                    _put_pixel(master_array, x, y, width, height, m_pixel)

        bpy.data.images.remove(img)
        print(f"Processed temp {i} in {time.perf_counter() - loop_start}")
    try:
        print("Saving file")
        master.pixels[:] = master_array
        master.save()
        print("Total time end:", time.perf_counter() - time_start  )
    except OSError:
        raise
    else:
        print("Saved")
    return {"SUCCESS"}
