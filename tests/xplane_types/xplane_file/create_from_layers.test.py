import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

class TestCreateFromLayers(XPlaneTestCase):
    def setUp(self):
        super(TestCreateFromLayers, self).setUp()

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

        self.assertObjectsInXPlaneFile(
            xplaneFile, [
            'Cube',
            'Cube.001',
            'Cube.002',
            'Cube.003'
        ])

        self.assertXplaneFileHasBoneTree(
            xplaneFile, [
            '0 ROOT',
                '1 Object: Cube',
                    '2 Object: Cube.001',
                        '3 Object: Cube.002',
                            '4 Object: Cube.003'
        ])

        xplaneFile2 = xplane_file.createFileFromBlenderLayerIndex(1)

        # should contain 2 cubes
        self.assertEqual(len(xplaneFile2.objects), 2)

        self.assertObjectsInXPlaneFile(
            xplaneFile2, [
            'Cube.004',
            'Cube.005'
        ])

        self.assertXplaneFileHasBoneTree(
            xplaneFile2, [
            '0 ROOT',
                '1 Object: Cube.005',
                '1 Object: Cube.004'
        ])

        xplaneFile3 = xplane_file.createFileFromBlenderLayerIndex(2)

        # should contain 4 cubes
        self.assertEqual(len(xplaneFile3.objects), 5)

        self.assertObjectsInXPlaneFile(
            xplaneFile3, [
            'Cube_arm_root',
            'Cube_Bone',
            'Cube_Bone.child',
            'Cube_Bone.001'
        ])

        self.assertXplaneFileHasBoneTree(
            xplaneFile3, [
            '0 ROOT',
                '1 Object: Cube_arm_root',
                    '2 Object: Armature',
                        '3 Bone: Bone',
                            '4 Object: Cube_Bone',
                                '5 Object: Cube_Bone.child',
                            '4 Bone: Bone.001',
                                '5 Object: Cube_Bone.001'
        ])

runTestCases([TestCreateFromLayers])
