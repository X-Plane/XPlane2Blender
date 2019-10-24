'''
This is the entry point for the exporter's collection and where it starts writing, proper.
There are mirroring methods for Layer and Root Objects mode. The important paths are

createFilesFromBlenderRootObjects
|___createFileFromBlenderRootObject (Exporter decides what to inspect)
    |
    |____collectBlenderObjects (Exporter also decides what to inspect),
    | |  |___convertBlenderObjects (Where BlenderObjects become XPlaneObjects)
    | |__collectBonesFromBlenderBones/Objects (tree traversal of collected Blender Objects)
    |
 ___createFileBlenderLayerIndex (Exporter decides what to inspect)
|
createFilesFromBlenderLayers
'''


import collections
import pprint

import bpy
import mathutils

import operator
from typing import Dict, List, Union, Optional
from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_types import xplane_empty
from io_xplane2blender.tests import test_creation_helpers

from ..xplane_helpers import floatToStr, logger
from .xplane_bone import XPlaneBone
from .xplane_commands import XPlaneCommands
from .xplane_header import XPlaneHeader
from .xplane_light import XPlaneLight
from .xplane_lights import XPlaneLights
from io_xplane2blender.xplane_types import xplane_material_utils
from .xplane_mesh import XPlaneMesh
from io_xplane2blender import xplane_props
from .xplane_object import XPlaneObject
from .xplane_primitive import XPlanePrimitive


"""
Given the difficulty in keeping all these words straight, these
types have been created. Use these to keep yourself from
running in circles
"""

"""An Object with an XPlaneLayer property"""
PotentialOBJRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
An Object with an XPlaneLayer property that also meets all other requirements.
It doesn't mean the contents will not have any warnings or errors
"""
ExportableOBJRoot = Union[bpy.types.Collection, bpy.types.Object]

"""
The heirarchy allows these as parents, but Collections can't be real children
"""
BlenderParentType = Union[bpy.types.Collection, bpy.types.Object]
BlenderObject = bpy.types.Object
BlenderCollection = bpy.types.Collection

def createFilesFromBlenderRootObjects(scene:bpy.types.Scene)->List["XPlaneFile"]:
    xplane_files = [] # type: List["XPlaneFile"]
    for root_object in filter(lambda o: xplane_helpers.is_root_object(o), scene.objects[:] + xplane_helpers.get_all_collections_in_scene(scene)[1:]):
        if root_object.xplane.layer.export:
            xplane_file = createFileFromBlenderRootObject(root_object)
            xplane_files.append(xplane_file)

    return xplane_files


def createFileFromBlenderRootObject(exportable_root:ExportableOBJRoot)->"XPlaneFile":
    layer_props = exportable_root.xplane.layer
    filename = layer_props.name if layer_props.name else exportable_root.name
    xplane_file = XPlaneFile(filename, layer_props)
    import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev.core_7.2.1.201904261721\pysrc')
    import pydevd;pydevd.settrace()
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

        #TODO: There is no export mode anymore, there is only root objects
        # But, I'd rather not deal with removing it all right now
        self.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

        # the root bone: origin for all animations/objects
        self.rootBone = None

        # materials representing the reference for export
        self.referenceMaterials = None

    def create_xplane_bone_hiearchy(self, root_object:ExportableOBJRoot)->Optional[XPlaneObject]:
        def convert_to_xplane_object(blender_obj:bpy.types.Object)->Optional[XPlaneObject]:
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

        def _recurse(parent: BlenderParentType, parent_bone: XPlaneBone, parent_blender_objects:BlenderObject)->None:
            """
            Main function for recursing down tree. parent_blender_objects will be different from blender_objects will not equal parent.children, when a parent is a collection
            """
            print(
                f"Parent: {parent.name}" if parent else f"Root: {root_object.name}",
                #f"Parent Bone: {parent_bone}" if parent_bone else "No Parent Bone",
                f"parent_blender_objects {[o.name for o in parent_blender_objects]}",
                sep="\n"
            )
            print("===========================================================")

            blender_obj = parent
            if blender_obj:
                new_xplane_obj = convert_to_xplane_object(blender_obj)
            else:
                new_xplane_obj = None

            if parent_bone:
                new_xplane_bone = XPlaneBone(
                        xplane_file=self,
                        blender_obj=blender_obj,
                        blender_bone=None,
                        xplane_obj=new_xplane_obj,
                        parent_xplane_bone=parent_bone)
            else:
                # We're in root, so,
                new_xplane_bone = self.rootBone
            #print(f"Current XPlaneBone", new_xplane_bone)

            if new_xplane_obj:
                print(f"New XPlaneObject: {new_xplane_obj.name}")
                # This is different than asking the blender Object its type!
                # this is refering to the old style default light
                if isinstance(new_xplane_obj, XPlaneLight):
                    self.lights.append(new_xplane_obj)
                new_xplane_obj.collect()
            else:
                try:
                    print(f"Blender Object: {blender_object.name}, didn't convert")
                except:
                    pass

            if blender_obj != self.rootBone.blenderObject and blender_obj.xplane.layer.get("isExportableRoot"):
                logger.error(f"{parent.name} is marked as an exportable root. Nested Exportable Roots are not allowed")

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
            #  but skipping making the conversion again

            if blender_obj and blender_obj.type == "ARMATURE":
                print(f"Recursing down {blender_obj.name}'s bone tree")
                real_bone_parents = make_bones_for_armature_bones(blender_obj)

            for child_obj in parent_blender_objects:
                print("Testing child's name", child_obj.name)
                if (blender_obj
                    and blender_obj.type == "ARMATURE"
                    and child_obj.parent_type == "BONE"):
                    if child_obj.parent_bone not in blender_obj.data.bones:
                        # Ignored cases don't get their children examined
                        continue
                    else:
                        _recurse(child_obj,
                                 real_bone_parents[child_obj.parent_bone],
                                 child_obj.children,
                                 )
                else:
                    _recurse(child_obj,
                             new_xplane_bone,
                             child_obj.children,
                             )
        #--- end _recurse function -------------------------------------------
        print("RootBone", self.rootBone)
        if isinstance(root_object, bpy.types.Collection):
            self.rootBone = XPlaneBone(self, None, None, None)
            _recurse(parent=None, parent_bone=None, parent_blender_objects=list(filter(lambda o: o.parent is None or o.parent.name not in root_object.all_objects, root_object.all_objects)))
        elif isinstance(root_object, bpy.types.Object):
            self.rootBone = XPlaneBone(self, root_object, None, convert_to_xplane_object(root_object))
            _recurse(parent=root_object, parent_bone=None, parent_blender_objects=root_object.children)
        else:
            assert False, f"Unsupported root_object type {type(root_object)}"


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
