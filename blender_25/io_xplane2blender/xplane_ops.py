# File: xplane_ops.py
# Defines Operators

import bpy
from io_xplane2blender.xplane_config import *

# Function: findFCurveByPath
# Helper function to find an FCurve by an data-path.
#
# Parameters:
#   list - FCurves
#   string - data path.
#
# Returns:
#   FCurve or None if no FCurve could be found.
def findFCurveByPath(fcurves,path):
    i = 0
    fcurve = None
    
    # find fcurve
    while i<len(fcurves):
        if fcurves[i].data_path == path:
            fcurve = fcurves[i]
            i = len(fcurves)
        i+=1
    return fcurve

# Function: makeKeyframesLinear
# Sets interpolation mode of keyframes to linear.
#
# Parameters:
#   obj - Blender object
#   string path - data path.
#
# Todos:
#   - not working
def makeKeyframesLinear(obj,path):
    fcurve = None
    
    if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
        fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)

        if fcurve:
            # find keyframe
            keyframe = None
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'

# Function: getDatarefValuePath
# Returns the data path for a <XPlaneDataref> value.
#
# Parameters:
#   int index - Index of the <XPlaneDataref>
#
# Returns:
#   string - data path
def getDatarefValuePath(index,bone = None):
    if bone:
        return 'bones["%s"].xplane.datarefs[%d].value' % (bone.name,index)
    else:
        return 'xplane.datarefs['+str(index)+'].value'

# Function: getPoseBone
# Returns the corresponding PoseBone of a BlenderBone.
#
# Parameters:
#   armature - Blender armature the bone is part of.
#   string name - Name of the Bone.
#
# Returns:
#   PoseBone - A Blender PoseBone or None if it could not be found.
def getPoseBone(armature,name):
    for poseBone in armature.pose.bones:
        if poseBone.bone.name == name:
            return poseBone
    return None

# Function: getPoseBoneIndex
# Returns the index of a PoseBone
#
# Parameters:
#   armature - Blender armature the bone is part of.
#   string name - Name of the Bone.
#
# Returns:
#   int - Index of the PoseBone or -1 if it could not be found.
def getPoseBoneIndex(armature,name):
    for i in range(0,len(armature.pose.bones)):
        if name==armature.pose.bones[i].bone.name:
            return i
    return -1

# Class: SCENE_OT_add_xplane_layers
# Initially creates xplane relevant data for <XPlaneLayers> in the current Blender scene.
class SCENE_OT_add_xplane_layers(bpy.types.Operator):
    bl_label = 'Add X-Plane layers'
    bl_idname = 'scene.add_xplane_layers'
    bl_label = 'Add X-Plane layers'
    bl_description = 'Add X-Plane export layers'

    def execute(self,context):
        scene = context.scene
        while len(scene.xplane.layers)<len(scene.layers):
            scene.xplane.layers.add()

        # re-add hidden data that user cannot change
        for i in range(0,len(scene.xplane.layers)):
            scene.xplane.layers[i].index = i
        return {'FINISHED'}

# Class: SCENE_OT_add_xplane_layer_attribute
# Adds a custom attribute to a <XPlaneLayer>.
class SCENE_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'scene.add_xplane_layer_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        scene = context.scene
        scene.xplane.layers[self.index].customAttributes.add()
        return {'FINISHED'}

# Class: SCENE_OT_remove_xplane_layer_attribute
# Removes a custom attribute from a <XPlaneLayer>.
class SCENE_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'scene.remove_xplane_layer_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntVectorProperty(size=2)

    def execute(self,context):
        scene = context.scene
        scene.xplane.layers[self.index[0]].customAttributes.remove(self.index[1])
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_object_attribute
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_object_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_object_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_object_anim_attribute
# Adds a custom animation attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_object_anim_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Animation Property'

    def execute(self,context):
        obj = context.object
        obj.xplane.customAnimAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_anim_attribute
# Removes a custom animation attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_object_anim_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Animation Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        obj.xplane.customAnimAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_material_attribute
# Adds a custom attribute to a Blender Material.
class OBJECT_OT_add_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_material_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.active_material
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Material.
class OBJECT_OT_remove_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_material_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object.active_material
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_lamp_attribute
# Adds a custom attribute to a Blender Lamp.
class OBJECT_OT_add_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_lamp_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.data
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Lamp.
class OBJECT_OT_remove_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'object.remove_xplane_lamp_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object.data
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender Object.
class OBJECT_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'object.add_xplane_dataref'
    bl_label = 'Add Dataref'
    bl_description = 'Add a X-Plane Dataref'

    def execute(self,context):
        obj = context.object
        obj.xplane.datarefs.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender Object.
class OBJECT_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = 'Remove Dataref'
    bl_idname = 'object.remove_xplane_dataref'
    bl_label = 'Remove Dataref'
    bl_description = 'Remove the X-Plane Dataref'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        obj.xplane.datarefs.remove(self.index)

        path = getDatarefValuePath(self.index)

        # remove FCurves too
        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve:              
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_dataref_keyframe
# Adds a Keyframe to the value of a <XPlaneDataref> of an object.
class OBJECT_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Add Dataref keyframe'
    bl_idname = 'object.add_xplane_dataref_keyframe'
    bl_label = 'Add Dataref keyframe'
    bl_description = 'Add a X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        value = obj.xplane.datarefs[self.index].value
        # inserting keyframes for custom nested properties working now. YAY!
        obj.xplane.datarefs[self.index].keyframe_insert(data_path="value",group="XPlane Datarefs")
        makeKeyframesLinear(obj,path)
        
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of an object.
class OBJECT_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'object.remove_xplane_dataref_keyframe'
    bl_label = 'Remove Dataref keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        obj.xplane.datarefs[self.index].keyframe_delete(data_path="value",group="XPlane Datarefs")
            
        return {'FINISHED'}

# Class: BONE_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender bone.
class BONE_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'bone.add_xplane_dataref'
    bl_label = 'Add Dataref'
    bl_description = 'Add a X-Plane Dataref'

    def execute(self,context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.add()
        return {'FINISHED'}

# Class: BONE_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender bone.
class BONE_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = 'Remove Dataref'
    bl_idname = 'bone.remove_xplane_dataref'
    bl_label = 'Remove Dataref'
    bl_description = 'Remove the X-Plane Dataref'

    index = bpy.props.IntProperty()

    def execute(self,context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.remove(self.index)
        path = getDatarefValuePath(self.index,bone)

        # remove FCurves too
        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve:
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {'FINISHED'}

# Class: BONE_OT_add_xplane_dataref_keyframe
# Adds a Keyframe to the value of a <XPlaneDataref> of a bone.
class BONE_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Add Dataref keyframe'
    bl_idname = 'bone.add_xplane_dataref_keyframe'
    bl_label = 'Add Dataref keyframe'
    bl_description = 'Add a X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    # bpy.data.objects["Armature"].data.keyframe_insert(data_path='bones["Bone"].my_prop_group.nested',group="Nested Property")
    def execute(self,context):
        bone = context.bone
        armature = context.object
        path = getDatarefValuePath(self.index,bone)
        armature.data.keyframe_insert(data_path=path, group="XPlane Datarefs "+bone.name)
        
        return {'FINISHED'}

# Class: BONE_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of a bone.
class BONE_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'bone.remove_xplane_dataref_keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        bone = context.bone
        path = getDatarefValuePath(self.index)
        armature = context.object
        path = getDatarefValuePath(self.index,bone)
        armature.data.keyframe_delete(data_path=path, group="XPlane Datarefs "+bone.name)

        return {'FINISHED'}


# Function: addXPlaneOps
# Registers all Operators.
def addXPlaneOps():
    bpy.utils.register_class(BONE_OT_add_xplane_dataref)
    bpy.utils.register_class(BONE_OT_add_xplane_dataref_keyframe)
    bpy.utils.register_class(BONE_OT_remove_xplane_dataref)
    bpy.utils.register_class(BONE_OT_remove_xplane_dataref_keyframe)

    bpy.utils.register_class(OBJECT_OT_add_xplane_dataref)
    bpy.utils.register_class(OBJECT_OT_add_xplane_dataref_keyframe)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_dataref)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_dataref_keyframe)

    bpy.utils.register_class(OBJECT_OT_add_xplane_lamp_attribute)
    bpy.utils.register_class(OBJECT_OT_add_xplane_material_attribute)
    bpy.utils.register_class(OBJECT_OT_add_xplane_object_attribute)
    bpy.utils.register_class(OBJECT_OT_add_xplane_object_anim_attribute)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_lamp_attribute)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_material_attribute)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_object_attribute)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_object_anim_attribute)

    bpy.utils.register_class(SCENE_OT_add_xplane_layer_attribute)
    bpy.utils.register_class(SCENE_OT_add_xplane_layers)
    bpy.utils.register_class(SCENE_OT_remove_xplane_layer_attribute)


# Function: removeXPlaneOps
# Unregisters all Operators.
def removeXPlaneOps():
    bpy.utils.unregister_class(BONE_OT_add_xplane_dataref)
    bpy.utils.unregister_class(BONE_OT_add_xplane_dataref_keyframe)
    bpy.utils.unregister_class(BONE_OT_remove_xplane_dataref)
    bpy.utils.unregister_class(BONE_OT_remove_xplane_dataref_keyframe)

    bpy.utils.unregister_class(OBJECT_OT_add_xplane_dataref)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_dataref_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_dataref)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_dataref_keyframe)

    bpy.utils.unregister_class(OBJECT_OT_add_xplane_lamp_attribute)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_material_attribute)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_object_attribute)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_object_anim_attribute)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_lamp_attribute)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_material_attribute)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_object_attribute)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_object_anim_attribute)

    bpy.utils.unregister_class(SCENE_OT_add_xplane_layer_attribute)
    bpy.utils.unregister_class(SCENE_OT_add_xplane_layers)
    bpy.utils.unregister_class(SCENE_OT_remove_xplane_layer_attribute)