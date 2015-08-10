import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file, XPlanePrimitive
from io_xplane2blender import xplane_config

class TestCreateFromRootObjects(XPlaneTestCase):
    def setUp(self):
        super(TestCreateFromRootObjects, self).setUp()

    def test_create_files_from_root_objects(self):
        tmpDir = os.path.realpath(os.path.join(__file__, '../../tmp'))

        xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_1'])

        # auto filename from blender object
        self.assertEqual(xplaneFile.filename, 'root_1')

        # should contain 3 cubes
        self.assertEqual(len(xplaneFile.objects), 4)

        self.assertObjectsInXPlaneFile(
            xplaneFile, [
            'root_1',
            'root_1_child_1',
            'root_1_child_1_child',
            'root_1_child_2'
        ])

        self.assertXplaneFileHasBoneTree(
            xplaneFile, [
            '0 ROOT',
                '1 Object: root_1',
                    '2 Object: root_1_child_1',
                        '3 Object: root_1_child_1_child',
                    '2 Object: root_1_child_2'
        ])

        xplaneFile2 = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_2'])

        # custom file name
        self.assertEqual(xplaneFile2.filename, 'custom_name')

        # should contain 1 cube
        self.assertEqual(len(xplaneFile2.objects), 1)

        self.assertObjectsInXPlaneFile(
            xplaneFile2, [
            'root_2'
        ])

        self.assertXplaneFileHasBoneTree(
            xplaneFile2, [
            '0 ROOT',
                '1 Object: root_2'
        ])

runTestCases([TestCreateFromRootObjects])
