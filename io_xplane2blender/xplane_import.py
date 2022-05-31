"""The starting point for the export process, the start of the addon"""
import dataclasses
import os
import os.path
import pathlib
import sys
from typing import IO, Any, Optional

import bpy
import mathutils

import io_xplane2blender
from bpy_extras.io_utils import ExportHelper, ImportHelper
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.xplane_helpers import logger


"""
class XPLANE_MT_xplane_export_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_export_log"
    bl_label = "XPlane2Blender Export Log Warning"

    def draw(self, context):
        self.layout.row().label(text="Export produced errors or warnings.")
        self.layout.row().label(
            text="Please see the internal text file XPlane2Blender.log"
        )
"""


class XPLANE_MT_xplane_import_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_import_log"
    bl_label = "XPlane2Blender Import"

    pass


class IMPORT_OT_ImportXPlane(bpy.types.Operator, ImportHelper):
    """Import X-Plane Object file format (.obj)"""

    bl_idname = "import_scene.xplane_obj"
    bl_label = "Import X-Plane Object"

    filename_ext = ".obj"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filename used for importing an X-Plane .obj",
        maxlen=1024,
        default="",
    )

    def execute(self, context):
        logger.clear()
        # logger.addTransport(logger.ConsoleTransport)
        logger.addTransport(
            logger.InternalTextTransport(
                f"Import for {pathlib.Path(self.filepath).name}"
            )
        )
        logger.addTransport(logger.ConsoleTransport())
        # logger.info("Begin importing")
        x = xplane_imp_parser.import_obj(self.filepath)

        # print("IMPORT!")
        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


_classes = (IMPORT_OT_ImportXPlane,)
register, unregister = bpy.utils.register_classes_factory(_classes)
