import bpy
import os
import sys
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_types import xplane_file

__dirname__ = os.path.dirname(__file__)

class TestMaterials(XPlaneTestCase):
    def test_manipulator_attributes(self):
        xplaneFile = xplane_file.createFileFromBlenderLayerIndex(0)

        drag_xy = xplaneFile.objects['drag_xy']
        self.assertAttributesEqualDict(drag_xy.cockpitAttributes, {
            'ATTR_manip_drag_xy': (
                'hand',
                1, 2, 3, 4, 5, 6,
                'dataref1', 'dataref2',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        drag_axis = xplaneFile.objects['drag_axis']
        self.assertAttributesEqualDict(drag_axis.cockpitAttributes, {
            'ATTR_manip_drag_axis': (
                'four_arrows',
                1, 2, 3, 4, 5,
                'dataref',
                'this should be the tooltip'
            )
        })

        command = xplaneFile.objects['command']
        self.assertAttributesEqualDict(command.cockpitAttributes, {
            'ATTR_manip_command': (
                'button',
                'the_command',
                'this should be the tooltip'
            )
        })

        command_axis = xplaneFile.objects['command_axis']
        self.assertAttributesEqualDict(command_axis.cockpitAttributes, {
            'ATTR_manip_command_axis': (
                'rotate_small',
                1, 2, 3,
                'pos_command', 'neg_command',
                'this should be the tooltip'
            )
        })

        push = xplaneFile.objects['push']
        self.assertAttributesEqualDict(push.cockpitAttributes, {
            'ATTR_manip_push': (
                'rotate_small_left',
                1, 2,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        radio = xplaneFile.objects['radio']
        self.assertAttributesEqualDict(radio.cockpitAttributes, {
            'ATTR_manip_radio': (
                'rotate_small_right',
                1,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        delta = xplaneFile.objects['delta']
        self.assertAttributesEqualDict(delta.cockpitAttributes, {
            'ATTR_manip_delta': (
                'rotate_medium',
                1, 2, 3, 4,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        wrap = xplaneFile.objects['wrap']
        self.assertAttributesEqualDict(wrap.cockpitAttributes, {
            'ATTR_manip_wrap': (
                'rotate_medium_left',
                1, 2, 3, 4,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        toggle = xplaneFile.objects['toggle']
        self.assertAttributesEqualDict(toggle.cockpitAttributes, {
            'ATTR_manip_toggle': (
                'rotate_medium_right',
                1, 2,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        noop = xplaneFile.objects['noop']
        self.assertAttributesEqualDict(noop.cockpitAttributes, {
            'ATTR_manip_noop': True
        })

        drag_axis_pix = xplaneFile.objects['drag_axis_pix']
        self.assertAttributesEqualDict(drag_axis_pix.cockpitAttributes, {
            'ATTR_manip_drag_axis_pix': (
                'rotate_large_left',
                1, 2, 3, 4, 5,
                'dataref',
                'this should be the tooltip'
            ),
            'ATTR_manip_wheel': (1)
        })

        command_knob = xplaneFile.objects['command_knob']
        self.assertAttributesEqualDict(command_knob.cockpitAttributes, {
            'ATTR_manip_command_knob': (
                'rotate_large_left',
                'pos_command', 'neg_command',
                'this should be the tooltip'
            )
        })

        command_switch_up_down = xplaneFile.objects['command_switch_up_down']
        self.assertAttributesEqualDict(command_switch_up_down.cockpitAttributes, {
            'ATTR_manip_command_switch_up_down': (
                'rotate_large_left',
                'pos_command', 'neg_command',
                'this should be the tooltip'
            )
        })

        command_switch_left_right = xplaneFile.objects['command_switch_left_right']
        self.assertAttributesEqualDict(command_switch_left_right.cockpitAttributes, {
            'ATTR_manip_command_switch_left_right': (
                'rotate_large_left',
                'pos_command', 'neg_command',
                'this should be the tooltip'
            )
        })

        axis_switch_up_down = xplaneFile.objects['axis_switch_up_down']
        self.assertAttributesEqualDict(axis_switch_up_down.cockpitAttributes, {
            'ATTR_manip_axis_switch_up_down': (
                'rotate_large_left',
                4, 5, 1, 0.5,
                'dataref',
                'this should be the tooltip'
            )
        })

        axis_switch_left_right = xplaneFile.objects['axis_switch_left_right']
        self.assertAttributesEqualDict(axis_switch_left_right.cockpitAttributes, {
            'ATTR_manip_axis_switch_left_right': (
                'rotate_large_left',
                4, 5, 1, 0.5,
                'dataref',
                'this should be the tooltip'
            )
        })

    def test_export_manipulators(self):
        def filterLines(line):
            return isinstance(line[0], str) and line[0].find('ATTR_manip_') == 0

        filename = 'test_manipulators'
        self.assertLayerExportEqualsFixture(
            0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
            filename,
            filterLines
        )

runTestCases([TestMaterials])
