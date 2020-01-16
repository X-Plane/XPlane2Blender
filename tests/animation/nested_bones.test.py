import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and ("ANIM" in line[0])

fixtures_path = os.path.join('fixtures','nested_bones')

class TestNestedBones(XPlaneTestCase):
    def test_1_Armature_child_bones_one_leaf_mesh(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filename,
            filterLines
            )

    def test_2_Armature_child_bones_mesh_on_each(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filename,
            filterLines
            )

    def test_3_Armature_multiple_arms_one_leaf_mesh(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filename,
            filterLines
            )

    def test_4_Armature_multiple_arms_child_bones_on_each(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            3, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filename,
            filterLines
            )

runTestCases([TestNestedBones])

