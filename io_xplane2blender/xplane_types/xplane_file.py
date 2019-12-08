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
import operator
import pprint
from typing import Dict, List, Optional, Set, Union

import bpy
import mathutils
from io_xplane2blender import xplane_constants, xplane_helpers, xplane_props
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_types import xplane_empty, xplane_material_utils, xplane_material

from ..xplane_helpers import (BlenderParentType, ExportableRoot, PotentialRoot,
                              floatToStr, logger)
from .xplane_bone import XPlaneBone
from .xplane_commands import XPlaneCommands
from .xplane_header import XPlaneHeader
from .xplane_light import XPlaneLight
from .xplane_lights import XPlaneLights
from .xplane_mesh import XPlaneMesh
from .xplane_object import XPlaneObject
from .xplane_primitive import XPlanePrimitive


def createFilesFromBlenderRootObjects(scene:bpy.types.Scene)->List["XPlaneFile"]:
    xplane_files: List["XPlaneFile"] = []
    for exportable_root in filter(lambda o: xplane_helpers.is_exportable_root(o), scene.objects[:] + xplane_helpers.get_collections_in_scene(scene)[1:]):
        if exportable_root.xplane.layer.export:
            xplane_file = createFileFromBlenderRootObject(exportable_root)
            xplane_files.append(xplane_file)

    return xplane_files

def createFileFromBlenderRootObject(exportable_root:PotentialRoot)->Optional["XPlaneFile"]:
    nested_errors: Set[str] = set()
    def log_nested_roots(exportable_roots: List[PotentialRoot]):
        err = "Exportable Roots cannot be nested, unmark {} as a Root or change its parentage"
        if isinstance(exportable_root, bpy.types.Collection):
            get_name = lambda r: r.name
            nested_errors.update(err.format(obj.name) for obj in filter(xplane_helpers.is_exportable_root, sorted(exportable_root.all_objects, key=get_name)))
        for child in exportable_roots:
            if xplane_helpers.is_exportable_root(child):
                nested_errors.add(err.format(child.name))
            log_nested_roots(child.children)

    log_nested_roots(exportable_root.children)
    for error in sorted(nested_errors):
        logger.error(error)

    layer_props = exportable_root.xplane.layer
    filename = layer_props.name if layer_props.name else exportable_root.name
    xplane_file = XPlaneFile(filename, layer_props)
    xplane_file.create_xplane_bone_hiearchy(exportable_root)
    assert xplane_file.rootBone, "Root Bone was not assaigned during __init__ function"
    #print("Final Root Bone (2.80)")
    #print(xplane_file.rootBone)
    return xplane_file

class XPlaneFile():
    """
    Represents the total contents of a .obj file and
    the settings affecting the output
    """
    def __init__(self, filename:str, options:xplane_props.XPlaneLayer)->None:
        # A mapping of Blender Object names and the XPlaneBones they were turned into
        # these are garunteed to be under the root bone
        self.commands = XPlaneCommands(self)
        self.filename = filename
        self.options = options

        self.lights = XPlaneLights()
        self.mesh = XPlaneMesh()
        self._bl_obj_name_to_bone:Dict[str, XPlaneBone] = {}

        # materials representing the reference for export
        self.referenceMaterials:List[xplane_material.XPlaneMaterial] = None

        # the root bone: origin for all animations/objects
        # This isn't really a None type, it is created immediately
        # after in create_xplane_bone_hierarchy
        self.rootBone:XPlaneBone = None

        # Header assumes that its xplaneFile is completely formed
        self.header = XPlaneHeader(self, 8)


    def create_xplane_bone_hiearchy(self, exportable_root:ExportableRoot)->Optional[XPlaneObject]:
        def allowed_children(parent_like:Union[bpy.types.Collection, bpy.types.Object])->List[bpy.types.Object]:
            """
            Returns only the objects the recurse function is allowed to use.
            If a problematic object is found, errors and warnings may be
            emitted
            """
            # bones also have a .children attribute
            assert isinstance(parent_like, (bpy.types.Collection, bpy.types.Object)), "Only Collections and Objects are allowed"
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

        def convert_to_xplane_object(blender_obj:bpy.types.Object)->Optional[XPlaneObject]:
            assert blender_obj, "blender_obj in convert_to_xplane_object must not be None"
            converted_xplane_obj = None
            if blender_obj.type == "MESH":
                converted_xplane_obj = XPlanePrimitive(blender_obj)
            elif blender_obj.type == "LIGHT":
                converted_xplane_obj  = XPlaneLight(blender_obj)
            elif blender_obj.type == "ARMATURE":
                converted_xplane_obj = XPlaneObject(blender_obj)
            elif blender_obj.type == "EMPTY":
                converted_xplane_obj = xplane_empty.XPlaneEmpty(blender_obj)

            return converted_xplane_obj

        def walk_upward(walk_start_bone:XPlaneBone):
            """
            Re-oganizes the XPlaneBone tree to include
            a Blender Object's out of collection parents
            """
            assert walk_start_bone.blenderObject.parent, "Walk up must have at least one parent to travel to"

            new_bones: List[XPlaneBone] = []
            def walk_upward_recursive(current_bone: XPlaneBone)->XPlaneBone:
                """
                Recurse up by parent until you find a reuse opportutiny
                or nothing. Returns the top of the branch which must be
                reconnected
                """
                # If we haven't reached the top yet, make a bone for parent and move the head
                blender_obj = current_bone.blenderObject
                parent_obj = blender_obj.parent
                #--- Check for a reuse opportunity ------------------------
                if parent_obj and parent_obj.name in self._bl_obj_name_to_bone:
                    #existing_parent_bone = self._bl_obj_name_to_bone[parent_obj.name]
                    #existing_parent_bone.
                    return current_bone
                elif parent_obj:
                    #--- This is all the manual work
                    # the __init__ of XPlaneBone and XPlaneObject, and _recurse normally does for us
                    #----------------------------------------------------------
                    new_parent_xplane_obj = convert_to_xplane_object(parent_obj)
                    if new_parent_xplane_obj:
                        new_parent_xplane_obj.export_animation_only = True
                    try:
                        if parent_obj.type == "ARMATURE" and blender_obj.parent_type == "BONE":
                            parent_bl_bone = parent_obj.data.bones[blender_obj.parent_bone]
                        else:
                            parent_bl_bone = None
                    except KeyError as e:
                        parent_bl_bone = None

                    new_parent_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=parent_obj,
                        #TODO: What if the parent is a nested bone? (bug #501)
                        blender_bone=parent_bl_bone,
                        xplane_obj=new_parent_xplane_obj,
                        parent_xplane_bone=None)

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
                reconnect_bone = self._bl_obj_name_to_bone[top_of_branch.blenderObject.parent.name]

            self.rootBone.children.remove(walk_start_bone)
            reconnect_bone.children.append(top_of_branch)
            top_of_branch.parent = self.rootBone

            # This time we will have a parent!
            [bone.collectAnimations() for bone in new_bones]
            self._bl_obj_name_to_bone.update({bone.blenderObject.name:bone for bone in new_bones})

        def recurse(parent: Optional[bpy.types.Object], parent_bone: Optional[XPlaneBone], parent_blender_objects:bpy.types.Object)->None:
            """
            Main function for recursing down tree.

            When parent is None
            - recurse is dealing with the first call of an exportable collection
            - parent_blender_objects = filtered coll.all_objects

            parent_blender_object should always be filtered by allowed_children
            """
            #print(
            #f"Parent: {parent.name}" if parent else f"Root: {exportable_root.name}",
            #f"Parent Bone: {parent_bone}" if parent_bone else "No Parent Bone",
            #f"parent_blender_objects {[o.name for o in parent_blender_objects]}",
            #sep="\n"
            #)
            #print("===========================================================")

            blender_obj = parent
            if blender_obj:
                new_xplane_obj = convert_to_xplane_object(blender_obj)
            else:
                new_xplane_obj = None
            #print(f"new_xplane_obj:\n{new_xplane_obj}")

            is_root_bone = not parent_bone # True for Exportable Collection and Object
            if (is_root_bone
                and isinstance(exportable_root, bpy.types.Collection)):
                new_xplane_bone = XPlaneBone(self, blender_obj=None)
            else:
                new_xplane_bone = XPlaneBone(
                    xplane_file=self,
                    blender_obj=blender_obj,
                    blender_bone=None,
                    xplane_obj=new_xplane_obj,
                    parent_xplane_bone=parent_bone)
                self._bl_obj_name_to_bone[blender_obj.name] = new_xplane_bone

            if is_root_bone:
                assert not self.rootBone, "recurse should never be assigning self.rootBone twice"
                self.rootBone = new_xplane_bone
            try:
                if (blender_obj.parent.name not in exportable_root.all_objects):
                    if (blender_obj.parent.name in bpy.context.scene.objects):
                        walk_upward(new_xplane_bone)
                    else:
                        logger.warn(
                            f"'{blender_obj.name}' parent is not in the same collection and is in a different scene. "
                            f"'{blender_obj.parent.name}' and any it's parents will not be searched for split animations")
            except AttributeError: # For whatever of many reasons, we didn't walk up
                pass

            if new_xplane_obj:
                # This is different than asking the Blender Light its type!
                # This is refering to the old style default light
                if isinstance(new_xplane_obj, XPlaneLight):
                    self.lights.append(new_xplane_obj)
                new_xplane_obj.collect()
            elif blender_obj:
                print(f"Blender Object: {blender_obj.name}, didn't convert")
                pass

            def make_bones_for_armature_bones(arm_obj:bpy.types.Object)->Dict[str, XPlaneBone]:
                """
                Makes XPlaneBones for all bones in an armature, returns a map betweeen
                Blender Bone Names and the XPlaneBones that are associated with them.

                These are used later to pair XPlaneObjects with their correct parent bones
                """
                assert arm_obj.type == "ARMATURE", arm_obj.name + " must be armature"
                blender_bones_to_xplane_bones = {}
                def _recurse_bone(bl_bone:bpy.types.Bone, parent_xp_bone:XPlaneBone):
                    """
                    Recurses down an armature's bone tree, making XPlaneBones for each Blender Bone
                    """
                    # For every 'Bone' we make an XPlaneBone all to itself, it becomes the new parent instead of the
                    # bone the armature is connected to
                    parent_xp_bone = XPlaneBone(xplane_file=self, blender_obj=arm_obj, blender_bone=bl_bone, xplane_obj=None, parent_xplane_bone=parent_xp_bone)
                    blender_bones_to_xplane_bones[bl_bone.name] = parent_xp_bone
                    for child in bl_bone.children:
                        _recurse_bone(child, parent_xp_bone)

                # Run recurse for the top level bones
                for top_level_bone in filter(lambda b: not b.parent, arm_obj.data.bones):
                    _recurse_bone(top_level_bone, new_xplane_bone)
                return blender_bones_to_xplane_bones

            # If this is an armature, first build up the bones by tracking recursively down, then continue on
            # but skipping making the conversion again
            if blender_obj and blender_obj.type == "ARMATURE":
                real_bone_parents = make_bones_for_armature_bones(blender_obj)

            for child_obj in parent_blender_objects:
                if (isinstance(exportable_root, bpy.types.Collection)
                    and child_obj.name not in exportable_root.all_objects):
                    continue
                if (blender_obj
                    and blender_obj.type == "ARMATURE"
                    and child_obj.parent_type == "BONE"):
                    if child_obj.parent_bone not in blender_obj.data.bones:
                        logger.warn("".join((
                            f"{child_obj.name}",
                            " and its children" if child_obj.children else "",
                            " will not export,",
                            f" it's parent bone '{child_obj.parent_bone}' is",
                            f" not a real bone in {blender_obj.name}" if child_obj.parent_bone else " empty")))
                        # Ignored cases don't get their children examined
                        continue
                    else:
                        parent_bone = real_bone_parents[child_obj.parent_bone]
                        assert parent_bone, "Must have parent bone for further recursion"
                        recurse(child_obj,
                                 parent_bone,
                                 allowed_children(child_obj)
                                 )
                else: # no parent by armature-bone
                    parent_bone = new_xplane_bone

                assert parent_bone, "Must have parent bone for further recursion"
                recurse(child_obj,
                         parent_bone,
                         allowed_children(child_obj)
                        )
            try:
                if new_xplane_bone.blenderObject.type == "ARMATURE":
                    for xp_bone in real_bone_parents.values():
                        xp_bone.sortChildren()
            except AttributeError: # Collection won't have a blenderObject
                pass
            new_xplane_bone.sortChildren()
        #--- end _recurse function -------------------------------------------
        if isinstance(exportable_root, bpy.types.Collection):
            all_allowed_objects = allowed_children(exportable_root)
            all_allowed_names = [o.name for o in all_allowed_objects]
            recurse(parent=None,
                    parent_bone=None,
                    parent_blender_objects=[
                        o for o in all_allowed_objects if o.parent is None
                        or o.parent.name not in all_allowed_names
                    ])
        elif isinstance(exportable_root, bpy.types.Object):
            recurse(parent=exportable_root,
                     parent_bone=None,
                     parent_blender_objects=allowed_children(exportable_root))
        else:
            assert False, f"Unsupported root_object type {type(exportable_root)}"

    #TODO: Test this, needs code coverage
    def get_xplane_objects(self)->List["XPlaneObjects"]:
        """
        Returns a list of all XPlaneObjects collected by recursing down the
        completed XPlaneBone tree
        """
        assert self.rootBone, "Must be called after collection is finished"

        def get_xplane_objects_from_bone_tree(bone:XPlaneBone)->List["XPlaneObjects"]:
            xp_objects = []
            if bone.xplaneObject:
                xp_objects.append(bone.xplaneObject)
            for child_bone in bone.children:
                xp_objects.extend(get_xplane_objects_from_bone_tree(child_bone))
            return xp_objects
        return get_xplane_objects_from_bone_tree(self.rootBone)

    def validateMaterials(self)->bool:
        objects = self.get_xplane_objects()

        for xplaneObject in objects:
            if xplaneObject.type == 'MESH' and xplaneObject.material.options:
                errors, warnings = xplaneObject.material.isValid(self.options.export_type)

                for error in errors:
                    logger.error('Material "%s" in object "%s" %s' % (xplaneObject.material.name, xplaneObject.blenderObject.name, error))

                for warning in warnings:
                    logger.warn('Material "%s" in object "%s" %s' % (xplaneObject.material.name, xplaneObject.blenderObject.name, warning))

        if logger.hasErrors():
            return False

        return True

    def getMaterials(self)->List[bpy.types.Material]:
        '''
        Returns a list of the materials used in the OBJ, or an empty list if none found
        Must be called after XPlaneFile.collectBlenderObjects
        '''

        materials = []
        objects = self.get_xplane_objects()

        for xplaneObject in objects:
            if xplaneObject.type == 'MESH' and xplaneObject.material and xplaneObject.material.options:
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
                        errors, warnings = material.isCompatibleTo(refMaterial, self.options.export_type, False)
                        xplaneObject = material.xplaneObject
                        for error in errors:
                            logger.error('Material "%s" in object "%s" %s' % (material.name, xplaneObject.blenderObject.name, error))

                        for warning in warnings:
                            logger.warn('Material "%s" in object "%s" %s' % (material.name, xplaneObject.blenderObject.name, warning))

        if logger.hasErrors():
            return False

        return True

    def writeFooter(self):
        return "# Build with Blender %s (build %s). Exported with XPlane2Blender %s" % (bpy.app.version_string, bpy.app.build_hash, xplane_helpers.VerStruct.current())


    def write(self)->str:
        """
        Writes the contents of the file to one giant string with \n's,
        to be written to a file or compared in a unit test
        """
        self.mesh.collectXPlaneObjects(self.get_xplane_objects())

        # validate materials
        if not self.validateMaterials():
            return ''

        # detect reference materials
        self.referenceMaterials = xplane_material_utils.getReferenceMaterials(
            self.getMaterials(),
            self.options.export_type
        )

        refMatNames = [refMat.name for refMat in self.referenceMaterials if refMat]
        logger.info("Using the following reference materials: %s" % ", ".join(refMatNames))

        # validation was successful
        # retrieve reference materials
        # and compare all materials against reference materials
        if self.options.autodetectTextures == False:
            logger.info('Autodetect textures overridden for file %s: not fully checking manually entered textures against Blender-based reference materials\' textures' % (self.filename))

        if not self.compareMaterials(self.referenceMaterials):
            return ''

        o = ''
        o += self.header.write()
        o += '\n'

        meshOut = self.mesh.write()
        o += meshOut


        if len(meshOut):
            o += '\n'

        # TODO: deprecate in v3.4
        lightsOut = self.lights.write()
        o += lightsOut

        if len(lightsOut):
            o += '\n'

        lodsOut = self._writeLods()
        o += lodsOut

        if len(lodsOut):
            o += '\n'

        o += self.writeFooter()

        return o

    def _writeLods(self):
        o = ''
        numLods = int(self.options.lods)

        # if lods are present we need one base lod containing all objects
        # not in a lod that should always be visible
        if numLods > 0:
            smallestNear = float(self.options.lod[0].near)
            tallestFar = float(self.options.lod[0].far)

            for lod in self.options.lod:
                near = float(lod.near)
                far = float(lod.far)

                if smallestNear > near:
                    smallestNear = near

                if tallestFar < far:
                    tallestFar = far

            if smallestNear > 0:
                o += "ATTR_LOD 0.0 %s\n" % floatToStr(smallestNear)
                o += self.commands.write()
        else:
            o += self.commands.write()

        # write commands for each additional LOD
        for lodIndex in range(0, numLods):
            if lodIndex < len(self.options.lod):
                o += "ATTR_LOD %s %s\n" % (
                    floatToStr(self.options.lod[lodIndex].near),
                    floatToStr(self.options.lod[lodIndex].far)
                )
                o += self.commands.write(lodIndex)

        #TODO: Who's idea was this? Is this in the OBJ Spec?
        # if lods are present we need to attach a closing lod
        # containing all objects not in a lod that should always be visible
        if numLods > 0 and tallestFar < 100000:
            o += "ATTR_LOD %s 100000\n" % floatToStr(tallestFar)
            o += self.commands.write()

        return o
