# File: xplane_export.py
# Defines Classes used to create OBJ files out of XPlane data types defined in <xplane_types.py>.

import os.path
import bpy
import mathutils
import os
import sys
from .xplane_helpers import XPlaneLogger, logger
from .xplane_types import xplane_file
from .xplane_config import getDebug
from bpy_extras.io_utils import ImportHelper, ExportHelper
import io_xplane2blender

class ExportLogDialog(bpy.types.Menu):
    bl_idname = "SCENE_MT_xplane_export_log"
    bl_label = "XPlane2Blender Export Log"

    def draw(self, context):
        row = self.layout.row()
        row.label('Export produced errors or warnings.')
        row = self.layout.row()
        row.label('Please take a look into the internal text file XPlane2Blender.log')

def showLogDialog():
    if not ('-b' in sys.argv or '--background' in sys.argv):
        bpy.ops.wm.call_menu(name = "SCENE_MT_xplane_export_log")

# Class: ExportXPlane
# Main Export class. Brings all parts together and creates the OBJ files.
class ExportXPlane(bpy.types.Operator, ExportHelper):
    '''Export to X-Plane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export X-Plane Object'

    filepath = bpy.props.StringProperty(
        name = "File Path",
        description = "Filepath used for exporting the X-Plane file(s)",
        maxlen= 1024, default= ""
    )

    filename_ext = '.obj'

    export_is_relative = bpy.props.BoolProperty(
        name = "Export Is Relative",
        description="Set to true when starting the export via the button (with or without the GUI on in case of unit testing)",
        default=False)

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
            if bpy.context.blend_data.filepath == '':
                #We can't just save files relative to nothing somewhere on a users HDD (bad usability!) so we say there is an error.
                logger.error("Save your blend file before using the '%s' button" % io_xplane2blender.xplane_ops.SCENE_OT_export_to_relative_dir.bl_label)
                self._endLogging()
                showLogDialog()
                return {'CANCELLED'}

        if bpy.context.scene.xplane.plugin_development and \
            bpy.context.scene.xplane.dev_enable_breakpoints:
            try:
                #If you do not have your interpreter set up to include pydev by default, do so, or manually fill
                #in the path. Likely something like ~\.p2\pool\plugins\org.python.pydev_5.7.0.201704111357\pysrc
                #import sys;sys.path.append(r'YOUR_PYDEVPATH')
                import pydevd;
                #Port must be set to 5678 for Blender to connect!
                pydevd.settrace(stdoutToServer=False,#Enable to have logger and print statements sent to 
                                                     #the Eclipse console, as well as Blender's console.
                                                     #Only logger statements will show in xplane2blender.log
                                stderrToServer=False,#Same as stdoutToServer
                                suspend=True) #Seems to only work having suspend be set to true.
                                              #Get used to immediately pressing continue unfortunately.
            except:
                logger.info("Pydevd could not be imported, breakpoints not enabled. Ensure PyDev is installed and configured properly")
        
        exportMode = bpy.context.scene.xplane.exportMode

        if exportMode == 'layers':
            # check if X-Plane layers have been created
            # TODO: only check if user selected the export from layers option, instead the export from root objects
            if len(bpy.context.scene.xplane.layers) == 0:
                logger.error('You must create X-Plane layers first.')
                self._endLogging()
                showLogDialog()
                return {'CANCELLED'}

        # store current frame as we will go back to it
        currentFrame = bpy.context.scene.frame_current

        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame = 1)
        bpy.context.scene.update()

        xplaneFiles = []

        if exportMode == 'layers':
            xplaneFiles = xplane_file.createFilesFromBlenderLayers()

        elif exportMode == 'root_objects':
            xplaneFiles = xplane_file.createFilesFromBlenderRootObjects(bpy.context.scene)

        for xplaneFile in xplaneFiles:
            if self._writeXPlaneFile(xplaneFile, export_directory) == False:
                if logger.hasErrors():
                    self._endLogging()
                    showLogDialog()

                if bpy.context.scene.xplane.plugin_development and \
                    bpy.context.scene.xplane.dev_continue_export_on_error:
                    logger.info("Continuing export despite error in %s" % xplaneFile.filename)
                    logger.clearMessages()
                    continue
                else:
                    return {'CANCELLED'}

        # return to stored frame
        bpy.context.scene.frame_set(frame = currentFrame)
        bpy.context.scene.update()

        #TODO: enable when log dialog box is working 
        #if logger.hasErrors() or logger.hasWarnings():
            #showLogDialog()

        if not logger.hasErrors():
            logger.success("Export finished without errors")

        self._endLogging()
        return {'FINISHED'}

    def _startLogging(self):
        debug = getDebug()
        logLevels = ['error', 'warning']

        self.logFile = None

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

    def _writeXPlaneFile(self, xplaneFile, dir):
        debug = getDebug()

        # only write layers that contain objects
        if len(xplaneFile.objects) == 0:
            return
        
        if xplaneFile.filename.find('//') == 0:
            xplaneFile.filename = xplaneFile.filename.replace('//','',1)
        
        #Change any backslashes to foward slashes for file paths
        xplaneFile.filename = xplaneFile.filename.replace('\\','/')    
        
        if os.path.isabs(xplaneFile.filename):
            logger.error("Bad export path %s: File paths must be relative to the .blend file" % (xplaneFile.filename))
            return False
        
        #Get the relative path
        #Append .obj if needed
        #Make paths based on the absolute path
        #Write
        relpath = os.path.normpath(os.path.join(dir, xplaneFile.filename))
        if not '.obj' in relpath:
            relpath += '.obj'
        
        fullpath = os.path.abspath(os.path.join(os.path.dirname(bpy.context.blend_data.filepath),relpath))
        out = xplaneFile.write()
       
        if logger.hasErrors():
            return False

        # write the file
        if (bpy.context.scene.xplane.plugin_development is False) or \
            (bpy.context.scene.xplane.plugin_development and         \
             bpy.context.scene.xplane.dev_export_as_dry_run is False):
            try:
                os.makedirs(os.path.dirname(fullpath),exist_ok=True)
                objFile = open(fullpath, "w")
                logger.info("Writing %s" % fullpath)
                objFile.write(out)
                logger.success("Wrote %s" % fullpath)
            except Exception as e:
                logger.error(e)
            finally:
                if objFile != None:
                    objFile.close()
        else:
            logger.info('Skipped writing %s due to "Dry Run"' % (fullpath))


    # Method: invoke
    # Used from Blender when user hits the Export-Entry in the File>Export menu.
    # Creates a file select window.
    #
    # Todos:
    #   - window does not seem to work on Mac OS. Is there something different in the py API?
    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
