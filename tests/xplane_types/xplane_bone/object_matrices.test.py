import bpy
import math
import mathutils
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

# This was useful for exploring noise in the low bits of matrices
#def print_acc(m):
#    print("(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n" %
#        (m[0][0], m[1][0], m[2][0], m[3][0],
#         m[0][1], m[1][1], m[2][1], m[3][1],
#         m[0][2], m[1][2], m[2][2], m[3][2],
#         m[0][3], m[1][3], m[2][3], m[3][3]))

class TestMatrices(XPlaneTestCase):
    def test_bone_root_matrices(self):
        identityMatrix = mathutils.Matrix.Identity(4)
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        cubeStatic = xplaneFile.getBoneByBlenderName('Cube_static')

        # FIXME: we are actually testing getBoneByBlenderName() here, should be in it's own test file
        self.assertIsNotNone(cubeStatic)

        cubeAnimated = xplaneFile.getBoneByBlenderName('Cube_animated')
        self.assertIsNotNone(cubeAnimated)

        preMatrix = cubeAnimated.getPreAnimationMatrix()
        postMatrix = cubeAnimated.getPostAnimationMatrix()
        bakeMatrix = cubeAnimated.getBakeMatrixForMyAnimations()

        # animated object should have identity matrix as pre animation
        self.assertMatricesEqual(preMatrix, identityMatrix)

        # post matrix must be blender objects world matrix
        self.assertMatricesEqual(postMatrix, cubeAnimated.blenderObject.matrix_world, 0.0001)

        # bake matrix should be identity matrix (world origin)
        self.assertMatricesEqual(bakeMatrix, identityMatrix)

    def test_child_bone_matrices(self):
        identityMatrix = mathutils.Matrix.Identity(4)
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        cubeStatic = xplaneFile.getBoneByBlenderName('Cube_static')
        cubeStaticChildStatic = xplaneFile.getBoneByBlenderName('Cube_static.child_static')

        # FIXME: we are actually testing getBoneByBlenderName() here, should be in it's own test file
        self.assertIsNotNone(cubeStaticChildStatic)

        # no to the animated child
        cubeStaticChildAnimated = xplaneFile.getBoneByBlenderName('Cube_static.child_animated')

        preMatrix = cubeStaticChildAnimated.getPreAnimationMatrix()
        postMatrix = cubeStaticChildAnimated.getPostAnimationMatrix()
        bakeMatrix = cubeStaticChildAnimated.getBakeMatrixForMyAnimations()

        # pre matrix should be parents world matrix * inverted matrix relative to parent
        self.assertMatricesEqual(preMatrix, cubeStaticChildAnimated.blenderObject.parent.matrix_world * cubeStaticChildAnimated.blenderObject.matrix_parent_inverse)

        # post matrix should be world matrix
        self.assertMatricesEqual(postMatrix, cubeStaticChildAnimated.blenderObject.matrix_world,0.0001)

        # bake matrix should be inverted identity matrix *  own preanimation matrix
        self.assertMatricesEqual(bakeMatrix, identityMatrix.inverted_safe() * preMatrix)

        cubeAnimated = xplaneFile.getBoneByBlenderName('Cube_animated')
        cubeAnimatedChildStatic = xplaneFile.getBoneByBlenderName('Cube_animated.child_static')

runTestCases([TestMatrices])
