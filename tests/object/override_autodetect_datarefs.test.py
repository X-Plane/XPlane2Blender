import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ATTR_manip" in line[0] or\
            "ATTR_axis_detented" in line[0])

class TestOverrideAutodetectDatarefs(XPlaneTestCase):
    def test_override_autodetect_datarefs_drag_axis(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_override_autodetect_datarefs_drag_axis_w_detents(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_override_autodetect_datarefs_drag_rotate(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

    def test_override_autodetect_datarefs_drag_rotate_dentent(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            3, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestOverrideAutodetectDatarefs])
 
