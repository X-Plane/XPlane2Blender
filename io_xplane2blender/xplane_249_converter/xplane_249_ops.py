'''Defines operators for the 249 conversion'''

import bpy

from io_xplane2blender.xplane_249_converter import xplane_249_constants, xplane_249_convert

class SCENE_OT_249_do_conversion(bpy.types.Operator):
    bl_label = 'Perform 2.49 to 2.79 Conversion'
    bl_idname = 'xplane.do_249_conversion'
    bl_description = "Convert a file's 2.49 property format to 2.7x. WARNING: Running multiple times may have disastrous consequences"

    project_type = bpy.props.StringProperty(
        name = "Project Type",
        description="The type of project contain in the blend file, one of " + ", ".join([attr.name for attr in xplane_249_constants.ProjectType])
        )
    workflow_type = bpy.props.StringProperty(
        name="Workflow Type",
        description="The workflow used in 2.49, one of " + ", ".join([attr.name for attr in xplane_249_constants.WorkflowType]),
        )

    def execute(self, context: bpy.types.Context):
        assert self.project_type in xplane_249_constants.ProjectType.__dict__, \
                "{} is not a known ProjectType".format(self.project_type)
        assert self.workflow_type in xplane_249_constants.WorkflowType.__dict__, \
                "{} is not a known WorkflowType".format(self.workflow_type)
        xplane_249_convert.do_249_conversion(
            context,
            project_type=xplane_249_constants.ProjectType[self.project_type],
            workflow_type=xplane_249_constants.WorkflowType[self.workflow_type]
            )
        return {'FINISHED'}


def register():
    bpy.utils.register_class(SCENE_OT_249_do_conversion)


def unregister():
    bpy.utils.unregister_class(SCENE_OT_249_do_conversion)

