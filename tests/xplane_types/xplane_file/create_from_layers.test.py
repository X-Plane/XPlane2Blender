import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

class TestCreateFromLayers(XPlaneTestCase):
    def test_create_files_from_single_layer(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../tmp'))

        xplaneFile = self.createXPlaneFileFromPotentialRoot(bpy.data.collections["Layer 1"])

        # should contain 4 cubes
        self.assertEqual(len(xplaneFile._bl_obj_name_to_bone), 4)

        self.assertObjectsInXPlaneFile(
            xplaneFile, [
            'Cube',
            'Cube.001',
            'Cube.002',
            'Cube.003'
        ])

        def assertXplaneFileHasBoneTree(self, xplaneFile, tree):
            self.assertIsNotNone(xplaneFile.rootBone)

            bones = []

            def collect(bone):
                bones.append(bone)
                for bone in bone.children:
                    collect(bone)

            collect(xplaneFile.rootBone)

            self.assertEqual(len(tree), len(bones))

            index = 0

            while index < len(bones):
                self.assertEqual(tree[index], bones[index].getName())
                index += 1
        assertXplaneFileHasBoneTree(
            self,
            xplaneFile, [
            '0 ROOT',
                '1 Mesh: Cube',
                    '2 Mesh: Cube.001',
                        '3 Mesh: Cube.002',
                            '4 Mesh: Cube.003'
        ])


        xplaneFile2 = self.createXPlaneFileFromPotentialRoot(bpy.data.collections["Layer 2"])

        # should contain 2 cubes
        self.assertEqual(len(xplaneFile2._bl_obj_name_to_bone), 2)

        self.assertObjectsInXPlaneFile(
            xplaneFile2, [
            'Cube.004',
            'Cube.005'
        ])

        assertXplaneFileHasBoneTree(
            self,
            xplaneFile2, [
            '0 ROOT',
                '1 Mesh: Cube.004',
                '1 Mesh: Cube.005'
        ])

        xplaneFile3 = self.createXPlaneFileFromPotentialRoot(bpy.data.collections["Layer 3"])

        # should contain 4 cubes
        self.assertEqual(len(xplaneFile3._bl_obj_name_to_bone), 5)

        self.assertObjectsInXPlaneFile(
            xplaneFile3, [
            'Cube_arm_root',
            'Cube_Bone',
            'Cube_Bone.child',
            'Cube_Bone.001'
        ])

        assertXplaneFileHasBoneTree(
            self,
            xplaneFile3, [
            '0 ROOT',
                '1 Mesh: Cube_arm_root',
                    '2 Armature: Armature',
                        '3 Bone: Bone',
                            '4 Bone: Bone.001',
                                '5 Mesh: Cube_Bone.001',
                            '4 Mesh: Cube_Bone',
                                '5 Mesh: Cube_Bone.child',
        ])

runTestCases([TestCreateFromLayers])
