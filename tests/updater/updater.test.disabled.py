import bpy
import os
from io_xplane2blender.tests import *
import io_xplane2blender

class TestUpdater(XPlaneTestCase):
    def test_updater_stores_current_version(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../tmp'))
        tmpFile = os.path.join(tmpDir, 'updater_stores_current_version.blend')
        # save the file
        bpy.ops.wm.save_as_mainfile(
           filepath=tmpFile,
           check_existing=False
        )

        self.assertEqual(
            bpy.data.worlds[0].xplane2blender_version,
            '.'.join(map(str, io_xplane2blender.bl_info['version']))
        )

        # load the file
        bpy.ops.wm.open_mainfile(
            filepath=tmpFile
        )

        self.assertEqual(
            bpy.data.worlds[0].xplane2blender_version,
            '.'.join(map(str, io_xplane2blender.bl_info['version']))
        )

runTestCases([TestUpdater])
