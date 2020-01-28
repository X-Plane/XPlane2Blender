import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)


class TestRootObjectOffsets(XPlaneTestCase):
    def test_root_object_offsets(self):

        per_obj_tests = [
            ['cube_a', 'root_object_offsets.test_a', 1, ['cube_a'], ['0 Mesh: cube_a'] ],
            ['b', 'root_object_offsets.test_b', 2, ['cube_b'], ['0 Empty: b','1 Mesh: cube_b'] ],
            ['c', 'root_object_offsets.test_c', 2, ['cube_c'], ['0 Empty: c','1 Mesh: cube_c'] ]
        ]

        for one_obj_test in per_obj_tests:

            root_block = one_obj_test[0]
            file_stem = one_obj_test[1]
            obj_count = one_obj_test[2]
            obj_list = one_obj_test[3]
            bone_tree = one_obj_test[4]

            tmpDir = os.path.realpath(os.path.join(__dirname__, '../../tmp'))

            xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.objects[root_block])

            out = xplaneFile.write()

            fh = open(os.path.join(tmpDir, file_stem + '.obj'), 'w')
            fh.write(out)
            fh.close()

            # auto filename from blender object
            self.assertEqual(xplaneFile.filename, file_stem)

            # Confirm total count and find all primitives
            self.assertEqual(len(xplaneFile._bl_obj_name_to_bone), obj_count)
            self.assertObjectsInXPlaneFile(xplaneFile,obj_list)

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

            # Confirm bone structure
            assertXplaneFileHasBoneTree(self, xplaneFile, bone_tree)

            self.assertFileOutputEqualsFixture(
                out,
                os.path.join(__dirname__, 'fixtures',  file_stem+'.obj'),
                {"ANIM", "TRIS"}
            )

runTestCases([TestRootObjectOffsets])
