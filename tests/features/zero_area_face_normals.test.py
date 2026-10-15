import os

import bpy

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests.test_creation_helpers import *
from io_xplane2blender.xplane_helpers import logger

__dirname__ = os.path.dirname(__file__)


class TestZeroAreaFaceNormals(XPlaneTestCase):
    def test_zero_area_face_corners_get_a_normal(self):
        create_initial_test_setup()

        # A smooth quad with a collinear (zero-area) triangle hanging off one
        # corner. Blender gives the sliver's far corner a (0, 0, 0) corner
        # normal, and that vertex's own normal is zero as well, since the
        # sliver is the only face it belongs to
        ob = create_datablock_mesh(
            DatablockInfo("MESH", "sliver", collection="Layer 1"), "plane"
        )
        bpy.data.collections["Layer 1"].xplane.is_exportable_collection = True
        mesh = ob.data
        mesh.clear_geometry()
        mesh.from_pydata(
            [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0), (2, 0, 0), (3, 0, 0)],
            [],
            [(0, 1, 2, 3), (1, 4, 5)],
        )
        mesh.update()
        mesh.uv_layers.new()
        for polygon in mesh.polygons:
            polygon.use_smooth = True

        out = self.exportLayer(0)
        self.assertFalse(logger.hasErrors())
        self.assertTrue(
            any(
                "had no normal" in warning["message"]
                for warning in logger.findWarnings()
            ),
            "expected a warning about zero-area face corners",
        )
        logger.clearMessages()

        vt_normals = [
            tuple(float(component) for component in line.split()[4:7])
            for line in out.splitlines()
            if line.startswith("VT")
        ]
        self.assertTrue(vt_normals, "no VT lines exported")
        self.assertNotIn((0.0, 0.0, 0.0), vt_normals)


runTestCases([TestZeroAreaFaceNormals])
