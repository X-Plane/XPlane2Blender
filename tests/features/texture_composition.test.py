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

    def test_texture_composition_nm_spec_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_nm_spec'

        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

        # move generated image files into temp dir and compare them with fixtures
        normalSpecTexPath = os.path.join(__dirname__, 'tex/normal_nm_spec.png')
        tmpNormalSpecTexPath = os.path.join(__dirname__, '../tmp/normal_nm_spec.png')
        fixtureNormalSpecTexPath = os.path.join(__dirname__, 'fixtures/tex/normal_nm_spec.png')
        self.assertTrue(os.path.exists(normalSpecTexPath), 'Normal+Specular texture was not generated.')
        self.assertEqual(self.checksum(normalSpecTexPath), self.checksum(fixtureNormalSpecTexPath), 'Image files are not equal.')

        # store modification time of composed texture
        normalSpecTexTime = os.path.getmtime(normalSpecTexPath)

        # export again
        self.exportLayer(0, filename)

        self.assertTrue(os.path.exists(normalSpecTexPath))
        self.assertEqual(normalSpecTexTime, os.path.getmtime(normalSpecTexPath))

        # move to tmp dir for manual investigation
        os.rename(normalSpecTexPath, tmpNormalSpecTexPath)

    def test_texture_composition_nm_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_nm'

        self.assertLayerExportEqualsFixture(
            1, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

        # move generated image files into temp dir and compare them with fixtures
        normalSpecTexPath = os.path.join(__dirname__, 'tex/normal_with_alpha_nm.png')
        tmpNormalSpecTexPath = os.path.join(__dirname__, '../tmp/normal_with_alpha_nm.png')
        fixtureNormalSpecTexPath = os.path.join(__dirname__, 'fixtures/tex/normal_with_alpha_nm.png')
        self.assertTrue(os.path.exists(normalSpecTexPath), 'Normal texture was not generated.')
        self.assertEqual(self.checksum(normalSpecTexPath), self.checksum(fixtureNormalSpecTexPath), 'Image files are not equal.')

        # store modification time of composed texture
        normalSpecTexTime = os.path.getmtime(normalSpecTexPath)

        # export again
        self.exportLayer(1, filename)

        self.assertTrue(os.path.exists(normalSpecTexPath))
        self.assertEqual(normalSpecTexTime, os.path.getmtime(normalSpecTexPath))

        # move to tmp dir for manual investigation
        os.rename(normalSpecTexPath, tmpNormalSpecTexPath)

    def test_texture_composition_spec_export(self):
        def filterLines(line):
            return isinstance(line[0], str) and \
                   line[0].find('TEXTURE') == 0

        filename = 'test_texture_composition_spec'

        self.assertLayerExportEqualsFixture(
            2, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

        # move generated image files into temp dir and compare them with fixtures
        normalSpecTexPath = os.path.join(__dirname__, 'tex/specular_spec.png')
        tmpNormalSpecTexPath = os.path.join(__dirname__, '../tmp/specular_spec.png')
        fixtureNormalSpecTexPath = os.path.join(__dirname__, 'fixtures/tex/specular_spec.png')
        self.assertTrue(os.path.exists(normalSpecTexPath), 'Normal texture was not generated.')
        self.assertEqual(self.checksum(normalSpecTexPath), self.checksum(fixtureNormalSpecTexPath), 'Image files are not equal.')

        # store modification time of composed texture
        normalSpecTexTime = os.path.getmtime(normalSpecTexPath)

        # export again
        self.exportLayer(2, filename)

        self.assertTrue(os.path.exists(normalSpecTexPath))
        self.assertEqual(normalSpecTexTime, os.path.getmtime(normalSpecTexPath))

        # move to tmp dir for manual investigation
        os.rename(normalSpecTexPath, tmpNormalSpecTexPath)

runTestCases([TestTextureComposition])
