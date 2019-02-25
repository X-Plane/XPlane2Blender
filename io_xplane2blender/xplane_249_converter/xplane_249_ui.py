'''
Defines the UI for converter related elements.
Prominately, the import dialog box.
'''
import bpy

def read_some_data(context, filepath, use_some_setting):
    #TODO: Create backup .blend file, quit if couldn't do it
    print("running read_some_data...")
    f = open(filepath, 'r', encoding='utf-8')
    data = f.read()
    f.close()

    # would normally load the data here
    print(data)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

from io_xplane2blender.xplane_249_converter.xplane_249_constants import WORKFLOW_DEFAULT_ROOT_NAME, WorkflowType

class ImportAndConvert(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "xplane.do_convert_old_blend"
    bl_label = "Convert 2.49 .blend File"
    bl_description = "A backup will be created, the file name + '_backup', in the same directory"

    # ImportHelper mixin class uses this
    filename_ext = ".blend"

    filter_glob = StringProperty(
        default="*.blend",
        options={'HIDDEN'},
        maxlen=255,  # Max internal buffer length, longer would be clamped.
        )

    custom_datarefs_file = StringProperty(
        name="Custom DataRefs.txt Filepath",
        description="Prevent 'Unknown Dataref' errors by using your original DataRefs.txt, if any",
        default="",
        subtype="FILE_PATH"
        )

    workflow_type = bpy.props.EnumProperty(
            items=[
                (
                    WorkflowType.SKIP.name,
                    "Skip Automatic Conversion (unrecommended)",
                    "Skips auto top-level reparenting and filling out Root Objects information (unrecommended)",
                    "ERROR",
                    0
                ),
                (
                    WorkflowType.REGULAR.name,
                    WorkflowType.REGULAR.name.title(),
                    "Project used Export v8/v9 script, top objects parented to " + WORKFLOW_DEFAULT_ROOT_NAME
                ),
                (WorkflowType.BULK.name, WorkflowType.BULK.name.title(), "Project used Bulk Export script"),
            ],
            name="Previous Workflow Type",
            description="Knowing the old workflow enables conversion to a modern equivalent",
            default=WorkflowType.REGULAR.name,
        )


    def execute(self, context):
        return read_some_data(context, self.filepath, self.use_setting)

# Only needed if you want to add into a dynamic menu
def menu_func_import(self, context):
    self.layout.operator(ImportAndConvert.bl_idname, text="Convert XPlane2Blender 2.49 .blend")


def register():
    pass
    bpy.utils.register_class(ImportAndConvert)
    bpy.types.INFO_MT_file_import.append(menu_func_import)


def unregister():
    pass
    bpy.utils.unregister_class(ImportAndConvert)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

