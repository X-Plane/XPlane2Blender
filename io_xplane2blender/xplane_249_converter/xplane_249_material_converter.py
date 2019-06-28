"""
This module is the starting point for converting 2.49's
combined UV + Texture, Material TextureFace button hybrid
model to our Material + Material's Textures model

It is not named material_and_texture_converter because
there is no texture datablock or setting to convert and
our modern model is entirely material based.
"""

import collections
import ctypes
import functools
import sys
import re
from typing import Callable, Dict, List, Match, Optional, Tuple, Union, cast

import bpy
import bmesh
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

# True when pressed (we interpret what that means later)
_CMembers = collections.namedtuple(
        "__CMembers",
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

_CMembers.__repr__ = lambda self: (
    "TEX={}, TILES={}, LIGHT={}, INVISIBLE={}, DYNAMIC={}, TWOSIDE={}, SHADOW={}, ALPHA={}, CLIP={}"
     .format(self.TEX, self.TILES, self.LIGHT, self.INVISIBLE, self.DYNAMIC, self.TWOSIDE, self.SHADOW, self.ALPHA, self.CLIP))


def _get_poly_struct_info(obj:bpy.types.Object)->Dict[_CMembers, int]:
    """
    This giant method finds the information from MPoly* and MTexPoly* in DNA_mesh_types.h's Mesh struct,
    and returns a dictionary of pressed states and all polygon indexes that share it

    If the mesh was not unwrapped, this throws a ValueError: NULL pointer access
    """
    assert obj.type == "MESH", obj.name + " is not a MESH type"
    import sys

    def repr_all(self):
        s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
        return s.format(**{key:getattr(self, key) for key, ctype in self._fields_})

    class ID(ctypes.Structure):
        pass

        def __repr__(self):
            return repr_all(self)

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

    class MTexPoly(ctypes.Structure):
        _fields_ = [
                ("tpage", ctypes.c_void_p), # Image *
                ("flag",  ctypes.c_char), # Also this!
                ("transp", ctypes.c_char),
                ("mode",   ctypes.c_short), # THIS IS WHAT IT HAS ALL BEEN ABOUT! RIGHT HERE!
                ("tile",   ctypes.c_short),
                ("pad",    ctypes.c_short)
            ]

        def __repr__(self):
            return repr_all(self)

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
            s = ("(" + " ".join((name + "={" + name + "}," for name, ctype in self._fields_)) + ")")
            return s.format(**{key:getattr(self, key) for key, ctype in self._fields_ if key in {"id","mtpoly"}})

    mesh = Mesh.from_address(obj.data.as_pointer())
    poly_c_info = collections.defaultdict(list) # type: Dict[_CMembers, List[int]]
    for idx, (mpoly_current, mtpoly_current) in enumerate(zip(mesh.mpoly[:mesh.totpoly], mesh.mtpoly[:mesh.totpoly])):
        mtpoly_mode = mtpoly_current.mode
        mtpoly_transp = int.from_bytes(mtpoly_current.transp, sys.byteorder)
        cmembers = _CMembers(
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

        poly_c_info[cmembers].append(idx)

    return poly_c_info

def convert_materials(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType, root_object: bpy.types.Object)->List[bpy.types.Object]:
    if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        search_objs = scene.objects
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        search_objs = [root_object] + xplane_249_helpers.get_all_children_recursive(root_object, scene)
    else:
        assert False, "Unknown workflow type"

    #scene.render.engine = 'BLENDER_GAME' # Only for testing purposes

    for search_obj in sorted(list(filter(lambda obj: obj.type == "MESH", search_objs)), key=lambda x: x.name):
        print("Converting materials for", search_obj.name)
        info = _get_poly_struct_info(search_obj)

        def copy_obj(obj):
            new_obj = search_obj.copy()
            scene.objects.link(new_obj)
            new_mesh = search_obj.data.copy()
            new_obj.data = new_mesh
            return new_obj

        info_more = {cmembers: (faces_idx, copy_obj(search_obj)) for cmembers, faces_idx in info.items()}
        print("Deleting " + search_obj.name)
        bpy.data.meshes.remove(search_obj.data)
        bpy.data.objects.remove(search_obj) # What about other work ahead of us to convert?
        for cmembers, (faceids, new_obj) in info_more.items():
            print("New Obj: ", new_obj.name)
            print("New Mesh:", new_obj.data.name)
            print("Group:" , cmembers)
            bm = bmesh.new()
            bm.from_mesh(new_obj.data)
            facesids_to_remove = [face for face in bm.faces if face.index not in faceids]
            print("Faces To Keep:  ", faceids)
            print("Faces To Remove:", [face.index for face in facesids_to_remove])
            bmesh.ops.delete(bm, geom=facesids_to_remove, context=5) #AKA DEL_ONLYFACES from bmesh_operator_api.h
            bm.to_mesh(new_obj.data)
            bm.free()

        continue

        #TODO: During split, what if Object already has a material?
        for slot in search_obj.material_slots:
            mat = slot.material
            print("Convertering", mat.name)

            #-- TexFace Flags ------------------------------------------------
            # If True, it means this is semantically enabled for export
            # (which is important for DYNAMIC)
            # PANEL isn't a button but a fact that
            ISCOCKPIT = any(
                        [(root_object.xplane.layer.name.lower() + ".obj").endswith(cockpit_suffix)
                         for cockpit_suffix in
                            ["_cockpit.obj",
                             "_cockpit_inn.obj",
                             "_cockpit_out.obj"]
                        ]
                    ) # type: bool
            ISPANEL = ISCOCKPIT # type: bool

            def print_data():
                print(
"""
           Button State
ISCOCKPIT: {ISCOCKPIT}
ISPANEL:   {ISPANEL}

TEX:       {TEX}
TILES:     {TILES}
LIGHT:     {LIGHT}
INVISIBLE: {INVISIBLE}
DYNAMIC:   {DYNAMIC}
TWOSIDE:   {TWOSIDE}
SHADOW:    {SHADOW}

ALPHA:     {ALPHA}
CLIP:      {CLIP}
""".format(
        ISCOCKPIT=ISCOCKPIT,
        ISPANEL=ISPANEL,

        TEX=mode.TEX,
        TILES=mode.TILES,
        LIGHT=mode.LIGHT,
        INVISIBLE=mode.INVISIBLE,

        DYNAMIC=mode.DYNAMIC, #AKA COLLISION
        TWOSIDE=mode.TWOSIDE,

        SHADOW=mode.SHADOW,

        ALPHA=mode_and_transp.ALPHA,
        CLIP=mode_and_transp.CLIP,
    )
)

            # This section roughly mirrors the order in which 2.49 deals with these face buttons
            #---TEX----------------------------------------------------------
            if mode_and_transp.TEX:
                if mode_and_transp.ALPHA:
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_shadow_blend")[1]):
                        mat.xplane.blend_v1000 = xplane_constants.BLEND_SHADOW
                        mat.xplane.blendRatio = 0.5
                        logger.info("{}: Blend Mode='Shadow' and Blend Ratio=0.5".format(mat.name))
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_shadow_blend")[1]):
                        mat.xplane.blend_v1000 = xplane_constants.BLEND_SHADOW
                        mat.xplane.blendRatio = 0.5
                        root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                        logger.info("{}: Blend Mode='Shadow' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
                if mode_and_transp.CLIP:
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_no_blend")[1]):
                        mat.xplane.blend_v1000 = xplane_constants.BLEND_OFF
                        mat.xplane.blendRatio = 0.5
                        logger.info("{}: Blend Mode='Off' and Blend Ratio=0.5".format(mat.name))
                    if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_no_blend")[1]):
                        mat.xplane.blend_v1000 = xplane_constants.BLEND_OFF
                        mat.xplane.blendRatio = 0.5
                        root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                        logger.info("{}: Blend Mode='Off' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))

            if mode_and_transp.TEX and (not (mode_and_transp.TILES or mode_and_transp.LIGHT)) and ISCOCKPIT:
                mat.xplane.poly_os = 2
                logger.info("{}: Poly Offset={}".format(mat.name, mat.xplane.poly_os))

            #-----------------------------------------------------------------

            #---TILES/LIGHT---------------------------------------------------
            if ((mode_and_transp.TILES
                or mode_and_transp.LIGHT)
                and xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_draped")[1]):
                    mat.xplane.draped = True
                    logger.info("{}: Draped={}".format(mat.name, mat.xplane.draped))
            #-----------------------------------------------------------------

            #---INVISIBLE-----------------------------------------------------
            if mode_and_transp.INVISIBLE:
                mat.xplane.draw = False
                logger.info("{}: Draw Objects With This Material={}".format(mat.name, mat.xplane.draw))
            #-----------------------------------------------------------------

            #---DYNAMIC-------------------------------------------------------
            if (not mode_and_transp.INVISIBLE
                and not ISCOCKPIT
                and not mode_and_transp.DYNAMIC):
                mat.xplane.solid_camera = True
                logger.info("{}: Solid Camera={}".format(mat.name, mat.xplane.solid_camera))
            #-----------------------------------------------------------------

            #---TWOSIDE-------------------------------------------------------
            if mode_and_transp.TWOSIDE:
                logger.warn("{}: Two Sided is deprecated, skipping".format(mat.name))
                pass
            #-----------------------------------------------------------------

            #---SHADOW--------------------------------------------------------
            mat.xplane.shadow_local = not mode_and_transp.SHADOW
            if not mat.xplane.shadow_local:
                logger.info("{}: Cast Shadow (Local)={}".format(mat.name, mat.xplane.shadow_local))
            #-----------------------------------------------------------------

