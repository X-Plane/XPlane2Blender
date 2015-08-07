import bpy
import unittest
import sys
import os
from ..xplane_types import xplane_file, XPlanePrimitive
from ..xplane_config import setDebug, getDebug
from .animation_file_mappings import mappings

EPSILON = sys.float_info.epsilon

__dirname__ = os.path.dirname(__file__)

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
            linesA = list(filter(filterCallback, linesA))
            linesB = list(filter(filterCallback, linesB))

        # ensure same number of lines
        self.assertEquals(len(linesA), len(linesB))

        for lineIndex in range(0, len(linesA)):
            lineA = linesA[lineIndex]
            lineB = linesB[lineIndex]

            # ensure same number of line segments
            self.assertEquals(len(lineA), len(lineB))

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

    def assertLayerExportEqualsFixture(self, layer, fixturePath, tmpFilename = None):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)

        out = xplaneFile.write()

        if tmpFilename:
            tmpDir = os.path.realpath(os.path.join(__dirname__, '../../tests/tmp'))
            tmpFile = os.path.join(tmpDir, tmpFilename + '.obj')
            fh = open(tmpFile, 'w')
            fh.write(out)
            fh.close()

        self.assertFileEqualsFixture(out, fixturePath)

    # asserts that an attributes object equals a dict
    def assertAttributesEqualDict(self, attrs, d, floatTolerance = None):
        self.assertEquals(len(d), len(attrs), 'Attribute lists have different length')

        for name in attrs:
            attr = attrs[name]
            value = attr.getValue()
            expectedValue = d[name]

            if isinstance(expectedValue, list) or isinstance(expectedValue, tuple):
                self.assertTrue(isinstance(value, list) or isinstance(value, tuple), 'Attribute value for "%s" is no list or tuple but: %s' % (name, str(value)))
                self.assertEquals(len(expectedValue), len(value), 'Attribute values for "%s" have different length' % name)

                for i in range(0, len(expectedValue)):
                    v = value[i]
                    expectedV = expectedValue[i]

                    if isinstance(expectedV, float) or isinstance(expectedV, int):
                        self.assertFloatsEqual(expectedV, v, floatTolerance)
                    else:
                        self.assertEquals(expectedV, v, 'Attribute list value %d for "%s" is different' % (i, name))
            else:
                self.assertEquals(expectedValue, value, 'Attribute "%s" is not equal' % name)

class XPlaneAnimationTestCase(XPlaneTestCase):
    def setUp(self):
        super(XPlaneAnimationTestCase, self).setUp()

    def exportAnimationTestCase(self, name, dest):
        self.assertTrue(mappings[name])

        for layer in mappings[name]:
            outFile = os.path.join(dest, os.path.basename(mappings[name][layer]))
            print('Exporting to "%s"' % outFile)

            xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)

            self.assertIsNotNone(xplaneFile, 'Unable to create XPlaneFile for %s layer %d' % (name, layer))

            out = xplaneFile.write()

            outFile = open(outFile, 'w')
            outFile.write(out)
            outFile.close()

    def runAnimationTestCase(self, name, __dirname__):
        self.assertTrue(mappings[name])

        def filterLine(line):
            # only keep ANIM_ lines
            return isinstance(line[0], str) and line[0].find('ANIM_') == 0

        for layer in mappings[name]:
            print('Testing animations against fixture "%s"' % mappings[name][layer])

            xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)

            self.assertIsNotNone(xplaneFile, 'Unable to create XPlaneFile for %s layer %d' % (name, layer))

            out = xplaneFile.write()
            fixtureFile = os.path.join(__dirname__, mappings[name][layer])

            self.assertTrue(os.path.exists(fixtureFile), 'File "%s" does not exits' % fixtureFile)
            self.assertFileEqualsFixture(out, fixtureFile, filterLine)

def runTestCases(testCases):
    for testCase in testCases:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)

    unittest.TextTestRunner().run(suite)
