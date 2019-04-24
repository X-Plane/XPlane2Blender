'''
This module is the starting point for converting 2.49's
combined UV + Texture, Material TextureFace button hybrid
model to our Material + Material's Textures model

It is not named material_and_texture_converter because
there is no texture datablock or setting to convert and
our modern model is entirely material based.
'''

import re
from typing import Callable, Dict, List, Match, Optional, Tuple, Union, cast

import bpy
import mathutils
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers)
from io_xplane2blender.xplane_helpers import logger

def _get_mtface_flag(mesh:bpy.types.Mesh)->int:
    '''
    This giant method finds the MTFace* in DNA_mesh_types.h's Mesh struct,
    and returns the flag that will tell us the state of TEX, TILES, and LIGHT.
    '''
    return 0


def _has_TEX(flag:int)->bool:
    return bool(flag & (1 << 2)) # See "DNA_meshdata_type.h" TF_TEX


def _has_LIGHT(flag:int)->bool:
    return bool(flag & (1 << 4)) # See "DNA_meshdata_type.h" TF_LIGHT


def _has_TILES(flag:int)->bool:
    return bool(flag & (1 << 7)) # See "DNA_meshdata_type.h" TF_TILES


def convert_materials(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object)->List[bpy.types.Object]:
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    print([s.name for s in search_objs])

    #
    for search_obj in search_objs:
        print(search_obj.name)
        print("slots:", [s.name for s in search_obj.material_slots])
        for slot in search_obj.material_slots:
            mat = slot.material
            print("Convertering", mat.name)

            #-- TexFace Flags ------------------------------------------------
            # If True, it means this is semantically enabled for export
            # (which is important for TWOSIDE)
            TEX = _has_TEX(_get_mtface_flag(search_obj.data)) # type: bool
            PANEL = False # type: bool
            TILES = _has_TILES(_get_mtface_flag(search_obj.data)) # type: bool
            LIGHT = _has_LIGHT(_get_mtface_flag(search_obj.data)) # type: bool
            INVISIBLE = mat.game_settings.invisible # type: bool
            COLLISION = mat.game_settings.physics # type: bool
            TWOSIDE   = not mat.game_settings.use_backface_culling # type: bool
            SHADOW    = mat.game_settings.face_orientation == "SHADOW" # type: bool
            ALPHA     = mat.game_settings.alpha_blend == "ALPHA" # type: bool
            CLIP      = mat.game_settings.alpha_blend == "CLIP" # type: bool
            print(
"""
TEX:       {TEX}
PANEL:     {PANEL}
TILES:     {TILES}
LIGHT:     {LIGHT}
INVISIBLE: {INVISIBLE}
COLLISION: {COLLISION}
TWOSIDE:   {TWOSIDE}
SHADOW:    {SHADOW}
ALPHA:     {ALPHA}
CLIP:      {CLIP}
""".format(
        TEX=TEX,
        PANEL=PANEL,
        TILES=TILES,
        LIGHT=LIGHT,
        INVISIBLE=INVISIBLE,
        COLLISION=COLLISION,
        TWOSIDE=TWOSIDE,
        SHADOW=SHADOW,
        ALPHA=ALPHA,
        CLIP=CLIP,
    )
)

            #-----------------------------------------------------------------



"""
            if TEX:
                prop, _ = xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_shadow_blend", default=0.5)
                if prop:
                    mat.xplane.blend_mode = "shadow"
                else:
                    prop, _ = xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_shadow_blend", default=0.5)
                    if prop:
                        mat.xplane.blend_mode = "shadow" # Instanced Mode turns this into GLOBAL_
                    else:
                        mat.xplane.blend_mode = "blend"
                if f.transp == Mesh.FaceTranspModes.CLIP:
                    if xplane_249_helpers.find_property_in_parents(search_obj,'ATTR_no_blend'):
                        face.alpha=[Prim.TEST,round(float(get_prop(object,'ATTR_no_blend',0.5)),2)]
                    elif has_prop(object,'GLOBAL_no_blend'):
                        face.alpha=[Prim.TEST,round(float(get_prop(object,'GLOBAL_no_blend',0.5)),2)]
                    else:
                        face.alpha=[Prim.TEST,0.5]
"""

