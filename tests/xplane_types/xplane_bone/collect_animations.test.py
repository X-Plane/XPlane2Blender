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
        xplaneFile = self.createXPlaneFileFromPotentialRoot("Layer 1")

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

        assertXplaneFileHasBoneTree(
            self,
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
        self.assertEqual(xplaneFile.rootBone.isAnimated(), False)

        # Armature is not animated
        self.assertEqual(armature.isAnimated(), False)

        # Bone is animated
        self.assertEqual(bone.isAnimated(), True)

        # Cube is animated
        self.assertEqual(cube.isAnimated(), True)

        # bone.cube is not animated
        self.assertEqual(boneCube.isAnimated(), False)

        # should have only one dataref and animation
        self.assertEqual(len(cube.datarefs), 1)
        self.assertEqual(len(cube.animations), 1)

        # cube should have one 'example' dataref and corresponding animation
        self.assertIn('example', cube.datarefs)
        self.assertIn('example', cube.animations)
        # should have 2 keyframes
        self.assertEqual(len(cube.animations['example']), 2)

        cubeKeyframes = cube.animations['example']

        # check for correct location and rotation
        self.assertEqual(cubeKeyframes[0].location, mathutils.Vector((0, 0, 0)))
        self.assertEqual(cubeKeyframes[0].rotation, mathutils.Euler((0, 0, 0), 'XYZ'))
        self.assertEqual(cubeKeyframes[0].rotationMode, 'XYZ')
        self.assertEqual(cubeKeyframes[1].location, mathutils.Vector((0, 2, 0)))
        self.assertFloatsEqual(cubeKeyframes[1].rotation[0], math.radians( 0),0.00001)
        self.assertFloatsEqual(cubeKeyframes[1].rotation[1], math.radians(90),0.00001)
        self.assertFloatsEqual(cubeKeyframes[1].rotation[2], math.radians( 0),0.00001)
        self.assertEqual(cubeKeyframes[1].rotationMode, 'XYZ')

        # should have only one dataref and animation
        self.assertEqual(len(bone.datarefs), 1)
        self.assertEqual(len(bone.animations), 1)

        # bone should have 'bone_example' dataref
        self.assertIn('bone_example', bone.datarefs)
        self.assertIn('bone_example', bone.animations)

        # should have 2 keyframes
        self.assertEqual(len(bone.animations['bone_example']), 2)

        boneKeyframes = bone.animations['bone_example']

        # check for correct location and rotation
        self.assertEqual(boneKeyframes[0].location, mathutils.Vector((0, 0, 0)))
        self.assertFloatsEqual(boneKeyframes[0].rotation[0], 0.0)
        self.assertFloatVectorsEqual(boneKeyframes[0].rotation[1], mathutils.Vector((0, 1, 0)))
        self.assertEqual(boneKeyframes[0].rotationMode, 'AXIS_ANGLE')

        self.assertEqual(boneKeyframes[1].location, mathutils.Vector((0, 0, 0)))
        self.assertFloatsEqual(boneKeyframes[1].rotation[0], 1.5707961320877075)
        self.assertFloatVectorsEqual(boneKeyframes[1].rotation[1], mathutils.Vector((-1.0, 0.0, 0.0)))
        self.assertEqual(boneKeyframes[1].rotationMode, 'AXIS_ANGLE')

runTestCases([TestAnimations])
