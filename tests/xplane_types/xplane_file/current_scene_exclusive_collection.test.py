import inspect
import os
import sys

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("POINT_COUNTS" in line[0])

class TestCurrentSceneExclusiveCollection(XPlaneTestCase):
    def test_current_scene_exclusive_collection(self):
        filename = inspect.stack()[0].function

        self.assertExportableRootExportEqualsFixture(
            'OBJ_Cockpit', os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

runTestCases([TestCurrentSceneExclusiveCollection])
