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
    img_draped_filepaths = set()
    for obj in filter(lambda o: o.type == "MESH", search_objs):
        try:
            active_uv_textures = obj.data.uv_textures.active # type: Optional[bpy.types.MeshTexturePolyLayer]
            obj_filepaths = {meshtexpoly.image.filepath for meshtexpoly in active_uv_textures.data if "panel." not in meshtexpoly.image.name.lower()}
            # We can this assumption about material slots thanks to the material converter
            if obj.material_slots[0].material.xplane.draped:
                img_draped_filepaths.update(obj_filepaths)
            else:
                img_filepaths.update(obj_filepaths)
        except AttributeError: #active_uv_textures or data or image is None
            pass
        except UnicodeDecodeError:
            logger.warn("Due to an unknown bug in 2.79, an image datablock used in '{}''s UV Map '{}' could crash Blender!"
                         " Rename or retype it as soon as possible, preferably in 2.49"
                         .format(obj.name, active_uv_textures.name))

    def get_core_texture(filepaths:Set[str])->Tuple[str,str]:
        if not filepaths:
            raise Exception
        elif len(filepaths) == 1:
            if " " in os.path.split(bpy.path.abspath(list(filepaths)[0]))[1]:
                logger.warn("texture name has spaces in path")
                raise Exception
            else:
                filepath, dot, ext = list(filepaths)[0].rpartition(".")
                return (filepath, dot + ext)
        else:
            logger.warn("Found multiple textures paths for " + root_object.name + ": " + ''.join(filepaths))
            raise Exception

    def apply_texture_paths(filepaths:Set[str], is_draped:bool)->bool:
        try:
            filepath, ext = get_core_texture(filepaths)
        except Exception:
            pass
        else:
            if ext.lower() not in {".png", ".dds"}:
                logger.warn(ext + " is not a supported file type, skipping")
            elif not is_draped:
                root_object.xplane.layer.autodetectTextures = False
                root_object.xplane.layer.texture = filepath + ext

                if os.path.exists(bpy.path.abspath(filepath + "_NML.png")):
                    root_object.xplane.layer.texture_normal = filepath + "_NML.png"
                elif os.path.exists(bpy.path.abspath(filepath + "_NML.dds")):
                    root_object.xplane.layer.texture_normal = filepath + "_NML.dds"
                if os.path.exists(bpy.path.abspath(filepath + "_LIT.png")):
                    root_object.xplane.layer.texture_lit = filepath + "_LIT.png"
                elif os.path.exists(bpy.path.abspath(filepath + "_LIT.dds")):
                    root_object.xplane.layer.texture_lit = filepath + "_LIT.dds"
                return True
            else:
                root_object.xplane.layer.autodetectTextures = False
                root_object.xplane.layer.texture_draped = filepath + ext
                if os.path.exists(bpy.path.abspath(filepath + "_NML" + ext)):
                    root_object.xplane.layer.texture_draped_normal = filepath + "_NML" + ext
                return True
        return False

    applied_img_filepaths = apply_texture_paths(img_filepaths, False)
    applied_img_draped_filepaths = apply_texture_paths(img_draped_filepaths, True)

    if applied_img_filepaths or applied_img_draped_filepaths:
        logger.info("NEXT STEPS: Check the Texture Paths in the Root Object OBJ Settings for " + root_object.name)
