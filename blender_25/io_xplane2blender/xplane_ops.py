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

def getDatarefValuePath(index):
    return '["xplane"]["datarefs"]['+str(index)+']["value"]'

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
        #obj.xplane.datarefs[self.index].keyframe_insert(data_path="value",group="XPlane Datarefs")
        #obj.xplane.datarefs[self.index].value.keyframe_insert(group="XPlane Datarefs")
        
        #current workaround for setting keyframes to nested custom properties is adding an FCurve manually and assign its data_path and then set a keyframe
        if (obj.animation_data == None):
            obj.animation_data_create()
        if (obj.animation_data.action == None):
            obj.animation_data.action = bpy.data.actions.new(name=obj.name+"Action")

        # add keyframe to fcurve
        fcurve = None

        if len(obj.animation_data.action.fcurves) == 0:
            fcurve = obj.animation_data.action.fcurves.new(data_path=path,action_group="XPlane Datarefs")
            #fcurve.extrapolation = "LINEAR" # assign linear extrapolation as XPlane only uses these
        else:
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)
            if fcurve == None:
                fcurve = obj.animation_data.action.fcurves.new(data_path=path,action_group="XPlane Datarefs")

        if fcurve:
            # FIXME: recent blender build returns none here!
            keyframe = fcurve.keyframe_points.add(frame=bpy.context.scene.frame_current,value=value)
            keyframe.interpolation = 'LINEAR' # assign linear interpolation as XPlane only uses these
        
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
        fcurve = None

        if (obj.animation_data != None and obj.animation_data.action != None and len(obj.animation_data.action.fcurves)>0):
            fcurve = findFCurveByPath(obj.animation_data.action.fcurves,path)

        if fcurve:
            # find keyframe
            keyframe = None
            if len(fcurve.keyframe_points)>0:
                i = 0
                while i<len(fcurve.keyframe_points):
                    if fcurve.keyframe_points[i].co[0] == bpy.context.scene.frame_current:
                        keyframe = fcurve.keyframe_points[i]
                        i = len(fcurve.keyframe_points)
                    i+=1

            if keyframe:
                fcurve.keyframe_points.remove(keyframe=keyframe)
            
        return {'FINISHED'}