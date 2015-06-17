import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

class TestAnimations(XPlaneTestCase):
    def setUp(self):
        if '--debug' in sys.argv:
            xplane_config.setDebug(True)

    def test_bone_animations(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        self.assertXplaneFileHasBoneTree(
            xplaneFile, [
            '0 ROOT',
                '1 Object: Armature',
                    '2 Bone: Bone',
                '1 Object: Cube',
        ])

        # Root bone is not animated
        self.assertEquals(xplaneFile.rootBone.isAnimated(), False)

        # Armature is not animated
        self.assertEquals(xplaneFile.rootBone.children[0].isAnimated(), False)

        # Bone is animated
        self.assertEquals(xplaneFile.rootBone.children[0].children[0].isAnimated(), True)

        # Cube is animated
        self.assertEquals(xplaneFile.rootBone.children[1].isAnimated(), True)

runTestCases([TestAnimations])
