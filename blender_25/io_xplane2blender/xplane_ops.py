import bpy
from io_xplane2blender.xplane_config import *

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

# FIXME: not working
def makeKeyframesLinear(obj,path):
    fcurve = None
    
    if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
        fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)

        if fcurve:
            # find keyframe
            keyframe = None
            for keyframe in fcurve.keyframe_points:
                keyframe.interpolation = 'LINEAR'


def getDatarefValuePath(index):
    return 'xplane.datarefs['+str(index)+'].value'

class SCENE_OT_add_xplane_layers(bpy.types.Operator):
    bl_label = 'Add X-Plane layers'
    bl_idname = 'scene.add_xplane_layers'
    bl_label = 'Add X-Plane layers'
    bl_description = 'Add a X-Plane export layers'

    def execute(self,context):
        scene = context.scene
        while len(scene.xplane.layers)<len(scene.layers):
            scene.xplane.layers.add()

        # re-add hidden data that user cannot change
        for i in range(0,len(scene.xplane.layers)):
            scene.xplane.layers[i].index = i
        return {'FINISHED'}

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

class OBJECT_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Remove Attribute'
    bl_idname = 'scene.remove_xplane_layer_attribute'
    bl_label = 'Remove Property'
    bl_description = 'Remove the custom X-Plane Property'

    index = bpy.props.IntVectorProperty(size=2)

    def execute(self,context):
        scene = context.scene
        scene.xplane.layers[self.index[0]].customAttributes.remove(self.index[1])
        return {'FINISHED'}

class OBJECT_OT_add_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_object_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

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

class OBJECT_OT_add_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_material_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.active_material
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

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

class OBJECT_OT_add_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Add Attribute'
    bl_idname = 'object.add_xplane_lamp_attribute'
    bl_label = 'Add Property'
    bl_description = 'Add a custom X-Plane Property'

    def execute(self,context):
        obj = context.object.data
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

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

class OBJECT_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'object.add_xplane_dataref'
    bl_label = 'Add Dataref'
    bl_description = 'Add a X-Plane Dataref'

    def execute(self,context):
        obj = context.object
        obj.xplane.datarefs.add()
        return {'FINISHED'}

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

class BONE_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'bone.add_xplane_dataref'
    bl_label = 'Add Dataref'
    bl_description = 'Add a X-Plane Dataref'

    def execute(self,context):
        bone = context.bone
        bone.xplane.datarefs.add()
        return {'FINISHED'}

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

        path = getDatarefValuePath(self.index)

        # remove FCurves too
        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve:
                obj.animation_data.action.fcurves.remove(fcurve=fcurve)

        return {'FINISHED'}

class BONE_OT_add_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Add Dataref keyframe'
    bl_idname = 'bone.add_xplane_dataref_keyframe'
    bl_label = 'Add Dataref keyframe'
    bl_description = 'Add a X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        bone = context.bone
        obj = context.object
        path = getDatarefValuePath(self.index)
        #value = bone.xplane.datarefs[self.index].value
        # inserting keyframes for custom nested properties working now. YAY!
        bone.xplane.datarefs[self.index].keyframe_insert(data_path="value",group="XPlane Datarefs "+bone.name)
        #makeKeyframesLinear(obj,path)

        return {'FINISHED'}

class BONE_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'bone.remove_xplane_dataref_keyframe'
    bl_label = 'Remove Dataref keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    index = bpy.props.IntProperty()

    def execute(self,context):
        bone = context.bone
        path = getDatarefValuePath(self.index)
        bone.xplane.datarefs[self.index].keyframe_delete(data_path="value",group="XPlane Datarefs")

        return {'FINISHED'}

#class OT_xplane_error(bpy.types.Operator):
#    bl_label = 'Show an XPlane Error message'
#    bl_idname = ''