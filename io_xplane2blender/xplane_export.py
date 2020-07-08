"""The starting point for the export process, the start of the addon"""

import os
import os.path
import sys

import bpy
import io_xplane2blender
import mathutils
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .xplane_config import getDebug
from .xplane_helpers import XPlaneLogger, logger
from .xplane_types import xplane_file

from typing import Any, IO, Optional


class XPLANE_MT_xplane_export_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_export_log"
    bl_label = "XPlane2Blender Export Log Warning"

    def draw(self, context):
        self.layout.row().label(text='Export produced errors or warnings.')
        self.layout.row().label(text='Please see the internal text file XPlane2Blender.log')

def showLogDialog():
    if not ('-b' in sys.argv or '--background' in sys.argv):
        bpy.ops.wm.call_menu(name="XPLANE_MT_xplane_export_log")

class EXPORT_OT_ExportXPlane(bpy.types.Operator, ExportHelper):
    '''Export to X-Plane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export X-Plane Object'

    filename_ext = ".obj"

    filepath: bpy.props.StringProperty(
        name = "File Path",
        description = "Filepath used for exporting the X-Plane file(s). If none given, use the directory of the .blend file",
        maxlen= 1024, default= ""
    )

    only_selected_roots: bpy.props.BoolProperty(
        name = "Only Selected Roots",
        description = "If true, only valid selected roots will be exported",
        default=False
    )

    # Method: execute
    # Used from Blender when user invokes export.
    # Invokes the exporting.
    #
    # Parameters:
    #   context - Blender context object.
    def execute(self, context):
        # prepare logging
        self._startLogging()

        debug = getDebug()

        xp_scene_settings = bpy.context.scene.xplane
        if (bpy.context.blend_data.filepath == ""
            and not xp_scene_settings.dry_run):
            # We can't just save files relative to nothing somewhere on a users HDD (bad usability!) so we say there is an error.
            logger.error("Save your .blend file before exporting")
            self._endLogging()
            showLogDialog()
            return {'CANCELLED'}

        if (xp_scene_settings.plugin_development
            and xp_scene_settings.dev_enable_breakpoints):
            breakpoint()

        # store current frame as we will go back to it
        currentFrame = bpy.context.scene.frame_current

        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame = 1)
        bpy.context.view_layer.update()

        xplaneFiles = xplane_file.createFilesFromBlenderRootObjects(
            bpy.context.scene,
            bpy.context.view_layer,
            self.only_selected_roots
        )
        for xplaneFile in xplaneFiles:
            try:
                self._writeXPlaneFile(xplaneFile)
            except (OSError, ValueError):
                if logger.hasErrors():
                    self._endLogging()
                    showLogDialog()

                if (xp_scene_settings.plugin_development
                    and xp_scene_settings.dev_continue_export_on_error):
                    logger.info(f"Continuing export despite possible errors in '{xplaneFile.filename}'")
                    logger.clearMessages()
                    continue
                else:
                    return {'CANCELLED'}

        # return to stored frame
        bpy.context.scene.frame_set(frame = currentFrame)
        bpy.context.view_layer.update()

        #TODO: enable when log dialog box is working
        #if logger.hasErrors() or logger.hasWarnings():
            #showLogDialog()

        if not xplaneFiles:
            logger.error("Could not find any Root Collections or Objects, did you forget check 'Root Collection' or 'Root Object'?")
            self._endLogging()
            return {'CANCELLED'}
        elif logger.hasErrors():
            self._endLogging()
            return {'CANCELLED'}
        elif not logger.hasErrors() and xplaneFiles:
            logger.success("Export finished without errors")
            self._endLogging()
            return {'FINISHED'}

    def _startLogging(self):
        debug = getDebug()
        logLevels = ['error', 'warning']

        self.logFile:Optional[IO[Any]] = None

        logger.clearTransports()
        logger.clearMessages()

        # in debug mode, we log everything
        if debug:
            logLevels.append('info')
            logLevels.append('success')

        # always log to internal text file and console
        logger.addTransport(XPlaneLogger.InternalTextTransport('xplane2blender.log'), logLevels)
        logger.addTransport(XPlaneLogger.ConsoleTransport(), logLevels)

        # log out to a file if logging is enabled
        if debug and bpy.context.scene.xplane.log:
            if bpy.context.blend_data.filepath != '':
                filepath = os.path.dirname(bpy.context.blend_data.filepath)
                #Something this? self.logfile = os.path.join(dir,name+'_'+time.strftime("%y-%m-%d-%H-%M-%S")+'_xplane2blender.log')
                self.logFile = open(os.path.join(filepath, 'xplane2blender.log'), 'w')
                logger.addTransport(XPlaneLogger.FileTransport(self.logFile), logLevels)
            else:
                logger.error("Cannot create log file if .blend file is not saved")

    def _endLogging(self):
        if self.logFile:
            self.logFile.close()

    def _writeXPlaneFile(self, xplaneFile: xplane_file.XPlaneFile) -> bool:
        """
        Finally, at the end of it all, attempts to write an XPlaneFile.
        Raises OSError or ValueError if something went wrong
        """
        debug = getDebug()

        # only write layers that contain objects
        if not xplaneFile.get_xplane_objects():
            raise ValueError
        elif os.path.isabs(
            xplaneFile.filename[2:]
            if xplaneFile.filename.startswith("//")
            else xplaneFile.filename
        ):
            logger.error(
                f"Root file name '{xplaneFile.filename}' must not be an absolute path - it must be relative to the .blend file"
            )
            raise ValueError

        xplaneFile.filename = bpy.path.ensure_ext(xplaneFile.filename, ".obj")
        if self.filepath:
            xplaneFile.filename = xplaneFile.filename.replace("//","")
            final_path = os.path.abspath(
                        os.path.join(
                            self.filepath,
                            xplaneFile.filename
                        )
                    )
        else:
            if xplaneFile.filename.startswith("//"):
                final_path = os.path.abspath(bpy.path.abspath(xplaneFile.filename))
            else:
                final_path = os.path.abspath(
                    os.path.join(
                        os.path.dirname(bpy.context.blend_data.filepath),
                        bpy.path.abspath(xplaneFile.filename),
                    )
                )

        plugin_development = bpy.context.scene.xplane.plugin_development
        dry_run = bpy.context.scene.xplane.dev_export_as_dry_run
        out = xplaneFile.write()
        if logger.hasErrors():
            raise ValueError
        elif plugin_development and dry_run:
            logger.info("Not writing '{fullpath}' due to 'Dry Run'")
        else:
            try:
                os.makedirs(os.path.dirname(final_path), exist_ok=True)
            except OSError as e:
                logger.error(e)
                raise
            else:
                with open(final_path, "w") as objFile:
                    logger.info(f"Writing '{final_path}'")
                    objFile.write(out)
                    logger.success(f"Wrote '{final_path}'")


    def invoke(self, context, event):
        """
        Used from Blender when user hits the Export-Entry in the File>Export menu.
        Creates a file select window.
        """
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

_classes = (
        XPLANE_MT_xplane_export_log,
        EXPORT_OT_ExportXPlane
    )

register, unregister = bpy.utils.register_classes_factory(_classes)
