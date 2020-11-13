import bpy
import os
import inspect
import sys

from io_xplane2blender.tests import *
from io_xplane2blender import xplane_config

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("ANIM" in line[0] or\
             "LIGHT_PARAM" in line[0])

fixtures_path = os.path.join('fixtures','armature_bone_block_parent_relationships')

class TestArmatureBoneBlockParentRelationships(XPlaneTestCase):
    def test_Armature_arm_anim_bone_anim(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            4, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filterLines,
            filename,
            )

    def test_Armature_arm_anim_bone_no_anim(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            3, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filterLines,
            filename,
            )

    def test_Armature_arm_no_anim_bone_anim(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filterLines,
            filename,
            )

    def test_Armature_arm_no_anim_bone_no_anim(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filterLines,
            filename,
            )

    def test_no_parent(self):
        filename = inspect.stack()[0][3]

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, fixtures_path, filename + '.obj'),
            filterLines,
            filename,
            )

runTestCases([TestArmatureBoneBlockParentRelationships])

