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
from typing import Callable, Dict, List, Match, Optional, Set, Tuple, Union, cast

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

_TexFaceModes.__repr__ = lambda self: ("".join(["{}={}".format(key, value) for (key, value) in self._asdict().items() if (key == "DYANMIC" and not value) or (key != "DYNAMIC" and value)]))

DEFAULT_TF_MODES = _TexFaceModes(
        TEX = False,
        TILES     = False,
        LIGHT     = False,
        INVISIBLE = False,
        DYNAMIC   = True,
        TWOSIDE   = False,
        SHADOW    = False,
        ALPHA     = False,
        CLIP      = False)

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
        for idx, (mpoly_current, mtpoly_current) in enumerate(zip(mesh.mpoly[:mesh.totpoly], mesh.mtpoly[:mesh.totpoly])):
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
        return poly_c_info
    except ValueError: #NULL Pointer access
        return None


def _convert_material(scene: bpy.types.Scene,
                      root_object: bpy.types.Object,
                      search_obj: bpy.types.Object,
                      is_cockpit: bool,
                      tf_modes: _TexFaceModes,
                      mat: bpy.types.Material):
    #TODO: During split, what if Object already has a material?
    print("Attempting to convert", mat.name)

    original_material_values = {
            attr:getattr(mat.xplane, attr) for attr in [
                "blend_v1000",
                "draped",
                "poly_os",
                "draw",
                "solid_camera",
                "shadow_local",
                ]
            }
    changed_material_values = dict(original_material_values)

    logger_info_msgs = [] # type: List[str]
    logger_warn_msgs = [] # type: List[str]
    # This section roughly mirrors the order in which 2.49 deals with these face buttons
    #---TEX----------------------------------------------------------
    if tf_modes.TEX:
        if tf_modes.ALPHA:
            if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_shadow_blend")[1]):
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_SHADOW
                logger_info_msgs.append("{}: Blend Mode='Shadow' and Blend Ratio=0.5".format(mat.name))
            if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_shadow_blend")[1]):
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_SHADOW
                root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                logger_info_msgs.append("{}: Blend Mode='Shadow' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
        if tf_modes.CLIP:
            if (xplane_249_helpers.find_property_in_parents(search_obj, "ATTR_no_blend")[1]):
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_OFF
                logger_info_msgs.append("{}: Blend Mode='Off' and Blend Ratio=0.5".format(mat.name))
            if (xplane_249_helpers.find_property_in_parents(search_obj, "GLOBAL_no_blend")[1]):
                changed_material_values["blend_v1000"] = xplane_constants.BLEND_OFF
                root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_INSTANCED_SCENERY
                logger_info_msgs.append("{}: Blend Mode='Off' and Blend Ratio=0.5, now Instanced Scenery".format(mat.name))
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
    if tf_modes.INVISIBLE:
        changed_material_values["draw"] = False
        logger_info_msgs.append("{}: Draw Objects With This Material={}".format(mat.name, changed_material_values["draw"]))
    #-----------------------------------------------------------------

    #---DYNAMIC-------------------------------------------------------
    if (not tf_modes.INVISIBLE
        and not is_cockpit
        and not tf_modes.DYNAMIC):
        changed_material_values["solid_camera"] = True
        logger_info_msgs.append("{}: Solid Camera={}".format(mat.name, changed_material_values["solid_camera"]))
    #-----------------------------------------------------------------

    #---TWOSIDE-------------------------------------------------------
    if tf_modes.TWOSIDE:
        logger_warn_msgs.append("{}: Two Sided is deprecated, skipping".format(mat.name))
        pass
    #-----------------------------------------------------------------

    #---SHADOW--------------------------------------------------------
    changed_material_values["shadow_local"] = not tf_modes.SHADOW
    if not changed_material_values["shadow_local"]:
        logger_info_msgs.append("{}: Cast Shadow (Local)={}".format(mat.name, changed_material_values["shadow_local"]))
    #-----------------------------------------------------------------

    if changed_material_values != original_material_values:
        for msg in logger_info_msgs:
            logger.info(msg)
        for msg in logger_warn_msgs:
            logger.warn(msg)
        # Here we ask "What Face Buttons really did end up mattering?" and make
        # a short name to hint the user as to what happened
        ov = original_material_values
        cv = changed_material_values
        hint_suffix = "".join((
                ("_TEX"    if cv["blend_v1000"] != ov["blend_v1000"] else ""),
                ("_TILES"  if (cv["draped"] != ov["draped"] or cv["poly_os"] != cv["poly_os"]) and tf_modes.TILES else ""),
                ("_LIGHT"  if (cv["draped"] != ov["draped"] or cv["poly_os"] != cv["poly_os"]) and tf_modes.LIGHT else ""),
                ("_INVIS"  if cv["draw"] != ov["draw"] and tf_modes.INVISIBLE else ""),
                ("_COLL"   if cv["solid_camera"] != ov["solid_camera"] and not tf_modes.DYNAMIC else ""),
                ("_SHADOW" if cv["shadow_local"] != ov["shadow_local"] and tf_modes.SHADOW else ""),
            ))

        new_name = (mat.name + hint_suffix)[:63] # Max datablock name length.
                                                 # If we're using these for dict keys we can't afford
                                                 # to get truncated and not know
        try:
            new_material = bpy.data.materials[new_name]
        except KeyError:
            new_material = mat.copy()
            new_material.name = new_name
            for prop, value in changed_material_values.items():
                setattr(new_material.xplane, prop, value)

            print("Created new converted material:", new_material.name)

        return new_material
    else:
        print("{} had nothing to convert".format(mat))
        return mat

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
    ISPANEL = ISCOCKPIT # type: bool
    #scene.render.engine = 'BLENDER_GAME' # Only for testing purposes

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
        # "Pragmatic paranioa is a programmer's pal" - Somebody's abandoned programming blog
        tf_modes_and_their_faces = _get_tf_modes_from_ctypes(search_obj) # type: TFModeAndFaceIndexes
        if not tf_modes_and_their_faces:
            tf_modes_and_their_faces[DEFAULT_TF_MODES] = [face.index for face in search_obj.data.polygons]
        #----------------------------------------------------------------------

        #--- Prepare the Object's Material Slots ------------------------------
        try:
            def _try(fn):
                try:
                    return fn()
                except:
                    pass

            print("Before (Slots):         ", *[_try(lambda: slot.material.name) for slot in search_obj.material_slots if slot.link == "DATA"], sep=",")
            print("Before (All Materials): ", *[_try(lambda: mat.name) for mat in search_obj.data.materials], sep=",")
        except:
            print("passing")
            pass
        print()
        # Faces without a 2.49 material are given a default (#1, 2, 10, 12, 21)
        if not search_obj.material_slots:
            scene.objects.active = search_obj
            bpy.ops.object.add_material_slot()

        for slot in search_obj.material_slots:
            if not slot.material:
                # We'll need a material in every slot no matter what anyways, why not now and save us trouble
                # In addition, a face's material_index will never be None or less than 0,
                # when asking "what faces have a mat index of 0", the answer is automatically "all of them"
                slot.material = test_creation_helpers.get_material(xplane_249_constants.DEFAULT_MATERIAL_NAME)
                slot.material.specular_intensity = 0.0 # This was the default in 2.49
        #----------------------------------------------------------------------

        # TODO: Auto-generated materials are replaced with Material_249_converter_default (#2, 12)
        # Unused materials aren't deleted (#19)

        #--- Get Materials and the faces that use them-------------------------
        materials_and_their_faces = collections.defaultdict(set) # type: Dict[bpy.types.MaterialSlot, Set[FaceId]]
        for face in search_obj.data.polygons:
            materials_and_their_faces[search_obj.material_slots[face.material_index].material].add(face.index)

        all_tf_faceids =       list(itertools.chain([face_ids for tf_modes, face_ids in tf_modes_and_their_faces.items()]))
        all_material_faceids = list(itertools.chain([face_ids for tf_modes, face_ids in materials_and_their_faces.items()]))
        print(all_tf_faceids)
        print(all_material_faceids)
        def flatten(l):
            for el in l:
                if isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
                    yield from flatten(el)
                else:
                    yield el
        assert sorted(flatten(all_tf_faceids)) == sorted(flatten(all_material_faceids)), "TF Face Ids and Material Face Ids must cover the same faces!"
        assert len(list(flatten(all_tf_faceids))) == len(list(flatten(all_material_faceids))) == len(search_obj.data.polygons), "TF FaceIds, Material FaceIds must cover all of object's faces!"
               #len(itertools.chain([faces for tf_modes, face_ids in tf_modes_and_their_faces.items()]), "dicts should cover the same range of faces"
        #----------------------------------------------------------------------
        print()
        print("Before (Slots):         ", *[slot.material.name for slot in search_obj.material_slots if slot.link == "DATA"], sep=",")
        print("Before (All Materials): ", *[mat.name for mat in search_obj.data.materials], sep=",")
        print()
        split_groups = {} # type: Dict[bpy.types.Material, List[FaceId]]
        for tf_modes, t_face_ids in tf_modes_and_their_faces.items():
            for material, m_face_ids in materials_and_their_faces.items():
                cross_over_faces = t_face_ids & m_face_ids
                if cross_over_faces:
                    converted = _convert_material(scene, root_object, search_obj, ISCOCKPIT, tf_modes, material)
                    if converted == material:
                        print("Didn't convert anything")
                    #material_slot.material = converted
                    split_groups[converted] = cross_over_faces
                else:
                    print("No cross over for ", tf_modes, "and", material.name)

        print("After (Slots):         ", *[slot.material.name for slot in search_obj.material_slots if slot.link == "DATA"], sep=",")
        print("After (All Materials): ", *[mat.name for mat in search_obj.data.materials], sep=",")
        print()

        new_objs = []
        # A mesh with <2 TF groups is unsplit
        if len(split_groups) == 0:
            new_objs = [search_obj.name]
        elif len(split_groups) == 1:
            new_objs = [search_obj.name]
        elif len(split_groups) > 2:
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
            #--Begining of Operation-----------------------
            for i, (material, face_ids) in enumerate(split_groups.items()):
                new_obj = copy_obj(search_obj, search_obj.name + "_%d" % i)
                print("New Obj: ", new_obj.name)
                print("New Mesh:", new_obj.data.name)
                print("Group:" , slot.material.name)
                if len(face_ids) < 2:
                    continue
                # Remove faces
                bm = bmesh.new()
                bm.from_mesh(new_obj.data)
                faces_to_keep   = [face for face in bm.faces if face.index in face_ids]
                faces_to_remove = [face for face in bm.faces if face.index not in face_ids]
                print("Faces To Keep:  ", [f.index for f in faces_to_keep])
                print("Faces To Remove:", [f.index for f in faces_to_remove])
                bmesh.ops.delete(bm, geom=faces_to_remove, context=5) #AKA DEL_ONLYFACES from bmesh_operator_api.h
                bm.to_mesh(new_obj.data)
                bm.free()

                scene.objects.active = new_obj
                for i in range(len(scene.objects.active.material_slots)-1):
                    bpy.ops.object.material_slot_remove()
                new_obj.material_slots[0].material = material
                new_objs.append(new_obj)

            logger.info("Split '{}' into {} groups".format(search_obj.name, len(split_groups)))
            #print("Deleting " + search_obj.name)
            #bpy.data.meshes.remove(search_obj.data, do_unlink=True)
            #bpy.data.objects.remove(search_obj, do_unlink=True) # What about other work ahead of us to convert?
            #--End of Split Operation----------------------

            intended_count = pre_split_obj_count - 1 + len(tf_modes_and_their_faces)
            #assert intended_count == len(scene.objects),\
            #        "After split, object count should be TF groups - deleted original ({}), is {}".format(intended_count, len(scene.objects))


        # The relationship between a face and its material is preserved when there is no split**
        # The relationship between a face and its material is preserved when splitting
        # After split, number of Materials should only include what is needed
