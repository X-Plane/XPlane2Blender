import os
import sysconfig

from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


def filterLines(line):
    return isinstance(line[0], str) and (line[0].find("BLEND_GLASS") == 0)


class TestBlendGlass(XPlaneTestCase):
    def test_air_glass_off_expect_no_dir(self):
        filename = "test_air_glass_off_expect_no_dir"
        self.assertLayerExportEqualsFixture(
            0,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_air_glass_on_expect_dir(self):
        filename = "test_air_glass_on_expect_dir"
        self.assertLayerExportEqualsFixture(
            1,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_ckpt_glass_off_expect_no_dir(self):
        filename = "test_ckpt_glass_off_expect_no_dir"
        self.assertLayerExportEqualsFixture(
            2,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_ckpt_glass_on_expect_dir(self):
        filename = "test_ckpt_glass_on_expect_dir"
        self.assertLayerExportEqualsFixture(
            3,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_panel_glass_off_expect_no_dir(self):
        filename = "test_panel_glass_off_expect_no_dir"
        self.assertLayerExportEqualsFixture(
            4,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_panel_glass_on_expect_dir(self):
        filename = "test_panel_glass_on_expect_dir"
        self.assertLayerExportEqualsFixture(
            5,
            make_fixture_path(__dirname__, filename),
            filterLines,
            filename,
        )

    def test_instanced_glass_illegal(self):
        filename = "test_instanced_glass_illegal"

        out = self.exportLayer(6)
        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()

    def test_scenery_glass_illegal(self):
        filename = "test_scenery_glass_illegal"

        out = self.exportLayer(7)
        self.assertEqual(len(logger.findErrors()), 1)
        logger.clearMessages()


runTestCases([TestBlendGlass])
