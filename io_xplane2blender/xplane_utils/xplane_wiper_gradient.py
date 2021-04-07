import array
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender.tests.test_creation_helpers import (
    create_datablock_image_from_disk,
)


@dataclass
class _Pixel:
    r: float
    g: float
    b: float
    a: float

    def __iter__(self) -> float:
        yield self.r
        yield self.g
        yield self.b
        yield self.a

import time
def _get_pixel(pixels: bpy.types.Image, x:int, y:int, width:int, height:int) -> _Pixel:
    num_pixels = width * height
    i = 4 * (y * width + x)
    return pixels[i:i+4]

def _put_pixel(pixels: bpy.types.Image, x:int, y:int, width:int, height:int, pixel: _Pixel) -> None:
    i = 4 * (y * width + x)
    pixels[i]   = pixel[0]
    pixels[i+1]   = pixel[1]
    pixels[i+2]   = pixel[2]
    pixels[i+3]   = pixel[3]

import PIL.Image
def make_wiper_images():
    try:
        master = bpy.data.images["master"]
    except KeyError:
        master = bpy.data.images.new("master", 1024, 1024, alpha=True)
        master.filepath = f"//textures/wiper_gradient.png"
    else:
        master.pixels[:] = [0.0] * len(master.pixels)
    master_array = array.array("f", master.pixels)
    width, height = master.size
    start =  0
    end = 250
    time_start = time.perf_counter()
    for i in range(start, end):
        print("i", i)
        loop_start = time.perf_counter()
        path = (f"//textures\wiper{i+1:04}.png")
        img = create_datablock_image_from_disk(path)

        width, height = img.size

        pixels = array.array("f", (img.pixels))
        print("something")

        for y in range(height-1, -1, -1):
            if y % 100 == 0:
                print("y", y)
            for x in range(0, width):
                #print("x", x)
                if start == 0:
                    pass #breakpoint()
                img_pixel = _get_pixel(pixels, x, y, width, height)
                if img_pixel[3] > 0:
                    #print(*img_pixel, f"@ ({x}, {y})")
                    m_pixel = _get_pixel(master.pixels, x, y, width, height)
                    red = i/end
                    _put_pixel(master_array, x, y, width, height, (red, *m_pixel[1:]))

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
        print("saved")
    return {"SUCCESS"}
