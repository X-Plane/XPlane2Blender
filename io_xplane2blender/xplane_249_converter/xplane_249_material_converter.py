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

    for search_obj in search_objs:
        print(search_obj.name)
        print("slots:", [s.name for s in search_obj.material_slots])
        for slot in search_obj.material_slots:
            mat = slot.material
            print("Convertering", mat.name)

            #-- TexFace Flags ------------------------------------------------
            # If True, it means this is semantically enabled for export
            # (which is important for TWOSIDE)
            # PANEL isn't a button but a fact that
            TEX = _has_TEX(_get_mtface_flag(search_obj.data)) or "tex" in search_obj.name # type: bool
            ISCOCKPIT = any(
                        [root_object.xplane.layer.name.lower().endswith(cockpit_suffix)
                         for cockpit_suffix in
                            ["_cockpit.obj",
                             "_cockpit_inn.obj",
                             "_cockpit_out.obj"]
                        ]
                    ) # type: bool
            ISPANEL = ISCOCKPIT # type: bool
            TILES = _has_TILES(_get_mtface_flag(search_obj.data)) or "tiles" in search_obj.name # type: bool, HACK
            LIGHT = _has_LIGHT(_get_mtface_flag(search_obj.data)) or "light" in search_obj.name # type: bool, HACK
            INVISIBLE = mat.game_settings.invisible # type: bool
            DYNAMIC   = not mat.game_settings.physics # type: bool
            TWOSIDE   = mat.game_settings.use_backface_culling # type: bool
            SHADOW    = mat.game_settings.face_orientation == "SHADOW" # type: bool
            ALPHA     = mat.game_settings.alpha_blend == "ALPHA" # type: bool
            CLIP      = mat.game_settings.alpha_blend == "CLIP" # type: bool
            print(
"""
TEX:       {TEX}
ISCOCKPIT  {ISCOCKPIT}
ISPANEL:   {ISPANEL}
TILES:     {TILES}
LIGHT:     {LIGHT}
INVISIBLE: {INVISIBLE}
DYNAMIC:   {DYNAMIC}
TWOSIDE:   {TWOSIDE}
SHADOW:    {SHADOW}
ALPHA:     {ALPHA}
CLIP:      {CLIP}
""".format(
        TEX=TEX,
        ISCOCKPIT=ISCOCKPIT,
        ISPANEL=ISPANEL,
        TILES=TILES,
        LIGHT=LIGHT,
        INVISIBLE=INVISIBLE,
        DYNAMIC=DYNAMIC, #AKA COLLISION
        TWOSIDE=TWOSIDE,
        SHADOW=SHADOW,
        ALPHA=ALPHA,
        CLIP=CLIP,
    )
)
            #---TEX----------------------------------------------------------
            #TODO: Can't capture yet
            if TEX:
                if ALPHA:
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_shadow_blend")):
                        mat.xplane.blend_v1000 = "shadow"
                        mat.xplane.blendRatio = 0.5
                        logger.info("{}: Blend Mode='Shadow' and Blend Ratio=0.5".format(mat.name))
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_shadow_blend")):
                        mat.xplane.blend_v1000 = "shadow"
                        mat.xplane.blendRatio = 0.5
                        root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                        logger.info("{}: Blend Mode='Shadow' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
                if CLIP:
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_no_blend")):
                        mat.xplane.blend_v1000 = "off"
                        mat.xplane.blendRatio = 0.5
                        logger.info("{}: Blend Mode='Off' and Blend Ratio=0.5".format(mat.name))
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_no_blend")):
                        mat.xplane.blend_v1000 = "off"
                        mat.xplane.blendRatio = 0.5
                        root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                        logger.info("{}: Blend Mode='Off' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
            #TODO: Haven't done panels yet
            if TEX and ISPANEL:
                pass

            if TEX and (not (TILES or LIGHT)) and ISCOCKPIT:
                mat.xplane.poly_os = 2
                logger.info("{}: Poly Offset=2".format(mat.name))

            #-----------------------------------------------------------------
            #---TILES/LIGHT---------------------------------------------------
            #TODO: Can't capture yet
            if ((TILES
                or LIGHT)
                and xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_draped")):
                mat.xplane.draped = True
                logger.info("{}: Draped=True".format(mat.name))

            #---INVISIBLE-----------------------------------------------------
            if INVISIBLE:
                mat.xplane.draw = False
                logger.info("{}: Draw Linked Objects=False".format(mat.name))
            #-----------------------------------------------------------------

            #---DYNAMIC-------------------------------------------------------
            if not INVISIBLE and not ISCOCKPIT and DYNAMIC: #TODO: And """not self.iscockpit"""
                mat.xplane.solid_camera = True
                logger.info("{}: Solid Camera=True".format(mat.name))
            #-----------------------------------------------------------------

            #---TWOSIDE-------------------------------------------------------
            if TWOSIDE:
                logger.info("{}: Two Sided deprecated, skipping".format(mat.name))
                pass
            #-----------------------------------------------------------------

            #---SHADOW--------------------------------------------------------
            if SHADOW:
                #TODO: Implement Shadow mat.xplane.shadow = True
                #logger.info("{}: Shadow=True".format(mat.name))
                logger.info("{}: ATTR_shadow not yet implemented, skipping".format(mat.name))
            #-----------------------------------------------------------------

