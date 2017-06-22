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
            ['a cube', 'root_object_offsets_animated_a', 1, ['a cube'], ['0 Object: a cube'] ],
            ['b', 'root_object_offsets_animated_b', 2, ['b cube'], ['0 Object: b','1 Object: b cube'] ],
            ['c', 'root_object_offsets_animated_c', 2, ['c cube'], ['0 Object: c','1 Object: c cube'] ]
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

            self.assertFileEqualsFixture(
                out,
                os.path.join(__dirname__, 'fixtures',  file_stem+'.obj')
            )

runTestCases([TestCreateFromRootObjects])
