"""
This is the entry point for the exporter's collection and where it starts writing, proper.
The important paths are

createFilesFromBlenderRootObjects # Iterates through objects and collections to find
|_createFileFromBlenderRootObject
    |_xplane_file.create_xplane_bone_hierarchy # Exporter begins and runs the recursion down the Blender hierarchy
        |_ _recurse # The heart of the collection process, which turns Blender Objects into XPlaneObjects

Later, the write process starts with xplane_file.write, and uses the collected data including
the header and XPlaneBone tree contents to a string
"""

import collections
import dataclasses
import itertools
import operator
import pprint
from typing import Dict, List, NamedTuple, Optional, Set, Tuple, Union

import bpy
import mathutils

from io_xplane2blender import xplane_constants, xplane_helpers, xplane_props
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_types import (
    xplane_empty,
    xplane_material,
    xplane_material_utils,
)

from ..xplane_helpers import (
    BlenderParentType,
    ExportableRoot,
    PotentialRoot,
    floatToStr,
    logger,
)
from .xplane_bone import XPlaneBone
from .xplane_commands import XPlaneCommands
from .xplane_header import XPlaneHeader
from .xplane_light import XPlaneLight
from .xplane_mesh import XPlaneMesh
from .xplane_object import XPlaneObject
from .xplane_primitive import XPlanePrimitive
from .xplane_vlights import XPlaneVLights


class NotExportableRootError(ValueError):
    pass


def createFilesFromBlenderRootObjects(
    scene: bpy.types.Scene, view_layer: bpy.types.ViewLayer
) -> List["XPlaneFile"]:
    """
    Returns a list of all created XPlaneFiles from all valid roots found,
    ignoring any that could not be created.

    view_layer is needed to test exportability
    """
    xplane_files: List["XPlaneFile"] = []
    for potential_root in (
        scene.objects[:] + xplane_helpers.get_collections_in_scene(scene)[1:]
    ):
        try:
            xplane_file = createFileFromBlenderRootObject(potential_root, view_layer)
        except NotExportableRootError as e:
            pass
        else:
            xplane_files.append(xplane_file)

    # Without this the cache never gets cleared
    # and no new animations are exported without a restart
    _all_keyframe_infos.clear()

    return xplane_files


def createFileFromBlenderRootObject(
    potential_root: PotentialRoot, view_layer: bpy.types.ViewLayer
) -> "XPlaneFile":
    """
    Creates the starting point for making an OBJ, creates the file and beings
    the collection phase.

    For the purposes of testing if the potential_root is exportable,
    we need a view_layer to test with

    Raises ValueError when exportable_root is not marked as exporter or something
    prevents collection
    """
    if not xplane_helpers.is_exportable_root(potential_root, view_layer):
        raise NotExportableRootError(f"{potential_root.name} is not a root")
    nested_roots: Set[PotentialRoot] = set()

    def find_nested_roots(potential_roots: List[PotentialRoot]):
        nonlocal nested_roots
        if isinstance(potential_root, bpy.types.Collection):
            nested_roots.update(
                o
                for o in potential_root.all_objects
                if xplane_helpers.is_exportable_root(o, view_layer)
            )

        for child in potential_roots:
            if xplane_helpers.is_exportable_root(child, view_layer):
                nested_roots.update({child})
            find_nested_roots(child.children)

    find_nested_roots(potential_root.children)
    if nested_roots:
        names = [f"'{potential_root.name}'"] + [f"'{r.name}'" for r in nested_roots]
        logger.error(
            f"Nested roots found below '{potential_root.name}'. Checkmark only one of these as the Root: {', '.join(names)}"
        )

    # Name change, we're now confirmed exportable!
    exportable_root = potential_root
    layer_props = exportable_root.xplane.layer
    filename = layer_props.name if layer_props.name else exportable_root.name

    xplane_file = XPlaneFile(filename, layer_props)
    xplane_file.create_xplane_bone_hiearchy(exportable_root)
    bpy.context.scene.frame_set(1)
    assert xplane_file.rootBone, "Root Bone was not assigned during __init__ function"
    return xplane_file


@dataclasses.dataclass(frozen=True)
class LocRotPerFrame:
    """Location/Rotation information at each frame we could care about, copied"""

    frame_num: int
    location: mathutils.Vector
    rotation_mode: str
    rotation: Union[
        mathutils.Euler, mathutils.Quaternion, Tuple[float, float, float, float]
    ]


ObjectBoneNameKey = Tuple[str, str]
FrameToLocRotPerFrame = Dict[int, LocRotPerFrame]


# IMPORTANT! You must clear this cache when finished exporting all your OBJs,
# or you'll never export new animations! We clear in
# - xplane_file.createFilesFromBlenderRootObjects - from using the export operator
# - tests/__init__.exportExportableRoot - from using a test
_all_keyframe_infos: Dict[
    str, Dict[ObjectBoneNameKey, FrameToLocRotPerFrame]
] = collections.defaultdict(dict)


def _pre_scan_all_keyframes():
    """Returns a copy of all this scene's LocRotPerFrame, scanning for it as needed"""

    ###--- THIS IS A HOTPATH -------------------------------------------------
    # Do not change without profiling
    #
    # Calling frame_set __once__ per every keyframe in a scene is
    # a huge performance win. We cache the results in case the user has multiple roots
    # in a scene

    global _all_keyframe_infos
    if bpy.context.scene.name in _all_keyframe_infos:
        return
    else:
        scene_keyframe_infos = collections.defaultdict(dict)

    # A set of all keyframes that could have data we care about
    frames_to_visit = sorted(
        {
            int(kf.co[0])
            for action in bpy.data.actions
            for fcurve in action.fcurves
            for kf in fcurve.keyframe_points
            if kf.co[0].is_integer()
        }
    )

    # --- Begin frames to visit-------------------
    for frame_num in frames_to_visit:
        bpy.context.scene.frame_set(frame_num)

        # --- Begin objects to visit -------------
        for obj in bpy.context.scene.objects:
            if obj.type == "ARMATURE":
                # --- Begin bones to visit -------
                for bone in obj.pose.bones:
                    l = LocRotPerFrame(
                        frame_num,
                        bone.location.copy(),
                        bone.rotation_mode,
                        xplane_helpers.get_rotation_from_rotatable(bone),
                    )

                    scene_keyframe_infos[(obj.name, bone.name)][frame_num] = l
                # --- End bones to visit ---------
            l = LocRotPerFrame(
                frame_num,
                obj.location.copy(),
                obj.rotation_mode,
                xplane_helpers.get_rotation_from_rotatable(obj),
            )
            scene_keyframe_infos[(obj.name, None)][frame_num] = l
        # --- End objects to visit ---------------
    # --- End frames to visit---------------------
    bpy.context.scene.frame_set(1)
    _all_keyframe_infos[bpy.context.scene.name] = scene_keyframe_infos
    return


class XPlaneFile:
    """
    Represents the total contents of a .obj file and
    the settings affecting the output
    """

    def __init__(self, filename: str, options: xplane_props.XPlaneLayer) -> None:
        # A mapping of Blender Object names and the XPlaneBones they were turned into
        # these are garunteed to be under the root bone
        self.commands = XPlaneCommands(self)
        self.filename = filename
        self.options = options

        self.lights = XPlaneVLights()
        self.mesh = XPlaneMesh()
        self._bl_obj_name_to_bone: Dict[str, XPlaneBone] = {}

        # materials representing the reference for export
        self.referenceMaterials: List[xplane_material.XPlaneMaterial] = None

        # the root bone: origin for all animations/objects
        # This isn't really a None type, it is created immediately
        # after in create_xplane_bone_hierarchy
        self.rootBone: XPlaneBone = None

        # Header assumes that its xplaneFile is completely formed
        self.header = XPlaneHeader(self, 8)

        # You'll never ever forget to call XPlaneFile, so,
        # we stick this here
        _pre_scan_all_keyframes()

    def create_xplane_bone_hiearchy(
        self, exportable_root: ExportableRoot
    ) -> Optional[XPlaneObject]:
        def allowed_children(
            parent_like: Union[bpy.types.Collection, bpy.types.Object]
        ) -> List[bpy.types.Object]:
            """
            Returns only the objects the recurse function is allowed to use.
            If a problematic object is found, errors and warnings may be
            emitted
            """
            # bones also have a .children attribute
            assert isinstance(
                parent_like, (bpy.types.Collection, bpy.types.Object)
            ), "Only Collections and Objects are allowed"
            try:
                children = sorted(parent_like.all_objects, key=lambda r: r.name)
            except AttributeError:
                children = parent_like.children

            allowed_children = []
            for child_obj in children:
                if child_obj.name not in bpy.context.scene.objects:
                    logger.warn(
                        f"{child_obj.name} is outside the current scene. It and any children cannot be collected"
                    )
                else:
                    allowed_children.append(child_obj)
            return allowed_children

        def convert_to_xplane_object(
            blender_obj: bpy.types.Object,
        ) -> Optional[XPlaneObject]:
            assert (
                blender_obj
            ), "blender_obj in convert_to_xplane_object must not be None"
            converted_xplane_obj = None
            if blender_obj.type == "MESH":
                converted_xplane_obj = XPlanePrimitive(blender_obj)
            elif blender_obj.type == "LIGHT":
                converted_xplane_obj = XPlaneLight(blender_obj)
            elif blender_obj.type == "ARMATURE":
                converted_xplane_obj = XPlaneObject(blender_obj)
            elif blender_obj.type == "EMPTY":
                converted_xplane_obj = xplane_empty.XPlaneEmpty(blender_obj)

            return converted_xplane_obj

        def walk_upward(walk_start_bone: XPlaneBone):
            """
            Re-oganizes the XPlaneBone tree to include
            a Blender Object's out of collection parents
            """
            assert (
                walk_start_bone.blenderObject.parent
            ), "Walk up must have at least one parent to travel to"

            new_bones: List[XPlaneBone] = []

            def walk_upward_recursive(current_bone: XPlaneBone) -> XPlaneBone:
                """
                Recurse up by parent until you find a reuse opportutiny
                or nothing. Returns the top of the branch which must be
                reconnected
                """
                # If we haven't reached the top yet, make a bone for parent and move the head
                blender_obj = current_bone.blenderObject
                parent_obj = blender_obj.parent
                # --- Check for a reuse opportunity ------------------------
                if parent_obj and parent_obj.name in self._bl_obj_name_to_bone:
                    return current_bone
                elif parent_obj:
                    # ---------------------------------------------------------
                    # This is all the manual work
                    # the __init__ of XPlaneBone and XPlaneObject, and _recurse normally does for us
                    # - Converting parent_obj to an XPlaneObject (if possible)
                    # - Setting export_animation_only to True if outside collection,
                    #   or if we're re-entering, setting based on visible_get
                    # - Creating an XPlaneBone, and attaching the current bone as the new bone's child*
                    # - Running the new_parent's collect
                    # - Running walk_up to find it's split parents
                    # *Okay, this isn't a part of _recurse, but, I thought I should mention it while on
                    # the subject
                    # ----------------------------------------------------------
                    new_parent_xplane_obj = convert_to_xplane_object(parent_obj)
                    if new_parent_xplane_obj:
                        if (
                            not new_parent_xplane_obj.blenderObject.name
                            in exportable_root.all_objects
                        ):
                            # We don't have to test for blender_obj.visible_get here,
                            # all objects that start inside the exportable collection will
                            # have the assumption of being False - XPlaneObject's default for this is False
                            new_parent_xplane_obj.export_animation_only = True
                        else:
                            new_parent_xplane_obj.export_animation_only = (
                                not new_parent_xplane_obj.blenderObject.visible_get()
                            )

                    try:
                        if (
                            parent_obj.type == "ARMATURE"
                            and blender_obj.parent_type == "BONE"
                        ):
                            parent_bl_bone = parent_obj.data.bones[
                                blender_obj.parent_bone
                            ]
                        else:
                            parent_bl_bone = None
                    except KeyError as e:
                        parent_bl_bone = None

                    new_parent_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=parent_obj,
                        # TODO: What if the parent is a nested bone? (bug #501)
                        blender_bone=parent_bl_bone,
                        xplane_obj=new_parent_xplane_obj,
                        parent_xplane_bone=None,
                    )

                    new_bones.append(new_parent_bone)
                    if new_parent_xplane_obj:
                        new_parent_xplane_obj.collect()
                    new_parent_bone.children.append(current_bone)
                    current_bone.parent = new_parent_bone
                    return walk_upward_recursive(new_parent_bone)
                else:
                    return current_bone

            top_of_branch = walk_upward_recursive(walk_start_bone)
            # 2 Types of reconnection
            # - Type A
            #   New branch needs re-connection to the root
            # - Type B
            #   Re-use of a previously walked to Blender Object out of collection
            if not top_of_branch.blenderObject.parent:
                reconnect_bone = self.rootBone
            else:
                reconnect_bone = self._bl_obj_name_to_bone[
                    top_of_branch.blenderObject.parent.name
                ]

            self.rootBone.children.remove(walk_start_bone)
            reconnect_bone.children.append(top_of_branch)
            top_of_branch.parent = reconnect_bone

            # This time we will have a parent!
            [bone.collectAnimations() for bone in new_bones]
            self._bl_obj_name_to_bone.update(
                {bone.blenderObject.name: bone for bone in new_bones}
            )

        def recurse(
            parent: Optional[bpy.types.Object],
            parent_bone: Optional[XPlaneBone],
            parent_blender_objects: bpy.types.Object,
        ) -> None:
            """
            Main function for recursing down tree.

            When parent is None
            - recurse is dealing with the first call of an exportable collection
            - parent_blender_objects = filtered coll.all_objects

            parent_blender_objects should always be filtered by allowed_children
            """
            # print(
            #   f"Parent: {parent.name}" if parent else f"Root: {exportable_root.name}",
            #   f"Parent Bone: {parent_bone}" if parent_bone else "No Parent Bone",
            #   f"parent_blender_objects {[o.name for o in parent_blender_objects]}",
            #   sep="\n"
            # )
            # print("===========================================================")

            blender_obj = parent

            try:
                self._bl_obj_name_to_bone[blender_obj.name]
            except (AttributeError, KeyError):
                found_blender_obj_already = False
            else:
                found_blender_obj_already = True

            def get_new_xplane_obj() -> Optional[XPlaneObject]:
                """
                When we're re-using a bone for various reasons,
                we call it a "new bone" and call it's object
                a "new object" so the rest of the algorithm doesn't get
                complicated
                """
                if found_blender_obj_already:
                    return self._bl_obj_name_to_bone[blender_obj.name].xplaneObject
                elif blender_obj:
                    return convert_to_xplane_object(blender_obj)
                else:
                    return None

            new_xplane_obj = get_new_xplane_obj()
            # print(f"new_xplane_obj:\n{new_xplane_obj}")

            is_root_bone = not parent_bone  # True for Exportable Collection and Object

            def get_new_xplane_bone() -> XPlaneBone:
                """
                If a non-root XPlaneBone is created
                it is auto added to the dict of existing bones.

                If we're re-using a bone we call it the "new" one,
                for the rest of the algorithm's sake
                """
                if found_blender_obj_already:
                    return self._bl_obj_name_to_bone[blender_obj.name]
                # We'll never have found the root bone already, you find it once
                elif is_root_bone and isinstance(exportable_root, bpy.types.Collection):
                    return XPlaneBone(self, blender_obj=None)
                elif not found_blender_obj_already:
                    new_xplane_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=blender_obj,
                        blender_bone=None,
                        xplane_obj=new_xplane_obj,
                        parent_xplane_bone=parent_bone,
                    )
                    self._bl_obj_name_to_bone[blender_obj.name] = new_xplane_bone
                    return new_xplane_bone

            new_xplane_bone = get_new_xplane_bone()
            if is_root_bone:
                assert (
                    not self.rootBone
                ), "recurse should never be assigning self.rootBone twice"
                self.rootBone = new_xplane_bone
            try:
                if (
                    not found_blender_obj_already
                    and blender_obj.parent.name not in exportable_root.all_objects
                ):
                    if blender_obj.parent.name in bpy.context.scene.objects:
                        walk_upward(new_xplane_bone)
                    else:
                        logger.warn(
                            f"'{blender_obj.name}' parent is not in the same collection and is in a different scene. "
                            f"'{blender_obj.parent.name}' and any it's parents will not be searched for split animations"
                        )
            except AttributeError:  # For whatever of many reasons, we didn't walk up
                pass

            # We only collect once
            if not found_blender_obj_already and new_xplane_obj:
                # If set from walking up, keep that. Otherwise, decide based on visiblity
                new_xplane_obj.export_animation_only = (
                    new_xplane_obj.export_animation_only
                    or not blender_obj.visible_get()
                )
                # This is asking if it is an old-style light,
                # not it's Blender Light Type!
                if (
                    isinstance(new_xplane_obj, XPlaneLight)
                    and not new_xplane_obj.export_animation_only
                ):
                    self.lights.append(new_xplane_obj)
                new_xplane_obj.collect()
            elif not found_blender_obj_already and blender_obj:
                print(f"Blender Object: {blender_obj.name}, didn't convert")

            def make_bones_for_armature_bones(
                arm_obj: bpy.types.Object,
            ) -> Dict[str, XPlaneBone]:
                """
                Makes XPlaneBones for all bones in an armature, returns a map between
                Blender Bone Names and the XPlaneBones that are associated with them.

                These are used later to pair XPlaneObjects with their correct parent bones
                """
                assert arm_obj.type == "ARMATURE", arm_obj.name + " must be armature"
                blender_bones_to_xplane_bones = {}

                def _recurse_bone(bl_bone: bpy.types.Bone, parent_xp_bone: XPlaneBone):
                    """
                    Recurses down an armature's bone tree, making XPlaneBones for each Blender Bone
                    """
                    # For every 'Bone' we make an XPlaneBone all to itself, it becomes the new parent instead of the
                    # bone the armature is connected to
                    parent_xp_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=arm_obj,
                        blender_bone=bl_bone,
                        xplane_obj=None,
                        parent_xplane_bone=parent_xp_bone,
                    )
                    blender_bones_to_xplane_bones[bl_bone.name] = parent_xp_bone
                    for child in bl_bone.children:
                        _recurse_bone(child, parent_xp_bone)

                # Run recurse for the top level bones
                for top_level_bone in filter(
                    lambda b: not b.parent, arm_obj.data.bones
                ):
                    _recurse_bone(top_level_bone, new_xplane_bone)
                return blender_bones_to_xplane_bones

            # If this is an armature, first build up the bones by tracking recursively down, then continue on
            # but skipping making the conversion again
            if blender_obj and blender_obj.type == "ARMATURE":
                real_bone_parents = make_bones_for_armature_bones(blender_obj)

            for child_obj in parent_blender_objects:
                if (
                    isinstance(exportable_root, bpy.types.Collection)
                    and child_obj.name not in exportable_root.all_objects
                ):
                    continue
                if (
                    blender_obj
                    and blender_obj.type == "ARMATURE"
                    and child_obj.parent_type == "BONE"
                ):
                    if child_obj.parent_bone not in blender_obj.data.bones:
                        logger.warn(
                            "".join(
                                (
                                    f"{child_obj.name}",
                                    " and its children" if child_obj.children else "",
                                    " will not export,",
                                    f" it's parent bone '{child_obj.parent_bone}' is",
                                    f" not a real bone in {blender_obj.name}"
                                    if child_obj.parent_bone
                                    else " empty",
                                )
                            )
                        )
                        # Ignored cases don't get their children examined
                        continue
                    else:
                        parent_bone = real_bone_parents[child_obj.parent_bone]
                        assert (
                            parent_bone
                        ), "Must have parent bone for further recursion"
                        recurse(child_obj, parent_bone, allowed_children(child_obj))
                else:  # no parent by armature-bone
                    parent_bone = new_xplane_bone
                    recurse(child_obj, parent_bone, allowed_children(child_obj))
            try:
                if new_xplane_bone.blenderObject.type == "ARMATURE":
                    for xp_bone in real_bone_parents.values():
                        xp_bone.sortChildren()
            except AttributeError:  # Collection won't have a blenderObject
                pass
            new_xplane_bone.sortChildren()

        # --- end _recurse function -------------------------------------------
        if isinstance(exportable_root, bpy.types.Collection):
            all_allowed_objects = allowed_children(exportable_root)
            all_allowed_names = [o.name for o in all_allowed_objects]
            recurse(
                parent=None,
                parent_bone=None,
                parent_blender_objects=[
                    o
                    for o in all_allowed_objects
                    if o.parent is None or o.parent.name not in all_allowed_names
                ],
            )
        elif isinstance(exportable_root, bpy.types.Object):
            recurse(
                parent=exportable_root,
                parent_bone=None,
                parent_blender_objects=allowed_children(exportable_root),
            )
        else:
            assert False, f"Unsupported root_object type {type(exportable_root)}"

    def get_xplane_objects(self) -> List["XPlaneObject"]:
        """
        Returns a list of all XPlaneObjects collected by recursing down the
        completed XPlaneBone tree
        """
        assert self.rootBone, "Must be called after collection is finished"

        def get_xplane_objects_from_bone_tree(
            bone: XPlaneBone,
        ) -> List["XPlaneObjects"]:
            xp_objects = []
            if bone.xplaneObject:
                xp_objects.append(bone.xplaneObject)
            for child_bone in bone.children:
                xp_objects.extend(get_xplane_objects_from_bone_tree(child_bone))
            return xp_objects

        return get_xplane_objects_from_bone_tree(self.rootBone)

    def validateMaterials(self) -> bool:
        objects = self.get_xplane_objects()

        for xplaneObject in objects:
            if xplaneObject.type == "MESH" and xplaneObject.material.options:
                errors, warnings = xplaneObject.material.isValid(
                    self.options.export_type
                )

                for error in errors:
                    logger.error(
                        'Material "%s" in object "%s" %s'
                        % (
                            xplaneObject.material.name,
                            xplaneObject.blenderObject.name,
                            error,
                        )
                    )

                for warning in warnings:
                    logger.warn(
                        'Material "%s" in object "%s" %s'
                        % (
                            xplaneObject.material.name,
                            xplaneObject.blenderObject.name,
                            warning,
                        )
                    )

        if logger.hasErrors():
            return False

        return True

    def getMaterials(self) -> List[bpy.types.Material]:
        """
        Returns a list of the materials used in the OBJ, or an empty list if none found
        Must be called after XPlaneFile.collectBlenderObjects
        """

        materials = []
        objects = self.get_xplane_objects()

        for xplaneObject in objects:
            if (
                xplaneObject.type == "MESH"
                and xplaneObject.material
                and xplaneObject.material.options
            ):
                materials.append(xplaneObject.material)

        return materials

    def compareMaterials(self, refMaterials):
        materials = self.getMaterials()

        for refMaterial in refMaterials:
            if refMaterial is not None:
                for material in materials:
                    # only compare draped materials agains draped
                    # and non-draped agains non-draped
                    if refMaterial.options.draped == material.options.draped:
                        errors, warnings = material.isCompatibleTo(
                            refMaterial, self.options.export_type, False
                        )
                        xplaneObject = material.xplaneObject
                        for error in errors:
                            logger.error(
                                'Material "%s" in object "%s" %s'
                                % (
                                    material.name,
                                    xplaneObject.blenderObject.name,
                                    error,
                                )
                            )

                        for warning in warnings:
                            logger.warn(
                                'Material "%s" in object "%s" %s'
                                % (
                                    material.name,
                                    xplaneObject.blenderObject.name,
                                    warning,
                                )
                            )

        if logger.hasErrors():
            return False

        return True

    def writeFooter(self):
        return "# Build with Blender %s (build %s). Exported with XPlane2Blender %s" % (
            bpy.app.version_string,
            bpy.app.build_hash,
            xplane_helpers.VerStruct.current(),
        )

    def write(self) -> str:
        """
        Writes the contents of the file to one giant string with \n's,
        to be written to a file or compared in a unit test
        """
        self.mesh.collectXPlaneObjects(self.get_xplane_objects())

        # validate materials
        if not self.validateMaterials():
            return ""

        # detect reference materials
        self.referenceMaterials = xplane_material_utils.getReferenceMaterials(
            self.getMaterials(), self.options.export_type
        )

        refMatNames = [refMat.name for refMat in self.referenceMaterials if refMat]
        logger.info(
            "Using the following reference materials: %s" % ", ".join(refMatNames)
        )

        # validation was successful
        # retrieve reference materials
        # and compare all materials against reference materials
        # TODO: One day we'll have a autodetect feature again
        # if self.options.autodetectTextures == False:
        #    logger.info('Autodetect textures overridden for file %s: not fully checking manually entered textures against Blender-based reference materials\' textures' % (self.filename))

        if not self.compareMaterials(self.referenceMaterials):
            return ""

        o = ""
        o += self.header.write()
        o += "\n"

        meshOut = self.mesh.write()
        o += meshOut

        if len(meshOut):
            o += "\n"

        # TODO: Deprecate this one day...
        lightsOut = self.lights.write()
        o += lightsOut

        if len(lightsOut):
            o += "\n"

        lodsOut = self._writeLods()
        o += lodsOut

        if len(lodsOut):
            o += "\n"

        o += self.writeFooter()

        return o

    def _writeLods(self) -> str:
        o = ""
        num_lods = int(self.options.lods)

        if num_lods:
            defined_buckets = self.options.lod[:num_lods]
            # --- ATTR_LOD validations ----------------------------------------
            # LOD spec #2
            if defined_buckets[0].near != 0:
                logger.error(
                    f"{self.filename}'s LOD buckets must start at 0, is {defined_buckets[0].near}"
                )
                return o

            for bucket_number in range(0, int(self.options.lods)):
                near = self.options.lod[bucket_number].near
                far = self.options.lod[bucket_number].far
                # LOD spec #7
                if near == far:
                    logger.error(
                        f"{self.filename}'s LOD bucket #{bucket_number+1}'s Near and Far match: ({near}, {far})"
                    )
                    return o
                # LOD spec #3
                elif near > far:
                    logger.error(
                        f"{self.filename}'s LOD bucket #{bucket_number+1}'s Near is greater than its Far: ({near}, {far})"
                    )

            class LODStruct(NamedTuple):
                near: int
                far: int

                def __repr__(self) -> str:
                    return f"({self.near}, {self.far})"

            # len(selective_pairs) in {0, 2, 4} == True
            # len(additive_pairs) in range(1, 5) == True
            # if len additive_pairs is 1 and len selective_pairs is greater than 2, you are in selective mode
            # if len additive_pairs is > 1 and len selective pairs is greater than 2, you are in mixed modes
            additive_pairs: Tuple[Tuple[int, LODStruct], ...] = tuple(
                [
                    (i, LODStruct(lod.near, lod.far))
                    for i, lod in enumerate(defined_buckets)
                    if i < num_lods and lod.near == 0
                ]
            )

            # To be in selective mode, you must have at least two LOD buckets,
            # (0, m), (m, m+something), where m is meters
            selective_pairs: List[Tuple[int, LODStruct]] = []
            try:
                for i, (prev_lod, next_lod) in enumerate(
                    zip(defined_buckets[: num_lods - 1], defined_buckets[1:])
                ):
                    if prev_lod.far == next_lod.near:
                        if (
                            not selective_pairs
                            or (i - 1, (prev_lod.near, prev_lod.far))
                            != selective_pairs[-1]
                        ):
                            selective_pairs.append(
                                (i, LODStruct(prev_lod.near, prev_lod.far))
                            )
                        selective_pairs.append(
                            (i + 1, LODStruct(next_lod.near, next_lod.far))
                        )
                    # LOD spec #6
                    elif prev_lod.far < next_lod.near:
                        logger.error(
                            f"In {self.filename}, gap found between LOD bucket #{i} and {i+1}. Far and Near should match: ({prev_lod}, {next_lod})"
                        )
                    elif (
                        prev_lod.far > next_lod.near and len(additive_pairs) == 1
                    ):  # every additive pair's far will always be greater than 0, ignore
                        logger.error(
                            f"In {self.filename}, overlap found between LOD bucket #{i} and {i+1}. Far and Near should match: ({prev_lod}, {next_lod})"
                        )
            except IndexError:  # fails when defined_buckets has only 1 bucket
                pass
            selective_pairs = tuple(selective_pairs)
            assert (
                len(selective_pairs) % 2 == 0
            ), f"{selective_pairs} not a multiple of two"

            # LOD spec #5
            # It isn't just having a pairs, they both have to be in meaningful amounts
            # to show mixing
            if len(additive_pairs) > 1 and len(selective_pairs) >= 2:
                logger.error(
                    f"{self.filename} uses Additive and Selective LODs modes. Choose only one: {[str(lod) for lod in defined_buckets]}"
                )

            # LOD spec #3 (Additive version)
            # additive_pairs and selective_pairs will always share a first
            # but never a second pair - avoids false positives
            if len(additive_pairs) > 1 and any(
                [
                    not prev_lod.far < next_lod.far
                    for (prev_index, (prev_lod)), (next_index, (next_lod)) in zip(
                        additive_pairs[:-1], additive_pairs[1:]
                    )
                ]
            ):
                logger.error(
                    f"{self.filename}'s LOD buckets' Far values must be in ascending order: {[(lod) for i, lod in additive_pairs]}"
                )
            # -----------------------------------------------------------------
            # LOD spec #1, this is written before the first ever
            # or subsequent calls to commands.write
            for lod_bucket_index, lod_bucket in enumerate(defined_buckets):
                o += f"ATTR_LOD\t{lod_bucket.near}\t{lod_bucket.far}\n"
                o += self.commands.write(lod_bucket_index=lod_bucket_index)
        else:
            o += self.commands.write(lod_bucket_index=None)

        # print(o)
        return o
