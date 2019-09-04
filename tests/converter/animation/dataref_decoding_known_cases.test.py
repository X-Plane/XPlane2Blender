import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import ProjectType, WorkflowType

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or\
             "IDX" in line[0] or\
             "TRIS" in line[0] or\
             "VT" in line[0])

class TestDatarefDecodingKnownCases(XPlaneTestCase):
    def test_dataref_decoding_known_cases(self):
        bpy.ops.xplane.do_249_conversion(project_type=ProjectType.AIRCRAFT.name, workflow_type=WorkflowType.SKIP.name)
        filename = inspect.stack()[0][3]
        filename = filename.replace("test_","")

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestDatarefDecodingKnownCases])
