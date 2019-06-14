'''
This module is the starting point for converting 2.49's
combined UV + Texture, Material TextureFace button hybrid
model to our Material + Material's Textures model

It is not named material_and_texture_converter because
there is no texture datablock or setting to convert and
our modern model is entirely material based.
'''

import re
import collections
from typing import Callable, Dict, List, Match, Optional, Tuple, Union, cast

import bpy
import mathutils
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers)
from io_xplane2blender.xplane_helpers import logger

# The members, and any collection of dealing with these things,
# they are in the order that 2.49's interface presents them in.
# An arbitrary choice had to be made, this is it.
_ModeMembers = collections.namedtuple(
        "_ModeMembers",
        ["TEX",
         "TILES",
         "LIGHT",
         "INVISIBLE",
         "DYNAMIC", # aka not "DYNAMIC", since we care about it when it isn't two sided
         "TWOSIDE",
         "SHADOW",
        ])


def _get_mtpoly_mode(obj:bpy.types.Object)->_ModeMembers:
    '''
    This giant method finds the MTFace* in DNA_mesh_types.h's Mesh struct,
    and returns the mode that will tell us the state of TEX, TILES, and LIGHT.
    '''
    assert obj.type == "MESH", obj.name + " is not a MESH type"
    import ctypes
    class ID(ctypes.Structure):
        pass

        def __repr__(self):
            s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
            return s.format(**{key:getattr(self, key) for key, ctype in self._fields_})

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

    class MTexPoly(ctypes.Structure):
        _fields_ = [
                ("tpage", ctypes.c_void_p), # Image *
                ("flag",  ctypes.c_char),
                ("transp", ctypes.c_char),
                ("mode",   ctypes.c_short), # THIS IS WHAT IT HAS ALL BEEN ABOUT! RIGHT HERE!
                ("tile",   ctypes.c_short),
                ("pad",    ctypes.c_short)
            ]

        def __repr__(self):
            s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
            return s.format(**{key:getattr(self, key) for key, ctype in self._fields_})

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
            ('mpoly',    ctypes.c_void_p), #MPoly *
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

            ("vdata", CustomData),
            ("edata", CustomData),
            ("fdata", CustomData),

        #/* BMESH ONLY */
            ("pdata", CustomData),
            ("ldata", CustomData),
        #/* END BMESH ONLY */

            ("totvert",   ctypes.c_int),
            ("totedge",   ctypes.c_int),
            ("totface",   ctypes.c_int),
            ("totselect", ctypes.c_int),

        #/* BMESH ONLY */
            ("totpoly", ctypes.c_int),
            ("totloop", ctypes.c_int),
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
            s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
            return s.format(**{key:getattr(self, key) for key, ctype in self._fields_ if key in {"id","mtpoly"}})
    mode = Mesh.from_address(obj.data.as_pointer()).mtpoly.contents.mode
    return _ModeMembers(TEX       = bool(mode & (1 << 2)),
                        TILES     = bool(mode & (1 << 7)),
                        LIGHT     = bool(mode & (1 << 4)),
                        INVISIBLE = bool(mode & (1 << 10)),
                        DYNAMIC   = not bool(mode & (1 << 0)),
                        TWOSIDE   = bool(mode & (1 << 9)),
                        SHADOW    = bool(mode & (1 << 13))
                    )

def convert_materials(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object)->List[bpy.types.Object]:
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    print([s.name for s in search_objs])
    scene.render.engine = 'BLENDER_GAME'

    for search_obj in sorted(list(filter(lambda obj: obj.type == "MESH", search_objs)), key=lambda x: x.name):
        print(search_obj.name)
        print("slots:", [s.name for s in search_obj.material_slots])
        mode = _get_mtpoly_mode(search_obj)
        for slot in search_obj.material_slots:
            mat = slot.material
            print("Convertering", mat.name)

            #-- TexFace Flags ------------------------------------------------
            # If True, it means this is semantically enabled for export
            # (which is important for TWOSIDE)
            # PANEL isn't a button but a fact that
            ISCOCKPIT = any(
                        [root_object.xplane.layer.name.lower().endswith(cockpit_suffix)
                         for cockpit_suffix in
                            ["_cockpit.obj",
                             "_cockpit_inn.obj",
                             "_cockpit_out.obj"]
                        ]
                    ) # type: bool
            ISPANEL = ISCOCKPIT # type: bool
            TEX = "tex" in search_obj.name # type: bool
            TILES = "tiles" in search_obj.name # type: bool, HACK
            LIGHT = "light" in search_obj.name # type: bool, HACK
            INVISIBLE = mat.game_settings.invisible # type: bool
            DYNAMIC   = not mat.game_settings.physics # type: bool
            TWOSIDE   = mat.game_settings.use_backface_culling # type: bool
            SHADOW    = mat.game_settings.face_orientation == "SHADOW" # type: bool

            ALPHA     = mat.game_settings.alpha_blend == "ALPHA" # type: bool
            CLIP      = mat.game_settings.alpha_blend == "CLIP" # type: bool

            print(
"""
         Buttons| mode flag
ISCOCKPIT  {ISCOCKPIT}
ISPANEL:   {ISPANEL}
TEX:       {TEX},  {mTEX}
TILES:     {TILES},  {mTILES}
LIGHT:     {LIGHT},  {mLIGHT}
INVISIBLE: {INVISIBLE},  {mINVISIBLE}
DYNAMIC:   {DYNAMIC},  {mDYNAMIC}
TWOSIDE:   {TWOSIDE},  {mTWOSIDE}
SHADOW:    {SHADOW},  {mSHADOW}
ALPHA:     {ALPHA}
CLIP:      {CLIP}
""".format(
        ISCOCKPIT=ISCOCKPIT,
        ISPANEL=ISPANEL,
        TEX=TEX,
        TILES=TILES,
        LIGHT=LIGHT,
        INVISIBLE=INVISIBLE,

        mTEX=mode.TEX,
        mTILES=mode.TILES,
        mLIGHT=mode.LIGHT,
        mINVISIBLE=mode.INVISIBLE,

        DYNAMIC=DYNAMIC, #AKA COLLISION
        TWOSIDE=TWOSIDE,

        mDYNAMIC=mode.DYNAMIC, #AKA COLLISION
        mTWOSIDE=mode.TWOSIDE,

        SHADOW=SHADOW,
        mSHADOW=mode.SHADOW,

        ALPHA=ALPHA,
        CLIP=CLIP,
    )
)
            # This section roughly mirrors the order in which 2.49 deals with these face buttons
            #---TEX----------------------------------------------------------
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

