import bpy
import unittest
import sys
from ..xplane_types import XPlanePrimitive

class XPlaneTestCase(unittest.TestCase):
    def setUp(self):
        if '--debug' in sys.argv:
            xplane_config.setDebug(True)

    # Utility method to check if objects are contained in file
    def assertObjectsInXPlaneFile(self, xplaneFile, objectNames):
        for name in objectNames:
            self.assertIsNotNone(xplaneFile.objects[name])
            self.assertTrue(isinstance(xplaneFile.objects[name], XPlanePrimitive))
            self.assertEquals(xplaneFile.objects[name].blenderObject, bpy.data.objects[name])

    def assertXplaneFileHasBoneTree(self, xplaneFile, tree):
        self.assertIsNotNone(xplaneFile.rootBone)

        bones = []

        def collect(bone):
            bones.append(bone)
            for bone in bone.children:
                collect(bone)

        collect(xplaneFile.rootBone)

        self.assertEquals(len(tree), len(bones))

        index = 0

        while index < len(bones):
            self.assertEquals(tree[index], bones[index].getName())
            index += 1

def runTestCases(testCases):
    for testCase in testCases:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)

    unittest.TextTestRunner().run(suite)
