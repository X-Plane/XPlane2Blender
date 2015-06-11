import bpy
import os
import unittest
from io_xplane2blender import xplane_file

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
            bpy.data.objects['Cube'],
            bpy.data.objects['Cube.001'],
            bpy.data.objects['Cube.002'],
            bpy.data.objects['Cube.003']
        ]

        for blenderObject in objects:
            self.assertIn(blenderObject, xplaneFile.objects)

        xplaneFile2 = xplane_file.createFileFromBlenderLayerIndex(1)

        # should contain 2 cubes
        self.assertEqual(len(xplaneFile2.objects), 2)

        objects = [
            bpy.data.objects['Cube.004'],
            bpy.data.objects['Cube.005']
        ]

        for blenderObject in objects:
            self.assertIn(blenderObject, xplaneFile2.objects)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(TestCreateFromLayers)
unittest.TextTestRunner().run(suite)
