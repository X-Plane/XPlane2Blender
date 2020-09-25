"""The starting point for the export process, the start of the addon"""

import os
import os.path
import sys
from typing import IO, Any, Optional

import bpy
import mathutils

import io_xplane2blender
from bpy_extras.io_utils import ExportHelper, ImportHelper

from .xplane_config import getDebug
from .xplane_helpers import XPlaneLogger, logger
from .xplane_types import xplane_file


class XPLANE_MT_xplane_export_log(bpy.types.Menu):
    bl_idname = "XPLANE_MT_xplane_export_log"
    bl_label = "XPlane2Blender Export Log Warning"

    def draw(self, context):
        self.layout.row().label(text="Export produced errors or warnings.")
        self.layout.row().label(
            text="Please see the internal text file XPlane2Blender.log"
        )


def showLogDialog():
    if not ("-b" in sys.argv or "--background" in sys.argv):
        bpy.ops.wm.call_menu(name="XPLANE_MT_xplane_export_log")


class EXPORT_OT_ExportXPlane(bpy.types.Operator, ExportHelper):
    """Export to X-Plane Object file format (.obj)"""

    bl_idname = "export.xplane_obj"
    bl_label = "Export X-Plane Object"

    filename_ext = ".obj"

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the X-Plane file(s)",
        maxlen=1024,
        default="",
    )

    export_is_relative: bpy.props.BoolProperty(
        name="Export Is Relative",
        description="Set to true when starting the export via the button (with or without the GUI on in case of unit testing)",
        default=False,
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
        export_directory = self.properties.filepath

        if not self.properties.export_is_relative:
            export_directory = os.path.dirname(export_directory)
        else:
            if bpy.context.blend_data.filepath == "":
                # We can't just save files relative to nothing somewhere on a users HDD (bad usability!) so we say there is an error.
                logger.error(
                    "Save your blend file before using the '%s' button"
                    % io_xplane2blender.xplane_ops.SCENE_OT_export_to_relative_dir.bl_label
                )
                self._endLogging()
                showLogDialog()
                return {"CANCELLED"}

        if (
            bpy.context.scene.xplane.plugin_development
            and bpy.context.scene.xplane.dev_enable_breakpoints
        ):
            breakpoint()

        # store current frame as we will go back to it
        currentFrame = bpy.context.scene.frame_current

        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame=1)
        bpy.context.view_layer.update()

        xplaneFiles = xplane_file.createFilesFromBlenderRootObjects(
            bpy.context.scene, bpy.context.view_layer
        )
        for xplaneFile in xplaneFiles:
            if not self._writeXPlaneFile(xplaneFile, export_directory):
                if logger.hasErrors():
                    self._endLogging()
                    showLogDialog()

                if (
                    bpy.context.scene.xplane.plugin_development
                    and bpy.context.scene.xplane.dev_continue_export_on_error
                ):
                    logger.info(
                        "Continuing export despite error in %s" % xplaneFile.filename
                    )
                    logger.clearMessages()
                    continue
                else:
                    return {"CANCELLED"}

        # return to stored frame
        bpy.context.scene.frame_set(frame=currentFrame)
        bpy.context.view_layer.update()

        # TODO: enable when log dialog box is working
        # if logger.hasErrors() or logger.hasWarnings():
        #     showLogDialog()

        if not xplaneFiles:
            logger.error(
                "Could not find any Exportable Collections or Objects, did you forget check 'Exportable Collection' or 'Exportable Object'?"
            )
            self._endLogging()
            return {"CANCELLED"}
        elif logger.hasErrors():
            self._endLogging()
            return {"CANCELLED"}
        elif not logger.hasErrors() and xplaneFiles:
            logger.success("Export finished without errors")
            self._endLogging()
            return {"FINISHED"}

    def _startLogging(self):
        debug = getDebug()
        logLevels = ["error", "warning"]

        self.logFile: Optional[IO[Any]] = None

        logger.clearTransports()
        logger.clearMessages()

        # in debug mode, we log everything
        if debug:
            logLevels.append("info")
            logLevels.append("success")

        # always log to internal text file and console
        logger.addTransport(
            XPlaneLogger.InternalTextTransport("xplane2blender.log"), logLevels
        )
        logger.addTransport(XPlaneLogger.ConsoleTransport(), logLevels)

        # log out to a file if logging is enabled
        if debug and bpy.context.scene.xplane.log:
            if bpy.context.blend_data.filepath != "":
                filepath = os.path.dirname(bpy.context.blend_data.filepath)
                # Something this? self.logfile = os.path.join(dir,name+'_'+time.strftime("%y-%m-%d-%H-%M-%S")+'_xplane2blender.log')
                self.logFile = open(os.path.join(filepath, "xplane2blender.log"), "w")
                logger.addTransport(XPlaneLogger.FileTransport(self.logFile), logLevels)
            else:
                logger.error("Cannot create log file if .blend file is not saved")

    def _endLogging(self):
        if self.logFile:
            self.logFile.close()

    def _writeXPlaneFile(
        self, xplaneFile: xplane_file.XPlaneFile, directory: str
    ) -> bool:
        """
        Finally, at the end of it all, attempts to write an XPlaneFile.
        Returns False if there was a problem, else True
        """
        debug = getDebug()

        # only write layers that contain objects
        if not xplaneFile.get_xplane_objects():
            return False

        if xplaneFile.filename.find("//") == 0:
            xplaneFile.filename = xplaneFile.filename.replace("//", "", 1)

        # Change any backslashes to foward slashes for file paths
        xplaneFile.filename = xplaneFile.filename.replace("\\", "/")

        if os.path.isabs(xplaneFile.filename):
            logger.error(
                "Bad export path %s: File paths must be relative to the .blend file"
                % (xplaneFile.filename)
            )
            return False

        # Get the relative path
        # Append .obj if needed
        # Make paths based on the absolute path
        # Write
        relpath = os.path.normpath(os.path.join(directory, xplaneFile.filename))
        if not ".obj" in relpath:
            relpath += ".obj"

        fullpath = os.path.abspath(
            os.path.join(os.path.dirname(bpy.context.blend_data.filepath), relpath)
        )
        out = xplaneFile.write()

        if logger.hasErrors():
            return False

        plugin_development = bpy.context.scene.xplane.plugin_development
        dry_run = bpy.context.scene.xplane.dev_export_as_dry_run
        if not plugin_development or (plugin_development and not dry_run):
            try:
                os.makedirs(os.path.dirname(fullpath), exist_ok=True)
            except OSError as e:
                logger.error(e)
            else:
                with open(fullpath, "w") as objFile:
                    logger.info("Writing %s" % fullpath)
                    objFile.write(out)
                    logger.success("Wrote %s" % fullpath)
        else:
            logger.info('Skipped writing %s due to "Dry Run"' % (fullpath))

        return True

    def invoke(self, context, event):
        """
        Used from Blender when user hits the Export-Entry in the File>Export menu.
        Creates a file select window.
        """
        wm = context.window_manager
        wm.fileselect_add(self)
        return {"RUNNING_MODAL"}


_classes = (XPLANE_MT_xplane_export_log, EXPORT_OT_ExportXPlane)

register, unregister = bpy.utils.register_classes_factory(_classes)
