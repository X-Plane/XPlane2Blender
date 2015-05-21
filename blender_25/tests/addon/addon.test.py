import unittest
import io_xplane2blender

class TestAddon(unittest.TestCase):
    def test_addon_enabled(self):
        self.assertIsNotNone(io_xplane2blender.bl_info)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestAddon)
unittest.TextTestRunner().run(suite)
