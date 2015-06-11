# File: xplane_file.py
# Defines X-Plane file data type.

import bpy

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

        # TODO: use XPlaneLights type here
        self.lights = None

        # list of temporary objects that will be removed after export
        self.tempObjects = []

        # list of xplane objects within the file
        self.objects = []

        # the root bone: origin for all animations/objects
        self.rootBone = None

    def collectFromBlenderLayerIndex(self, layerIndex):
        # clear object list
        del self.objects[:]

        for blenderObject in bpy.context.scene.objects:
            for i in range(len(blenderObject.layers)):
                if blenderObject.layers[i] == True and i == layerIndex:
                    self.objects.append(blenderObject)

    def collectFromRootObject(self, rootObject):
        pass

    def write(self):
        # TODO: implement it
        pass

    # Method: cleanup
    # Removes temporary objects from scene
    def cleanup(self):
        while(len(self.tempObjects) > 0):
            tempObject = self.tempObjects.pop()
            bpy.data.objects.remove(tempObject)
