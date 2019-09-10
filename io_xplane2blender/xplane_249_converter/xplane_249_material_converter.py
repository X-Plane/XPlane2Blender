"""
This module is the starting point for converting 2.49's
combined UV + Texture, Material TextureFace button hybrid
model to our Material + Material's Textures model

It is not named material_and_texture_converter because
there is no texture datablock or setting to convert and
our modern model is entirely material based.
"""

import collections
import functools
import itertools
import re
import sys

import bmesh
import bpy
import ctypes
import mathutils
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers)
from io_xplane2blender.xplane_helpers import logger
from typing import (Any, Callable, Dict, List, Match, Optional,
                    Set, Tuple, Union, cast)

# The members, and any collection of dealing with these things,
# they are in the order that 2.49's interface presents them in.
# An arbitrary choice had to be made, this is it.

# True when pressed (we interpret what that means later)
_TexFaceModes = collections.namedtuple(
        "_TexFaceModes",
        ["TEX",
         "TILES",
         "LIGHT",
         "INVISIBLE",
         "DYNAMIC", # This is pressed by default, unlike the others (also, called "Collision" in UI)
         "TWOSIDE",
         "SHADOW",
         "ALPHA",
         "CLIP"
         ]) # type: Tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool]


DEFAULT_TF_MODES = _TexFaceModes(
        TEX       = False,
        TILES     = False,
        LIGHT     = False,
        INVISIBLE = False,
        DYNAMIC   = True,
        TWOSIDE   = False,
        SHADOW    = False,
        ALPHA     = False,
        CLIP      = False)

_TexFaceModes.__repr__ = lambda self: ("DEFMODE" if self == DEFAULT_TF_MODES else " ".join(["{}={}".format(key, value) for (key, value) in self._asdict().items() if (key == "DYANMIC" and not value) or (key != "DYNAMIC" and value)]))
# The face ids of an Object's mesh, usually to keep or remove
FaceId = int
TFModeAndFaceIndexes = Dict[_TexFaceModes, Set[FaceId]]
def _get_tf_modes_from_ctypes(obj:bpy.types.Object)->Optional[TFModeAndFaceIndexes]:
    """
    Finds the information from MPoly* and MTexPoly* in DNA_mesh_types.h's Mesh struct,
    and returns a dictionary of pressed states and all polygon indexes that share it.

    It is garunteed to cover every polygon index in the mesh.

    Returns None if the mesh was not unwrapped, or it had other trouble
    """
    assert obj.type == "MESH", obj.name + " is not a MESH type"
    import sys

    def repr_all(self, include_attrs: Optional[Set[str]]=None)->str:
        """
        A general purpose __repr__ for all attributes in a ctypes.Structure,
        or if specified, only a subset of them
        """
        if not include_attrs:
            include_attrs = {}

        s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
        return s.format(**{
            key:getattr(self, key)
            for key, ctype in filter(lambda k: k in include_attrs, self._fields_)})

    class ID(ctypes.Structure):
        pass

        def __repr__(self):
            return repr_all(self, {"name"})

    ID._fields_ = [
                ("next",       ctypes.c_void_p), # void*
                ("prev",       ctypes.c_void_p), # void*
                ("newid",      ctypes.POINTER(ID)), # ID*
                ("lib",        ctypes.c_void_p), # Library*
                ("name",       ctypes.c_char * 66), # char [66]
                ("flag",       ctypes.c_short),
                ("tag",        ctypes.c_short),
                ("pad_s1",     ctypes.c_short),
                ("us",         ctypes.c_int),
                ("icon_id",    ctypes.c_int),
                ("properties", ctypes.c_void_p) # IDProperty *
            ]

    # /* new face structure, replaces MFace, which is now only used for storing tessellations.*/
    class MPoly(ctypes.Structure):
        _fields_ = [
                #/* offset into loop array and number of loops in the face */
                ("loopstart", ctypes.c_int),
                ("totloop",   ctypes.c_int), # /* keep signed since we need to subtract when getting the previous loop */
                ("mat_nr", ctypes.c_short), # We can use this to interact with Mesh.mat, to get a Material *. 0 is no material?
                ("flag", ctypes.c_char),
                ("pad", ctypes.c_char),
            ]

        def __repr__(self):
            return repr_all(self, {"loopstart", "totloop", "mat_nr"})

    class MTexPoly(ctypes.Structure):
        _fields_ = [
                ("tpage", ctypes.c_void_p), # Image *
                ("flag",  ctypes.c_char),
                ("transp", ctypes.c_char), # Also this!
                ("mode",   ctypes.c_short), # THIS IS WHAT IT HAS ALL BEEN ABOUT! RIGHT HERE!
                ("tile",   ctypes.c_short),
                ("pad",    ctypes.c_short)
            ]

        def __repr__(self):
            return repr_all(self, {"transp", "mode"})

    class CustomData(ctypes.Structure):
        _fields_ = [
            ("layers",   ctypes.c_void_p),   # CustomDataLayer *      /* CustomDataLayers, ordered by type */
            ("typemap",  ctypes.c_int * 42), # /* runtime only! - maps types to indices of first layer of that type,
                                             #  * MUST be >= CD_NUMTYPES, but we cant use a define here.
                                             #  * Correct size is ensured in CustomData_update_typemap assert() */
            ("pad_i1",   ctypes.c_int),
            ("totlayer", ctypes.c_int),
            ("maxlayer", ctypes.c_int),    # /* number of layers, size of layers array */
            ("totsize",  ctypes.c_int),    # /* in editmode, total size of all data layers */
            ("pool",     ctypes.c_void_p), # BLI_mempool *     /* (BMesh Only): Memory pool for allocation of blocks */
            ("external", ctypes.c_void_p), # CustomDataExternal * /* external file storing customdata layers */
        ]

    class Mesh(ctypes.Structure):
        _fields_ = [
            ('id', ID),
            ('adt', ctypes.c_void_p), # AnimData *
            ('bb',  ctypes.c_void_p), # BoundBox *
            ('ipo', ctypes.c_void_p), #Ipo * (deprecated)
            ('key', ctypes.c_void_p), #Key *
            ('mat', ctypes.c_void_p), # Material **
            ('mselect',  ctypes.c_void_p), # MSelect *
            ('mpoly',    ctypes.POINTER(MPoly)), #MPoly *
            ('mtpoly',   ctypes.POINTER(MTexPoly)), #MTexPoly *, THIS IS WHAT WE'VE BEEN FIGHTING FOR!!!
            ("mloop",    ctypes.c_void_p), # MLoop *
            ("mloopuv",  ctypes.c_void_p), # MLoopUV *
            ("mloopcol", ctypes.c_void_p), # MLoopCol *

            # /* mface stores the tessellation (triangulation) of the mesh,
            # * real faces are now stored in nface.*/
            ("mface",  ctypes.c_void_p), # MFace *  /* array of mesh object mode faces for tessellation */
            ("mtface", ctypes.c_void_p), # MTFace * /* store tessellation face UV's and texture here */
            ("tface",  ctypes.c_void_p), # TFace *  /* deprecated, use mtface */
            ("mvert",  ctypes.c_void_p), # MVert *  /* array of verts */
            ("medge",  ctypes.c_void_p), # MEdge *  /* array of edges */
            ("dvert",  ctypes.c_void_p), # MDeformVert * /* deformgroup vertices */

            #/* array of colors for the tessellated faces, must be number of tessellated
            # * faces * 4 in length */
            ("mcol",      ctypes.c_void_p), # MCol *
            ("texcomesh", ctypes.c_void_p), # Mesh *

            #/* When the object is available, the preferred access method is: BKE_editmesh_from_object(ob) */
            ("edit_btmesh", ctypes.c_void_p), # BMEditMesh * /* not saved in file! */

            ("vdata", CustomData), # CustomData is CD_MVERT
            ("edata", CustomData), # CustomData is CD_MEDGE
            ("fdata", CustomData), # CustomData is CD_MFACE

        #/* BMESH ONLY */
            ("pdata", CustomData), # CustomData is CD_MPOLY
            ("ldata", CustomData), # CustomData is CD_MLOOP
        #/* END BMESH ONLY */

            ("totvert",   ctypes.c_int), # Applies to length of mvert
            ("totedge",   ctypes.c_int), # Applies to length of medge
            ("totface",   ctypes.c_int), # Applies to length of mface
            ("totselect", ctypes.c_int),

        #/* BMESH ONLY */
            ("totpoly", ctypes.c_int), # Applies to length of mpoly
            ("totloop", ctypes.c_int), # Applies to length of mloop
        #/* END BMESH ONLY */

            #/* the last selected vertex/edge/face are used for the active face however
            # * this means the active face must always be selected, this is to keep track
            # * of the last selected face and is similar to the old active face flag where
            # * the face does not need to be selected, -1 is inactive */
            ("act_face", ctypes.c_int),

            #/* texture space, copied as one block in editobject.c */
            ("loc",  ctypes.c_float * 3),
            ("size", ctypes.c_float * 3),
            ("rot",  ctypes.c_float * 3),

            ("drawflag",   ctypes.c_int),
            ("texflag",    ctypes.c_short),
            ("flag",       ctypes.c_int),
            ("smoothresh", ctypes.c_float),
            ("pad2",       ctypes.c_int),

            #/* customdata flag, for bevel-weight and crease, which are now optional */
            ("cd_flag", ctypes.c_char),
            ("pad",     ctypes.c_char),

            ("subdiv",      ctypes.c_char),
            ("subdivr",     ctypes.c_char),
            ("subsurftype", ctypes.c_char), #/* only kept for ("compat",ctypes.c_backwards), not used anymore */
            ("editflag",    ctypes.c_char),

            ("totcol", ctypes.c_short),

            ("mr", ctypes.c_void_p), # Multires * DNA_DEPRECATED /* deprecated multiresolution modeling data, only keep for loading old files */
        ]

        def __repr__(self):
            return repr_all(self, {"id", "mpoly", "mtpoly", "totpoly"})

    try:
        poly_c_info = collections.defaultdict(set) # type: TFModeAndFaceIndexes
        mesh = Mesh.from_address(obj.data.as_pointer())
        mpolys  = mesh.mpoly[:mesh.totpoly]
        mtpolys = mesh.mtpoly[:mesh.totpoly]
        #print(mpolys)
        #print(mtpolys)
        for idx, (mpoly_current, mtpoly_current) in enumerate(zip(mpolys, mtpolys)):
            mtpoly_mode = mtpoly_current.mode
            mtpoly_transp = int.from_bytes(mtpoly_current.transp, sys.byteorder)
            #print("mtpoly_mode", "mypoly_transp", mtpoly_mode, mtpoly_transp)
            tf_modes = _TexFaceModes(
                            # From DNA_meshdata_types.h, lines 477-495
                            TEX       = bool(mtpoly_mode & (1 << 2)),
                            TILES     = bool(mtpoly_mode & (1 << 7)),
                            LIGHT     = bool(mtpoly_mode & (1 << 4)),
                            INVISIBLE = bool(mtpoly_mode & (1 << 10)),
                            DYNAMIC   = bool(mtpoly_mode & (1 << 0)),
                            TWOSIDE   = bool(mtpoly_mode & (1 << 9)),
                            SHADOW    = bool(mtpoly_mode & (1 << 13)),
                            # From DNA_meshdata_types.h, lines 502-503
                            ALPHA     = bool(mtpoly_transp & (1 << 1)),
                            CLIP      = bool(mtpoly_transp & (1 << 2)),
                        )

            poly_c_info[tf_modes].add(idx)
    except ValueError as ve: #NULL Pointer access
        pass
        #print("VE:", ve, obj.name)
    except KeyError as ke: #That weird 'loopstart' not found in __repr__ call...
        pass
        #print("KE:", ke, obj.name)
    except SystemError as se: # <class 'zip'> returned a result with an error set
        pass
        #print("SE:", se, obj.name)
    except Exception as e:
        pass
        #print("E:", e, obj.name)
    else:
        return poly_c_info

    return None

def _convert_material(scene: bpy.types.Scene,
                      root_object: bpy.types.Object,
                      search_obj: bpy.types.Object,
                      is_cockpit: bool,
                      is_panel: bool,
                      tf_modes: _TexFaceModes,
                      mat: bpy.types.Material)->Optional[bpy.types.Material]:
    """
    Attempts to convert TexFace, game prop, and material data
    to produce or return an existing unique derivative.

    scene - The current scene TODO: remove unused paramater
    root_object - Changes Export Type hint
    search_obj - Used to search for game properties
    is_cockpit - Used for lookup
    tf_modes - For turning button presses into props
    mat - The material referenced by search_obj's i-th slot's material (where i is the face's material index)

    Returns None if there was nothing to convert
    """
    print("Attempting to convert", mat.name)

    original_material_values = {
            attr:getattr(mat.xplane, attr) for attr in [
                "blend_v1000",
                "draped",
                "draw", #TexFace and Game Prop
                "lightLevel",
                "lightLevel_v1",
                "lightLevel_v2",
                "lightLevel_dataref",
                "panel",
                "poly_os",
                "solid_camera", #TexFace and Game Prop
                "shadow_local",
                ]
            }

    # For debugging purposes
    #original_material_values.update({attr:getattr(mat, attr) for attr in ["diffuse_color", "specular_intensity"]})
    changed_material_values = original_material_values.copy()
    changed_material_values["panel"] = is_panel
    logger_info_msgs = [] # type: List[str]
    logger_warn_msgs = [] # type: List[str]
    # This section roughly mirrors the order in which 2.49 deals with these face buttons
    #---TEX----------------------------------------------------------
    if tf_modes.TEX:
        def attempt_conversion_to_float(prop_name:str)->Tuple[Any,Any]:
            prop_value, prop_source = xplane_249_helpers.find_property_in_parents(search_obj, prop_name)
            try:
                prop_value = float(prop_value)
            except (TypeError, ValueError):
                # Slightly pedantic, but only a bad float or None found on a real found object
                # shows we have a real problem
                if prop_source:
                    logger.warn("{} found, but could not convert '{}' to a float".format(prop_name, prop_value))
                return (None, None)
            else:
                return (prop_value, prop_source)

        if tf_modes.ALPHA:
            attr_shadow_blend = attempt_conversion_to_float("ATTR_shadow_blend")
            global_shadow_blend = attempt_conversion_to_float("GLOBAL_shadow_blend")
            if attr_shadow_blend[1]:
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_SHADOW
                changed_material_values["blendRatio"] = round(attr_shadow_blend[0],2)
                logger_info_msgs.append("{}: Blend Mode='Shadow' and Blend Ratio={}".format(mat.name, attr_shadow_blend[0]))
            elif global_shadow_blend[1]:
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_SHADOW
                changed_material_values["blendRatio"] = round(global_shadow_blend[0],2)
                root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                logger_info_msgs.append("{}: Blend Mode='Shadow' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
            else:
                logger_warn_msgs.append("'Tex' and 'Alpha' buttons pressed, but no 'ATTR_/GLOBAL_shadow_blend' game property given. Did you forget something?")
        elif tf_modes.CLIP:
            attr_no_blend = attempt_conversion_to_float("ATTR_no_blend")
            global_no_blend = attempt_conversion_to_float("GLOBAL_no_blend")
            if attr_no_blend[1]:
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_OFF
                changed_material_values["blendRatio"] = round(attr_no_blend[0], 2)
                logger_info_msgs.append("{}: Blend Mode='Off' and Blend Ratio=0.5".format(mat.name))
            elif global_no_blend[1]:
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_OFF
                changed_material_values["blendRatio"] = round(global_no_blend[0], 2)
                root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                logger_info_msgs.append("{}: Blend Mode='Off' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
            else:
                logger_warn_msgs.append("'Tex' and 'Clip' buttons pressed, but no 'ATTR_/GLOBAL_no_blend' game property given. Did you forget something?")
    #-----------------------------------------------------------------

    #---TILES/LIGHT---------------------------------------------------
    # Yes! This is not 2.49's code, but it is what 2.49 produces!
    if not is_cockpit and (tf_modes.TILES or tf_modes.LIGHT):
        if xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_draped")[1]:
            changed_material_values["draped"] = True
            logger_info_msgs.append("{}: Draped={}".format(mat.name, changed_material_values["draped"]))
        else:
            changed_material_values["poly_os"] = 2
            logger_info_msgs.append("{}: Poly Offset={}".format(mat.name, changed_material_values["poly_os"]))
    #-----------------------------------------------------------------

    #---INVISIBLE-----------------------------------------------------
    draw_disable_by_texface = tf_modes.INVISIBLE
    draw_disable_by_prop = bool(xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_draw_disable")[1])
    if draw_disable_by_texface or draw_disable_by_prop:
        changed_material_values["draw"] = False
        logger_info_msgs.append("{}: Draw Objects With This Material={}".format(mat.name, changed_material_values["draw"]))
    #-----------------------------------------------------------------

    #---DYNAMIC-------------------------------------------------------
    solid_cam_by_texface = not any((tf_modes.INVISIBLE, is_cockpit, tf_modes.DYNAMIC))
    solid_cam_by_prop = bool(xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_solid_camera")[1])
    if (solid_cam_by_texface or solid_cam_by_prop):
        changed_material_values["solid_camera"] = True
        logger_info_msgs.append("{}: Solid Camera={}".format(mat.name, changed_material_values["solid_camera"]))
    #-----------------------------------------------------------------

    #---TWOSIDE-------------------------------------------------------
    if tf_modes.TWOSIDE:
        logger_warn_msgs.append("{}: Two Sided is deprecated, skipping".format(mat.name))
    #-----------------------------------------------------------------

    #---SHADOW--------------------------------------------------------
    changed_material_values["shadow_local"] = not tf_modes.SHADOW
    if not changed_material_values["shadow_local"]:
        logger_info_msgs.append("{}: Cast Shadow (Local)={}".format(mat.name, changed_material_values["shadow_local"]))
    #-----------------------------------------------------------------

    #---Lit Level-----------------------------------------------------
    #lit_level is the whole data for v1, v2, dataref
    lit_level = str(xplane_249_helpers.find_property_in_parents(search_obj, "lit_level", default="")[0]).strip()
    #ATTR_light_level could be just the dataref or the v1, v2, dataref
    ATTR_light_level    = str(xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_light_level", default="")[0]).strip()
    # TODO: beware - this could be semantically wrong - if ATTR_light_level_v1/2 was not found in 249, it didn't get a value! Right?
    ATTR_light_level_v1 = str(xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_light_level_v1", default=0.0)[0])
    ATTR_light_level_v2 = str(xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_light_level_v2", default=1.0)[0])

    lightLevel_v1, lightLevel_v2, lightLevel_dataref = ("", "", "")

    #Why this complicated logic? It mirrors how 2.49 would allow ATTR_light_level to override lit_level
    if lit_level:
        try:
            lightLevel_v1, lightLevel_v2, lightLevel_dataref = lit_level.split()
        except ValueError: # Too few or too many args
            logger.warn("Game property `{}`:'{}', had too many or too few arguments".format("lit_level", lit_level))

    if len(ATTR_light_level.split()) == 3:
        try:
            lightLevel_v1, lightLevel_v2, lightLevel_dataref = ATTR_light_level.split()
        except ValueError: # Too few or too many args
            logger.warn("Game property `{}`:'{}', had too many or too few arguments".format("ATTR_light_level", ATTR_light_level))
    elif ATTR_light_level:
        lightLevel_v1, lightLevel_v2, lightLevel_dataref = ATTR_light_level_v1, ATTR_light_level_v2, ATTR_light_level

    if all((lightLevel_v1, lightLevel_v2, lightLevel_dataref)):
        try:
            v1 = float(lightLevel_v1)
        except (ValueError, TypeError):
            logger.warn("Light Level v1 value could not convert to float: {}".format(lightLevel_v1))
        else:
            try:
                v2 = float(lightLevel_v2)
            except (ValueError, TypeError):
                logger.warn("Light Level v2 value could not convert to float: {}".format(lightLevel_v2))
            else:
                # Only after all the data is converted and convertable do we actually commit to changing this
                changed_material_values["lightLevel"] = True
                changed_material_values["lightLevel_v1"] = v1
                changed_material_values["lightLevel_v2"] = v2
                changed_material_values["lightLevel_dataref"] = lightLevel_dataref
    #-----------------------------------------------------------------

    #TODO: Deck
    #deck = bool(xplane_249_helpers.find_property_in_parents(search_obj, "deck", default=0)[0]) and surfaceType != NONE #TODO That is how it works in 2.78, maybe different
    if changed_material_values != original_material_values:
        for msg in logger_info_msgs:
            logger.info(msg)
        for msg in logger_warn_msgs:
            logger.warn(msg)
        # Here we ask "What Face Buttons really did end up mattering?" and make
        # a short name to hint the user as to what happened.
        # !!! THIS IS NOT JUST FOR READABILITY!!!
        # We use the key-name for bpy.data.materials to re-use materials and limit new data creation
        ov = original_material_values
        cv = changed_material_values
        #round_tuple = lambda t, ndigits=3: tuple(round(n, ndigits) for n in t)
        cmp_cv_ov = lambda key: cv[key] != ov[key]
        xp249c = xplane_249_constants
        # Join a list of only the relavent hint suffixes
        hint_suffix = "_" + "_".join(filter(None, (
            (xp249c.HINT_UV_PANEL if is_panel else ""),
            ("%s_%s" % (xplane_249_constants.HINT_TF_TEX, {"off":"CLIP", "shadow":"ALPHA"}[cv["blend_v1000"]])
                if cmp_cv_ov("blend_v1000") else ""),

            (xp249c.HINT_TF_TILES if tf_modes.TILES and (cmp_cv_ov("draped") or cmp_cv_ov("poly_os")) else ""),
            (xp249c.HINT_TF_LIGHT if tf_modes.LIGHT and (cmp_cv_ov("draped") or cmp_cv_ov("poly_os")) else ""),

            (xp249c.HINT_TF_INVIS          if draw_disable_by_texface and cmp_cv_ov("draw") else ""),
            (xp249c.HINT_PROP_DRAW_DISABLE if draw_disable_by_prop    and cmp_cv_ov("draw") else ""),

            (xp249c.HINT_TF_COLL        if solid_cam_by_texface and cmp_cv_ov("solid_camera") else ""),
            (xp249c.HINT_PROP_SOLID_CAM if solid_cam_by_prop    and cmp_cv_ov("solid_camera") else ""),

            (xp249c.HINT_TF_SHADOW     if cmp_cv_ov("shadow_local") else ""),

            (xp249c.HINT_PROP_LIT_LEVEL if cmp_cv_ov("lightLevel") else ""),

            # Debugging only. Since we don't combine materials with the same diffuse or specularity,
            # we don't need to make it part of the lookup key
            #(",".join(str(n) for n in round_tuple(cv["diffuse_color"], ndigits=2)) if cv["diffuse_color"] != (0.8, 0.8, 0.8) else ""), # Don't add the default
            #(str(round(cv["specular_intensity"], 2)) if cv["specular_intensity"] != 0.5 else "") # Don't add the default
        )))

        #2.49's max name length is 21, so we have 42 characters to work with
        if len(mat.name + hint_suffix) > 63:
            logger.error(mat.name + hint_suffix, "is about to get truncated, potentially messing up a lot of stuff! Should should highly consider renaming them to be shorter and check if your TexFace buttons are correct")
            assert False

        #new_name is restricted to the max datablock name length, because we can't afford for these to get truncated
        new_name = (mat.name + hint_suffix)[:63] # Max datablock name length.

        if cmp_cv_ov("lightLevel"):
            # This is a "don't be too clever" moment
            # Assumptions:
            # - We will always make _LIT_LEVEL materials in the following sequence:
            # _LIT_LEVEL, _LIT_LEVEL1, _LIT_LEVEL2, ...
            # - LIT_LEVEL will always be last. If we get another like this, we'll have to get serious
            # about string munging
            cv_ll = (cv["lightLevel_v1"], cv["lightLevel_v2"], cv["lightLevel_dataref"])

            def get_ll_index(m:bpy.types.Material):
                """m is guaranteed to start with '249.*LIT_LEVEL'"""
                try:
                    return int(re.match("249.*" + xp249c.HINT_PROP_LIT_LEVEL + "(\d*)", m.name).group(1))
                except ValueError:
                    return 0

            i = 0
            sorted_ll_mats = sorted(filter(lambda m:m.name.startswith(new_name), bpy.data.materials), key=get_ll_index)
            for i, ll_mat in enumerate(sorted_ll_mats):
                # Re-use an existing material whenever possible
                if cv_ll == (ll_mat.xplane.lightLevel_v1, ll_mat.xplane.lightLevel_v2, ll_mat.xplane.lightLevel_dataref):
                    new_name = ll_mat.name
                    break
            else: #nobreak
                # If we if we have ll_mats
                if sorted_ll_mats:
                    # With a new name, we make a new derivative
                    new_name += str(i+1)
                else:
                    # This is our first ll_material, so don't add anything
                    pass

        if new_name in bpy.data.materials:
            new_material = bpy.data.materials[new_name]
        else:
            new_material = mat.copy()
            new_material.name = new_name
            for prop, value in changed_material_values.items():
                setattr(new_material.xplane, prop, value)

            print("Created new converted material:", new_material.name)

        return new_material
    else:
        print("Material '{}' had nothing to convert".format(mat.name))
        return None


def convert_materials(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object)->List[bpy.types.Object]:
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    ISCOCKPIT = any(
                [(root_object.xplane.layer.name.lower() + ".obj").endswith(cockpit_suffix)
                 for cockpit_suffix in
                    ["_cockpit.obj",
                     "_cockpit_inn.obj",
                     "_cockpit_out.obj"]
                ]
            ) # type: bool
    # Note: ISPANEL is not entirely dependent on ISCOCKPIT because of "panel_ok"
    # Its value is considered constant after the attempt to find "panel_ok"
    ISPANEL = ISCOCKPIT

    #--- Attempt to find all GLOBAL material attributes ----------------------
    # Dictionary of "GLOBAL_attr" to value, to be applied later
    global_mat_props = {} # type: Dict[str, Union[bool, float, Tuple[float, float]]]
    # I needed an OrderedSet with no external dependencies, so, here we are. Only the keys are used
    global_hint_suffix = collections.OrderedDict() # type: Dict[str,None]

    def check_for_prop(obj_name:str, props:str, prop_name:str, suffix:str, conversion_fn:Callable[[Any],float])->None:
        """
        If possible, gets the value of a prop_name from an obj's game properties and converts it to a float, appending the suffix.
        If not possible, gives a logger warning
        """
        nonlocal global_mat_props, global_hint_suffix
        try:
            global_mat_props[prop_name] = conversion_fn(props[prop_name.lower()].value)
            global_hint_suffix[suffix] = None
        except ValueError: #fn_if_found couldn't convert value to correct type
            logger.warn("{}'s '{}' property could not be converted to a float".format(obj_name, prop_name))
        except KeyError:
            pass
        except Exception:
            pass

    for obj in filter(lambda obj: obj.game.properties, scene.objects):
        props = {key.casefold():value for key, value in obj.game.properties.items()}
        # There are two look ups of "GLOBAL_no_blend", the global one and the TexFace dependent version
        # They are as far as I can see, identical:
        # - Case insenstive
        # - Not set unless the prop is known to exist, thereby never falling back to a default value
        # The rules for when one overrides the other seem to be esoteric/a matter of luck.
        # If a user is going to mix multiple GLOBAL_(no|shadow) properties, it is at their own risk
        # How this bug came to be, I don't know, but the converter is Bug-For-Bug as long as it exported in 2.49! Joy!
        check_for_prop(obj.name, props, "GLOBAL_no_blend", xplane_249_constants.HINT_GLOBAL_NO_BLEND, float)
        check_for_prop(obj.name, props, "GLOBAL_shadow_blend", xplane_249_constants.HINT_GLOBAL_SHADOW_BLEND, float)

        def specular_check(value:Any)->float:
            try:
                v = round(float(value),2)
            except ValueError:
                raise
            else:
                if v > 0.0:
                    return v
                else:
                    raise Exception
        check_for_prop(obj.name, props, "GLOBAL_specular", xplane_249_constants.HINT_GLOBAL_SPECULAR, specular_check)

        try:
            tint_prop = props["GLOBAL_tint".casefold()]
            if tint_prop.type != "STRING":
                logger.warn("{}'s GLOBAL_tint's property value '{}' is not a string".format(obj.name, props["GLOBAL_tint".casefold()].value))
                raise Exception
            else:
                tints_value = tuple(float(v) for v in props["GLOBAL_tint".casefold()].value.split())
                if len(tints_value) != 2:
                    raise ValueError
                global_mat_props["GLOBAL_tint"] = tints_value
                global_hint_suffix[xplane_249_constants.HINT_GLOBAL_TINT] = None
                #TODO: We need a logger call somehow to tell the user that tint has been set on some material
                #logger.info("Albedo tint and emissive tint has been set to .2 and .3 on all materials in root object")
                #etc for others
        except AttributeError: # 'non-str' object has no attribute 'split'
            logger.warn("{}'s GLOBAL_tint's property value '{}' is not a string".format(obj.name, props["GLOBAL_tint".casefold()]))
        except ValueError: # incorrect number of values to unpack or bad float conversion
            logger.warn("Could not convert {}'s GLOBAL_tint property could not be parsed to two floats")
        except (KeyError,Exception):
            pass
        if "panel_ok".casefold() in props:
            # We don't know at this point what materials should
            # be affected because we haven't examined faces,
            # so we simply mark to inspect that later on
            ISPANEL = True
        if "NORMAL_METALNESS".casefold() in props:
            global_mat_props["NORMAL_METALNESS"] = True
            global_hint_suffix[xplane_249_constants.HINT_GLOBAL_NORM_MET] = None
        elif "BLEND_GLASS".casefold() in props:
            global_mat_props["BLEND_GLASS"] = True
            global_hint_suffix[xplane_249_constants.HINT_GLOBAL_BLEND_GLASS] = None
    # Switch back to a tuple and no one realizes the dumb hack that was used
    global_hint_suffix = tuple(global_hint_suffix.keys())
    #-------------------------------------------------------------------------
    for search_obj in sorted(list(filter(lambda obj: obj.type == "MESH", search_objs)), key=lambda x: x.name):
        """
        This tests that:
            - Every Object ends with a Material, even if it is the 249_default Material
            - Blender's auto generated Materials are removed and replaced with the 249_default
            - Meshs are split according to their TexFace groups (including None or Collision Only), not Materials
            - Meshes are split only as much as needed
            - The relationship between a face and its Material's specularity and Diffuse/Emissive RGB* is preserved,
            even when splitting a mesh
            - Materials and material slots are created as little as possible and never deleted
            - During a split, the minimal amount of Materials are preserved

        * Why? Though deprecated, we shouldn't delete data. We should, in fact copy first instead of create and assign,
        but that is UX, not spec correctness.

        # Spec implications for algorithm
        In more detail this results in:
        """
        print("Converting materials for", search_obj.name)

        # Rules:
        # Every face is going to have a TexFace mode (even if we have to force it to be default)
        # Every face is going to have a material_index to a real material (even if we have to make a default for the 0 slot)
        #--- Get TexFace Modes and the faces that use them--------------------
        ############################################
        # DO NOT CHANGE THE MESH BEFORE THIS LINE! #
        ############################################
        # We do this at the top to limit anything that could affect the C data
        # "Pragmatic paranoia is a programmer's pal" - Somebody's abandoned programming blog
        #print("Before get TF modes")
        tf_modes_and_their_faces = _get_tf_modes_from_ctypes(search_obj) # type: TFModeAndFaceIndexes
        if not tf_modes_and_their_faces:
            tf_modes_and_their_faces = collections.defaultdict(set)
            tf_modes_and_their_faces[DEFAULT_TF_MODES] = {face.index for face in search_obj.data.polygons}
        faces_and_their_tf_modes = {face_id:modes for modes, face_ids in tf_modes_and_their_faces.items() for face_id in face_ids} # type: Dict[FaceID, _TexFaceModes]
        #print("faces_and_their_modes", faces_and_their_tf_modes)
        #print("After get TF modes")
        #----------------------------------------------------------------------

        #--- Prepare the Object's Material Slots ------------------------------
        def _try(fn: Callable[[],str], ret_on_except=""):
            try:
                return fn()
            except:
                return ""

        #print("Before Material Slots Prep (Slots):         ", ",".join([_try(lambda: slot.material.name) for slot in search_obj.material_slots if slot.link == "DATA"]))
        #print("Before Material Slots Prep (All Materials): ", ",".join([_try(lambda: mat.name) for mat in search_obj.data.materials]))
        #print()

        # Faces without a 2.49 material are given a default (#1, 2, 10, 12, 21)
        # All slots are filled something or the default so this is easier to reason with.
        if not search_obj.material_slots:
            search_obj.data.materials.append(None)

        for slot in search_obj.material_slots:
            # Auto-generated materials are replaced with Material_249_converter_default (#2, 12)
            # This still has the weird name and is the same as a DEFAULT_MATERIAL. No point
            # confusing the user
            if not slot.material or re.match("Material\.TF\.\d{1,5}", slot.material.name):
                # We'll need a material in every slot no matter what anyways, why not now and save us trouble
                # In addition, a face's material_index will never be None or less than 0,
                # when asking "what faces have a mat index of 0", the answer is automatically "all of them"
                slot.material = test_creation_helpers.get_material(xplane_249_constants.DEFAULT_MATERIAL_NAME)
                slot.material.specular_intensity = 0.0 # This was the default behavior in XPlane2Blender 2.49

            # After ensuring each slot has a material, we need to apply
            # the global hints to them, re-using existing materials as possible
            if global_mat_props:
                # GLOBAL_specular will only be applied to default materials,
                # if we're not about to apply it, we remove it from the hint suffix
                final_hint_suffix = list(global_hint_suffix)
                if ("GLOBAL_specular" in global_mat_props):
                    if (slot.material.name != xplane_249_constants.DEFAULT_MATERIAL_NAME):
                        final_hint_suffix.remove(xplane_249_constants.HINT_GLOBAL_SPECULAR)

                final_hint_suffix = "_" + "_".join(final_hint_suffix) if final_hint_suffix else ""
                if (slot.material.name + final_hint_suffix) not in bpy.data.materials:
                    oname = slot.material.name
                    slot.material = slot.material.copy()
                    slot.material.name = oname + final_hint_suffix
                elif (slot.material.name + final_hint_suffix) in bpy.data.materials:
                    slot.material = bpy.data.materials[slot.material.name + final_hint_suffix]

            # Now, finally, we actually apply those values to those properties
            for prop_name, prop_value in global_mat_props.items():
                if prop_name == "GLOBAL_no_blend":
                    slot.material.xplane.blend_v1000 = xplane_constants.BLEND_OFF
                    slot.material.xplane.blendRatio = prop_value
                elif prop_name == "GLOBAL_shadow_blend":
                    slot.material.xplane.blend_v1000 = xplane_constants.BLEND_SHADOW
                    #TODO: We'll be ready for when bug #426 is closed and fixed -Ted, 8/20/2019
                    slot.material.xplane.blendRatio = prop_value
                # GLOBAL_specular should only be applied to default materials. We use string matching
                # because that is what the hint_suffix system is all about. Yay...
                elif (prop_name == "GLOBAL_specular"):
                    if (re.match("^249.*_" + xplane_249_constants.HINT_GLOBAL_SPECULAR, slot.material.name)):
                        # Problem on `249_my_special_case`
                        # if anyone actually reports the issue they can change the name or
                        # I'll make a better solution
                        slot.material.specular_intensity = prop_value
                elif prop_name == "GLOBAL_tint":
                    slot.material.xplane.tint = True
                    slot.material.xplane.tint_albedo, slot.material.xplane.tint_emissive = prop_value
                elif prop_name == "NORMAL_METALNESS":
                    slot.material.xplane.normal_metalness = prop_value
                elif prop_name == "BLEND_GLASS":
                    slot.material.xplane.blend_glass = prop_value

        #print("After Material Slots Prep (Slots):         ", "".join([slot.material.name for slot in search_obj.material_slots if slot.link == "DATA"]))
        #print("After Material Slots Prep (All Materials): ", "".join([mat.name for mat in search_obj.data.materials]))
        #print()
        #----------------------------------------------------------------------

        # Unused materials aren't deleted (#19)

        #--- Get old materials and the faces that use them---------------------
        def get_materials_and_their_faces(search_obj: bpy.types.Object)->Dict[bpy.types.MaterialSlot, Set[FaceId]]:
            materials_and_their_faces = collections.defaultdict(set) # type: Dict[bpy.types.MaterialSlot, Set[FaceId]]
            for face in search_obj.data.polygons:
                materials_and_their_faces[search_obj.material_slots[face.material_index].material].add(face.index)
            return materials_and_their_faces

        materials_and_their_faces = get_materials_and_their_faces(search_obj)

        def get_panel_tex_faces(search_obj: bpy.types.Object)->Dict[bool,FaceId]:
            panel_tex_faces = collections.OrderedDict([(True,set()), (False,set())])
            if ISPANEL:
                try:
                    active_data = search_obj.data.uv_textures.active.data
                except AttributeError: # No active uv_textures, none active
                    panel_tex_faces[False] = set(face.index for face in search_obj.data.polygons)
                else:
                    for i, mtexpolylayer in enumerate(active_data):
                        if (mtexpolylayer.image and "panel." in mtexpolylayer.image.name.lower()
                            and faces_and_their_tf_modes[i].TEX):
                            panel_tex_faces[True].add(i)
                        else:
                            panel_tex_faces[False].add(i)
            else:
                panel_tex_faces[False] = set(face.index for face in search_obj.data.polygons)

            assert (len(panel_tex_faces[True]) + len(panel_tex_faces[False])) == len(search_obj.data.polygons)
            assert not (panel_tex_faces[True] & panel_tex_faces[False]) # assert the two lists have nothing in common
            return panel_tex_faces

        panel_states_and_their_faces = get_panel_tex_faces(search_obj)

        #--- Print FaceId related data structures for debugging ----------------
        #all_tf_faceids =       list(itertools.chain([face_ids for tf_modes, face_ids in tf_modes_and_their_faces.items()]))
        #all_material_faceids = list(itertools.chain([face_ids for tf_modes, face_ids in materials_and_their_faces.items()]))
        #print("TF FaceIds:", all_tf_faceids)
        #print("Material FaceIds:", all_material_faceids)
        # The debug version prints the file name and its face ids
        #def debug_get_panel_tex_faces(search_obj: bpy.types.Object)->Dict[str, FaceId]:
            #import os
            #panel_texs_and_their_faces = collections.defaultdict(set)
            #try:
                #active_data = search_obj.data.uv_textures.active.data
            #except AttributeError: # No active uv_textures, none active
                #return panel_texs_and_their_faces
            #else:
                #for i, mtexpolylayer in enumerate(active_data):
                    #if (mtexpolylayer.image and "panel." in mtexpolylayer.image.name.lower()):
                       #panel_texs_and_their_faces[mtexpolylayer.image.filepath].add(str(i) + " TEX? " + str(faces_and_their_tf_modes[i].TEX))

            #return panel_texs_and_their_faces

        #if debug_get_panel_tex_faces(search_obj):
            ## While debugging, we'll probably always have the first face have an image, right?
            #print("Panel Texs and FaceIds:", debug_get_panel_tex_faces(search_obj))
        #else:
            #print("No  Panel Texs and Faces")

        # Thanks to https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists/48569551#48569551
        #def flatten(l):
        #    for el in l:
        #        if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
        #            yield from flatten(el)
        #        else:
        #            yield el
        #assert sorted(flatten(all_tf_faceids)) == sorted(flatten(all_material_faceids)), "TF Face Ids and Material Face Ids must cover the same faces!"
        #assert len(list(flatten(all_tf_faceids))) == len(list(flatten(all_material_faceids))) == len(search_obj.data.polygons), "TF FaceIds, Material FaceIds must cover all of object's faces!"
               #len(itertools.chain([faces for tf_modes, face_ids in tf_modes_and_their_faces.items()]), "dicts should cover the same range of faces"
        #----------------------------------------------------------------------
        #----------------------------------------------------------------------
        print()

        # Split Groups Guarantees:
        # - List[FaceId], will never be Empty
        # - split_groups will eventually contain every FaceId, once
        # - At the end of getting groups, you will have a dictionary of materials to put in the first slot and face ids to keep when splitting the mesh
        split_groups = collections.OrderedDict() # type: Dict[bpy.types.Material, List[FaceId]]
        for tf_modes, t_face_ids in tf_modes_and_their_faces.items():
            for material, m_face_ids in materials_and_their_faces.items():
                for panel_state, p_face_ids in panel_states_and_their_faces.items():
                    cross_over_faces = t_face_ids & m_face_ids & p_face_ids
                    if cross_over_faces:
                        converted = _convert_material(scene,
                            root_object,
                            search_obj,
                            ISCOCKPIT,
                            panel_state, # At this point we know if we have panel_tex_faces, they're good to use
                            tf_modes,
                            material)
                        if not converted:
                            print("Didn't convert anything")
                            # Why extend on None?
                            # (TEX Pressed, MaterialA) and (TEX, ALPHA, and has "ATTR_shadow_blend", MaterialA)
                            # represent different semantic groups of FaceIds. What we really have is
                            # - (All combinations of meaningless buttons, MaterialA)
                            # - (TEX, ALPHA, and has "ATTR_shadow_blend", MaterialA)
                            # so for every combination of meaningless buttons, we combine their FaceIds
                            split_groups.setdefault(material, set()).update(cross_over_faces)
                        else:
                            split_groups[converted] = cross_over_faces
                    else:
                        print("No cross over for", tf_modes, "and", material.name, "and maybe texfaces", panel_state)

        #print("After Splitting (Slots):         ", "".join([slot.material.name for slot in search_obj.material_slots if slot.link == "DATA"]))
        #print("After Splitting (All Materials): ", "".join([mat.name for mat in search_obj.data.materials]))
        #print()
        #print("Split Groups", {mat.name:faces for mat, faces in split_groups.items()})

        new_objs = []
        if len(split_groups): #TODO: Dumb, split_groups will always be at least 1 because of DEF_MAT in place of no slot
            # The number of new meshes after a split should match its # of TF groups
            pre_split_obj_count = len(scene.objects)

            def copy_obj(obj: bpy.types.Object, name:str)->bpy.types.Object:
                """Makes a copy of obj and links it to the current scene"""
                new_obj = search_obj.copy()
                scene.objects.link(new_obj)
                new_mesh = search_obj.data.copy()
                new_obj.data = new_mesh
                new_obj.name = name
                return new_obj

            ##############################
            # The heart of this function #
            ##############################
            #--Beginning of Operation-----------------------
            # A mesh with <2 TF groups is unsplit
            if len(split_groups) > 1 and len(search_obj.data.polygons) > 1:
                for i, (material, face_ids) in enumerate(split_groups.items()):
                    new_obj = copy_obj(search_obj, search_obj.name + "_%d" % i)
                    new_objs.append(new_obj)
                    #print("New Obj: ", new_obj.name)
                    #print("New Mesh:", new_obj.data.name)
                    #print("Group:" , material.name)
                    # Remove faces
                    bm = bmesh.new()
                    bm.from_mesh(new_obj.data)
                    faces_to_keep   = [face for face in bm.faces if face.index in face_ids]
                    faces_to_remove = [face for face in bm.faces if face.index not in face_ids]
                    #print("Faces To Keep:  ", [f.index for f in faces_to_keep])
                    #print("Faces To Remove:", [f.index for f in faces_to_remove])
                    bmesh.ops.delete(bm, geom=faces_to_remove, context=5) #AKA DEL_ONLYFACES from bmesh_operator_api.h
                    bm.to_mesh(new_obj.data)
                    bm.free()

                    scene.objects.active = new_obj
                    #TODO: But what about `NoSplit` with Materials A, B, and C? What should go here?
                    #TODO: After split, number of Materials should only include what is needed
                    #TODO: What about slots [None, Material.TF.135]?
                    for i in range(len(scene.objects.active.material_slots)-1):
                        bpy.ops.object.material_slot_remove()
                    new_obj.material_slots[0].material = material
                else:
                    scene.objects.active = search_obj
                    new_obj = search_obj # TODO: Bad name
                logger.info("Split '{}' into {} groups".format(search_obj.name, len(split_groups)))
                print("Deleting " + search_obj.name)
                bpy.data.meshes.remove(search_obj.data, do_unlink=True)
                bpy.data.objects.remove(search_obj, do_unlink=True) # What about other work ahead of us to convert?
            else:
                # Case 1: Split group has a DEF_MAT, wasting time to assign, but its fine
                # Case 2: Split group has a converted_material, gotta have it!
                search_obj.material_slots[0].material = list(split_groups.keys())[0]
            #--End of Split Operation----------------------

            intended_count = pre_split_obj_count - 1 + len(split_groups)
            assert intended_count == len(scene.objects),\
                    "Object count (%d) should match pre_count -1 + # split groups (%d)" % (len(scene.objects), intended_count)
        else:
            new_objs = [search_obj.name]
