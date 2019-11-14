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
from io_xplane2blender.xplane_types import xplane_empty, xplane_material_utils

from ..xplane_helpers import floatToStr, logger
from .xplane_bone import XPlaneBone
from .xplane_commands import XPlaneCommands
from .xplane_header import XPlaneHeader
from .xplane_light import XPlaneLight
from .xplane_lights import XPlaneLights
from .xplane_mesh import XPlaneMesh
from .xplane_object import XPlaneObject
from .xplane_primitive import XPlanePrimitive

"""
Given the difficulty in keeping all these words straight, these
types have been created. Use these to keep yourself from
running in circles
"""

"""An Object with an XPlaneLayer property"""
PotentialRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
An Object with an XPlaneLayer property that also meets all other requirements.
It doesn't mean the contents will not have any warnings or errors
"""
ExportableRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
The heirarchy allows these as parents, but Collections can't be real children
"""
BlenderParentType = Union[bpy.types.Collection, bpy.types.Object]
BlenderObject = bpy.types.Object
BlenderCollection = bpy.types.Collection

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
        for child in exportable_roots:
            if xplane_helpers.is_exportable_root(child):
                nested_errors.add(f"Exportable Roots cannot be nested, unmark {child.name} as a Root or change its parentage")
            log_nested_roots(child.children)

    log_nested_roots(exportable_root.children)
    for error in sorted(nested_errors):
        logger.error(error)

    layer_props = exportable_root.xplane.layer
    filename = layer_props.name if layer_props.name else exportable_root.name
    xplane_file = XPlaneFile(filename, layer_props)
    xplane_file.create_xplane_bone_hiearchy(exportable_root)
    print("Final Root Bone (2.80)")
    print(xplane_file.rootBone)
    return xplane_file

class XPlaneFile():
    """
    Represents the total contents of a .obj file and
    the settings affecting the output
    """
    def __init__(self, filename:str, options:xplane_props.XPlaneLayer)->None:
        self.filename = filename

        self.options = options

        self.mesh = XPlaneMesh()

        self.lights = XPlaneLights()

        self.header = XPlaneHeader(self, 8)

        self.commands = XPlaneCommands(self)

        # the root bone: origin for all animations/objects
        self.rootBone = None

        # materials representing the reference for export
        self.referenceMaterials = None

    def create_xplane_bone_hiearchy(self, exportable_root:ExportableRoot)->Optional[XPlaneObject]:
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

        def walk_upward(walk_start_bone:XPlaneBone)->XPlaneBone:
            """
            Walks upwards the parent-child tree.

            start-bone must
            """
            assert walk_start_bone.blenderObject

            tmp_bone_head = walk_start_bone
            o_bone_parent = walk_start_bone.parent
            def walk_upward_recursive(current_bone: XPlaneBone):
                nonlocal tmp_bone_head
                # If we haven't reached the top yet, make a bone for parent and move the head
                if current_bone.blenderObject.parent:
                    new_parent_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=current_bone.blenderObject.parent,
                        blender_bone=None,
                        xplane_obj=convert_to_xplane_object(current_bone.blenderObject.parent),
                        parent_xplane_bone=None)
                    new_parent_bone.children.append(current_bone)
                    current_bone.parent = new_parent_bone
                    tmp_bone_head = new_parent_bone
                    walk_upward_recursive(new_parent_bone)

            walk_upward_recursive(tmp_bone_head)
            index = o_bone_parent.children.index(walk_start_bone)
            o_bone_parent.children.remove(walk_start_bone)
            o_bone_parent.children.append(tmp_bone_head)
            tmp_bone_head.parent = o_bone_parent

            return tmp_bone_head


        def _recurse(parent: BlenderParentType, parent_bone: Optional[XPlaneBone], parent_blender_objects:BlenderObject)->None:
            """
            Main function for recursing down tree. parent_blender_objects will be different from blender_objects will not equal parent.children, when a parent is a collection
            """
            #print(
            #    f"Parent: {parent.name}" if parent else f"Root: {exportable_root.name}",
            #    #f"Parent Bone: {parent_bone}" if parent_bone else "No Parent Bone",
            #    f"parent_blender_objects {[o.name for o in parent_blender_objects]}",
            #    sep="\n"
            #)
            #print("===========================================================")

            blender_obj = parent
            if blender_obj:
                new_xplane_obj = convert_to_xplane_object(blender_obj)
            else:
                new_xplane_obj = None
            #print(f"new_xplane_obj:\n{new_xplane_obj}")

            if parent_bone:
                new_xplane_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=blender_obj,
                        blender_bone=None,
                        xplane_obj=new_xplane_obj,
                        parent_xplane_bone=parent_bone)
            else:
                # We have to do the manual work
                new_xplane_bone = XPlaneBone(self,
                                             blender_obj=blender_obj,
                                             blender_bone=None,
                                             xplane_obj=new_xplane_obj,
                                             parent_xplane_bone=None)

                self.rootBone = new_xplane_bone
                #new_xplane_bone.xplaneObject = new_xplane_obj
                #new_xplane_bone.xplaneObject.xplaneBone = new_xplane_bone
            try:
                if blender_obj.parent and blender_obj.parent.name not in exportable_root.all_objects:
                    branch_head = walk_upward(new_xplane_bone)
                    print("HERE", blender_obj.name)
            except AttributeError:
                print(blender_obj)
                pass

            if new_xplane_obj:
                # This is different than asking the blender Object its type!
                # this is refering to the old style default light
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
                        _recurse(child_obj,
                                 real_bone_parents[child_obj.parent_bone],
                                 child_obj.children,
                                 )
                else:
                    if (isinstance(exportable_root, bpy.types.Collection)
                        and child_obj.name not in exportable_root.all_objects):
                        logger.error(
                            f"{child_obj.name} is outside the current exportable collection. It and any children cannot be collected"
                        )
                        continue

                    if child_obj.name not in bpy.context.scene.objects:
                        # This will only ever trigger for Exportable Objects,
                        # not Exportable Collections
                        logger.error(
                            f"{child_obj.name} is outside the current scene. It and any children cannot be collected"
                        )
                        continue

                    _recurse(child_obj,
                             new_xplane_bone,
                             child_obj.children)

            try:
                if new_xplane_bone.blenderObject.type == "ARMATURE":
                    for xp_bone in real_bone_parents.values():
                        xp_bone.sortChildren()
            except AttributeError: # Collection won't have a blenderObject
                pass
            new_xplane_bone.sortChildren()
        #--- end _recurse function -------------------------------------------
        if isinstance(exportable_root, bpy.types.Collection):
            _recurse(parent=None,
                     parent_bone=None,
                     parent_blender_objects=list(
                         filter(
                             lambda o: o.parent is None or o.parent.name not in
                             exportable_root.all_objects,
                             exportable_root.all_objects)))
        elif isinstance(exportable_root, bpy.types.Object):
            self.rootBone = XPlaneBone(self,
                                       blender_obj=exportable_root,
                                       blender_bone=None,
                                       xplane_obj=None,
                                       parent_xplane_bone=None)
            _recurse(parent=exportable_root,
                     parent_bone=None,
                     parent_blender_objects=exportable_root.children)
        else:
            assert False, f"Unsupported root_object type {type(exportable_root)}"

    #TODO: Test this, needs code coverage
    def get_xplane_objects(self)->List["XPlaneObjects"]:
        """
        Returns a list of all XPlaneObjects collected by recursing down the
        completed XPlaneBone tree
        """
        assert self.rootBone, "Must be called after collection is finished"

        def get_xplane_objects_from_bone_tree(bone:"XPlaneBone")->List["XPlaneObjects"]:
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

        refMatNames = []
        for refMat in self.referenceMaterials:
            if refMat:
                refMatNames.append(refMat.name)

        logger.info('Using the following reference materials: %s' % ', '.join(refMatNames))

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
