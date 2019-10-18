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

import bpy
import mathutils

import operator
from typing import List, Union, Optional
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
    if isinstance(exportable_root, bpy.types.Collection):
        fake_empty = test_creation_helpers.create_datablock_empty(
                test_creation_helpers.DatablockInfo(name=exportable_root.name)
                )
    try:
        xplane_file.create_xplane_bone_hiearchy(exportable_root)
    except:
        raise
    finally:
        #bpy.data.objects.remove(fake_empty, do_unlink=True)
        pass

    print("Final Bones")
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

        # dict of xplane objects within the file
        self.objects = collections.OrderedDict() # type: collections.OrderedDict

        #TODO: There is no export mode anymore, there is only root objects
        # But, I'd rather not deal with removing it all right now
        self.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

        # the root bone: origin for all animations/objects
        self.rootBone = None

        # materials representing the reference for export
        self.referenceMaterials = None

    def create_xplane_bone_hiearchy(self, root_object:ExportableOBJRoot)->Optional[XPlaneObject]:
        def _convert_to_blender_obj(blender_obj:bpy.types.Object)->Optional[XPlaneObject]:
            assert isinstance(blender_obj, bpy.types.Object), "Can only convert bpy.types.Object to XPlaneObject"
            converted_xplane_obj = None
            if blender_obj.type == "MESH":
                converted_xplane_obj = XPlanePrimitive(blender_obj)
            elif blender_obj.type == "LIGHT":
                converted_xplane_obj  = XPlaneLight(blender_obj)
            elif blender_obj.type == "ARMATURE":
                converted_xplane_obj = XPlaneObject(blender_obj)
            elif blender_obj.type == "EMPTY":
                converted_xplane_obj = xplane_empty.XPlaneEmpty(blender_obj)
            else:
                assert False, blender_obj.type + " is an unknown Type"

            #print("\t %s: adding to list" % blender_obj.name)
            return converted_xplane_obj

        def _get_child_blender_objects(parent: BlenderParentType):
            pass

        def _recurse(parent: BlenderParentType, parent_bone: XPlaneBone, parent_blender_objects:BlenderObject, is_root:bool=False)->XPlaneBone:
            print(
                f"Parent: {parent.name}",
                f"Parent Bone: {parent_bone}",
                f"parent_blender_objects {[o.name for o in parent_blender_objects]}",
                sep="\n"
            )
            """
            Main function for recursing down tree. blender_objects will not equal parent.children, when a parent is a collection
            """
            #if (parent != self.rootBone.blenderObject
            #    and (parent.xplane.layer.get("isExportableRoot")
            #        or parent.xplane.layer.get("isExportableCollection"))):
            #    logger.error("Cannot have nested root objects!")
            import sys;sys.path.append(r'C:\Users\Ted\.p2\pool\plugins\org.python.pydev.core_7.2.1.201904261721\pysrc')
            #import pydevd;pydevd.settrace()
            #if isinstance(parent, bpy.types.Collection) and parent.children:
                #last_mode = "collection"
                # Recurse to the bottom of all the collections
                #for child_col in parent.children:
                    #_recurse(last_mode, child_col, child_collection.objects) #TODO: These are unsorted! WTF!
                #return

            assert not isinstance(parent, bpy.types.Collection), "After recursing to {parent.name}, top-level objects should have been used"
            """
            for top_level in sorted(
                    parent_blender_objects,
                    # collection version, gotta fix that filter(lambda o: o.parent not in parent.objects or o.parent is None, blender_objects),
                    #filter(lambda o: o.parent not in parent.children or o.parent is None, blender_objects),
                    key=lambda o: o.name):
                print(f"TopLevel {top_level.name}")

            """
            # Create XPlaneObject/XPlaneBone
            # Set up bone relationships
            # Collect from bones and XPlane
            new_xplane_obj = _convert_to_blender_obj(parent)
            new_xplane_bone = XPlaneBone(blender_obj=parent, xplane_file=self, xplane_obj=new_xplane_obj, parent_bone=parent_bone)
            if not is_root:
                parent_bone.children.append(new_xplane_bone)

            new_xplane_bone.collectAnimations()
            if new_xplane_obj:
                print(f"New XPlaneObject: {new_xplane_obj.name}")
                # This is different than asking the blender Object its type!
                # this is refering to the old style default light
                if isinstance(new_xplane_obj, XPlaneLight):
                    self.lights.append(new_xplane_obj)
                new_xplane_obj.collect()
            else:
                print(f"Blender Object: {top_level.name}, didn't convert")
            print(f"New XPlaneBone", new_xplane_bone)

            if is_root:
                self.rootBone = new_xplane_bone

            for child_obj in parent.children:
                print("trying child", child_obj.name)
                _recurse(child_obj, new_xplane_bone, child_obj.children)

        print("RootBone", self.rootBone)
        _recurse(parent=root_object, parent_bone=None, parent_blender_objects=root_object.children, is_root=True)

    #def collectBlenderObjects(self, blenderObjects):
        #for blenderObject in blenderObjects:
            #xplaneObject = self.convertBlenderObject(blenderObject)

            #if xplaneObject:
                #if isinstance(xplaneObject, XPlaneLight):
                    ## attach xplane light to lights list
                    #self.lights.append(xplaneObject)

                ## store xplane object under same name as blender object in dict
                #self.objects[blenderObject.name] = xplaneObject

    # collects all child bones for a given parent bone given a list of blender objects
    def collectBonesFromBlenderObjects(self, parentBone, blenderObjects,
                                       needsFilter:bool = True, # Set to true for when it is unsure if blenderObjects only contains
                                                                # things with parentBone as it's parent. Needs to filter collection of blenderObjects to just
                                                                # find the one whose parent is the root, root bone of an Armature, or parentBone
                                       noRealBones:bool = False): #noRealBones is used for
        '''
        The collectBonesFromBlender(Bones|Objects) walk through Blender's parent-child hierarchy and translate it to our XPlaneBone tree
        - Each XPlaneObject has an XPlaneBone
        - Not all XPlaneBones have an XPlaneObject (ROOT bone and bones connected to unconvertable BlenderObjects)
        '''
        parentBlenderObject = parentBone.blenderObject
        parentBlenderBone = parentBone.blenderBone

        def objectFilter(blenderObject):
            if noRealBones and blenderObject.parent_type == 'BONE':
                return False
            if parentBlenderObject:
                return blenderObject.parent == parentBlenderObject
            elif parentBlenderBone:
                return blenderObject.parent_type == 'BONE' and blenderObject.parent_bone == parentBlenderBone
            elif blenderObject.parent_type == 'OBJECT':
                # Find objects whose parent is the root
                return blenderObject.parent == None
            elif blenderObject.parent_type == 'BONE':
                # Find bones whose parent is the
                # Armature Block (and don't have a parent bone)
                return blenderObject.parent_bone == ""

        if needsFilter:
            blenderObjects = list(filter(objectFilter, blenderObjects))

        for blenderObject in blenderObjects:
            xplaneObject = None
            if blenderObject.name in self.objects:
                xplaneObject = self.objects[blenderObject.name]

            bone = XPlaneBone(blenderObject, xplaneObject, parentBone, self)
            parentBone.children.append(bone)
            bone.collectAnimations()

            # xplaneObject is now complete and can collect all data
            if xplaneObject:
                xplaneObject.collect()

            # expand group objects to temporary objects
            # TODO: Blender 2.8 removes groups in favor of collections.
            # obj.dupli_type == "GROUP" is no more, obj.instance_type == "COLLECTION" seems similar but until we understand fully how
            # collections and instanced collections work, this feature is removed

            # collect armature bones
            if blenderObject.type == 'ARMATURE':
                self.collectBonesFromBlenderBones(bone, blenderObject, blenderObject.data.bones)
                # Collect direct data-block children - some authors parent data blocks directly to the
                # armature, then pose the armature via data block key framing.  The second 'true' here
                # tells us to SKIP any direct child with a bone parent.  In Blender, a data block that
                # is parented to a bone shows up as a datablock child of the armature, so without this
                # we'd export each data block twice, which is bad.
                self.collectBonesFromBlenderObjects(bone, blenderObject.children, True, True)

            # collect regular children
            else:
                self.collectBonesFromBlenderObjects(bone, blenderObject.children, False)

        parentBone.sortChildren()

    def collectBonesFromBlenderBones(self, parentBone, blenderArmature, blenderBones, needsFilter = True):
        parentBlenderBone = parentBone.blenderBone

        def boneFilter(blenderBone):
            if parentBlenderBone:
                return blenderBone.parent == parentBlenderBone
            else:
                return blenderBone.parent == None

        # filter out all objects with given parent
        if needsFilter:
            blenderBones = filter(boneFilter, blenderBones)

        for blenderBone in blenderBones:
            bone = XPlaneBone(blenderArmature, None, parentBone, self)
            bone.blenderBone = blenderBone
            parentBone.children.append(bone)

            bone.collectAnimations()

            # collect child blender objects of this bone
            childBlenderObjects = self.getChildBlenderObjectsForBlenderBone(blenderBone, blenderArmature)

            self.collectBonesFromBlenderObjects(bone, childBlenderObjects, False)
            self.collectBonesFromBlenderBones(bone, blenderArmature, blenderBone.children, False)

        parentBone.sortChildren()

    def getChildBlenderObjectsForBlenderBone(self, blenderBone, blenderArmature):
        blenderObjects = []

        for name in self.objects:
            xplaneObject = self.objects[name]

            if xplaneObject.blenderObject.parent_type == 'BONE' and \
               xplaneObject.blenderObject.parent == blenderArmature and \
               xplaneObject.blenderObject.parent_bone == blenderBone.name:
                blenderObjects.append(xplaneObject.blenderObject)

        return blenderObjects

    def collectFromBlenderRootObject(self, blenderRootObject:PotentialOBJRoot)->None:
        """
        Collects all objects in a Root Object, recursing down the
        Blender heirarchy by Collection, Object's child, and Armature's Child by Bone
        """

        currentFrame = bpy.context.scene.frame_current

        blenderObjects = [blenderRootObject]

        def collectChildren(parentObject):
            for blenderObject in filter(lambda child: child.name in bpy.context.scene.objects, parentObject.children):
                logger.info("scanning %s" % blenderObject.name)

                blenderObjects.append(blenderObject)
                collectChildren(blenderObject)

        collectChildren(blenderRootObject)
        self.collectBlenderObjects(blenderObjects)

        # setup root bone and root xplane object
        rootXPlaneObject = self.objects[blenderRootObject.name]
        self.rootBone = XPlaneBone(blenderRootObject, rootXPlaneObject, None, self)

        # need to collect data
        rootXPlaneObject.collect()

        self.collectBonesFromBlenderObjects(self.rootBone, blenderObjects)

        # restore frame before export
        bpy.context.scene.frame_set(frame = currentFrame)

    def convertBlenderObject(self, blenderObject: bpy.types.Object)->Optional[XPlaneObject]:
        '''
        Converts Blender object into an XPlaneObject or subtype and returns it.
        Returns None if Blender Object isn't supported
        '''
        xplaneObject = None # type: Optional[XPlaneObject]

        # mesh: let's create a prim out of it
        if blenderObject.type == "MESH":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlanePrimitive(blenderObject)
        # light: let's create a XPlaneLight. Those cannot have children (yet).
        elif blenderObject.type == "LIGHT":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject  = XPlaneLight(blenderObject)
        elif blenderObject.type == "ARMATURE":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlaneObject(blenderObject)
        elif blenderObject.type == "EMPTY":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = xplane_empty.XPlaneEmpty(blenderObject)

        return xplaneObject

    def getBoneByBlenderName(self, name: str, parent: XPlaneBone)->Optional[XPlaneBone]:
        '''
        Performs a depth first search of the child bones for a bone with matching name.
        Returns the bone or None if not found
        '''
        for bone in parent.children:
            if bone.getBlenderName() == name:
                return bone
            else: # decsent to children
                _bone = self.getBoneByBlenderName(name, bone)
                if _bone:
                    return _bone

        return None

    # Method: getObjectsList
    # Returns objects as a list
    def getObjectsList(self)->List[XPlaneObject]:
        '''
        Returns the objects that could be in this .obj.
        Can only be called after collectBlenderObjects during xplane_file's collection
        '''
        return self.objects.values()

    def validateMaterials(self):
        objects = self.getObjectsList()

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
        objects = self.getObjectsList()

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

    # Method: write
    # Returns OBJ file code
    def write(self):
        self.mesh.collectXPlaneObjects(self.getObjectsList())

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

        self.cleanup()

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
