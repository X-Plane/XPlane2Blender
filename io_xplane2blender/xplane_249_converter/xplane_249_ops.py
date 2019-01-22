'''Defines operators for the 249 conversion'''

import re

import bpy
import io_xplane2blender

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_249_converter.xplane_249_workflow_converter import WorkflowType


class SCENE_OT_249_do_conversion(bpy.types.Operator):
    bl_label='Perform 2.49 to 2.7x Summary'
    bl_idname='xplane.do_249_conversion'
    bl_description = "Convert a file's 2.49 property format to 2.7x. WARNING: Running multiple times may have disastrous consequences"

    workflow_type = bpy.props.StringProperty(
        name="Workflow type",
        description="The workflow type to be used",
        )

    def execute(self, context):
        assert self.workflow_type in WorkflowType.__dict__, \
                "{} is not a known WorkflowType".format(self.workflow_type)
        io_xplane2blender.xplane_249_converter.do_249_conversion(
            context,
            workflow_type=WorkflowType[self.workflow_type]
            )
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SCENE_OT_249_do_conversion)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_249_do_conversion)

