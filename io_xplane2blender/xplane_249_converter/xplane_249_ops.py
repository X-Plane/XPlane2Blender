'''Defines operators for the 249 conversion'''

import re

import bpy
import io_xplane2blender

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender import xplane_249_converter


class SCENE_OT_249_do_conversion(bpy.types.Operator):
    bl_label='Perform 2.49 to 2.7x Summary'
    bl_idname='xplane.do_249_conversion'
    bl_description = "Convert a file's 2.49 property format to 2.7x. WARNING: Running multiple times may have disasterious consequences"

    def execute(self,context):
        xplane_249_converter.do_249_conversion()
        return {'FINISHED'}
