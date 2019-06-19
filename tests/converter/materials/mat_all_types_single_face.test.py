import inspect
import os
import sys

import bpy

from typing import Any, Dict, Iterable
from io_xplane2blender import xplane_config, xplane_constants
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType

__dirname__ = os.path.dirname(__file__)

def filterLines(line):
    return isinstance(line[0],str) and\
            ("VLIGHT" in line[0] and
             "LIGHTS" in line[0])

class TestMatAllTypesSingleFace(XPlaneTestCase):
    """
    One day we'll replace this manual property checking, or add onto it,
    with real fixtures, but right now we don't have a good enough converter
    or complete enough
    def _test(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function.replace("test_", "OBJ")

        self.assertRootObjectExportEqualsFixture(
                filename.replace("test_", "OBJ"),
                os.path.join(__dirname__, 'fixtures', filename + ".obj"),
                filename,
                filterLines
            )
    """

    """
    Material property names that get changed by the section of
    xplane_249_material_converter we're testing (TexFace Mode buttons)
    """
    _relavent_properties = {
                    "blend_v1000",
                    "blendRatio",
                    "draped",
                    "draw",
                    "poly_os",
                    "solid_camera",
                    "shadow_local"
                    }
    # These are the possible properties this test could alter
    @classmethod
    def _get_default_values_for_test_props(cls):
        return {
                prop: bpy.types.XPlaneMaterialSettings.bl_rna.properties[prop].default
                for prop in cls._relavent_properties
                }

    @classmethod
    def _get_mat_values_for_test_props(cls, mat: bpy.types.Material):
        defaults = cls._get_default_values_for_test_props()
        return {prop: mat.xplane.get(prop, defaults[prop]) for prop in cls._relavent_properties}

    def _test_prop_values_still_default(self, obj: bpy.types.Object, ignore_keys: Iterable[str]):
        """
        Given a dictionary of properties that should change and what their new value should be,
        test that only those properties of that material have changed to their intended data
        """
        mat = obj.material_slots[0].material

        # First, compare that all unchanged keys are still the defaults
        default_props = self._get_default_values_for_test_props()
        current_props = self._get_mat_values_for_test_props(mat)

        for item_default, item_current in filter(lambda item: item[0][0] not in ignore_keys,
                                                 zip(sorted(default_props.items()),
                                                     sorted(current_props.items()))
                                                 ):
            self.assertEqual(item_default[1], item_current[1], msg="Default and current values for prop '{}' don't match: '{}', {}'".format(item_default[0], item_default[1], item_current[1]))

    def _test_prop_values_have_changes(self, obj: bpy.types.Object, changed_props: Dict[str, Any]):
        mat = obj.material_slots[0].material
        current_props = self._get_mat_values_for_test_props(mat)
        # Then compare that the relavent changed props have been changed
        for item_current, item_changed in zip(sorted(current_props.items()), sorted(changed_props.items())):
            self.assertEqual(item_current[1], item_changed[1])


    def test_01_default(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        self._test_prop_values_still_default(bpy.data.objects["01_default"], [])

        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_02a_tex_alpha(self):
        #shadow, .5
        pass
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_02b_tex_clip(self):
        #off, .5
        pass
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_02c_tex_panel(self):
        pass

    @unittest.skip
    def test_02d_tex_no_tiles_or_light_cockpit(self):
        #poly_os =2
        pass

    @unittest.skip
    def test_02e_tex_tiles_cockpit(self):
        #no poly_os 2
        pass

    def test_03a_tiles(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["draped"] = True # Mirrors what should happen
        self._test_prop_values_still_default(bpy.data.objects["03_tiles"], ["draped"])
        self._test_prop_values_have_changes(bpy.data.objects["03_tiles"], changed_props)
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_03b_tiles_no_attr_draped(self):
        """
        This should not have any changes
        """

    @unittest.skip
    def test_04_light(self):
        pass
        #TestMatAllTypesSingleFace._test(self)
    @unittest.skip
    def test_04b_light_no_attr_draped(self):
        pass
        #TestMatAllTypesSingleFace._test(self)
    @unittest.skip
    def test_05_invisible(self):
        pass
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_06_dynamic(self):
        pass
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_07_twoside(self):
        pass
        #TestMatAllTypesSingleFace._test(self)

    @unittest.skip
    def test_08_shadow(self):
        pass
        #TestMatAllTypesSingleFace._test(self)


runTestCases([TestMatAllTypesSingleFace])
