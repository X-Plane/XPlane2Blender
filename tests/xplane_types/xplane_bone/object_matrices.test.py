import bpy
import math
import mathutils
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_types import xplane_file
from io_xplane2blender import xplane_config

FLOAT_TOLERANCE = 0.000001

# This was useful for exploring noise in the low bits of matrices
#def print_acc(m):
#    print("(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n(%.9f %.9f %.9f %.9f)\n" %
#        (m[0][0], m[1][0], m[2][0], m[3][0],
#         m[0][1], m[1][1], m[2][1], m[3][1],
#         m[0][2], m[1][2], m[2][2], m[3][2],
#         m[0][3], m[1][3], m[2][3], m[3][3]))

class TestMatrices(XPlaneTestCase):

    # Ben says: when we decompose and re-compose
    def assertMatricesEqual(self,m1,m2,T):
        self.assertEquals(m1,m2)
        self.assertFloatVectorsEqual(m1[0],m2[0], T)
        self.assertFloatVectorsEqual(m1[1],m2[1], T)
        self.assertFloatVectorsEqual(m1[2],m2[2], T)
        self.assertFloatVectorsEqual(m1[3],m2[3], T)

    def test_bone_root_matrices(self):
        identityMatrix = mathutils.Matrix.Identity(4)
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        cubeStatic = xplaneFile.getBoneByBlenderName('Cube_static')

        # FIXME: we are actually testing getBoneByBlenderName() here, should be in it's own test file
        self.assertIsNotNone(cubeStatic)

        # Ben says: fix for issue 219 makes it ILLEGAL to ask for pre-and post animation or animation-bake matrices for a NON-animated bone!

#       preMatrix = cubeStatic.getPreAnimationMatrix()
#       postMatrix = cubeStatic.getPostAnimationMatrix()
#       bakeMatrix = cubeStatic.getBakeMatrixForMyAnimations()

#       self.assertFloatVectorsEqual(preMatrix.to_translation(), cubeStatic.blenderObject.location, FLOAT_TOLERANCE)
#       self.assertFloatVectorsEqual(preMatrix.to_scale(), cubeStatic.blenderObject.scale, FLOAT_TOLERANCE)
#       self.assertFloatVectorsEqual(preMatrix.to_euler('XYZ'), cubeStatic.blenderObject.rotation_euler, FLOAT_TOLERANCE)

        # post and pre are the same if not animated
#       self.assertEquals(preMatrix, postMatrix)

        # bake matrix should be objects world matrix as its not animated
#       self.assertEquals(bakeMatrix, cubeStatic.blenderObject.matrix_world)

        cubeAnimated = xplaneFile.getBoneByBlenderName('Cube_animated')
        self.assertIsNotNone(cubeAnimated)

        preMatrix = cubeAnimated.getPreAnimationMatrix()
        postMatrix = cubeAnimated.getPostAnimationMatrix()
        bakeMatrix = cubeAnimated.getBakeMatrixForMyAnimations()

        # animated object should have identity matrix as pre animation
        self.assertEquals(preMatrix, identityMatrix)

        # post matrix must be blender objects world matrix
        self.assertMatricesEqual(postMatrix, cubeAnimated.blenderObject.matrix_world, 0.0001)

        # bake matrix should be identity matrix (world origin)
        self.assertEquals(bakeMatrix, identityMatrix)

    def test_child_bone_matrices(self):
        identityMatrix = mathutils.Matrix.Identity(4)
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        cubeStatic = xplaneFile.getBoneByBlenderName('Cube_static')
        cubeStaticChildStatic = xplaneFile.getBoneByBlenderName('Cube_static.child_static')

        # FIXME: we are actually testing getBoneByBlenderName() here, should be in it's own test file
        self.assertIsNotNone(cubeStaticChildStatic)

#       preMatrix = cubeStaticChildStatic.getPreAnimationMatrix()
#       postMatrix = cubeStaticChildStatic.getPostAnimationMatrix()
#       bakeMatrix = cubeStaticChildStatic.getBakeMatrixForMyAnimations()

#       self.assertEquals(preMatrix, cubeStaticChildStatic.blenderObject.matrix_world)
#       self.assertEquals(postMatrix, preMatrix)

        # bakematrix should be objects world matrix, as object and its parent are not animated
#       self.assertEquals(bakeMatrix, cubeStaticChildStatic.blenderObject.matrix_world)

        # no to the animated child
        cubeStaticChildAnimated = xplaneFile.getBoneByBlenderName('Cube_static.child_animated')

        preMatrix = cubeStaticChildAnimated.getPreAnimationMatrix()
        postMatrix = cubeStaticChildAnimated.getPostAnimationMatrix()
        bakeMatrix = cubeStaticChildAnimated.getBakeMatrixForMyAnimations()

        # pre matrix should be parents world matrix * inverted matrix relative to parent
        self.assertEquals(preMatrix, cubeStaticChildAnimated.blenderObject.parent.matrix_world * cubeStaticChildAnimated.blenderObject.matrix_parent_inverse)

        # post matrix should be world matrix
        self.assertMatricesEqual(postMatrix, cubeStaticChildAnimated.blenderObject.matrix_world,0.0001)

        # bake matrix should be inverted identity matrix *  own preanimation matrix
        self.assertEquals(bakeMatrix, identityMatrix.inverted_safe() * preMatrix)

        cubeAnimated = xplaneFile.getBoneByBlenderName('Cube_animated')
        cubeAnimatedChildStatic = xplaneFile.getBoneByBlenderName('Cube_animated.child_static')

#       preMatrix = cubeAnimatedChildStatic.getPreAnimationMatrix()
#       postMatrix = cubeAnimatedChildStatic.getPostAnimationMatrix()
#       bakeMatrix = cubeAnimatedChildStatic.getBakeMatrixForMyAnimations()

#       self.assertEquals(preMatrix, cubeAnimatedChildStatic.blenderObject.matrix_world)
#       self.assertEquals(postMatrix, preMatrix)

        # TODO: what should the bake matrix be like?
        # self.assertFloatVectorsEqual(bakeMatrix.to_translation(), cubeAnimated.blenderObject.location + cubeAnimatedChildStatic.blenderObject.location, FLOAT_TOLERANCE)


runTestCases([TestMatrices])
