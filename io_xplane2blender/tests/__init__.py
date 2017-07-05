import bpy
import unittest
import sys
import os
from ..xplane_types import xplane_file, XPlanePrimitive
from ..xplane_config import setDebug, getDebug
from ..xplane_helpers import logger, XPlaneLogger
from .animation_file_mappings import mappings

#TODO: Make this import from XPlane2Blender/tests.py instead of just keeping it in sync manually
ERROR_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED ERRORS"
WARNING_LOGGER_REGEX = "LOGGER HAD ([+-]?\d+) UNEXPECTED WARNINGS"

FLOAT_TOLERANCE = 0.0001

__dirname__ = os.path.dirname(__file__)

class XPlaneTestCase(unittest.TestCase):
    
    #If you are expecting errors as as part of your test, every part of your test must expect errors.
    #Split facets that must pass and facets that must fail into separate tests
    expected_logger_errors = 0
    expected_logger_warnings = 0
    
    def setUp(self, useLogger = True):
        if '--debug' in sys.argv:
            setDebug(True)

        if useLogger:
            self.useLogger()

    def useLogger(self):
        debug = getDebug()
        logLevels = ['error', 'warning']

        if debug:
            logLevels.append('info')
            logLevels.append('success')

        logger.clearTransports()
        logger.addTransport(XPlaneLogger.ConsoleTransport(), logLevels)

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
            tolerance = FLOAT_TOLERANCE

        if abs(a - b) < tolerance:
            return True
        else:
            raise AssertionError('%s does not equal %s within a tolerance of %f' % (a, b, tolerance))

    def assertFloatVectorsEqual(self, a, b, tolerance = None):
        if tolerance == None:
            tolerance = FLOAT_TOLERANCE

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

    def assertFilesEqual(self, a, b, filterCallback = None, floatTolerance = None):
        def isnumber(d):
            return isinstance(d, float) or isinstance(d, int)

        def toFloat(d, fail = None):
            try:
                return float(d)
            except Exception:
                return fail


        if floatTolerance == None:
            floatTolerance = FLOAT_TOLERANCE

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

                # convert numeric strings
                if isinstance(segmentA, str):
                    segmentA = toFloat(segmentA, segmentA)

                if isinstance(segmentB, str):
                    segmentB = toFloat(segmentB, segmentB)

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

    def exportLayer(self, layer, dest = None):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)

        out = xplaneFile.write()

        if dest:
            tmpDir = os.path.realpath(os.path.join(__dirname__, '../../tests/tmp'))
            tmpFile = os.path.join(tmpDir, dest + '.obj')
            fh = open(tmpFile, 'w')
            fh.write(out)
            fh.close()

        return out

    def assertLayerExportEqualsFixture(self, layer, fixturePath, tmpFilename = None, filterCallback = None, floatTolerance = None):
        if not '--quiet' in sys.argv:
            print("Comparing: '%s', '%s'" % (tmpFilename, fixturePath))
        out = self.exportLayer(layer, tmpFilename)
        self.assertFileEqualsFixture(out, fixturePath, filterCallback, floatTolerance)

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

def make_fixture_path(dirname,filename,sub_dir=""):
    return os.path.join(dirname, 'fixtures', sub_dir, filename + '.obj')

def runTestCases(testCases):
    #Until a better solution for knowing if the logger's error count should be used to quit the testing,
    #we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
    assert len(testCases) == 1, "Currently, only one test case per suite is supported at a time"
    expected_logger_errors = 0
    expected_logger_warnings = 0
    for testCase in testCases:    
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCase)
        expected_logger_errors += testCase.expected_logger_errors
        expected_logger_warnings += testCase.expected_logger_warnings
    
    unittest.TextTestRunner().run(suite)
    
    #WARNING! There is a chance for false positives with this - if the total number of errors is correct,
    #but their distribution throughout the asserts are not. Therefore it is recommended to only create one
    #self.assertEquals(len(logger.findErrors()), num_errors) at the end of the test
    unexpected_errors   = len(logger.findErrors())   - expected_logger_errors
    unexpected_warnings = len(logger.findWarnings()) - expected_logger_warnings
    
    #See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    return_string = ERROR_LOGGER_REGEX.replace("([+-]?\d+)", str(unexpected_errors))
    print(return_string)
    #For if we ever create a --verbose flag
    #print(WARNING_LOGGER_REGEX.replace("([+-]?\d+)", str(unexpected_warnings)))
