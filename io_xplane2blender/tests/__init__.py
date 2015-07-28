import bpy
import unittest
import sys
from ..xplane_types import XPlanePrimitive
from ..xplane_config import setDebug

EPSILON = sys.float_info.epsilon

class XPlaneTestCase(unittest.TestCase):
    def setUp(self):
        if '--debug' in sys.argv:
            setDebug(True)

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

    def assertFloatsEqual(self, a, b, tolerance = None):
        if tolerance == None:
            tolerance = EPSILON

        if abs(a - b) < tolerance:
            return True
        else:
            raise AssertionError('%s does not equal %s within a tolerance of %f' % (a, b, tolerance))

    def assertFloatVectorsEqual(self, a, b, tolerance = None):
        if tolerance == None:
            tolerance = EPSILON

        self.assertEquals(len(a), len(b))

        equals = True

        for i in range(0, len(a)):
            if equals == False:
                raise AssertionError('%s does not equal %s within a toleracne of %f' % (a, b, tolerance))

            equals = abs(a[i] - b[i]) < tolerance

    def parseFileToLines(self, data):
        def parseNumbersInLine(part):
            if part.isnumeric():
                return float(part)

            return part

        def parseLine(line):
            # remove trailing comments
            line = line.split('#')[0]
            return list(map(parseNumbersInLine, line.strip().split()))

        def filterLine(line):
            return len(line) > 0 and line[0] != '#'

        return list(map(parseLine, filter(filterLine, map(str.strip, data.strip().split('\n')))))

    def assertFilesEqual(self, a, b, filterCallback = None, floatTolerance = 0.000001):
        def isnumber(d):
            return isinstance(d, float) or isinstance(d, int)

        if floatTolerance == None:
            floatTolerance = EPSILON

        linesA = self.parseFileToLines(a)
        linesB = self.parseFileToLines(b)

        # if a filter function is provided, additionally filter lines with it
        if filterCallback:
            linesA = filter(filterCallback, linesA)
            linesB = filter(filterCallback, linesB)

        # ensure same number of lines
        self.assertEquals(len(linesA), len(linesB))

        for lineIndex in range(0, len(linesA)):
            lineA = linesA[lineIndex]
            lineB = linesB[lineIndex]

            # ensure same number of line segments
            self.assertEquals(len(lineA), len(lineB))

            print('comparing ' + str(lineA) + ' with ' + str(lineB))

            for linePos in range(0, len(lineA)):
                segmentA = lineA[linePos]
                segmentB = lineB[linePos]

                # assure same values (floats must be compared with tolerance)
                if isnumber(segmentA) and isnumber(segmentB):
                    self.assertFloatsEqual(segmentA, segmentB, floatTolerance)
                else:
                    self.assertEquals(segmentA, segmentB)

    def assertFileEqualsFixture(self, fileOutput, fixturePath, filterCallback = None, floatTolerance = None):
        fixtureFile = open(fixturePath, 'r')
        fixtureOutput = fixtureFile.read()
        fixtureFile.close()

        return self.assertFilesEqual(fileOutput, fixtureOutput, filterCallback, floatTolerance)

def runTestCases(testCases):
    for testCase in testCases:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)

    unittest.TextTestRunner().run(suite)
