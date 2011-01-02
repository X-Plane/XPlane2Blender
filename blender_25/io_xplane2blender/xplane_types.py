import bpy
import math
import struct
from bpy.props import *
from collections import OrderedDict
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_config import *

debug = True

class XPlaneKeyframe():
    def __init__(self,keyframe,index,dataref,obj):
        self.value = keyframe.co[1]
        self.dataref = dataref
        self.translation = [0.0,0.0,0.0]
        self.rotation = [0.0,0.0,0.0]
        self.scale = [0.0,0.0,0.0]
        self.index = index
        self.object = obj

        # goto keyframe and read out object values
        # TODO: support subframes?
        self.frame = int(round(keyframe.co[0]))
        bpy.context.scene.frame_set(frame=self.frame)
        coords = XPlaneCoords(self.object.object)

        if self.object.type != 'BONE':
            self.hide = self.object.object.hide_render

        #if prim.parent!=None:
        # update objects so we get values from the keyframe
        if self.object.type=='BONE':
            self.object.armature.object.update(scene=bpy.context.scene)
        else:
            if self.object.parent!=None and self.object.parent.type!='BONE':
                self.object.parent.object.update(scene=bpy.context.scene)
            self.object.object.update(scene=bpy.context.scene)

        local = coords.local()
        if self.object.type!='BONE':
            world = coords.world()
        else:
            world = local

#        if self.object.parent!=None:
#            local = coords.local(self.object.parent.object)
#        else:
#            local = coords.local()

        self.location = world["location"]
        self.angle = world["angle"]
        self.scale = world["scale"]

        self.locationLocal = local["location"]
        self.angleLocal = local["angle"]
        self.scaleLocal = local["scale"]
        # TODO: multiply location with scale of parent

        if debug:
            print(self.object.name)
            print(self.locationLocal)
            print(self.object.locationLocal)
            print(self.angleLocal)
            print(self.object.angleLocal)

        for i in range(0,3):
            # remove initial location and rotation to get offset
            self.translation[i] = self.locationLocal[i]-self.object.locationLocal[i]
            self.rotation[i] = self.angleLocal[i]-self.object.angleLocal[i]
#        else:
#            # update object so we get values from the keyframe
#            object.update(scene=bpy.context.scene)
#
#            world = coords.world()
#
#            self.location = world["location"]
#            self.angle = world["angle"]
#            self.scale = world["scale"]
#
#            self.locationLocal = self.location
#            self.angleLocal = self.angle
#            self.scaleLocal = self.scale
#
#            # remove initial location and rotation to get offset
#            for i in range(0,3):
#                self.translation[i] = self.location[i]-prim.location[i]
#                self.rotation[i] = self.angle[i]-prim.angle[i]

class XPlaneObject():
    def __init__(self,object,parent = None):
        self.object = object
        self.name = object.name
        self.children = []
        self.parent = parent
        self.animations = {}
        self.datarefs = {}

        try:
            self.type = self.object.type
        except:
            self.type = None

    def getAnimations(self,object = None):
        if object == None:
            object = self.object
        #check for animation
        if debug:
            debugger.debug("\t\t checking animations")
        if (object.animation_data != None and object.animation_data.action != None and len(object.animation_data.action.fcurves)>0):
            if debug:
                debugger.debug("\t\t animation found")
            #check for dataref animation by getting fcurves with the dataref group
            for fcurve in object.animation_data.action.fcurves:
                if debug:
                    debugger.debug("\t\t checking FCurve %s" % fcurve.data_path)
                if (fcurve.group != None and fcurve.group.name == "XPlane Datarefs"):
                    # get dataref name
                    index = int(fcurve.data_path.replace('["xplane"]["datarefs"][','').replace(']["value"]',''))
                    dataref = object.xplane.datarefs[index].path

                    if debug:
                        debugger.debug("\t\t adding dataref animation: %s" % dataref)

                    if len(fcurve.keyframe_points)>1:
                        # time to add dataref to animations
                        self.animations[dataref] = []
                        self.datarefs[dataref] = object.xplane.datarefs[index]

                        # store keyframes temporary, so we can resort them
                        keyframes = []

                        for keyframe in fcurve.keyframe_points:
                            if debug:
                                debugger.debug("\t\t adding keyframe: %6.3f" % keyframe.co[0])
                            keyframes.append(keyframe)

                        # sort keyframes by frame number
                        keyframesSorted = sorted(keyframes, key=lambda keyframe: keyframe.co[0])

                        for i in range(0,len(keyframesSorted)):
                            self.animations[dataref].append(XPlaneKeyframe(keyframesSorted[i],i,dataref,self))

    def getVector(self):
        return (0.0,0.0,1.0)

    def getCoordinates(self):
        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame=1)
        coords = XPlaneCoords(self.object)

        # update object display so we have initial values
        if self.parent != None:
            if self.parent.type=='BONE':
                self.parent.parent.object.update(scene=bpy.context.scene)
            else:
                self.parent.object.update(scene=bpy.context.scene)

        if self.type != 'BONE':
            self.object.update(scene=bpy.context.scene)

        # store initial coordinates
        local = coords.local()
        if self.type != 'BONE':
            world = coords.world()
        else:
            world = local
#            if self.parent!=None:
#                local = coords.local(self.parent.object)
#            else:
#                local = coords.local()

        self.location = world["location"]
        self.angle = world["angle"]
        self.scale = world["scale"]

        self.locationLocal = local["location"]
        self.angleLocal = local["angle"]
        self.scaleLocal = local["scale"]
#        else:
#            # update object display so we have initial values
#            if self.type != 'BONE':
#                self.object.update(scene=bpy.context.scene)
#
#            world = coords.world()
#
#            # store initial location, rotation and scale
#            self.location = world["location"]
#            self.angle = world["angle"]
#            self.scale = world["scale"]
#            self.locationLocal = self.location
#            self.angleLocal = self.angle
#            self.scaleLocal = self.scale


class XPlaneBone(XPlaneObject):
    def __init__(self,object,parent = None):
        super(XPlaneBone,self).__init__(object,parent)
        self.type = 'BONE'
        self.armature = None

        # store armature
        if self.parent.type == 'ARMATURE':
            self.armature = self.parent
        elif self.parent.aramture != None:
            self.armature = self.parent.armature

        self.getCoordinates()
        self.getAnimations(self.armature.object)

    def getVector(self):
        return self.object.vector()


class XPlaneLight(XPlaneObject):
    def __init__(self,object,parent = None):
        super(XPlaneLight,self).__init__(object,parent)
        self.indices = [0,0]
        self.color = [object.data.color[0],object.data.color[1],object.data.color[2]]
        self.type = 'LIGHT'
        self.lightType = object.data.xplane.lightType

        # change color according to type
        if self.lightType=='flashing':
            self.color[0] = -self.color[0]
        elif self.lightType=='pulsing':
            self.color[0] = 9.9
            self.color[1] = 9.9
            self.color[2] = 9.9
        elif self.lightType=='strobe':
            self.color[0] = 9.8
            self.color[1] = 9.8
            self.color[2] = 9.8
        elif self.lightType=='traffic':
            self.color[0] = 9.7
            self.color[1] = 9.7
            self.color[2] = 9.7


class XPlaneLine(XPlaneObject):
    def __init_(self,object, parent = None):
        super(object,parent)
        self.indices = [0,0]
        self.type = 'LINE'

class XPlanePrimitive(XPlaneObject):
    def __init__(self,object,parent = None):
        super(XPlanePrimitive,self).__init__(object,parent)
        self.type = 'PRIMITIVE'
        self.indices = [0,0]
        self.material = XPlaneMaterial(self.object)
        self.faces = None
        self.attributes = {}

        # add custom attributes
        for attr in object.xplane.customAttributes:
            self.attributes[attr.name] = attr.value

        self.getCoordinates()
        self.getAnimations()

class XPlaneMaterial():
    def __init__(self,object):
        self.object = object
        self.texture = None
        self.uv_name = None

        # Material
        self.attributes = {"ATTR_diffuse_rgb":None,
                           "ATTR_specular_rgb":None,
                           "ATTR_emission_rgb":None,
                           "ATTR_shiny_rat":None,
                           "ATTR_hard":None,
                           "ATTR_no_hard":None,
                           "ATTR_cull":None,
                           "ATTR_no_cull":None,
                           "ATTR_depth":None,
                           "ATTR_no_depth":None,
                           "ATTR_blend":None,
                           "ATTR_no_blend":None}

        if len(object.data.materials)>0:
            mat = object.data.materials[0]

            # diffuse
            if mat.diffuse_intensity>0:
                diffuse = [mat.diffuse_intensity*mat.diffuse_color[0],
                            mat.diffuse_intensity*mat.diffuse_color[1],
                            mat.diffuse_intensity*mat.diffuse_color[2]]
                self.attributes['ATTR_diffuse_rgb'] = "%6.3f %6.3f %6.3f" % (diffuse[0], diffuse[1], diffuse[2])

            # specular
            if mat.specular_intensity>0:
                specular = [mat.specular_intensity*mat.specular_color[0],
                            mat.specular_intensity*mat.specular_color[1],
                            mat.specular_intensity*mat.specular_color[2]]
                self.attributes['ATTR_specular_rgb'] = "%6.3f %6.3f %6.3f" % (specular[0], specular[1], specular[2])
                self.attributes['ATTR_shiny_rat'] = "%6.3f" % mat.specular_hardness

            # emission
            if mat.emit>0:
                emission = [mat.emit*mat.diffuse_color[0],
                            mat.emit*mat.diffuse_color[1],
                            mat.emit*mat.diffuse_color[2]]
                self.attributes['ATTR_emission_rgb'] = "%6.3f %6.3f %6.3f" % (emission[0], emission[1], emission[2])

            # surface type
            if mat.xplane.surfaceType != 'none':
                self.attributes['ATTR_hard'] = mat.xplane.surfaceType

            # backface culling
            if self.object.data.show_double_sided:
                self.attributes['ATTR_no_cull'] = True
            else:
                self.attributes['ATTR_cull'] = True

            # blend
            if mat.xplane.blend:
                self.attributes['ATTR_no_blend'] = "%6.3f" % mat.xplane.blendRatio

            # depth check
            if self.object.xplane.depth == False:
                self.attributes['ATTR_no_depth'] = True;

            # Texture and uv-coordinates
            if(len(mat.texture_slots)>0 and hasattr(mat.texture_slots[0],'use') and mat.texture_slots[0].use and mat.texture_slots[0].texture.type=="IMAGE"):
                tex =  mat.texture_slots[0].texture
                if(tex.image.file_format=='PNG'):
                    self.texture = os.path.basename(tex.image.filepath)

                if mat.texture_slots[0].texture_coords == 'UV':
                    self.uv_name = mat.texture_slots[0].uv_layer

            # add custom attributes
            for attr in mat.xplane.customAttributes:
                self.attributes[attr.name] = attr.value

class XPlaneFace():
    def __init__(self):
        self.vertices = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.normals = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.indices = [0,0,0]
        self.uvs = [(0.0,0.0),(0.0,0.0),(0.0,0.0)]
        self.smooth = False


class XPlaneFaces():
    def __init__(self):
        self.faces = []

    def append(self,face):
        self.faces.append(face)

    def remove(self,face):
        del self.faces[face]

    def get(self,i):
        if len(self.faces)-1>=i:
            return self.faces[i]
        else:
            return None
