import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestRootObjectOffsetsAnimated(XPlaneTestCase):
    def test_root_object_offsets_animated(self):
    
        per_obj_tests = [
            ['a cube', 'root_object_offsets_animated_a', 1, ['a cube'], ['0 Mesh: a cube'] ],
            ['b', 'root_object_offsets_animated_b', 2, ['b cube'], ['0 Empty: b','1 Mesh: b cube'] ],
            ['c', 'root_object_offsets_animated_c', 2, ['c cube'], ['0 Empty: c','1 Mesh: c cube'] ]
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
            self.assertEqual(len(xplaneFile.objects), obj_count)
            self.assertObjectsInXPlaneFile(xplaneFile,obj_list)

            # Confirm bone structure
            self.assertXplaneFileHasBoneTree(xplaneFile, bone_tree)

            self.assertFileOutputEqualsFixture(
                out,
                os.path.join(__dirname__, 'fixtures',  file_stem+'.obj')
            )

runTestCases([TestRootObjectOffsetsAnimated])
