import os
import shutil
import sys
import unittest

from typing import Callable, List, Optional, Tuple, Union

import bpy

import io_xplane2blender
from io_xplane2blender.xplane_config import setDebug, getDebug
from io_xplane2blender import xplane_config
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_helpers import logger, XPlaneLogger
from io_xplane2blender.xplane_types import xplane_file, xplane_primitive
from ..xplane_types import xplane_file
from ..xplane_types.xplane_primitive import XPlanePrimitive
from .animation_file_mappings import mappings


#TODO: Make this import from XPlane2Blender/tests.py instead of just keeping it in sync manually
TEST_RESULTS_REGEX = "RESULT: After {num_tests} tests got {errors} errors, {fails} failures, and {skip} skipped"

FLOAT_TOLERANCE = 0.0001

__dirname__ = os.path.dirname(__file__)
TMP_DIR = os.path.realpath(os.path.join(__dirname__, '../../tests/tmp'))

class XPlaneTestCase(unittest.TestCase):
    def setUp(self, useLogger = True):
        dd_index = sys.argv.index('--')
        blender_args, xplane_args = sys.argv[:dd_index],sys.argv[dd_index+1:]
        setDebug('--force-xplane-debug' in xplane_args)

        if useLogger:
            self.useLogger()

        #logger.warn("---------------")
    def useLogger(self):
        debug = getDebug()
        logLevels = ['error', 'warning']

        if debug:
            logLevels.append('info')
            logLevels.append('success')

        logger.clear()
        logger.addTransport(XPlaneLogger.ConsoleTransport(), logLevels)

    def assertMatricesEqual(self,mA,mB,tolerance=FLOAT_TOLERANCE):
        for row_a,row_b in zip(mA,mB):
            self.assertFloatVectorsEqual(row_a, row_b, tolerance)

    # Utility method to check if objects are contained in file
    def assertObjectsInXPlaneFile(self, xplaneFile, objectNames):
        for name in objectNames:
            self.assertIsNotNone(xplaneFile.objects[name])
            self.assertTrue(isinstance(xplaneFile.objects[name],xplane_primitive.XPlanePrimitive))
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

    def parseFileToLines(self, data:str)->List[Union[float,str]]:
        '''
        Turns a string of \n seperated lines into a List[Union[float,str]]
        without comments or 0 length strings. All numeric parts are converted
        '''
        lines = [] # type: List[Union[float,str]]
        for line in filter(lambda l: len(l) > 0 and l[0] != '#', data.split('\n')):
            if '#' in line:
                line = line[0:line.index('#')]
            line = line.strip()
            if line:
                lines.append(list(map(lambda part: float(part) if part.isnumeric() else part, line.split())))

        return lines

    def assertFilesEqual(self, a:str, b:str, filterCallback = None, floatTolerance = None):
        '''
        a and b should be the contents of files a and b as returned
        from open(file).read()
        '''
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

            #print("lineA:%s lineB:%s" %(lineA,lineB))
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

                def isdegree(segment,line):
                    if isnumber(segment):
                        return not isnumber(line) and ("rotate" in line or "manip_keyframe" in line) and isnumber(segment)
                    else:
                        return False

                # assure same values (floats must be compared with tolerance)
                if isnumber(segmentA) and isnumber(segmentB):
                    segmentA = abs(segmentA) if isdegree(segmentA,lineA[0]) else segmentA
                    segmentB = abs(segmentB) if isdegree(segmentB,lineB[0]) else segmentB
                    self.assertFloatsEqual(segmentA, segmentB, floatTolerance)
                else:
                    self.assertEquals(segmentA, segmentB)

    def assertFileOutputEqualsFixture(self, fileOutput, fixturePath, filterCallback = None, floatTolerance = None):
        fixtureFile = open(fixturePath, 'r')
        fixtureOutput = fixtureFile.read()
        fixtureFile.close()

        return self.assertFilesEqual(fileOutput, fixtureOutput, filterCallback, floatTolerance)

    def assertFileTmpEqualsFixture(self,tmpPath,fixturePath,filterCallback=None, floatTolerance=None):
        tmpFile = open(tmpPath, 'r')
        tmpOutput = tmpFile.read()
        tmpFile.close()
        
        return self.assertFileOutputEqualsFixture(tmpOutput, fixturePath, filterCallback, floatTolerance)
    

    # Method: assertLoggerErrors
    #
    # expected_logger_errors - The number of errors you expected to have happen
    # asserts the number of errors and clears the logger of all messages
    def assertLoggerErrors(self, expected_logger_errors):
        self.assertEqual(len(logger.findErrors()), expected_logger_errors)
        logger.clearMessages()
    
    #TODO: Must filter warnings to have this be useful
    # Method: assertLoggerWarnings
    #
    # expected_logger_warnings - The number of warnings you expected to have happen
    # asserts the number of warnings and clears the logger of all messages
    #def assertLoggerWarnings(self, expected_logger_warnings):    
    #    self.assertEqual(len(logger.findWarnings()), expected_logger_warnings)
    #    logger.clearMessages()
    def assertLayerExportEqualsFixture(self, layer, fixturePath, tmpFilename = None, filterCallback = None, floatTolerance = None):
        if not ('-q' in sys.argv or '--quiet' in sys.argv):
            print("Comparing: '%s', '%s'" % (tmpFilename, fixturePath))
        out = self.exportLayer(layer, tmpFilename)
        self.assertFileOutputEqualsFixture(out, fixturePath, filterCallback, floatTolerance)

    def assertRootObjectExportEqualsFixture(self,
            root_object:Union[bpy.types.Object, str],
            fixturePath: str = None,
            tmpFilename: Optional[str] = None,
            filterCallback: Callable[[List[Union[float, str]]], bool] = None,
            floatTolerance: Optional[float] = None):
        out = self.exportRootObject(root_object, tmpFilename)
        self.assertFileOutputEqualsFixture(out, fixturePath, filterCallback, floatTolerance)

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

    def exportLayer(self, layer, dest = None):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(layer)

        out = xplaneFile.write()

        if dest:
            with open(os.path.join(TMP_DIR, dest + '.obj'), 'w') as tmp_file:
                tmp_file.write(out)

        return out

    def exportRootObject(self, root_object:Union[bpy.types.Object,str], dest:str = None)->str:
        '''
        Returns the result of calling xplaneFile.write(),
        where xplaneFile came from a root object (by name or Blender data).

        The output can also simultaniously written to a destination
        '''
        if isinstance(root_object,str):
            root_object = bpy.data.objects[root_object]

        xplaneFile = xplane_file.createFileFromBlenderRootObject(root_object)
        out = xplaneFile.write()

        if dest:
            with open(os.path.join(TMP_DIR, dest + '.obj'), 'w') as tmp_file:
                tmp_file.write(out)

        return out

    def exportXPlaneFileFromLayerIndex(self,layer):
        #COPY-PASTA WARNING from xplane_file: 65-75
        # What we need is an xplaneFile in the data model and interrupt
        # the export before the xplane_file gets deleted when going out of scope
        xplaneLayer = xplane_file.getXPlaneLayerForBlenderLayerIndex(layer)

        assert xplaneLayer is not None
        xplaneFile = xplane_file.XPlaneFile(xplane_file.getFilenameFromXPlaneLayer(xplaneLayer), xplaneLayer)

        assert xplaneFile is not None
        xplaneFile.collectFromBlenderLayerIndex(layer)

        return xplaneFile

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

            self.assertTrue(os.path.exists(fixtureFile), 'File "%s" does not exist' % fixtureFile)
            self.assertFileOutputEqualsFixture(out, fixtureFile, filterLine)

def make_fixture_path(dirname,filename,sub_dir=""):
    return os.path.join(dirname, 'fixtures', sub_dir, filename + '.obj')

def runTestCases(testCases):
    #Until a better solution for knowing if the logger's error count should be used to quit the testing,
    #we are currently saying only 1 is allow per suite at a time (which is likely how it should be anyways)
    assert len(testCases) == 1, "Currently, only one test case per suite is supported at a time"
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(testCases[0])
    test_result = unittest.TextTestRunner().run(suite)

    #See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    return_string = "RESULT: After {testsRun} tests got {errors} errors, {failures} failures, and {skipped} skipped"\
        .format(testsRun=test_result.testsRun,
                errors=len(test_result.errors),
                failures=len(test_result.failures),
                skipped=len(test_result.skipped))
    print(return_string)

