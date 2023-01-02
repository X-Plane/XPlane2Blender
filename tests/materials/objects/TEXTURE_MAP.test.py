import bpy
import os
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestTEXTURE_MAP_export(XPlaneTestCase):
    def test_export(self):
        def filterLines(line):
            return isinstance(line[0],str) and (\
                'TEXTURE' in line[0] or\
                'NORMAL' in line[0]\
                )

        filename = 'test_TEXTURE_MAP'

        for test_case in [ 'TEXTURE_MAP_normal_material_gloss', 'TEXTURE_MAP_normal', 'TEXTURE_MAP_normal_gloss' ]:
            self.assertExportableRootExportEqualsFixture(
                test_case,
                os.path.join(__dirname__, "../fixtures", f"{test_case}.obj"),
                filterLines,
                filename,
        )

    def test_mixed_source_error(self):
        filename = 'test_TEXTURE_MAP'

        self.exportExportableRoot('TEXTURE_MAP_normal_error', filename)
        self.assertLoggerErrors(1)

runTestCases([TestTEXTURE_MAP_export])
