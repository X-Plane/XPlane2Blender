# File: xplane_file.py
# Defines X-Plane file data type.

import bpy
from ..xplane_helpers import *
from . import XPlaneBone, XPlaneLight, XPlaneLine, XPlaneObject, XPlanePrimitive, XPlaneLights
from ..xplane_config import *

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

def createFilesFromBlenderLayers():
    files = []

    for layerIndex in getActiveBlenderLayerIndexes():
        xplaneFile = createFileFromBlenderLayerIndex(layerIndex)
        if xplaneFile:
            files.append(xplaneFile)


def createFileFromBlenderLayerIndex(layerIndex):
    xplaneFile = None
    xplaneLayer = getXPlaneLayerForBlenderLayerIndex(layerIndex)

    if xplaneLayer:
        xplaneFile = XPlaneFile(getFilenameFromXPlaneLayer(xplaneLayer))

        if xplaneFile:
            xplaneFile.collectFromBlenderLayerIndex(layerIndex)

    return xplaneFile

# Class: XPlaneFile
# X-Plane OBJ file
class XPlaneFile():

    def __init__(self, filename):
        self.filename = filename

        # TODO: use XPlaneHeader type here
        self.header = None

        # TODO: use XPlaneMesh type here
        self.mesh = None

        self.lights = XPlaneLights()

        # list of temporary objects that will be removed after export
        self.tempBlenderObjects = []

        # dict of xplane objects within the file
        self.objects = {}

        # the root bone: origin for all animations/objects
        self.rootBone = None

    # Method: collectFromBlenderLayerIndex
    # collects all objects in a given blender layer
    #
    # Parameters:
    #   layerIndex - int
    def collectFromBlenderLayerIndex(self, layerIndex):
        blenderObjects = []

        for blenderObject in bpy.context.scene.objects:
            for i in range(len(blenderObject.layers)):
                if debug:
                    debugger.debug("scanning %s" % blenderObject.name)

                if blenderObject.layers[i] == True and i == layerIndex and blenderObject.hide == False:
                    blenderObjects.append(blenderObject)

        self.collectBlenderObjects(blenderObjects)

    def collectBlenderObjects(self, blenderObjects):
        # clear object dict
        self.ubjects = {}

        # clear root bone
        self.rootBone = None

        for blenderObject in blenderObjects:
            xplaneObject = self.convertBlenderObject(blenderObject)

            if xplaneObject:
                if isinstance(xplaneObject, XPlaneLight):
                    # attach xplane light to lights list
                    self.lights.append(xplaneObject)

                # store xplane object under same name as blender object in dict
                self.objects[blenderObject.name] = xplaneObject

    # Method: collectFromBlenderRootObject
    # collects all objects in a given blender root object
    #
    # Parameters:
    #   rootObject - blender object
    def collectFromBlenderRootObject(self, rootObject):
        pass

    # Method: convertBlenderObject
    # Converts/wraps blender object into an <XPlaneObject> or subtype
    #
    # Returns:
    #   <XPlaneObject> or None if object type is not supported
    def convertBlenderObject(self, blenderObject):
        xplaneObject = None

        # mesh: let's create a prim out of it
        if blenderObject.type == "MESH":
            if debug:
                debugger.debug("\t %s: adding to list" % blenderObject.name)
            xplaneObject = XPlanePrimitive(blenderObject)

        # lamp: let's create a XPlaneLight. Those cannot have children (yet).
        elif blenderObject.type == "LAMP":
            if debug:
                debugger.debug("\t %s: adding to list" % blenderObject.name)
            xplaneObject  = XPlaneLight(blenderObject)

        return xplaneObject

    # Method: write
    # Returns OBJ file code
    def write(self):
        # TODO: implement it
        pass

    # Method: cleanup
    # Removes temporary blender data
    def cleanup(self):
        while(len(self.tempObjects) > 0):
            tempObject = self.tempObjects.pop()
            bpy.data.objects.remove(tempObject)
