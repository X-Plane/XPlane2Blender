# File: xplane_ops.py
# Defines Operators
import pathlib

import bpy
from io_xplane2blender.xplane_config import *
from io_xplane2blender.xplane_constants import MAX_COCKPIT_REGIONS, MAX_LODS
from io_xplane2blender.xplane_ops_dev import *
from io_xplane2blender.xplane_utils import xplane_commands_txt_parser, \
                                           xplane_datarefs_txt_parser

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
def makeKeyframesLinear(obj, path):
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
def getDatarefValuePath(index, bone = None):
    if bone:
        return 'bones["%s"].xplane.datarefs[%d].value' % (bone.name, index)
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
def getPoseBone(armature, name):
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
def getPoseBoneIndex(armature, name):
    for i in range(0, len(armature.pose.bones)):
        if name==armature.pose.bones[i].bone.name:
            return i
    return -1

class OBJECT_OT_add_xplane_axis_detent_range(bpy.types.Operator):
    bl_label = 'Add X-Plane Axis Detent Range'
    bl_idname = 'object.add_xplane_axis_detent_range'
    bl_description = 'Add X-Plane Axis Detent Range'

    def execute(self, context):
        obj = context.object
        obj.xplane.manip.axis_detent_ranges.add()
        return {'FINISHED'}
 
class OBJECT_OT_remove_xplane_axis_detent_range(bpy.types.Operator):
    bl_label = 'Remove Axis Detent Range'
    bl_idname = 'object.remove_xplane_axis_detent_range'
    bl_description = 'Remove axis detent range'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.manip.axis_detent_ranges.remove(self.index)
        return {'FINISHED'}
    
# Class: SCENE_OT_add_xplane_layers
# Initially creates xplane relevant data for <XPlaneLayers> in the current Blender scene.
class SCENE_OT_add_xplane_layers(bpy.types.Operator):
    bl_label = 'Add X-Plane layers'
    bl_idname = 'scene.add_xplane_layers'
    bl_description = 'Add X-Plane export layers'

    def execute(self, context):
        scene = context.scene

        i = 0
        while len(scene.xplane.layers)<len(scene.layers):
            scene.xplane.layers.add()

            # add all lods
            for ii in range(0, MAX_LODS-1):
                scene.xplane.layers[i].lod.add()

            # add cockpit regions
            for ii in range(0, 4):
                scene.xplane.layers[i].cockpit_region.add()

            i+=1

        # re-add hidden data that user cannot change
        for i in range(0, len(scene.xplane.layers)):
            scene.xplane.layers[i].index = i
        return {'FINISHED'}

class SCENE_OT_add_xplane_layer_lods(bpy.types.Operator):
    bl_label = 'Add levels of detail'
    bl_idname = 'scene.add_xplane_layer_lods'
    bl_description = 'Add X-Plane layer LODs'

    index = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene

        num_lods = int(scene.xplane.layers[self.index].lods)

        while len(scene.xplane.layers[self.index].lod) < MAX_LODS:
            scene.xplane.layers[self.index].lod.add()

        return {'FINISHED'}

class OBJECT_OT_add_xplane_layer_lods(bpy.types.Operator):
    bl_label = 'Add levels of detail'
    bl_idname = 'object.add_xplane_layer_lods'
    bl_description = 'Add X-Plane layer LODs'

    def execute(self, context):
        obj = context.object

        num_lods = int(obj.xplane.layer.lods)

        while len(obj.xplane.layer.lod) < MAX_LODS:
            obj.xplane.layer.lod.add()

        return {'FINISHED'}

class SCENE_OT_add_xplane_layer_cockpit_regions(bpy.types.Operator):
    bl_label = 'Add cockpit regions'
    bl_idname = 'scene.add_xplane_layer_cockpit_regions'
    bl_description = 'Add X-Plane layer Cockpit Regions'

    index = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene

        num_regions = int(scene.xplane.layers[self.index].cockpit_regions)

        while len(scene.xplane.layers[self.index].cockpit_region) < 4:
            scene.xplane.layers[self.index].cockpit_region.add()

        return {'FINISHED'}

class OBJECT_OT_add_xplane_layer_cockpit_regions(bpy.types.Operator):
    bl_label = 'Add cockpit regions'
    bl_idname = 'object.add_xplane_layer_cockpit_regions'
    bl_description = 'Add X-Plane layer Cockpit Regions'

    def execute(self, context):
        obj = context.object

        num_regions = int(obj.xplane.layer.cockpit_regions)

        while len(obj.xplane.layer.cockpit_region) < xplane_constants.MAX_COCKPIT_REGIONS:
            obj.xplane.layer.cockpit_region.add()

        return {'FINISHED'}

# Class: SCENE_OT_add_xplane_layer_attribute
# Adds a custom attribute to a <XPlaneLayer>.
class SCENE_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Add Layer Property'
    bl_idname = 'scene.add_xplane_layer_attribute'
    bl_description = 'Add a custom X-Plane Layer Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.xplane.layers[self.index].customAttributes.add()
        return {'FINISHED'}

# Class: SCENE_OT_remove_xplane_layer_attribute
# Removes a custom attribute from a <XPlaneLayer>.
class SCENE_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Remove Layer Property'
    bl_idname = 'scene.remove_xplane_layer_attribute'
    bl_description = 'Remove the custom X-Plane Layer Property'

    index = bpy.props.IntVectorProperty(size=2)

    def execute(self, context):
        scene = context.scene
        scene.xplane.layers[self.index[0]].customAttributes.remove(self.index[1])
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_layer_attribute
# Adds a custom attribute to a <XPlaneLayer>.
class OBJECT_OT_add_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Add Layer Property'
    bl_idname = 'object.add_xplane_layer_attribute'
    bl_description = 'Add a custom X-Plane Layer Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_layer_attribute
# Removes a custom attribute from a <XPlaneLayer>.
class OBJECT_OT_remove_xplane_layer_attribute(bpy.types.Operator):
    bl_label = 'Remove Layer Property'
    bl_idname = 'object.remove_xplane_layer_attribute'
    bl_description = 'Remove the custom X-Plane Layer Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_object_attribute
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Add Object Property'
    bl_idname = 'object.add_xplane_object_attribute'
    bl_description = 'Add a custom X-Plane Object Property'

    def execute(self, context):
        obj = context.object
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_attribute(bpy.types.Operator):
    bl_label = 'Remove Object Property'
    bl_idname = 'object.remove_xplane_object_attribute'
    bl_description = 'Remove the custom X-Plane Object Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_object_anim_attribute
# Adds a custom animation attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = 'Add Animation Property'
    bl_idname = 'object.add_xplane_object_anim_attribute'
    bl_description = 'Add a custom X-Plane Animation Property'

    def execute(self, context):
        obj = context.object
        obj.xplane.customAnimAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_anim_attribute
# Removes a custom animation attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_anim_attribute(bpy.types.Operator):
    bl_label = 'Remove Animation Property'
    bl_idname = 'object.remove_xplane_object_anim_attribute'
    bl_description = 'Remove the custom X-Plane Animation Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.customAnimAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_material_attribute
# Adds a custom attribute to a Blender Material.
class OBJECT_OT_add_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Add Material Property'
    bl_idname = 'object.add_xplane_material_attribute'
    bl_description = 'Add a custom X-Plane Material Property'

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Material.
class OBJECT_OT_remove_xplane_material_attribute(bpy.types.Operator):
    bl_label = 'Remove Material Property'
    bl_idname = 'object.remove_xplane_material_attribute'
    bl_description = 'Remove the custom X-Plane Material Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_lamp_attribute
# Adds a custom attribute to a Blender Lamp.
class OBJECT_OT_add_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Add Lamp Property'
    bl_idname = 'object.add_xplane_lamp_attribute'
    bl_description = 'Add a custom X-Plane Lamp Property'

    def execute(self, context):
        obj = context.object.data
        obj.xplane.customAttributes.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_attribute
# Removes a custom attribute from a Blender Lamp.
class OBJECT_OT_remove_xplane_lamp_attribute(bpy.types.Operator):
    bl_label = 'Remove Lamp Property'
    bl_idname = 'object.remove_xplane_lamp_attribute'
    bl_description = 'Remove the custom X-Plane Lamp Property'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.data
        obj.xplane.customAttributes.remove(self.index)
        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender Object.
class OBJECT_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'object.add_xplane_dataref'
    bl_description = 'Add an X-Plane Dataref'

    def execute(self, context):
        obj = context.object
        obj.xplane.datarefs.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender Object.
class OBJECT_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = 'Remove Dataref'
    bl_idname = 'object.remove_xplane_dataref'
    bl_description = 'Remove the X-Plane Dataref'

    index = bpy.props.IntProperty()

    def execute(self, context):
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
    bl_description = 'Add/Update an X-Plane Dataref keyframe'

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        value = obj.xplane.datarefs[self.index].value

        if "XPlane Datarefs" not in obj.animation_data.action.groups:
            obj.animation_data.action.groups.new('XPlane Datarefs')

        obj.xplane.datarefs[self.index].keyframe_insert(data_path="value", group="XPlane Datarefs")
        makeKeyframesLinear(obj, path)

        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of an object.
class OBJECT_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'object.remove_xplane_dataref_keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        path = getDatarefValuePath(self.index)
        obj.xplane.datarefs[self.index].keyframe_delete(data_path="value", group="XPlane Datarefs")

        return {'FINISHED'}

class OBJECT_OT_add_xplane_export_path_directive(bpy.types.Operator):
    bl_label = 'Add Export Path Directive'
    bl_idname = 'object.add_xplane_export_path_directive'
    bl_description = 'Add Export Path Directive'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.export_path_directives.add()
        return {'FINISHED'}
 
class OBJECT_OT_remove_xplane_export_path_directive(bpy.types.Operator):
    bl_label = 'Remove Export Path Directive'
    bl_idname = 'object.remove_xplane_export_path_directive'
    bl_description = 'Remove export path directive'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.layer.export_path_directives.remove(self.index)
        return {'FINISHED'}
    
class SCENE_OT_add_xplane_export_path_directive(bpy.types.Operator):
    bl_label = 'Add Export Path Directive'
    bl_idname = 'scene.add_xplane_export_path_directive'
    bl_description = 'Add Export Path Directive'

    # Index represents which xplane layer's export_path_directives list should
    # be appended
    index = bpy.props.IntProperty()

    def execute(self, context):
        scene = context.scene
        scene.xplane.layers[self.index].export_path_directives.add()
        return {'FINISHED'}
 
class SCENE_OT_remove_xplane_export_path_directive(bpy.types.Operator):
    bl_label = 'Remove Export Path Directive'
    bl_idname = 'scene.remove_xplane_export_path_directive'
    bl_description = 'Remove export path directive'

    index = bpy.props.IntVectorProperty(size=2)

    def execute(self, context):
        scene = context.scene
        scene.xplane.layers[self.index[0]].export_path_directives.remove(self.index[1])
        return {'FINISHED'}

# Class: BONE_OT_add_xplane_dataref
# Adds a <XPlaneDataref> to a Blender bone.
class BONE_OT_add_xplane_dataref(bpy.types.Operator):
    bl_label = 'Add Dataref'
    bl_idname = 'bone.add_xplane_dataref'
    bl_description = 'Add/Update an X-Plane Dataref'

    def execute(self, context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.add()
        return {'FINISHED'}

# Class: BONE_OT_remove_xplane_dataref
# Removes a <XPlaneDataref> from a Blender bone.
class BONE_OT_remove_xplane_dataref(bpy.types.Operator):
    bl_label = 'Remove Dataref'
    bl_idname = 'bone.remove_xplane_dataref'
    bl_description = 'Remove the X-Plane Dataref'

    index = bpy.props.IntProperty()

    def execute(self, context):
        bone = context.bone
        obj = context.object
        bone.xplane.datarefs.remove(self.index)
        path = getDatarefValuePath(self.index, bone)

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
    bl_description = 'Add/Update an X-Plane Dataref keyframe'

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index = bpy.props.IntProperty()

    # bpy.data.objects["Armature"].data.keyframe_insert(data_path='bones["Bone"].my_prop_group.nested', group="Nested Property")
    def execute(self, context):
        bone = context.active_bone # context.bone is not always available, for instance, during test_creation_helpers
                                   # Other uses will be replaced as needed. context.object doesn't appear to be affected
                                   # See also: https://blender.stackexchange.com/q/31759
        armature = context.object
        path = getDatarefValuePath(self.index, bone)

        groupName = "XPlane Datarefs "+bone.name

        if groupName not in armature.animation_data.action.groups:
            armature.animation_data.action.groups.new(groupName)

        armature.data.keyframe_insert(data_path=path, group=groupName)

        return {'FINISHED'}

# Class: BONE_OT_remove_xplane_dataref_keyframe
# Removes a Keyframe from the value of a <XPlaneDataref> of a bone.
class BONE_OT_remove_xplane_dataref_keyframe(bpy.types.Operator):
    bl_label = 'Remove Dataref keyframe'
    bl_idname = 'bone.remove_xplane_dataref_keyframe'
    bl_description = 'Remove the X-Plane Dataref keyframe'

    # index here refers to the index of the datarefs collection,
    # NOT the keyframe index
    index = bpy.props.IntProperty()

    def execute(self, context):
        bone = context.bone
        path = getDatarefValuePath(self.index)
        armature = context.object
        path = getDatarefValuePath(self.index, bone)
        armature.data.keyframe_delete(data_path=path, group="XPlane Datarefs "+bone.name)

        return {'FINISHED'}

# Class: OBJECT_OT_add_xplane_object_condition
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_object_condition(bpy.types.Operator):
    bl_label = 'Add Condition'
    bl_idname = 'object.add_xplane_object_condition'
    bl_description = 'Add an X-Plane condition'

    def execute(self, context):
        obj = context.object
        obj.xplane.conditions.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_object_condition
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_object_condition(bpy.types.Operator):
    bl_label = 'Remove Condition'
    bl_idname = 'object.remove_xplane_object_condition'
    bl_description = 'Remove X-Plane Condition'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object
        obj.xplane.conditions.remove(self.index)
        return {'FINISHED'}

    # Class: OBJECT_OT_add_xplane_material_condition
# Adds a custom attribute to a Blender Object.
class OBJECT_OT_add_xplane_material_condition(bpy.types.Operator):
    bl_label = 'Add Condition'
    bl_idname = 'object.add_xplane_material_condition'
    bl_description = 'Add an X-Plane condition'

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.conditions.add()
        return {'FINISHED'}

# Class: OBJECT_OT_remove_xplane_material_condition
# Removes a custom attribute from a Blender Object.
class OBJECT_OT_remove_xplane_material_condition(bpy.types.Operator):
    bl_label = 'Remove Condition'
    bl_idname = 'object.remove_xplane_material_condition'
    bl_description = 'Remove X-Plane Condition'

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = context.object.active_material
        obj.xplane.conditions.remove(self.index)
        return {'FINISHED'}

# Class: SCENE_OT_export_to_relative_dir
# Exports OBJS into the same folder as the .blend file, and/or folders beneath it
class SCENE_OT_export_to_relative_dir(bpy.types.Operator):
    bl_label = 'Export OBJs'
    bl_idname = 'scene.export_to_relative_dir'
    bl_description = 'Exports OBJs relative to the .blend file'
    
    #initial_dir that will be prepended to the path.
    initial_dir = bpy.props.StringProperty()
    
    def execute(self, context):
        bpy.ops.export.xplane_obj(filepath=self.initial_dir, export_is_relative=True)
        return {'FINISHED'}


class XPLANE_OT_CommandSearchToggle(bpy.types.Operator):
    '''
    This operator very simply passes it's associated command to the search window, which then opens it in the UI. 
    '''
    bl_label = 'Open/Close Command Search Window'
    bl_description = 'Open/Close Command Search Window'
    bl_idname = 'xplane.command_search_toggle'

    # Each operator is placed next to a command string property,
    # 
    paired_command_prop = bpy.props.StringProperty()
    def execute(self, context):
        command_search_window_state = context.scene.xplane.command_search_window_state
        #Load on first use
        if len(command_search_window_state.command_search_list) == 0:
            filepath=pathlib.Path(xplane_helpers.get_plugin_resources_folder(),"Commands.txt")
            get_commands_txt_result = xplane_commands_txt_parser.get_commands_txt_file_content(filepath.as_posix())
            if isinstance(get_commands_txt_result,str):
                short_filepath = "..."+os.path.sep.join(filepath.parts[-3:])
                bpy.ops.xplane.error('INVOKE_DEFAULT',msg_text=short_filepath + " could not be parsed", report_text=get_commands_txt_result)
                return {'CANCELLED'}
            else:
                file_content = get_commands_txt_result

            command_search_list = bpy.context.scene.xplane.command_search_window_state.command_search_list

            for command_info in file_content:
                command_search_list.add()
                command_search_list[-1].command = command_info.command
                command_search_list[-1].command_description = command_info.description

        prop = command_search_window_state.command_prop_dest

        #Toggle ourselves
        if prop == self.paired_command_prop:
            command_search_window_state.command_prop_dest = "" 
        else:
            command_search_window_state.command_prop_dest = self.paired_command_prop

        return {'FINISHED'}

class XPLANE_OT_DatarefSearchToggle(bpy.types.Operator):
    '''
    This operator very simply passes it's associated dataref to the search window, which then opens it in the UI. 
    '''
    bl_label = 'Open/Close Dataref Search Window'
    bl_description = 'Open/Close Dataref Search Window'
    bl_idname = 'xplane.dataref_search_toggle'

    # Each operator is placed next to a dataref string property,
    # 
    paired_dataref_prop = bpy.props.StringProperty()
    def execute(self, context):
        dataref_search_window_state = context.scene.xplane.dataref_search_window_state
        #Load on first use
        if len(dataref_search_window_state.dataref_search_list) == 0:
            filepath=pathlib.Path(xplane_helpers.get_plugin_resources_folder(),"DataRefs.txt")
            get_datarefs_txt_result = xplane_datarefs_txt_parser.get_datarefs_txt_file_content(filepath.as_posix())
            if isinstance(get_datarefs_txt_result,str):
                short_filepath = "..."+os.path.sep.join(filepath.parts[-3:])
                bpy.ops.xplane.error('INVOKE_DEFAULT',msg_text=short_filepath + " could not be parsed", report_text=get_datarefs_txt_result)
                return {'CANCELLED'}
            else:
                file_content = get_datarefs_txt_result

            dataref_search_list = bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list

            for dref_info in file_content:
                dataref_search_list.add()
                dataref_search_list[-1].dataref_path = dref_info.path
                dataref_search_list[-1].dataref_type = dref_info.type
                dataref_search_list[-1].dataref_is_writable = dref_info.is_writable
                dataref_search_list[-1].dataref_units = dref_info.units
                dataref_search_list[-1].dataref_description = dref_info.description

        prop = dataref_search_window_state.dataref_prop_dest

        #Toggle ourselves
        if prop == self.paired_dataref_prop:
            dataref_search_window_state.dataref_prop_dest = "" 
        else:
            dataref_search_window_state.dataref_prop_dest = self.paired_dataref_prop

        return {'FINISHED'}

# Function: addXPlaneOps
# Registers all Operators.
def addXPlaneOps():
    #List all adds, then all removes in alphabetical order.
    #Insert line breaks between related groups
    bpy.utils.register_class(BONE_OT_add_xplane_dataref)
    bpy.utils.register_class(BONE_OT_add_xplane_dataref_keyframe)
    bpy.utils.register_class(BONE_OT_remove_xplane_dataref)
    bpy.utils.register_class(BONE_OT_remove_xplane_dataref_keyframe)

    bpy.utils.register_class(OBJECT_OT_add_xplane_dataref)
    bpy.utils.register_class(OBJECT_OT_add_xplane_dataref_keyframe)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_dataref)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_dataref_keyframe)

    bpy.utils.register_class(OBJECT_OT_add_xplane_export_path_directive)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_export_path_directive)

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

    bpy.utils.register_class(OBJECT_OT_add_xplane_object_condition)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_object_condition)
    bpy.utils.register_class(OBJECT_OT_add_xplane_material_condition)
    bpy.utils.register_class(OBJECT_OT_remove_xplane_material_condition)
    
    bpy.utils.register_class(SCENE_OT_export_to_relative_dir)

    #See xplane_ops_dev.py
    #bpy.utils.register_class(SCENE_OT_dev_export_to_current_dir)
    bpy.utils.register_class(SCENE_OT_dev_layer_names_from_objects)
    bpy.utils.register_class(SCENE_OT_dev_rerun_updater)
    bpy.utils.register_class(SCENE_OT_dev_create_lights_txt_summary)

    bpy.utils.register_class(XPLANE_OT_CommandSearchToggle)
    bpy.utils.register_class(XPLANE_OT_DatarefSearchToggle)
# Function: removeXPlaneOps
# Unregisters all Operators.
def removeXPlaneOps():
    #List all adds, then all removes in alphabetical order.
    #Insert line breaks between related groups
    bpy.utils.unregister_class(BONE_OT_add_xplane_dataref)
    bpy.utils.unregister_class(BONE_OT_add_xplane_dataref_keyframe)
    bpy.utils.unregister_class(BONE_OT_remove_xplane_dataref)
    bpy.utils.unregister_class(BONE_OT_remove_xplane_dataref_keyframe)

    bpy.utils.unregister_class(OBJECT_OT_add_xplane_dataref)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_dataref_keyframe)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_dataref)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_dataref_keyframe)

    bpy.utils.unregister_class(OBJECT_OT_add_xplane_export_path_directive)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_export_path_directive)

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

    bpy.utils.unregister_class(OBJECT_OT_add_xplane_object_condition)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_object_condition)
    bpy.utils.unregister_class(OBJECT_OT_add_xplane_material_condition)
    bpy.utils.unregister_class(OBJECT_OT_remove_xplane_material_condition)

    bpy.utils.unregister_class(SCENE_OT_export_to_relative_dir)

    bpy.utils.unregister_class(SCENE_OT_dev_layer_names_from_objects)
    bpy.utils.unregister_class(SCENE_OT_dev_rerun_updater)
    bpy.utils.unregister_class(SCENE_OT_dev_create_lights_txt_summary)

    bpy.utils.unregister_class(XPLANE_OT_CommandSearchToggle)
    bpy.utils.unregister_class(XPLANE_OT_DatarefSearchToggle)
