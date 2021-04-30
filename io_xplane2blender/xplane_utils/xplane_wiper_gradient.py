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


def _get_pixel(
    pixels: bpy.types.Image, x: int, y: int, width: int, height: int
) -> _Pixel:
    num_pixels = width * height
    i = 4 * (y * width + x)
    return list(pixels[i : i + 4])


def _put_pixel(
    pixels: bpy.types.Image, x: int, y: int, width: int, height: int, pixel: _Pixel
) -> None:
    i = 4 * (y * width + x)
    pixels[i] = pixel[0]
    pixels[i + 1] = pixel[1]
    pixels[i + 2] = pixel[2]
    pixels[i + 3] = pixel[3]


def make_wiper_images(
    img_paths: List[Path], master_width: int, master_height: int, master_filepath: Path
) -> Path:
    """
    Using a list of paths, make the channel oriented wiper_gradient_texture.png.
    Raises OSError is saving the texture has an issue.

    Paths must be less than 255 entries long (useful for debugging)

    master_width, master_height must match the dimensions of the images referenced
    by the paths.

    master_filepath is the absolute path of the final wiper gradient, filename must be
    'wiper_gradient_texture.png'

    These are passed by hand so we can do less work with image data blocks in here.
    """
    assert (
        len(img_paths) and len(img_paths) % 255 == 0
    ), f"{len(img_paths)} is not a multiple of 255"
    assert len(img_paths) <= (255 * 4), f"{len(img_paths)} is > {255*4}"

    try:
        bpy.data.images.remove(bpy.data.images[master_filepath.stem])
    except KeyError:
        pass
    finally:
        master_array = array.array(
            "f", (0.0 for _ in range(master_width * master_height * 4))
        )

    for i, path in enumerate(img_paths):
        step = (i % 255) + 1
        slot = int(path.name[path.name.rfind("slot") + 4])
        frame = int(path.name[path.name.rfind("_") + 1 : path.name.rfind("_") + 4])

        img = create_datablock_image_from_disk(path)
        pixels = array.array("f", img.pixels)

        for y in range(master_height - 1, -1, -1):
            for x in range(0, master_width):
                img_pixel = _get_pixel(pixels, x, y, master_width, master_height)
                if img_pixel[3] > 0:
                    m_pixel = _get_pixel(
                        master_array, x, y, master_width, master_height
                    )
                    m_pixel[slot - 1] = step / 255

                    _put_pixel(master_array, x, y, master_width, master_height, m_pixel)

        bpy.data.images.remove(img)
    try:
        master = bpy.data.images.new(
            master_filepath.stem, master_width, master_height, alpha=True
        )
        master.filepath = str(master_filepath)
        print("Saving", master.filepath)
        master.pixels[:] = master_array
        master.save()
        print("Saved")
    except OSError:
        raise
    else:
        bpy.data.images.remove(master)
