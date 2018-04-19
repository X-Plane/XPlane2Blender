# File: xplane_ops_dev.py
# Defines Operators specifically for plugin development

import os
import re

import bpy
import io_xplane2blender
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_utils import xplane_datarefs_txt_parser
from io_xplane2blender.xplane_types import xplane_lights_txt_parser
from collections import OrderedDict

class SCENE_OT_dev_create_lights_txt_summary(bpy.types.Operator):
    bl_label = "Create lights.txt Summary"
    bl_idname = 'scene.dev_create_lights_txt_summary'
    bl_description = "Create a text block listing all known lights and attributes about them"
    
    def execute(self,context):
        # Why have I temporarily stuck this here? Because it is 3 in the morning and I am sick of trying to find the "Nice perfect place" Blender wants me to have to test integrating this stuff in.
        # The filter function uses our the python data model and the blender property, kept in line, then filters.
        # (TODO is this needed? Can we just stick everything in dataref_search_list and be done with it? Filtering doesn't mutate the list, right....?
        # So, we must simulate creating the python data model and feeding it to our list.
        # Apparently and who knows why(!!!) you can't do it in __init__.py after the call to register.
        # Maybe I missed something or maybe ghosts infected my CPU at the wrong moment, but I could not get sanity to return in that instance.
        # This is convienent. This is temporary. Moving on.
        file_content = xplane_datarefs_txt_parser.get_datarefs_txt_file_content(os.path.join(xplane_helpers.get_plugin_resources_folder(),"DataRefs.txt"))

        for dref_info in file_content:
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list.add()
            print(dref_info)
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list[-1].dataref_path = dref_info.path
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list[-1].dataref_type = dref_info.type
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list[-1].dataref_is_writable = dref_info.is_writable
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list[-1].dataref_units = dref_info.units
            bpy.context.scene.xplane.dataref_search_window_state.dataref_search_list[-1].dataref_description = dref_info.description

        return {'FINISHED'}
        xplane_lights_txt_parser.parse_lights_file()
        # Use an internal text file called "Manipulator Type Differeces
        filename = "lights.txt Summary"
        if bpy.data.texts.find(filename) == -1:
            text_file = bpy.data.texts.new(filename)
        else:
            text_file = bpy.data.texts[filename]
            text_file.clear()
        
        named_lights = []
        param_lights = []
        other_lights = []

        for key,value in xplane_lights_txt_parser._parsed_lights.items():
            overload = value
            if overload.is_param_light():
                param_lights.append(overload)
            else:
                if "CONE" in overload.data_source.type or\
                   "SPILL_GND" in overload.data_source.type:
                    other_lights.append(overload)
                else:
                    named_lights.append(overload)
        
        text_file.write("Named Lights\n")
        text_file.write("------------\n")
        for named_light in named_lights:
            text_file.write("%s\n" % named_light.light_name)

        text_file.write("\nParam Lights (Light name, followed by parameters required)\n")
        text_file.write("------------\n")
        for param_light in param_lights:
            cleaned_prototype = ''.join([c for c in str(param_light.light_param_def.prototype) if c not in "(),'\""])
            text_file.write("%s\n%s\n\n" % (param_light.light_name,cleaned_prototype))

        text_file.write("Old X-Plane 8 Lights\n")
        text_file.write("------------\n")
        for other_light in other_lights:
            text_file.write("%s\n" % other_light.light_name)
        
        return {'FINISHED'}
   
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
        io_xplane2blender.xplane_updater.update(xplane_helpers.VerStruct.parse_version(bpy.context.scene.xplane.dev_fake_xplane2blender_version))
        return { 'FINISHED' }

