# File: xplane_ops_dev.py
# Defines Operators specifically for plugin development

import bpy
import re
import io_xplane2blender
from .xplane_constants import *

#class SCENE_OT_dev_export_to_current_dir(bpy.types.Operator):
#    bl_label  = 'Export .blend file to current dir'
#    bl_idname = 'scene.dev_export_to_current_dir'
#    bl_description = 'Exports blender file to current working directory. Useful for quick plugin testing'
#
#    def execute(self, context):
#        bpy.ops.export.xplane_obj(filepath=self.initial_dir, export_is_relative=True)
#        return {'FINISHED'}

class SCENE_OT_dev_layer_names_from_objects(bpy.types.Operator):
    bl_label = 'Create Layer Names from Objects'
    bl_idname = 'scene.dev_layer_names_from_objects'
    bl_description = 'Create layer names from objects, stripping Cube_ and Empty_ and prepending "test_" to them'
    
    name_prefix = "test_"
    clean_data_block_string = True
    
    def execute(self,context):
        objects = bpy.context.scene.objects
        xplane_layers = bpy.context.scene.xplane.layers
        
        for object in sorted(objects.keys()):
            if objects[object].parent != None:
                continue
            
            cleaned_name = objects[object].name
            if self.clean_data_block_string:
                m = re.match("(Cube_|Empty_)(.*)", objects[object].name)
                if m != None:
                    cleaned_name = m.group(2)
                
            #Find first true
            idx = 0
            for obj_layer_idx in objects[object].layers:
                print(idx)
                if obj_layer_idx == True:
                    break
                idx += 1

            xplane_layers[idx].name = self.name_prefix + cleaned_name
        return {'FINISHED'}

class SCENE_OT_dev_rerun_updater(bpy.types.Operator):
    bl_label = "Re-run Updater"
    bl_idname = "scene.dev_rerun_updater"
    bl_description = "Re-runs the updater. This does not undo an update that happened on load!"
   
    def execute(self,context):
        io_xplane2blender.xplane_updater.update(bpy.context.scene.xplane.dev_fake_xplane2blender_version)
        return { 'FINISHED' }
    
class SCENE_OT_dev_manip_1050_downgrader(bpy.types.Operator):
    bl_label       = "Manipulator type_1050 Downgrader"
    bl_idname      = "scene.dev_manip_1050_downgrader"
    bl_description = "Downgrades and copies manipulator type changes made during 3.4.0 0." + \
                     'Use if your aircraft suddenly has had all of its types reset to "Drag XY" (see 3.4.0-beta.5 release notes)'

    def execute(self,context):
        # Use an internal text file called "Manipulator Type Differeces
        filename = "Manipulator Downgrade Report"
        text_file = bpy.data.texts.new(filename)
        text_file.write(filename + '\n')
        
        #Mirror the drop down menu order which existed from 7fe534ad - d9c766e1ad    
        manip_types_900 = [
                MANIP_DRAG_XY,
                MANIP_DRAG_AXIS,
                MANIP_COMMAND,
                MANIP_COMMAND_AXIS,
                MANIP_PUSH,
                MANIP_RADIO,
                MANIP_DELTA,
                MANIP_WRAP,
                MANIP_TOGGLE,
                MANIP_NOOP,
            ]

        manip_types_1050 = [
                MANIP_AXIS_SWITCH_LEFT_RIGHT,
                MANIP_AXIS_SWITCH_UP_DOWN,
                MANIP_COMMAND_KNOB,
                MANIP_COMMAND_SWITCH_LEFT_RIGHT,
                MANIP_COMMAND_SWITCH_UP_DOWN,
                MANIP_DRAG_AXIS_PIX,
            ]

        type_1050_items = manip_types_900 + manip_types_1050
                
        for obj in bpy.data.objects:
            if obj.xplane.manip:
                type_old = obj.xplane.manip.get('type')
                type_1050 = obj.xplane.manip.get('type_1050')
                
                if (type_old is None or bpy.context.scene.xplane.dev_manip_1050_downgrader_overwrite_all) and \
                    type_1050 is not None:
                    type_1050_value = type_1050_items[obj.xplane.manip.get('type_1050')]
                    res_str = "Overwriting %s's manip.type value (%s) with type_1050's value (%s)" % (obj.name,obj.xplane.manip.type,type_1050_value)
                    print(res_str)
                    text_file.write(res_str + '\n')

                    obj.xplane.manip.type = type_1050_value

        if len(text_file.lines) == 2: #File name + newline
            no_downgrade_str = "No object's manipulator type downgraded"
            print(no_downgrade_str)
            text_file.write(no_downgrade_str)

        return {'FINISHED'}
