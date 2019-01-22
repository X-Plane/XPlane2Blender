import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0], str) and \
            (
                "ANIM" in line[0] or \
                "ATTR_manip" in line[0] or \
                "TRIS" in line[0]
            )

class TestManipDecodingOndrej(XPlaneTestCase):
    def test_manip_decoding_ondrej(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.SKIP.name)
        bpy.context.scene.xplane.layers[0].export_type = xplane_constants.EXPORT_TYPE_COCKPIT
        filename = inspect.stack()[0][3].replace("test_", "")

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_manip_decoding_ondrej_drag_rotate(self):
        # This is okay, after it runs once it won't run again
        # TestRunner doesn't always run these in order
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.SKIP.name)
        bpy.context.scene.xplane.layers[1].export_type = xplane_constants.EXPORT_TYPE_COCKPIT
        filename = inspect.stack()[0][3].replace("test_", "")
        bpy.context.scene.xplane.layers[0].name = filename

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_manip_decoding_ondrej_one_of_everything(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.SKIP.name)
        bpy.context.scene.xplane.layers[2].export_type = xplane_constants.EXPORT_TYPE_COCKPIT
        filename = inspect.stack()[0][3].replace("test_", "")
        bpy.context.scene.xplane.layers[0].name = filename

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )


runTestCases([TestManipDecodingOndrej])
