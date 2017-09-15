import io_xplane2blender
from io_xplane2blender.tests import *

class TestAddon(XPlaneTestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_xplane2blender.bl_info)

runTestCases([TestAddon])
