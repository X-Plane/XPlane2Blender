# File: xplane_types.py
# Defines X-Plane data types.

import bpy
import math
import mathutils
import struct
from bpy.props import *
from collections import OrderedDict
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_config import *

# Class: XPlaneKeyframe
# A Keyframe.
class XPlaneKeyframe():
    # Property: object
    # XPlaneObject - The <XPlaneObject> this keyframe belongs to.

    # Property: value
    # float - Contains the Dataref value in this keyframe.

    # Property: dataref
    # string - The Path of the dataref this keyframe refers to.

    # Property: translation
    # list - [x,y,z] With translations of the <object> relative to the <object> rest position (frame 1).

    # Property: rotation
    # list - [x,y,z] With rotation angles of the <object> in this keyframe.

    # Property: scale
    # list - [x,y,z] With scale of the <object> in this keyframe.

    # Property: index
    # int - The index of this keyframe in the <object> keyframe list.
    
    # Constructor: __init__
    # Caclulates <translation>, <rotation> and <scale>.
    #
    # Parameters:
    #   keyframe - A Blender keyframe
    #   int index - The index of this keyframe in the <object> keyframe list.
    #   string dataref - Path of the dataref this keyframe refers to.
    #   XPlaneObject obj - A <XPlaneObject>.
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

        if self.object.type != 'BONE':
            self.hide = self.object.object.hide_render
            
        # update objects so we get values from the keyframe
        #self.object.update()
        
        local = self.object.getLocal()
        world = self.object.getWorld()

        self.location = world["location"]
        self.angle = world["angle"]
        self.scale = world["scale"]
        
        self.locationLocal = local["location"]
        self.angleLocal = local["angle"]
        self.scaleLocal = local["scale"]
        # TODO: multiply location with scale of parent?

#        if debug:
#            print(self.object.name)
#            print(self.locationLocal)
#            print(self.object.locationLocal)
#            print(self.angleLocal)
#            print(self.object.angleLocal)

        self.rotation = self.angleLocal

        # local position will be applied by static translations right now
        # so remove initial location to get offset
        for i in range(0,3):
            self.translation[i] = self.locationLocal[i]-self.object.locationLocal[i]

# Class: XPlaneObject
# A basic object
#
# Sublcasses:
#   <XPlaneBone>
#   <XPlaneArmature>
#   <XPlaneLight>
#   <XPlaneLine>
#   <XPlanePrimitive>
class XPlaneObject():
    # Property: object
    # The blender object this <XPlaneObject> refers to.

    # Property: name
    # string - Name of this object. The same as the <object> name.

    # Property: type
    # string - Type of the object. Mostly the same as the <object> type.

    # Property: children
    # list - All child <XPlaneObjects>.

    # Property: parent
    # XPlaneObject - The parent <XPlaneObject>.

    # Property: animations
    # dict - The keys are the dataref paths and the values are lists of <XPlaneKeyframes>.

    # Property: datarefs
    # dict - The keys are the dataref paths and the values are references to <XPlaneDatarefs>.

    # Property: bakeMatrix
    # Matrix - The matrix this object was baked with. See <XPlaneMesh.getBakeMatrix> for more information.

    # Property: location
    # list - [x,y,z] With world location

    # Property: angle
    # list - [x,y,z] With world angle

    # Property: scale
    # list - [x,y,z] With world scale

    # Property: locationLocal
    # list - [x,y,z] With local location

    # Property: angleLocal
    # list - [x,y,z] With local angle

    # Property: scaleLocal
    # list - [x,y,z] With local scale

    # Property: vectors
    # Vector of vectors - (vx,vy,vz) With orientation of each rotational axis.

    # Constructor: __init__
    #
    # Parameters:
    #   object - A Blender object
    #   XPlaneObject parent - (default=None) A <XPlaneObject> or None.
    def __init__(self,object,parent = None):
        self.object = object
        self.name = object.name
        self.children = []
        self.parent = parent
        self.animations = {}
        self.datarefs = {}
        self.bakeMatrix = None

        if hasattr(self.object,'type'):
            self.type = self.object.type
        else:
            self.type = None

    # Method: firstAnimatedParent
    # Returns the first <parent> in hierarchy that is animated.
    #
    # Parameters:
    #   XPlaneObject child - (default=None) Used internally for recursion. If given the search starts upwards from this <XPlaneObject>.
    #
    # Returns:
    #   XPlaneObject - The first <parent> in hierarchy that is animated or None if no animated parent could be found.
    def firstAnimatedParent(self, child = None):
        if child:
            if child.parent:
                if child.parent.animated():
                    # found an animated parent
                    return child.parent
                else:
                    # parent is not animated so go up in the hierarchy
                    return self.firstAnimatedParent(child.parent)
            else:
                # reached root level and found no animated object
                return None
        else:
            return self.firstAnimatedParent(self)

    # Method: getAnimations
    # Stores all animations of <object> or another Blender object in <animations>.
    #
    # Parameters:
    #   object - (default=None) A Blender object. If given animation of this object will be stored.
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
                    index = fcurve.data_path.replace('xplane.datarefs[','').replace('].value','')

                    # old style datarefs with wrong datapaths can cause errors so we just skip them
                    try:
                        index = int(index)
                    except:
                        return
                    
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

    # Method: getMatrix
    # Returns the matrix of <object>.
    # This is a simple wrapper function and becomes more complex in inheritted classes.
    # So please use it instead of directly accessing object matrices.
    #
    # Parameters:
    #   bool world - (default=False) True if the world matrix should be returned.
    def getMatrix(self,world = False):
        if world:
            return self.object.matrix_world
        else:
            return self.object.matrix_local

    # Method: getVectors
    # Returns the objects axis vectors. Thats the orientation of each rotational axis.
    # It takes the <bakeMatrix> into consideration.
    # Uses <XPlaneCoords.vectorsFromMatrix>.
    #
    # Returns:
    #   Vector of vectors - (vx,vy,vz)
    def getVectors(self):
        animatedParent = self.firstAnimatedParent()
        if self.parent == None:
            # root level
            # regular global vectors
            return ((1.0,0.0,0.0),(0.0,1.0,0.0),(0.0,0.0,1.0))
        else:
            if animatedParent:
                # not root level and an animated parent in hierarchy
                # mesh is baked with parent rotation relative to animated parent, so take that vectors
                if self.bakeMatrix:
                    return XPlaneCoords.vectorsFromMatrix(self.bakeMatrix)
                else:
                    return XPlaneCoords.vectorsFromMatrix(XPlaneCoords.relativeConvertedMatrix(self.parent.getMatrix(True),animatedParent.getMatrix(True)))
                
            else:
                # not root level and no animated parent
                # mesh is baked with parent rotation so we need that vectors
                if self.bakeMatrix:
                    return XPlaneCoords.vectorsFromMatrix(self.bakeMatrix)
                else:
                    return XPlaneCoords.vectorsFromMatrix(XPlaneCoords.convertMatrix(self.parent.getMatrix()))
        
    # Method: getLocal
    # Returns the local coordinates of the object.
    # Uses <getMatrix>, <XPlaneCoords.convertMatrix> and <XPlaneCoords.fromMatrix>.
    #
    # Returns:
    #   dict - {'location':[x,y,z],'rotation':[x,y,z],'scale':[x,y,z],'angle':[x,y,z]} Whith local coordinates.
    def getLocal(self):
        return XPlaneCoords.fromMatrix(XPlaneCoords.convertMatrix(self.getMatrix()))

    # Method: getWorld
    # Returns the world coordinates of the object.
    # Uses <getMatrix>, <XPlaneCoords.convertMatrix> and <XPlaneCoords.fromMatrix>.
    #
    # Returns:
    #   dict - {'location':[x,y,z],'rotation':[x,y,z],'scale':[x,y,z],'angle':[x,y,z]} Whith world coordinates.
    def getWorld(self):
        return XPlaneCoords.fromMatrix(XPlaneCoords.convertMatrix(self.getMatrix(True)))

    # Method: getRelative
    # Returns the coordinates of the object relative to another <XPlaneObject>.
    # Uses <getMatrix>, <XPlaneCoords.relativeConvertedMatrix> and <XPlaneCoords.fromMatrix>.
    #
    # Returns:
    #   dict - {'location':[x,y,z],'rotation':[x,y,z],'scale':[x,y,z],'angle':[x,y,z]} Whith relative coordinates.
    def getRelative(self,to):
        return XPlaneCoords.fromMatrix(XPlaneCoords.relativeConvertedMatrix(self.getMatrix(True),to.getMatrix(True)))

    # Method: update
    # A wrapper function to update the display/coordinates of the <object> after switching of frames.
    # Since Blender r35028 this function does nothing anymore, as updating seems to be done by Blender already.
    def update(self):
        pass
#        if self.parent!=None and self.parent.type!='BONE':
#            self.parent.object.update()
#        self.object.update()

    # Method: getCoordinates
    # Stores the local and world coordinates and the vectors of the object in rest position (frame 1).
    # Uses <getLocal>, <getWorld> and <getVectors>.
    def getCoordinates(self):
        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame=1)

        # update object display so we have initial values
        self.update()

        # store initial coordinates
        local = self.getLocal()
        world = self.getWorld()
        
        self.location = world["location"]
        self.angle = world["angle"]
        self.scale = world["scale"]

        self.locationLocal = local["location"]
        self.angleLocal = local["angle"]
        self.scaleLocal = local["scale"]

        self.vectors = self.getVectors()

    # Method: animated
    # Checks if the object is animated.
    #
    # Returns:
    #   bool - True if object is animated, False if not.
    def animated(self):
        return (hasattr(self,'animations') and len(self.animations)>0)

# Class: XPlaneBone
# A Bone.
#
# Extends:
#   <XPlaneObject>
class XPlaneBone(XPlaneObject):
    # Property: armature
    # A <XPlaneArmature>.

    # Constructor: __init__
    # Finds the <armature>, runs <XPlaneObject.getCoordinates> and <XPlaneObject.getAnimations>.
    #
    # Parameters:
    #   object - A Blender object
    #   XPlaneObject parent - (default=None) A <XPlaneObject> or None.
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

    # Method: getMatrix
    # Overrides <XPlaneObject.getMatrix> as bone matrices need to be taken from PoseBones.
    # Uses <XPlaneArmature.getPoseBone>.
    #
    # Todos:
    #   - This is not getting the correct matrix.
    def getMatrix(self,world = False):
        poseBone = self.armature.getPoseBone(self.object.name)
        if poseBone:
            matrix = poseBone.matrix_basis
        else:
            matrix = self.object.matrix_local
        if world:
#            print(XPlaneCoords.fromMatrix(matrix))
#            print(XPlaneCoords.fromMatrix(self.armature.getMatrix(True)))
#            print(XPlaneCoords.fromMatrix(self.armature.getMatrix(True)*matrix))
            return self.armature.getMatrix(True)*matrix
        else:
            return matrix
    # Method: update
    # overrides <XPlaneObject.update>, but does nothing at all for same reason as in <XPlaneObject.update>.
    def update(self):
        pass
#        self.armature.object.update()
#
#        if self.parent != None:
#            if self.parent.type=='BONE':
#                self.parent.armature.object.update()
#            else:
#                self.parent.object.update()
        
# Class: XPlaneArmature
# A Armature
#
# Extends:
#   <XPlaneObject>
class XPlaneArmature(XPlaneObject):
    # Constructor: __init__
    # Runs <XPlaneObject.getCoordinates> and currently not <XPlaneObject.getAnimations>.
    #
    # Parameters:
    #   object - A Blender object
    #   XPlaneObject parent - (default=None) A <XPlaneObject> or None.
    def __init__(self,object,parent = None):
        super(XPlaneArmature,self).__init__(object,parent)
        self.type = 'ARMATURE'

        self.getCoordinates()
        #self.getAnimations()

    # Method: getPoseBone
    # Returns a Blender bones PoseBone.
    #
    # Parameters:
    #   string name - Name of the Blender bone
    #
    # Returns:
    #   PoseBone - A Blender PoseBone or None, if PoseBone could not be found.
    def getPoseBone(self,name):
        for poseBone in self.object.pose.bones:
            if poseBone.bone.name == name:
                return poseBone
        return None

# Class: XPlaneLight
# A Light
#
# Extends:
#   <XPlaneObject>
class XPlaneLight(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this light.

    # Property: color
    # list - [r,g,b] Color taken from the original Blender light. Can change depending on <lightType>.

    # Property: energy
    # float - Energy taken from Blender light.

    # Property: lightType
    # string - Type of the light taken from <XPlaneLampSettings>.

    # Property: size
    # float - Size of the light taken from <XPlaneLampSettings>.

    # Property: lightName
    # string - Name of the light taken from <XPlaneLampSettings>.

    # Property: params
    # string - Parameters taken from <XPlaneLampSettings>.

    # Property: dataref
    # string - Dataref path taken from <XPlaneLampSettings>.

    # Constructor: __init__
    #
    # Parameters:
    #   object - A Blender object
    #   XPlaneObject parent - (default=None) A <XPlaneObject> or None.
    def __init__(self,object,parent = None):
        super(XPlaneLight,self).__init__(object,parent)
        self.indices = [0,0]
        self.color = [object.data.color[0],object.data.color[1],object.data.color[2]]
        self.energy = object.data.energy
        self.type = 'LIGHT'
        self.lightType = object.data.xplane.type
        self.size = object.data.xplane.size
        self.lightName = object.data.xplane.name
        self.params = object.data.xplane.params
        self.dataref = object.data.xplane.dataref

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

# Class: XPlaneLine
# A Line/Curve
# This class is not in use yet.
#
# Extends:
#   <XPlaneObject>
class XPlaneLine(XPlaneObject):
    def __init_(self,object, parent = None):
        super(object,parent)
        self.indices = [0,0]
        self.type = 'LINE'

# Class: XPlanePrimitive
# A Mesh object.
#
# Extends:
#   <XPlaneObject>
class XPlanePrimitive(XPlaneObject):
    # Property: indices
    # list - [start,end] Starting end ending indices for this object.

    # Property: material
    # XPlaneMaterial - A <XPlaneMaterial>

    # Property: faces
    # XPlaneFaces - Instance of <XPlaneFaces> with all face of this mesh. Currently not in use. This should be used when commands will work on a per face basis.

    # Property: attributes
    # dict - Object attributes that will be turned into commands with <XPlaneCommands>.

    # Property: reseters
    # dict - Object attribute reseters that will be turned into commands with <XPlaneCommands>.

    # Property: cockpitAttributes
    # dict - Object attributes for cockpit settings, that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines basic <attributes> and <cockpitAttributes>, Creates <material>, runs <getManipulatorAttributes>, <getLightLevelAttributes>, <XPlaneObject.getCoordinates> and <XPlaneObject.getAnimations>.
    #
    # Parameters:
    #   object - A Blender object
    #   XPlaneObject parent - (default=None) A <XPlaneObject> or None.
    def __init__(self,object,parent = None):
        super(XPlanePrimitive,self).__init__(object,parent)
        self.type = 'PRIMITIVE'
        self.indices = [0,0]
        self.material = XPlaneMaterial(self.object)
        self.faces = None
        self.attributes = {
            'ATTR_light_level':None
        }

        self.reseters = {}

        self.cockpitAttributes = {
            'ATTR_cockpit':None,
            'ATTR_cockpit_region':None
        }

        # add custom attributes
        for attr in object.xplane.customAttributes:
            self.attributes[attr.name] = attr.value
            self.reseters[attr.name] = attr.reset

        # add cockpit attributes
        if object.xplane.panel:
            self.cockpitAttributes['ATTR_cockpit'] = True

        # add manipulator attributes
        self.getManipulatorAttributes()

        # add light level attritubes
        self.getLightLevelAttributes()

        self.getCoordinates()
        self.getAnimations()

    # Method: getManipulatorAttributes
    # Defines Manipulator attributes in <cockpitAttributes> based on settings in <XPlaneManipulator>.
    def getManipulatorAttributes(self):
        attr = 'ATTR_manip_'
        value = True
        
        if self.object.xplane.manip.enabled:
            manip = self.object.xplane.manip
            type = self.object.xplane.manip.type
            attr+=type    
            if type=='drag_xy':
                value = '%s\t%d\t%d\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%s\t%s\t%s' % (manip.cursor,manip.dx,manip.dy,manip.v1_min,manip.v1_max,manip.v2_min,manip.v2_max,manip.dataref1,manip.dataref2,manip.tooltip)
            if type=='drag_axis':
                value = '%s\t%d\t%d\t%d\t%6.4f\t%6.4f\t%s\t%s' % (manip.cursor,manip.dx,manip.dy,manip.dz,manip.v1,manip.v2,manip.dataref1,manip.tooltip)
            if type=='command':
                value = '%s\t%s\t%s' % (manip.cursor,manip.command,manip.tooltip)
            if type=='command_axis':
                value = '%s\t%d\t%d\t%d\t%s\t%s\t%s' % (manip.cursor,manip.dx,manip.dy,manip.dz,manip.positive_command,manip.negative_command,manip.tooltip)
            if type=='push':
                value = '%s\t%6.4f\t%6.4f\t%s\t%s' % (manip.cursor,manip.v_down,manip.v_up,manip.dataref1,manip.tooltip)
            if type=='radio':
                value = '%s\t%6.4f\t%s\t%s' % (manip.cursor,manip.v_down,manip.dataref1,manip.tooltip)
            if type=='toggle':
                value = '%s\t%6.4f\t%6.4f\t%s\t%s' % (manip.cursor,manip.v_on,manip.v_off,manip.dataref1,manip.tooltip)
            if type in ('delta','wrap'):
                value = '%s\t%6.4f\t%6.4f\t%6.4f\t%6.4f\t%s\t%s' % (manip.cursor,manip.v_down,manip.v_hold,manip.v1_min,manip.v1_max,manip.dataref1,manip.tooltip)
        else:
            attr=None

        if attr is not None:
            self.cockpitAttributes[attr] = value

    # Method: getLightLevelAttributes
    # Defines light level attributes in <attributes> based on settings in <XPlaneObjectSettings>.
    def getLightLevelAttributes(self):
        if self.object.xplane.lightLevel:
            self.attributes['ATTR_light_level'] = "%6.4f\t%6.4f\t%s" % (self.object.xplane.lightLevel_v1,self.object.xplane.lightLevel_v2,self.object.xplane.lightLevel_dataref)

# Class: XPlaneMaterial
# A Material
class XPlaneMaterial():
    # Property: object
    # XPlaneObject - A <XPlaneObject>

    # Property: texture
    # string - Path to the texture in use for this material, or None if no texture is present.
    # This property is no longer important as textures are defined by layer.

    # Property: uv_name
    # string - Name of the uv layer to be used for texture UVs.

    # Property: attributes
    # dict - Material attributes that will be turned into commands with <XPlaneCommands>.

    # Constructor: __init__
    # Defines the <attributes> by reading the original Blender material from the <object>.
    # Also adds custom attributes to <attributes>.
    #
    # Parameters:
    #   object - A Blender object
    def __init__(self,object):
        from os import path

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
            #if mat.diffuse_intensity>0:
            diffuse = [mat.diffuse_intensity*mat.diffuse_color[0],
                        mat.diffuse_intensity*mat.diffuse_color[1],
                        mat.diffuse_intensity*mat.diffuse_color[2]]
            self.attributes['ATTR_diffuse_rgb'] = "%6.3f %6.3f %6.3f" % (diffuse[0], diffuse[1], diffuse[2])

            # specular
            #if mat.specular_intensity>0:
            specular = [mat.specular_color[0],
                        mat.specular_color[1],
                        mat.specular_color[2]]
            self.attributes['ATTR_specular_rgb'] = "%6.3f %6.3f %6.3f" % (specular[0], specular[1], specular[2])
            self.attributes['ATTR_shiny_rat'] = "%6.3f" % (mat.xplane.shinyRatio)

            # emission
            #if mat.emit>0:
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
                    self.texture = path.basename(tex.image.filepath)

                if mat.texture_slots[0].texture_coords == 'UV':
                    self.uv_name = mat.texture_slots[0].uv_layer

            # add custom attributes
            for attr in mat.xplane.customAttributes:
                self.attributes[attr.name] = attr.value

# Class: XPlaneFace
# A mesh face. This class is just a data wrapper used by <XPlaneFaces>.
class XPlaneFace():
    # Property: vertices
    # list of vectors - [v1,v2,v3] The vertices forming the face.

    # Property: normals
    # list of vectors - [n1,n2,n3] The normals of each vertice in <vertices>.

    # Property: indices
    # list - [i1,i2,i3] The indices for each vertice in <vertices>.

    # Property: uvs
    # list of vectors - [(u1,v1),(u2,v2),(u3,v3)] With UV coordinates for each vertice in <vertices>.

    # Property: smooth
    # bool - (default=False) True if face is smooth shaded, False if it is flat shaded.

    def __init__(self):
        self.vertices = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.normals = [(0.0,0.0,0.0),(0.0,0.0,0.0),(0.0,0.0,0.0)]
        self.indices = [0,0,0]
        self.uvs = [(0.0,0.0),(0.0,0.0),(0.0,0.0)]
        self.smooth = False

# Class: XPlaneFaces
# A collection of <XPlaneFace>.
class XPlaneFaces():
    # Property: faces
    # list - List of <XPlaneFace>.
    faces = []

    # Constructor: __init__
    def __init__(self):
        pass

    # Method: append
    # Adds a <XPlaneFace> to <faces>.
    #
    # Parameters:
    #   XPlaneFace face - A <XPlaneFace>
    def append(self,face):
        self.faces.append(face)

    # Method: remove
    # Removes a <XPlaneFace> from <faces>.
    #
    # Parameters:
    #   XPlaneFace face - A <XPlaneFace>
    def remove(self,face):
        del self.faces[face]

    # Method: get
    # Returns a <XPlaneFace> from <faces>.
    #
    # Parameters:
    #   int i - Index of the face
    #
    # Returns:
    #   XPlaneFace - A <XPlaneFace>
    def get(self,i):
        if len(self.faces)-1>=i:
            return self.faces[i]
        else:
            return None
