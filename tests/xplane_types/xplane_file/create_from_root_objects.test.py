import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

class TestCreateFromRootObjects(XPlaneTestCase):
    def setUp(self):
        super(TestCreateFromRootObjects, self).setUp()

    def test_create_files_from_root_objects(self):
        tmpDir = os.path.realpath(os.path.join(__dirname__, '../../tmp'))

        xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_1'])

        out = xplaneFile.write()

        fh = open(os.path.join(tmpDir, 'test_export_root_objects_1.obj'), 'w')
        fh.write(out)
        fh.close()

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
            '0 Mesh: root_1',
                '1 Mesh: root_1_child_1',
                    '2 Mesh: root_1_child_1_child',
                '1 Mesh: root_1_child_2'
        ])

        self.assertFileOutputEqualsFixture(
            out,
            os.path.join(__dirname__, 'fixtures',  'test_export_root_objects_1.obj')
        )

        xplaneFile2 = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_2'])

        out = xplaneFile2.write()

        fh = open(os.path.join(tmpDir, 'test_export_root_objects_2.obj'), 'w')
        fh.write(out)
        fh.close()

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
            '0 Mesh: root_2'
        ])

        self.assertFileOutputEqualsFixture(
            out,
            os.path.join(__dirname__, 'fixtures', 'test_export_root_objects_2.obj')
        )

runTestCases([TestCreateFromRootObjects])
