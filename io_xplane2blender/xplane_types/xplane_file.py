# File: xplane_file.py
# Defines X-Plane file data type.

import collections

import bpy
import mathutils

from typing import Union
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_types import xplane_empty

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

#TODO: Delete all traces of XPlaneLine from .xplane_line import XPlaneLine
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

        #TODO: This will never be None, so why have the check?
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
    def __init__(self, filename:str, options:xplane_props.XPlaneLayer):
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
        self.objects = collections.OrderedDict() # type: collections.OrderedDict

        self.exportMode = 'layers'

        # the root bone: origin for all animations/objects
        self.rootBone = None

        # materials representing the reference for export
        self.referenceMaterials = None

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
        self.rootBone = XPlaneBone(None,None,None,self)
        self.collectBonesFromBlenderObjects(self.rootBone, blenderObjects)

        # restore frame before export
        bpy.context.scene.frame_set(frame = currentFrame)

        # go through blender objects and warn user if there is no xplaneBone for it
        for name in self.objects:
            xplaneObject = self.objects[name]

            if not xplaneObject.xplaneBone:
                logger.warn('Object "%s" will not be exported as it has parent(s) in another layer. Move it\'s parent(s) into layer %d.' % (name, layerIndex + 1))

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
    def collectBonesFromBlenderObjects(self,parentBone, blenderObjects,
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
            if blenderObject.dupli_type == 'GROUP' and blenderObject.name not in self._resolvedBlenderGroupInstances:
                tempBlenderObjects = self._resolveBlenderGroupInstance(blenderObject)
                self.collectBlenderObjects(tempBlenderObjects)
                self.collectBonesFromBlenderObjects(bone, blenderObject.children, False)

            # collect armature bones
            elif blenderObject.type == 'ARMATURE':
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
            bone = XPlaneBone(blenderArmature, None, parentBone,self)
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
        self.rootBone = XPlaneBone(blenderRootObject, rootXPlaneObject,None,self)

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
        xplaneObject = None # type: Union[XPlanePrimitive,XPlaneLight,XPlaneObject]

        # mesh: let's create a prim out of it
        if blenderObject.type == "MESH":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlanePrimitive(blenderObject)

        # lamp: let's create a XPlaneLight. Those cannot have children (yet).
        elif blenderObject.type == "LAMP":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject  = XPlaneLight(blenderObject)
        elif blenderObject.type == "ARMATURE":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlaneObject(blenderObject)
        elif blenderObject.type == "EMPTY":
            logger.info("\t %s: adding to list" % blenderObject.name)
            xplaneObject = xplane_empty.XPlaneEmpty(blenderObject)
            
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
            if xplaneObject.type == 'MESH' and xplaneObject.material.options:
                errors,warnings = xplaneObject.material.isValid(self.options.export_type)

                for error in errors:
                    logger.error('Material "%s" in object "%s" %s' % (xplaneObject.material.name, xplaneObject.blenderObject.name, error))

                for warning in warnings:
                    logger.warn('Material "%s" in object "%s" %s' % (xplaneObject.material.name, xplaneObject.blenderObject.name, warning))

        if logger.hasErrors():
            return False

        return True

    def getMaterials(self):
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
                        errors,warnings = material.isCompatibleTo(refMaterial, self.options.export_type,self.options.autodetectTextures)
                        xplaneObject = material.xplaneObject
                        for error in errors:
                            logger.error('Material "%s" in object "%s" %s' % (material.name, xplaneObject.blenderObject.name, error))

                        for warning in warnings:
                            logger.warn('Material "%s" in object "%s" %s' % (material.name, xplaneObject.blenderObject.name, warning))

        if logger.hasErrors():
            return False

        return True

    def writeFooter(self):
        build = 'unknown'

        if hasattr(bpy.app, 'build_hash'):
            build = bpy.app.build_hash
        else:
            build = bpy.app.build_revision
        
        return "# Build with Blender %s (build %s). Exported with XPlane2Blender %s" % (bpy.app.version_string, build, xplane_helpers.VerStruct.current())

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

    # Method: cleanup
    # Removes temporary blender data
    def cleanup(self):
        while(len(self._tempBlenderObjects) > 0):
            tempBlenderObject = self._tempBlenderObjects.pop()
            bpy.data.objects.remove(tempBlenderObject)
