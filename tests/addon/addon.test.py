from io_xplane2blender.tests import *
import io_xplane2blender

class TestAddon(XPlaneTestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_xplane2blender.bl_info)

runTestCases([TestAddon])
