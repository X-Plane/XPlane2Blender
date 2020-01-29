import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line:Tuple[str])->bool:
    return (isinstance(line[0], str)
            and any(d in line[0]
                    for d in {"ATTR_LOD",
                              "ATTR_shiny_rat",
                              "TRIS",
                              "TEXTURE"}))

class TestCreateFromRootObjects(XPlaneTestCase):
    def test_create_files_from_root_objects(self):
        tmpDir = os.path.realpath(os.path.join(__dirname__, '../../tmp'))

        xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_1'])

        out = xplaneFile.write()

        with open(os.path.join(tmpDir, 'test_export_root_objects_1.obj'), 'w') as fh:
            fh.write(out)

        # auto filename from blender object
        self.assertEqual(xplaneFile.filename, 'root_1')

        # should contain 3 cubes
        self.assertEqual(len(xplaneFile._bl_obj_name_to_bone), 4)

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
        self.assertIn('root_1', xplaneFile._bl_obj_name_to_bone)

        self.assertIn('root_1_child_1', xplaneFile._bl_obj_name_to_bone)
        self.assertIn('root_1_child_1_child', xplaneFile._bl_obj_name_to_bone)
        self.assertIn('root_1_child_2', xplaneFile._bl_obj_name_to_bone)

        assertXplaneFileHasBoneTree(
            self,
            xplaneFile, [
            '0 Mesh: root_1',
                '1 Mesh: root_1_child_1',
                    '2 Mesh: root_1_child_1_child',
                '1 Mesh: root_1_child_2'
        ])

        self.assertFileOutputEqualsFixture(
            out,
            os.path.join(__dirname__, 'fixtures',  'test_export_root_objects_1.obj'),
            filterLines,
        )

        xplaneFile2 = xplane_file.createFileFromBlenderRootObject(bpy.data.objects['root_2'])

        out = xplaneFile2.write()

        with  open(os.path.join(tmpDir, 'test_export_root_objects_2.obj'), 'w') as fh:
            fh.write(out)

        # custom file name
        self.assertEqual(xplaneFile2.filename, 'custom_name')

        # should contain 1 cube
        self.assertEqual(len(xplaneFile2._bl_obj_name_to_bone), 1)

        self.assertIn("root_2", xplaneFile2._bl_obj_name_to_bone)

        assertXplaneFileHasBoneTree(
            self,
            xplaneFile2, [
            '0 Mesh: root_2'
        ])

        self.assertFileOutputEqualsFixture(
            out,
            os.path.join(__dirname__, 'fixtures', 'test_export_root_objects_2.obj'),
            filterLines,
        )

runTestCases([TestCreateFromRootObjects])
