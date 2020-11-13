import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file
from hashlib import md5

__dirname__ = os.path.dirname(__file__)

class TestTextureComposition(XPlaneTestCase):
    def checksum(self, file):
        return md5(open(file, 'rb').read()).hexdigest()

    #returns a tuple of texture, generated texture, and fixture texture
    def make_test_paths(self,file_name):
        #The file referenced in the blender file
        blenderTexPath = os.path.join(__dirname__, 'tex/' + file_name)

        #The file generated during the test
        tmpTexPath     = os.path.join(__dirname__, '../tmp/' + file_name)

        #The test fixture file to test sameness with
        fixtureTexPath = os.path.join(__dirname__, 'fixtures/tex/'  + file_name)
        return (blenderTexPath,tmpTexPath,fixtureTexPath)

    # move generated image files into temp dir and compare them with fixtures
    def move_image_for_manual_comparison(self, blenderTexPath, tmpTexPath):
         # move to tmp dir for manual investigation
        os.rename(blenderTexPath, tmpTexPath)

        print("Manually inspect blender image %s with generated image %s" % (blenderTexPath,tmpTexPath))

    #TODO: Is this needed?
    #Assert that the modification is the same
    def do_modified_time_test(self,blenderTexPath,layer_index, filename):
        # store modification time of composed texture
        blenderTexTime = os.path.getmtime(blenderTexPath)

        # export again
        self.exportLayer(layer_index, filename)

        self.assertTrue(os.path.exists(blenderTexPath))
        self.assertEqual(blenderTexTime, os.path.getmtime(blenderTexPath))

    def test_texture_composition_nm_spec_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_nm_spec'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

        # move generated image files into temp dir and compare them with fixtures
        (blenderNormSpecTexPath, tmpNormSpecTexPath, fixtureNormSpecTexPath) = self.make_test_paths('normal_nm_spec.png')

        self.assertTrue(os.path.exists(blenderNormSpecTexPath), 'Normal+Specular texture was not generated.')
        self.assertEqual(self.checksum(blenderNormSpecTexPath), self.checksum(fixtureNormSpecTexPath), 'Image files are not equal.')

        self.do_modified_time_test(blenderNormSpecTexPath,0,filename)
        self.move_image_for_manual_comparison(blenderNormSpecTexPath,tmpNormSpecTexPath)

    def test_texture_composition_nm_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_nm'

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

        # move generated image files into temp dir and compare them with fixtures
        (blenderNormWithAlphaTexPath,tmpNormWithAlphaTexPath,fixtureAlphaTexPath) = self.make_test_paths('normal_with_alpha_nm.png')

        self.assertTrue(os.path.exists(blenderNormWithAlphaTexPath), 'Normal w/ alpha texture was not generated.')
        self.assertEqual(self.checksum(blenderNormWithAlphaTexPath), self.checksum(fixtureAlphaTexPath), 'Image files are not equal.')

        self.do_modified_time_test(blenderNormWithAlphaTexPath,1,filename)

        # move to tmp dir for manual investigation
        self.move_image_for_manual_comparison(blenderNormWithAlphaTexPath, tmpNormWithAlphaTexPath)

    def test_texture_composition_spec_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_spec'

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filterLines,
            filename,
        )

        (blenderSpecTexPath,tmpSpecTexPath,fixtureSpecTextPath) = self.make_test_paths('specular_spec.png')

        self.assertTrue(os.path.exists(blenderSpecTexPath), 'Specular spec texture was not generated.')
        self.assertEqual(self.checksum(blenderSpecTexPath), self.checksum(fixtureSpecTextPath), 'Image files are not equal.')

        self.do_modified_time_test(blenderSpecTexPath,2,filename)

        self.move_image_for_manual_comparison(blenderSpecTexPath, tmpSpecTexPath)

runTestCases([TestTextureComposition])
