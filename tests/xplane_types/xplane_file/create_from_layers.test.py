import bpy
import os
import unittest
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive

class TestCreateFromLayers(unittest.TestCase):
    def setUp(self):
        # initially create xplane layers
        bpy.ops.scene.add_xplane_layers()

    def test_getActiveBlenderLayerIndexes(self):
        # blender by default only activates first layer
        layers = xplane_file.getActiveBlenderLayerIndexes()
        self.assertEqual(len(layers), 1)
        self.assertEqual(layers[0], 0)

    def test_create_files_from_single_layer(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../tmp'))

        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        # should contain 4 cubes
        self.assertEqual(len(xplaneFile.objects), 4)

        objects = [
            'Cube',
            'Cube.001',
            'Cube.002',
            'Cube.003'
        ]

        for name in objects:
            self.assertIsNotNone(xplaneFile.objects[name])
            self.assertTrue(isinstance(xplaneFile.objects[name], XPlanePrimitive))
            self.assertEquals(xplaneFile.objects[name].blenderObject, bpy.data.objects[name])

        # print bone tree for now
        print(xplaneFile.filename)
        print(xplaneFile.rootBone)

        xplaneFile2 = xplane_file.createFileFromBlenderLayerIndex(1)

        # should contain 2 cubes
        self.assertEqual(len(xplaneFile2.objects), 2)

        objects = [
            'Cube.004',
            'Cube.005'
        ]

        for name in objects:
            self.assertIsNotNone(xplaneFile2.objects[name])
            self.assertTrue(isinstance(xplaneFile2.objects[name], XPlanePrimitive))
            self.assertEquals(xplaneFile2.objects[name].blenderObject, bpy.data.objects[name])

        # print bone tree for now
        print(xplaneFile2.filename)
        print(xplaneFile2.rootBone)

suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCreateFromLayers)
unittest.TextTestRunner().run(suite)
