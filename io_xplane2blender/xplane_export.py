# File: xplane_export.py
# Defines Classes used to create OBJ files out of XPlane data types defined in <xplane_types.py>.

import os.path
import bpy
import mathutils
import os
from .xplane_types import xplane_file
from .xplane_config import getDebug, getDebugger, getLog, initConfig, setErrors, getErrors

# TODO: on newer Blender builds io_utils seems to be in bpy_extras, on older ones bpy_extras does not exists. Should be removed with the official Blender release where bpy_extras is present.
try:
    from bpy_extras.io_utils import ImportHelper, ExportHelper
except ImportError:
    from io_utils import ImportHelper, ExportHelper

# Class: ExportXPlane
# Main Export class. Brings all parts together and creates the OBJ files.
class ExportXPlane(bpy.types.Operator, ExportHelper):
    '''Export to XPlane Object file format (.obj)'''
    bl_idname = "export.xplane_obj"
    bl_label = 'Export XPlane Object'

    filepath = bpy.props.StringProperty(
        name = "File Path",
        description = "Filepath used for exporting the XPlane file(s)",
        maxlen= 1024, default= ""
    )
    filename_ext = ''

    # Method: execute
    # Used from Blender when user invokes export.
    # Invokes the exporting.
    #
    # Parameters:
    #   context - Blender context object.
    def execute(self, context):
        initConfig()
        log = getLog()
        debug = getDebug()
        debugger = getDebugger()

        setErrors(False)

        if debug:
            debugger.start(log)

        filepath = self.properties.filepath
        if filepath=='':
            filepath = bpy.context.blend_data.filepath

        filepath = os.path.dirname(filepath)
        # filepath = bpy.path.ensure_ext(filepath, ".obj")

        # check if X-Plane layers have been created
        # TODO: only check if user selected the export from layers option, instead the export from root objects
        if len(bpy.context.scene.xplane.layers) == 0:
            errors = True
            # showError('You must create X-Plane layers first.')
            return {'FINISHED'}

        # store current frame as we will go back to it
        currentFrame = bpy.context.scene.frame_current

        # goto first frame so everything is in inital state
        bpy.context.scene.frame_set(frame = 1)
        bpy.context.scene.update()

        xplaneLayers = bpy.context.scene.xplane.layers.items()

        # create files for each exportable layer
        for layer in range(0, len(xplaneLayers)):
            xplaneLayer = bpy.context.scene.xplane.layers[layer]
            if xplaneLayer.export:
                xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)
                self._writeXPlaneFile(xplaneFile, filepath)

        # return to stored frame
        bpy.context.scene.frame_set(frame = currentFrame)
        bpy.context.scene.update()

        if debug:
            debugger.end()

        # if getErrors() == False:
        #    showProgress(1.0, 'Done!')

        return {'FINISHED'}

    def _writeXPlaneFile(self, xplaneFile, dir):
        debug = getDebug()
        debugger = getDebugger()

        # only write layers that contain objects
        if len(xplaneFile.objects) == 0:
            return

        fullpath = os.path.join(dir, xplaneFile.filename) + '.obj'

        # write the file
        if debug:
            debugger.debug("Writing %s" % xplaneFile.filename)

        file = open(fullpath, "w")
        file.write(xplaneFile.write())
        file.close()

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
