import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCreateFromRootObjects(XPlaneTestCase):
    def setUp(self):
        super(TestCreateFromRootObjects, self).setUp()

    def test_create_files_from_root_objects(self):
    
        per_obj_tests = [
            ['cube_a', 'root_object_offsets.test_a', 1, ['cube_a'], ['0 Object: cube_a'] ],
            ['b', 'root_object_offsets.test_b', 2, ['cube_b'], ['0 Object: b','1 Object: cube_b'] ],
            ['c', 'root_object_offsets.test_c', 2, ['cube_c'], ['0 Object: c','1 Object: cube_c'] ]
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

runTestCases([TestCreateFromRootObjects])
