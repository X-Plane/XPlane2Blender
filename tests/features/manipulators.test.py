import os
import sys

import bpy

from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)


class TestMaterials(XPlaneTestCase):
    def test_manipulator_attributes(self):
        xplaneFile = self.createXPlaneFileFromPotentialRoot(
            bpy.data.collections["Layer 1"]
        )
        drag_xy = xplaneFile._bl_obj_name_to_bone["drag_xy"].xplaneObject
        self.assertAttributesEqualDict(
            drag_xy.cockpitAttributes,
            {
                "ATTR_manip_drag_xy": (
                    "hand",
                    "1.000",
                    "2.000",
                    "3.000",
                    "4.000",
                    "5.000",
                    "6.000",
                    "dataref1",
                    "dataref2",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        drag_axis = xplaneFile._bl_obj_name_to_bone["drag_axis"].xplaneObject
        self.assertAttributesEqualDict(
            drag_axis.cockpitAttributes,
            {
                "ATTR_manip_drag_axis": (
                    "four_arrows",
                    "1.000",
                    "2.000",
                    "3.000",
                    "4.000",
                    "5.000",
                    "dataref",
                    "this should be the tooltip",
                )
            },
        )

        command = xplaneFile._bl_obj_name_to_bone["command"].xplaneObject
        self.assertAttributesEqualDict(
            command.cockpitAttributes,
            {
                "ATTR_manip_command": (
                    "button",
                    "the_command",
                    "this should be the tooltip",
                )
            },
        )

        command_axis = xplaneFile._bl_obj_name_to_bone["command_axis"].xplaneObject
        self.assertAttributesEqualDict(
            command_axis.cockpitAttributes,
            {
                "ATTR_manip_command_axis": (
                    "rotate_small",
                    "1.000",
                    "2.000",
                    "3.000",
                    "pos_command",
                    "neg_command",
                    "this should be the tooltip",
                )
            },
        )

        push = xplaneFile._bl_obj_name_to_bone["push"].xplaneObject
        self.assertAttributesEqualDict(
            push.cockpitAttributes,
            {
                "ATTR_manip_push": (
                    "rotate_small_left",
                    "1.000",
                    "2.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        radio = xplaneFile._bl_obj_name_to_bone["radio"].xplaneObject
        self.assertAttributesEqualDict(
            radio.cockpitAttributes,
            {
                "ATTR_manip_radio": (
                    "rotate_small_right",
                    "1.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        delta = xplaneFile._bl_obj_name_to_bone["delta"].xplaneObject
        self.assertAttributesEqualDict(
            delta.cockpitAttributes,
            {
                "ATTR_manip_delta": (
                    "rotate_medium",
                    "1.000",
                    "2.000",
                    "3.000",
                    "4.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        wrap = xplaneFile._bl_obj_name_to_bone["wrap"].xplaneObject
        self.assertAttributesEqualDict(
            wrap.cockpitAttributes,
            {
                "ATTR_manip_wrap": (
                    "rotate_medium_left",
                    "1.000",
                    "2.000",
                    "3.000",
                    "4.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        toggle = xplaneFile._bl_obj_name_to_bone["toggle"].xplaneObject
        self.assertAttributesEqualDict(
            toggle.cockpitAttributes,
            {
                "ATTR_manip_toggle": (
                    "rotate_medium_right",
                    "1.000",
                    "2.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        noop = xplaneFile._bl_obj_name_to_bone["noop"].xplaneObject
        self.assertEqual(bpy.data.objects["noop"].xplane.manip.dataref1, "dataref")
        self.assertEqual(
            bpy.data.objects["noop"].xplane.manip.tooltip, "this should be the tooltip"
        )
        self.assertAttributesEqualDict(
            noop.cockpitAttributes,
            {"ATTR_manip_noop": ()},
        )

        drag_axis_pix = xplaneFile._bl_obj_name_to_bone["drag_axis_pix"].xplaneObject
        self.assertAttributesEqualDict(
            drag_axis_pix.cockpitAttributes,
            {
                "ATTR_manip_drag_axis_pix": (
                    "rotate_large_left",
                    "1.000",
                    "2.000",
                    "3.000",
                    "4.000",
                    "5.000",
                    "dataref",
                    "this should be the tooltip",
                ),
                "ATTR_manip_wheel": "1.000",
            },
        )

        command_knob = xplaneFile._bl_obj_name_to_bone["command_knob"].xplaneObject
        self.assertAttributesEqualDict(
            command_knob.cockpitAttributes,
            {
                "ATTR_manip_command_knob": (
                    "rotate_large_left",
                    "pos_command",
                    "neg_command",
                    "this should be the tooltip",
                )
            },
        )

        command_switch_up_down = xplaneFile._bl_obj_name_to_bone[
            "command_switch_up_down"
        ].xplaneObject
        self.assertAttributesEqualDict(
            command_switch_up_down.cockpitAttributes,
            {
                "ATTR_manip_command_switch_up_down": (
                    "rotate_large_left",
                    "pos_command",
                    "neg_command",
                    "this should be the tooltip",
                )
            },
        )

        command_switch_left_right = xplaneFile._bl_obj_name_to_bone[
            "command_switch_left_right"
        ].xplaneObject
        self.assertAttributesEqualDict(
            command_switch_left_right.cockpitAttributes,
            {
                "ATTR_manip_command_switch_left_right": (
                    "rotate_large_left",
                    "pos_command",
                    "neg_command",
                    "this should be the tooltip",
                )
            },
        )

        axis_switch_up_down = xplaneFile._bl_obj_name_to_bone[
            "axis_switch_up_down"
        ].xplaneObject
        self.assertAttributesEqualDict(
            axis_switch_up_down.cockpitAttributes,
            {
                "ATTR_manip_axis_switch_up_down": (
                    "rotate_large_left",
                    "4.000",
                    "5.000",
                    "1.000",
                    "0.500",
                    "dataref",
                    "this should be the tooltip",
                )
            },
        )

        axis_switch_left_right = xplaneFile._bl_obj_name_to_bone[
            "axis_switch_left_right"
        ].xplaneObject
        self.assertAttributesEqualDict(
            axis_switch_left_right.cockpitAttributes,
            {
                "ATTR_manip_axis_switch_left_right": (
                    "rotate_large_left",
                    "4.000",
                    "5.000",
                    "1.000",
                    "0.500",
                    "dataref",
                    "this should be the tooltip",
                )
            },
        )

    def test_export_manipulators(self):
        def filterLines(line):
            return isinstance(line[0], str) and line[0].find("ATTR_manip_") == 0

        filename = "test_manipulators"
        self.assertLayerExportEqualsFixture(
            0,
            os.path.join(__dirname__, "fixtures", filename + ".obj"),
            filterLines,
            filename,
        )


runTestCases([TestMaterials])
