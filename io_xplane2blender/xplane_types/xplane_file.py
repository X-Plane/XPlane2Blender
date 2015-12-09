# File: xplane_file.py
# Defines X-Plane file data type.

import bpy
import mathutils
from .xplane_bone import XPlaneBone
from .xplane_light import XPlaneLight
# from .xplane_line import XPlaneLine
# from .xplane_object import XPlaneObject
from .xplane_primitive import XPlanePrimitive
from .xplane_lights import XPlaneLights
from .xplane_mesh import XPlaneMesh
from .xplane_header import XPlaneHeader
from .xplane_commands import XPlaneCommands
from ..xplane_config import version
from ..xplane_helpers import floatToStr, logger
from .xplane_material_utils import getReferenceMaterials

# Function: getActiveLayers
# Returns indices of all active Blender layers.
#
# Returns:
#   list - Indices of all active blender layers.
def getActiveBlenderLayerIndexes():
    layers = []
    for i in range(0,len(bpy.context.scene.layers)):
        if bpy.context.scene.layers[i] and bpy.context.scene.xplane.layers[i].export:
            layers.append(i)

    return layers

def getXPlaneLayerForBlenderLayerIndex(layerIndex):
    if len(bpy.context.scene.xplane.layers) > 0:
        return bpy.context.scene.xplane.layers[layerIndex]
    else:
        return None

def getFilenameFromXPlaneLayer(xplaneLayer):
    if xplaneLayer.name == "":
        filename = "layer_%s" % (str(xplaneLayer.index+1).zfill(2))
    else:
        filename = xplaneLayer.name

    return filename

def getFileNameFromBlenderObject(blenderObject, xplaneLayer):
    if xplaneLayer.name == "":
        filename = blenderObject.name
    else:
        filename = xplaneLayer.name

    return filename

def createFilesFromBlenderLayers():
    xplaneFiles = []

    for layerIndex in getActiveBlenderLayerIndexes():
        xplaneFile = createFileFromBlenderLayerIndex(layerIndex)

        if xplaneFile:
            xplaneFiles.append(xplaneFile)

    return xplaneFiles

def createFileFromBlenderLayerIndex(layerIndex):
    xplaneFile = None
    xplaneLayer = getXPlaneLayerForBlenderLayerIndex(layerIndex)

    if xplaneLayer:
        xplaneFile = XPlaneFile(getFilenameFromXPlaneLayer(xplaneLayer), xplaneLayer)

        if xplaneFile:
            xplaneFile.exportMode = bpy.context.scene.xplane.exportMode
            xplaneFile.collectFromBlenderLayerIndex(layerIndex)

    return xplaneFile

def createFileFromBlenderRootObject(blenderObject):
    xplaneFile = None
    xplaneLayer = blenderObject.xplane.layer

    if xplaneLayer:
        xplaneFile = XPlaneFile(getFileNameFromBlenderObject(blenderObject, xplaneLayer), xplaneLayer)

        if xplaneFile:
            xplaneFile.exportMode = bpy.context.scene.xplane.exportMode
            xplaneFile.collectFromBlenderRootObject(blenderObject)

    return xplaneFile

def createFilesFromBlenderRootObjects(scene):
    xplaneFiles = []

    for blenderObject in scene.objects:
        if blenderObject.xplane.isExportableRoot and blenderObject.xplane.layer.export:
            xplaneFile = createFileFromBlenderRootObject(blenderObject)

            if xplaneFile:
                xplaneFiles.append(xplaneFile)

    return xplaneFiles

# Class: XPlaneFile
# X-Plane OBJ file
class XPlaneFile():
    def __init__(self, filename, options):
        self.filename = filename

        self.options = options

        self.mesh = XPlaneMesh()

        self.lights = XPlaneLights()

        self.header = XPlaneHeader(self, 8)

        self.commands = XPlaneCommands(self)

        # list of temporary objects that will be removed after export
        self._tempBlenderObjects = []

        # list of already expanded/resolved blender group instances
        self._resolvedBlenderGroupInstances = []

        # dict of xplane objects within the file
        self.objects = {}

        self.exportMode = 'layers'

        # the root bone: origin for all animations/objects
        self.rootBone = None

    # Method: collectFromBlenderLayerIndex
    # collects all objects in a given blender layer
    #
    # Parameters:
    #   layerIndex - int
    def collectFromBlenderLayerIndex(self, layerIndex):
        currentFrame = bpy.context.scene.frame_current

        blenderObjects = []

        for blenderObject in bpy.context.scene.objects:
            logger.info("scanning %s" % blenderObject.name)

            for i in range(len(blenderObject.layers)):
                if blenderObject.layers[i] == True and i == layerIndex and blenderObject.hide == False:
                    if not hasattr(blenderObject.xplane, 'export_mesh') or blenderObject.xplane.export_mesh[layerIndex] == True:
                        blenderObjects.append(blenderObject)

        self.collectBlenderObjects(blenderObjects)
        self.rootBone = XPlaneBone()
        self.rootBone.xplaneFile = self
        self.collectBonesFromBlenderObjects(self.rootBone, blenderObjects)

        # restore frame before export
        bpy.context.scene.frame_set(frame = currentFrame)

    def collectBlenderObjects(self, blenderObjects):
        for blenderObject in blenderObjects:
            xplaneObject = self.convertBlenderObject(blenderObject)

            if xplaneObject:
                if isinstance(xplaneObject, XPlaneLight):
                    # attach xplane light to lights list
                    self.lights.append(xplaneObject)

                # store xplane object under same name as blender object in dict
                self.objects[blenderObject.name] = xplaneObject

    def _resolveBlenderGroupInstance(self, blenderObject):
        tempBlenderObjects = []
        blenderGroupObjects = blenderObject.dupli_group.objects
        groupOffset = blenderObject.dupli_group.dupli_offset

        for blenderGroupObject in blenderGroupObjects:
            # create a copy
            blenderObjectCopy = blenderGroupObject.copy()
            self._tempBlenderObjects.append(blenderObjectCopy)
            tempBlenderObjects.append(blenderObjectCopy)

            # make it a child of the parent, to keep hierachy and transforms
            blenderObjectCopy.parent = blenderObject

            # set same layer as the parent
            blenderObjectCopy.layers = blenderObject.layers

            # set correct matrix
            blenderObjectCopy.matrix_world = blenderObject.matrix_world * mathutils.Matrix.Translation(-groupOffset) * blenderGroupObject.matrix_world

        self._resolvedBlenderGroupInstances.append(blenderObject.name)

        return tempBlenderObjects

    # collects all child bones for a given parent bone given a list of blender objects
    def collectBonesFromBlenderObjects(self, parentBone, blenderObjects, needsFilter = True):
        parentBlenderObject = parentBone.blenderObject
        parentBlenderBone = parentBone.blenderBone

        def objectFilter(blenderObject):
            if parentBlenderObject:
                return blenderObject.parent == parentBlenderObject
            elif parentBlenderBone:
                return blenderObject.parent_type == 'Bone' and blenderObject.parent_bone == parentBlenderBone
            elif blenderObject.parent_type == 'OBJECT':
                return blenderObject.parent == None
            elif blenderObject.parent_type == 'BONE':
                return blenderObject.parent_bone == ""

        # filter out all objects with given parent
        if needsFilter:
            blenderObjects = list(filter(objectFilter, blenderObjects))

        for blenderObject in blenderObjects:
            xplaneObject = None
            if blenderObject.name in self.objects:
                xplaneObject = self.objects[blenderObject.name]

            bone = XPlaneBone(blenderObject, xplaneObject, parentBone)
            bone.xplaneFile = self
            parentBone.children.append(bone)

            # xplaneObject is now complete and can collect all data
            if xplaneObject:
                xplaneObject.collect()

            bone.collectAnimations()

            # expand group objects to temporary objects
            if blenderObject.dupli_type == 'GROUP' and blenderObject.name not in self._resolvedBlenderGroupInstances:
                tempBlenderObjects = self._resolveBlenderGroupInstance(blenderObject)
                self.collectBlenderObjects(tempBlenderObjects)
                self.collectBonesFromBlenderObjects(bone, blenderObject.children, False)

            # collect armature bones
            elif blenderObject.type == 'ARMATURE':
                self.collectBonesFromBlenderBones(bone, blenderObject, blenderObject.data.bones)

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
            bone = XPlaneBone(blenderArmature, None, parentBone)
            bone.xplaneFile = self
            bone.blenderBone = blenderBone
            parentBone.children.append(bone)

            bone.collectAnimations()

            # collect child blender objects of this bone
            childBlenderObjects = self.getChildBlenderObjectsForBlenderBone(blenderBone)

            self.collectBonesFromBlenderObjects(bone, childBlenderObjects, False)
            self.collectBonesFromBlenderBones(bone, blenderArmature, blenderBone.children, False)

        parentBone.sortChildren()

    def getChildBlenderObjectsForBlenderBone(self, blenderBone):
        blenderObjects = []

        for name in self.objects:
            xplaneObject = self.objects[name]

            if xplaneObject.blenderObject.parent_type == 'BONE' and xplaneObject.blenderObject.parent_bone == blenderBone.name:
                blenderObjects.append(xplaneObject.blenderObject)

        return blenderObjects

    # Method: collectFromBlenderRootObject
    # collects all objects in a given blender root object
    #
    # Parameters:
    #   rootObject - blender object
    def collectFromBlenderRootObject(self, blenderRootObject):
        currentFrame = bpy.context.scene.frame_current

        blenderObjects = [blenderRootObject]

        def collectChildren(parentObject):
            for blenderObject in parentObject.children:
                logger.info("scanning %s" % blenderObject.name)

                blenderObjects.append(blenderObject)
                collectChildren(blenderObject)

        collectChildren(blenderRootObject)
        self.collectBlenderObjects(blenderObjects)

        # setup root bone and root xplane object
        rootXPlaneObject = self.objects[blenderRootObject.name]
        self.rootBone = XPlaneBone(blenderRootObject, rootXPlaneObject)
        self.rootBone.xplaneFile = self

        # need to collect data
        rootXPlaneObject.collect()

        self.collectBonesFromBlenderObjects(self.rootBone, blenderObjects)

        # restore frame before export
        bpy.context.scene.frame_set(frame = currentFrame)

    # Method: convertBlenderObject
    # Converts/wraps blender object into an <XPlaneObject> or subtype
    #
    # Returns:
    #   <XPlaneObject> or None if object type is not supported
    def convertBlenderObject(self, blenderObject):
        xplaneObject = None

        # mesh: let's create a prim out of it
        if blenderObject.type == "MESH":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlanePrimitive(blenderObject)

        # lamp: let's create a XPlaneLight. Those cannot have children (yet).
        elif blenderObject.type == "LAMP":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject  = XPlaneLight(blenderObject)

        return xplaneObject

    def getBoneByBlenderName(self, name, parent = None):
        if not parent:
            parent = self.rootBone

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
    def getObjectsList(self):
        objects = []
        for name in self.objects:
            objects.append(self.objects[name])

        return objects

    def validateMaterials(self):
        objects = self.getObjectsList()

        for xplaneObject in objects:
            if xplaneObject.type == 'PRIMITIVE' and xplaneObject.material.options:
                errors = xplaneObject.material.isValid(self.options.export_type)

                if errors and len(errors):
                    for error in errors:
                        logger.error('Material in object "%s" %s' % (xplaneObject.blenderObject.name, error))

        if logger.hasErrors():
            return False

        return True

    def getMaterials(self):
        materials = []
        objects = self.getObjectsList()

        for xplaneObject in objects:
            if xplaneObject.type == 'PRIMITIVE' and xplaneObject.material and xplaneObject.material.options:
                materials.append(xplaneObject.material)

        return materials

    def compareMaterials(self, refMaterials):
        materials = self.getMaterials()

        for refMaterial in refMaterials:
            if refMaterial is not None:
                for material in materials:
                    errors = material.isCompatibleTo(refMaterial, self.options.export_type)

                    if errors and len(errors):
                        for error in errors:
                            logger.error('Material in object "%s" %s.' % (material.xplaneObject.blenderObject.name, error))

        if logger.hasErrors():
            return False

        return True

    def writeFooter(self):
        build = 'unknown'

        if hasattr(bpy.app, 'build_hash'):
            build = bpy.app.build_hash
        else:
            build = bpy.app.build_revision

        return "# Build with Blender %s (build %s) Exported with XPlane2Blender %d.%d.%d" % (bpy.app.version_string,build, version[0], version[1], version[2])

    # Method: write
    # Returns OBJ file code
    def write(self):
        self.mesh.collectXPlaneObjects(self.getObjectsList())

        # validate materials
        if not self.validateMaterials():
            return ''

        # validation was successful
        # retrieve reference materials
        # and compare all materials against reference materials
        if not self.compareMaterials(
            getReferenceMaterials(self.getMaterials(),
            self.options.export_type)
        ):
            return ''

        o = ''
        o += self.header.write()
        o += '\n'
        o += self.mesh.write()

        # TODO: deprecate in v3.4
        o += '\n'
        o += self.lights.write()

        o += '\n'
        o += self._writeLods()

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

        # if lods are present we need to attach a closing lod
        # containing all objects not in a lod that should always be visible
        if numLods > 0 and tallestFar < 100000:
            o += "ATTR_LOD %s 100000\n" % floatToStr(tallestFar)
            o += self.commands.write()

        return o

    # Method: cleanup
    # Removes temporary blender data
    def cleanup(self):
        while(len(self._tempBlenderObjects) > 0):
            tempBlenderObject = self._tempBlenderObjects.pop()
            bpy.data.objects.remove(tempBlenderObject)
