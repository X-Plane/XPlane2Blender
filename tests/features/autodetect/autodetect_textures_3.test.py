import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestAutodetectTextures3(XPlaneTestCase):
    expected_logger_warnings = 1
    def test_autodetect_textures_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_autodetect_textures_3'
        self.assertEqual(bpy.data.scenes[0].xplane.layers[0].autodetectTextures, False)
        
        #Test if the texture is correct and that users are warned that their materials are going to get checked to reference materials
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, '..', 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )
        
runTestCases([TestAutodetectTextures3])
