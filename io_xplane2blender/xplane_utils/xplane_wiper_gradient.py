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


def make_wiper_images(paths:List[Path], master_width:int, master_height:int)->Path:
    """
    Using a list of paths, make the channel oriented wiper_gradient_texture.png.
    Raises OSError is saving the texture has an issue.

    Returns Path of the final wiper_gradient_texture.png
    """
    assert all(path.parent == paths[0].parent for path in paths)

    master_img_name = "master_wiper_gradient"
    try:
        bpy.data.images.remove(bpy.data.images[master_img_name])
    except KeyError:
        pass
    master = bpy.data.images.new(master_img_name, master_width, master_height, alpha=True)
    master_array = array.array("f", master.pixels)
    master.filepath = f"{paths[0].parent.parent}/wiper_gradient_texture.png"
    gradient_texture_path = Path(master.filepath)

    offset_start, offset_end = bpy.context.scene.xplane.wiper_bake_start, bpy.context.scene.xplane.wiper_bake_end
    # + 1 because offset_start:offset_end is inclusive
    num_steps = (offset_end - offset_start) + 1
    time_start = time.perf_counter()
    for step, path in enumerate(paths):
        loop_start = time.perf_counter()
        slot = int(path.name[path.name.rfind("slot")+4])
        frame = int(path.name[path.name.rfind("_")+1:path.name.rfind("_")+4])

        img = create_datablock_image_from_disk(path)
        pixels = array.array("f", img.pixels)

        for y in range(master_height-1, -1, -1):
            for x in range(0, master_width):
                img_pixel = _get_pixel(pixels, x, y, master_width, master_height)
                if img_pixel[3] > 0:
                    #print(*img_pixel, f"@ ({x}, {y})")
                    m_pixel = _get_pixel(master_array, x, y, master_width, master_height)
                    m_pixel[slot-1] = step/num_steps
                    _put_pixel(master_array, x, y, master_width, master_height, m_pixel)

        bpy.data.images.remove(img)
        print(f"Processed slot{slot}_{frame} in {time.perf_counter() - loop_start}")
    try:
        print("Saving", master.filepath)
        master.pixels[:] = master_array
        master.save()
        print("Saved")
        print("Total time end:", time.perf_counter() - time_start)
    except OSError:
        raise
    else:
        bpy.data.images.remove(master)

    return gradient_texture_path
