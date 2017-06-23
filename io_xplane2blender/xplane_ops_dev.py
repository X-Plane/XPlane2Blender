# File: xplane_ops_dev.py
# Defines Operators specifically for plugin development

import bpy
import re
from .xplane_config import *


class SCENE_OT_dev_export_to_current_dir(bpy.types.Operator):
    bl_label = 'Export .blend File To Current Dir'
    bl_idname = 'scene.dev_export_to_current_dir'
    bl_description = 'Exports blender file to current working directory. Useful for quick plugin testing'

    def execute(self, context):
        bpy.ops.export.xplane_obj(filepath="")
        return {'FINISHED'}

class SCENE_OT_dev_layer_names_from_objects(bpy.types.Operator):
    bl_label = 'Create Layer Names from Objects'
    bl_idname = 'scene.dev_layer_names_to_current_dir'
    bl_description = 'Create layer names from objects, stripping Cube_ and Empty_ and prepending "test_" to them'
    
    name_prefix = "test_"
    clean_data_block_string = True
    
    def execute(self,context):
        objects = bpy.context.scene.objects
        xplane_layers = bpy.context.scene.xplane.layers
        
        for object in objects:
            cleaned_name = object.name
            if self.clean_data_block_string:
                m = re.match("(Cube_|Empty_)(.*)", object.name)
                if m != None:
                    cleaned_name = m.group(2)
                
            #Find first true
            idx = 0
            for obj_layer_idx in object.layers:
                if obj_layer_idx == True:
                    break
                idx += 1

            xplane_layers[idx].name = self.name_prefix + cleaned_name
        return {'FINISHED'}