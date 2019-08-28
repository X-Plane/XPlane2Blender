"""
This contains the texture autodetect algorithm that mimics 2.49's
texture autodetection algorithm. There are some slight differences:
everything is a warning, not an error, and we don't look at custom
light's material's texture slot's image's path because it is bugged
and too few people (we know of) use that feature to make it worth
while

It depends on all materials being converted before hand so we can
detect if Draped Textures should be taken
"""

import os
import bpy
from typing import List, Set, Tuple
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_helpers)


def convert_textures(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object):
    """
    Converts OBJ Texture Path information from being stored in UV/Image Editor
    to being in (currently) the Root Object's Texture Path properties

    Must be run after material conversion!
    """
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    img_filepaths = set()
    draped_img_filepaths = set()
    for obj in filter(lambda o: o.type == "MESH", search_objs):
        try:
            active_uv_textures = obj.data.uv_textures.active # type: Optional[bpy.types.MeshTexturePolyLayer]
            obj_filepaths = {meshtexpoly.image.filepath for meshtexpoly in active_uv_textures.data if "panel." not in meshtexpoly.image.name.lower()}
            # We can this assumption about material slots thanks to the material converter
            if obj.material_slots[0].material.xplane.draped:
                draped_img_filepaths.update(obj_filepaths)
            else:
                img_filepaths.update(obj_filepaths)
        except AttributeError: #uv_textures is None
            pass

    def get_single_path(set_of_paths:Set[str])->Tuple[str,str]:
        if not set_of_paths:
            raise Exception
        elif len(set_of_paths) == 1:
            if " " in os.path.split(bpy.path.abspath(list(img_filepaths)[0]))[1]:
                logger.warn("texture name has spaces in path")
                raise Exception
            else:
                filepath, dot, ext = list(set_of_paths)[0].rpartition(".")
                return (filepath, dot + ext)
        else:
            logger.warn("Found multiple textures paths for " + root_object.name + ": " + ''.join(set_of_paths))
            raise Exception

    try:
        img_filepath, ext = get_single_path(img_filepaths)
    except Exception:
        pass
    else:
        if ext.lower() not in {".png", ".dds"}:
            logger.warn(ext + " is not a supported file type, skipping")
        else:
            root_object.xplane.layer.autodetectTextures = False
            root_object.xplane.layer.texture = img_filepath + ext
            if os.path.exists(bpy.path.abspath(img_filepath + "_NML" + ext)):
                root_object.xplane.layer.texture_normal = img_filepath + "_NML" + ext
            if os.path.exists(bpy.path.abspath(img_filepath + "_LIT" + ext)):
                root_object.xplane.layer.texture_lit = img_filepath + "_LIT" + ext

    try:
        import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev.core_7.2.1.201904261721\pysrc')
        draped_img_filepath, draped_ext = get_single_path(draped_img_filepaths)
    except Exception:
        pass
    else:
        if ext.lower() not in {".png", ".dds"}:
            logger.warn(ext + " is not a supported file type, skipping")
        else:
            root_object.xplane.layer.autodetectTextures = False
            root_object.xplane.layer.texture_draped = draped_img_filepath + ext
            if os.path.exists(bpy.path.abspath(draped_img_filepath + "_NML" + ext)):
                root_object.xplane.layer.texture_draped_normal = draped_img_filepath + "_NML" + ext
