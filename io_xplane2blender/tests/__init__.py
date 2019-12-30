import os
import shutil
import sys
import unittest

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bpy

import io_xplane2blender
from io_xplane2blender.xplane_config import setDebug, getDebug
from io_xplane2blender import xplane_config
from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_helpers import logger, XPlaneLogger
from io_xplane2blender.xplane_types import xplane_bone, xplane_file, xplane_primitive
from ..xplane_types import xplane_file
from ..xplane_types.xplane_primitive import XPlanePrimitive
from .animation_file_mappings import mappings


#TODO: Make this import from XPlane2Blender/tests.py instead of just keeping it in sync manually
TEST_RESULTS_REGEX = "RESULT: After {num_tests} tests got {errors} errors, {fails} failures, and {skip} skipped"

FLOAT_TOLERANCE = 0.0001

__dirname__ = os.path.dirname(__file__)
TMP_DIR = os.path.realpath(os.path.join(__dirname__, '../../tests/tmp'))

FilterLinesCallback = Callable[[List[Union[float, str]]], bool]

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
            # TODO:  Remove/change
            self.assertIsNotNone(xplaneFile.objects[name])
            self.assertTrue(isinstance(xplaneFile.objects[name],xplane_primitive.XPlanePrimitive))
            self.assertEquals(xplaneFile.objects[name].blenderObject, bpy.data.objects[name])

    def assertXPlaneBoneTreeEqual(self, file_root_bone:xplane_bone.XPlaneBone, fixture_root_bone:xplane_bone.XPlaneBone)->None:
        """
        Recurses down two XPlaneBone trees, and compares each XPlaneBone's
        - xplaneObject
        - blenderObject
        - blenderBone

        self.xplaneFile and self.parent are not compared
        """
        assert file_root_bone
        assert fixture_root_bone

        def recursively_check(file_bone: xplane_bone.XPlaneBone,
                              fixture_bone: xplane_bone.XPlaneBone)->None:
            file_bone_name = getattr(file_bone.xplaneObject, 'name', 'None')
            fixture_bone_name = getattr(fixture_bone.xplaneObject, 'name', 'None')
            self.assertEqual(
                bool(file_bone.xplaneObject),
                bool(fixture_bone.xplaneObject),
                msg=f"File Bone '{file_bone.getName(ignore_indent_level=True)}'"\
                    f" and Fixture Bone '{file_bone.getName(ignore_indent_level=True)}'"\
                    f" don't have the same xplaneObject: ({file_bone_name, fixture_bone_name}),"
            )
            self.assertEqual(file_bone.blenderObject,
                             fixture_bone.blenderObject)
            self.assertEqual(file_bone.blenderBone,
                             fixture_bone.blenderBone)
            self.assertEqual(len(file_bone.children), len(fixture_bone.children))
            for child_file_bone, child_fixture_bone in zip(file_bone.children, fixture_bone.children):
                recursively_check(child_file_bone, child_fixture_bone)
        recursively_check(file_root_bone, fixture_root_bone)

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

    def assertFilesEqual(self,
                         a: str,
                         b: str,
                         filterCallback:Optional[FilterLinesCallback] = None,
                         floatTolerance:float = None):
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

    def assertFileOutputEqualsFixture(
            self,
            fileOutput:str,
            fixturePath:str,
            filterCallback:Optional[FilterLinesCallback] = None,
            floatTolerance:Optional[float] = None) -> None:
        """
        Compares the output of XPlaneFile.write (a \n separated str) to a fixture on disk.

        A filterCallback ensures only matching lines are compared.
        Highly recommended, with as simple a function as possible to prevent fixture fragility.
        """
        with open(fixturePath, "r") as fixtureFile:
            fixtureOutput = fixtureFile.read()

        return self.assertFilesEqual(fileOutput, fixtureOutput, filterCallback, floatTolerance)

    def assertFileTmpEqualsFixture(
            self,
            tmpPath:str,
            fixturePath:str,
            filterCallback: Optional[FilterLinesCallback] = None,
            floatTolerance: Optional[float] = None):
        tmpFile = open(tmpPath, 'r')
        tmpOutput = tmpFile.read()
        tmpFile.close()

        return self.assertFileOutputEqualsFixture(tmpOutput, fixturePath, filterCallback, floatTolerance)

    def assertLoggerErrors(self, expected_logger_errors:int)->None:
        """
        Asserts the logger has some number of errors, then clears the logger
        of all messages
        """
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

    def assertLayerExportEqualsFixture(self,
            layer:int,
            fixturePath:str,
            tmpFilename:Optional[str] = None,
            filterCallback:Optional[FilterLinesCallback] = None,
            floatTolerance:Optional[float] = None)->None:
        if not ('-q' in sys.argv or '--quiet' in sys.argv):
            print("Comparing: '%s', '%s'" % (tmpFilename, fixturePath))

        out = self.exportExportableRoot(bpy.data.collections[f"Layer {layer + 1}"], tmpFilename)
        self.assertFileOutputEqualsFixture(out, fixturePath, filterCallback, floatTolerance)

    #TODO: Rename assertExportableRootExportEqualsFixture
    def assertRootObjectExportEqualsFixture(self,
            root_object:Union[bpy.types.Collection, bpy.types.Object, str],
            fixturePath: str = None,
            tmpFilename: Optional[str] = None,
            filterCallback:Optional[FilterLinesCallback] = None,
            floatTolerance: Optional[float] = None):
        """
        Exports only a specific exportable root and compares the output
        to a fixutre.

        If filterCallback is None, no filter (besides stripping comments)
        will be used.
        """
        out = self.exportExportableRoot(root_object, tmpFilename)
        self.assertFileOutputEqualsFixture(out, fixturePath, filterCallback, floatTolerance)

    # asserts that an attributes object equals a dict
    def assertAttributesEqualDict(self,
                                  attrs:List[str],
                                  d:Dict[str, Any],
                                  floatTolerance:Optional[float] = None):
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

    def exportLayer(self, layer_number:int, dest:str = None)->str:
        """
        DEPRECATED: New unit tests should not use this!

        - layer_number starts at 0, as it used to access the scene.layers collection
        - dest is a filepath without the file extension .obj, written to the TMP_DIR if not None
        """
        return self.exportExportableRoot(bpy.data.collections[f"Layer {layer_number + 1}"], dest)

    def exportExportableRoot(self, root_object:Union[bpy.types.Collection, bpy.types.Object, str], dest:str = None)->str:
        """
        Returns the result of calling xplaneFile.write(),
        where xplaneFile came from a root object (by name or Blender data).

        - dest is a filepath without the file extension .obj, written to the TMP_DIR if not None

        If root_object is an str, matching collections are looked up first.
        If you don't want an ambiguity of root objects, don't use the name twice
        """
        if isinstance(root_object, str):
            try:
                root_object = bpy.data.collections[root_object]
            except KeyError:
                try:
                    root_object = bpy.data.objects[root_object]
                except KeyError:
                    assert False, f"{root_object} must be in bpy.data.collections|objects"

        xplaneFile = xplane_file.createFileFromBlenderRootObject(root_object)
        out = xplaneFile.write()

        if dest:
            with open(os.path.join(TMP_DIR, dest + '.obj'), 'w') as tmp_file:
                tmp_file.write(out)

        return out


class XPlaneAnimationTestCase(XPlaneTestCase):
    def setUp(self):
        super(XPlaneAnimationTestCase, self).setUp()

    def exportAnimationTestCase(self, name, dest):
        self.assertTrue(mappings[name])

        for layer in mappings[name]:
            outFile = os.path.join(dest, os.path.basename(mappings[name][layer]))
            print('Exporting to "%s"' % outFile)

            xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.collections[f"Layer {layer + 1}"])

            self.assertIsNotNone(xplaneFile, f"Unable to create XPlaneFile for {name} from Layer {layer + 1}")

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

            xplaneFile = xplane_file.createFileFromBlenderRootObject(bpy.data.collections[f"Layer {layer + 1}"])

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

    # See XPlane2Blender/tests.py for documentation. The strings must be kept in sync!
    # This is not an optional debug print statement! The test runner needs this print statement to function
    print(f"RESULT: After {(test_result.testsRun)} tests got {len(test_result.errors)} errors, {len(test_result.failures)} failures, and {len(test_result.skipped)} skipped")
