import bpy
import math
import mathutils
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

class TestAnimations(XPlaneTestCase):
    def test_bone_animations(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        self.assertXplaneFileHasBoneTree(
            xplaneFile, [
            '0 ROOT',
                '1 Armature: Armature',
                    '2 Bone: Bone',
                        '3 Mesh: Cube.001',
                '1 Mesh: Cube',
        ])

        armature = xplaneFile.rootBone.children[0]
        cube = xplaneFile.rootBone.children[1]
        bone = armature.children[0]
        boneCube = bone.children[0]

        # Root bone is not animated
        self.assertEquals(xplaneFile.rootBone.isAnimated(), False)

        # Armature is not animated
        self.assertEquals(armature.isAnimated(), False)

        # Bone is animated
        self.assertEquals(bone.isAnimated(), True)

        # Cube is animated
        self.assertEquals(cube.isAnimated(), True)

        # bone.cube is not animated
        self.assertEquals(boneCube.isAnimated(), False)

        # should have only one dataref and animation
        self.assertEquals(len(cube.datarefs), 1)
        self.assertEquals(len(cube.animations), 1)

        # cube should have one 'example' dataref and corresponding animation
        self.assertIn('example', cube.datarefs)
        self.assertIn('example', cube.animations)
        # should have 2 keyframes
        self.assertEquals(len(cube.animations['example']), 2)

        cubeKeyframes = cube.animations['example']

        # check for correct location and rotation
        self.assertEquals(cubeKeyframes[0].location, mathutils.Vector((0, 0, 0)))
        self.assertEquals(cubeKeyframes[0].rotation, mathutils.Euler((0, 0, 0), 'XYZ'))
        self.assertEquals(cubeKeyframes[0].rotationMode, 'XYZ')
        self.assertEquals(cubeKeyframes[1].location, mathutils.Vector((0, 2, 0)))
        self.assertFloatsEqual(cubeKeyframes[1].rotation[0], math.radians( 0),0.00001)
        self.assertFloatsEqual(cubeKeyframes[1].rotation[1], math.radians(90),0.00001)
        self.assertFloatsEqual(cubeKeyframes[1].rotation[2], math.radians( 0),0.00001)
        self.assertEquals(cubeKeyframes[1].rotationMode, 'XYZ')

        # should have only one dataref and animation
        self.assertEquals(len(bone.datarefs), 1)
        self.assertEquals(len(bone.animations), 1)

        # bone should have 'bone_example' dataref
        self.assertIn('bone_example', bone.datarefs)
        self.assertIn('bone_example', bone.animations)

        # should have 2 keyframes
        self.assertEquals(len(bone.animations['bone_example']), 2)

        boneKeyframes = bone.animations['bone_example']

        # check for correct location and rotation
        self.assertEquals(boneKeyframes[0].location, mathutils.Vector((0, 0, 0)))
        self.assertEquals(boneKeyframes[0].rotation, mathutils.Quaternion((1, 0, 0, 0)))
        self.assertEquals(boneKeyframes[0].rotationMode, 'QUATERNION')
        self.assertEquals(boneKeyframes[1].location, mathutils.Vector((0, 0, 0)))
        self.assertEquals(boneKeyframes[1].rotation, mathutils.Quaternion((1, 0, 0), math.radians(-90)))
        self.assertEquals(boneKeyframes[1].rotationMode, 'QUATERNION')

runTestCases([TestAnimations])
