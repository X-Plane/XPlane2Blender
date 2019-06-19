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
        def get_enum_aware(mat:bpy.types.Material, prop:str):
            """
            Like get, but turns enum values back into their identifiers
            """
            mat_props = mat.xplane.bl_rna.properties
            if mat_props[prop].type == "ENUM":
                return mat_props[prop].enum_items[mat.xplane.get(prop, defaults[prop])].identifier
            else:
                return mat.xplane.get(prop, defaults[prop])

        return {prop: get_enum_aware(mat, prop) for prop in cls._relavent_properties}

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
            self.assertEqual(item_default[1], item_current[1],
                    msg="Default and current values for prop '{}' don't match: '{}', {}'"
                    .format(item_default[0], item_default[1], item_current[1]))

    def _test_prop_values_have_changes(self, obj: bpy.types.Object, changed_props: Dict[str, Any]):
        mat = obj.material_slots[0].material
        current_props = self._get_mat_values_for_test_props(mat)
        # Then compare that the relavent changed props have been changed
        for item_current, item_changed in zip(sorted(current_props.items()), sorted(changed_props.items())):
            self.assertEqual(item_current[1], item_changed[1],
                    msg="Current and required values for prop '{}' don't match: '{}', '{}'"
                    .format(item_current[0], item_current[1], item_changed[1]))

    def _no_change(self, name):
        self._test_prop_values_still_default(bpy.data.objects[name], [])

    def test_01_default(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        self._no_change("01_default")

    def _shadow_test(self, name):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["blend_v1000"] = xplane_constants.BLEND_SHADOW
        changed_props["blendRatio"] = 0.5
        self._test_prop_values_still_default(bpy.data.objects[name], ["blend_v1000", "blendRatio"])
        self._test_prop_values_have_changes(bpy.data.objects[name], changed_props)

    def _clip_test(self, name):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["blend_v1000"] = xplane_constants.BLEND_OFF
        changed_props["blendRatio"] = 0.5
        self._test_prop_values_still_default(bpy.data.objects[name], ["blend_v1000", "blendRatio"])
        self._test_prop_values_have_changes(bpy.data.objects[name], changed_props)

    def test_02a_tex_alpha_at(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function.replace("test_", "")
        self._shadow_test(filename)

    def test_02b_tex_alpha_gl(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function.replace("test_", "")
        self._shadow_test(filename)

    def test_02c_tex_alpha_no(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        self._no_change("02c_tex_alpha_no")

    def test_02d_tex_clip_at(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function.replace("test_", "")
        self._clip_test(filename)

    def test_02e_tex_clip_gl(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        filename = inspect.stack()[0].function.replace("test_", "")
        self._clip_test(filename)

    def test_02f_tex_clip_no(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        self._no_change("02f_tex_clip_no")


    def test_02g_tex_poly_os_2(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["poly_os"] = 2
        self._test_prop_values_still_default(bpy.data.objects["02g_tex_poly_os_2"], ["poly_os"])
        self._test_prop_values_have_changes(bpy.data.objects["02g_tex_poly_os_2"], changed_props)

    def test_02h_tex_no_poly_os(self):
        self._no_change("02h_tex_no_poly_os")

    def test_03a_tiles(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["draped"] = True # Mirrors what should happen
        filename = inspect.stack()[0].function.replace("test_", "")
        self._test_prop_values_still_default(bpy.data.objects[filename], ["draped"])
        self._test_prop_values_have_changes(bpy.data.objects[filename], changed_props)
        #TestMatAllTypesSingleFace._test(self)

    def test_03b_tiles_no_attr_draped(self):
        self._no_change("03b_tiles_no_att")

    def test_04a_light(self):
        bpy.ops.xplane.do_249_conversion(workflow_type=WorkflowType.BULK.name)
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["draped"] = True # Mirrors what should happen
        filename = inspect.stack()[0].function.replace("test_", "")
        self._test_prop_values_still_default(bpy.data.objects[filename], ["draped"])
        self._test_prop_values_have_changes(bpy.data.objects[filename], changed_props)
        #TestMatAllTypesSingleFace._test(self)

    def test_04b_light_no_attr_draped(self):
        self._no_change("04b_light_no_att")
        #TestMatAllTypesSingleFace._test(self)

    def test_05_invisible(self):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["draw"] = False
        filename = inspect.stack()[0].function.replace("test_", "")
        self._test_prop_values_still_default(bpy.data.objects[filename], ["draw"])
        self._test_prop_values_have_changes(bpy.data.objects[filename], changed_props)
        #TestMatAllTypesSingleFace._test(self)

    def test_06a_dynamic(self):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["solid_camera"] = True
        filename = inspect.stack()[0].function.replace("test_", "")
        self._test_prop_values_still_default(bpy.data.objects[filename], ["solid_camera"])
        self._test_prop_values_have_changes(bpy.data.objects[filename], changed_props)
        #TestMatAllTypesSingleFace._test(self)

    def test_06b_dynamic_invisible(self):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["draw"] = False
        self._test_prop_values_still_default(bpy.data.objects["06b_dynamic_invi"], ["draw"])
        self._test_prop_values_have_changes(bpy.data.objects["06b_dynamic_invi"], changed_props)

    def test_06c_dynamic_cockpit(self):
        self._test_prop_values_still_default(bpy.data.objects["06c_dynamic_ckp"], [])

    def test_07_twoside(self):
        filename = inspect.stack()[0].function.replace("test_", "")
        self._no_change(filename)
        #TestMatAllTypesSingleFace._test(self)

    def test_08_shadow(self):
        changed_props = TestMatAllTypesSingleFace._get_default_values_for_test_props()
        changed_props["shadow_local"] = False
        filename = inspect.stack()[0].function.replace("test_", "")
        self._test_prop_values_still_default(bpy.data.objects[filename], ["shadow_local"])
        self._test_prop_values_have_changes(bpy.data.objects[filename], changed_props)
        #TestMatAllTypesSingleFace._test(self)


runTestCases([TestMatAllTypesSingleFace])
