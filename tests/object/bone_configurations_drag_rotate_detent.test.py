import inspect
import os
import sys

import bpy
import io_xplane2blender
import io_xplane2blender.xplane_constants
import io_xplane2blender.tests.test_creation_helpers
from io_xplane2blender.tests.test_creation_helpers import *
from io_xplane2blender import tests, xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.xplane_constants import *
__dirname__ = os.path.dirname(__file__)

class TestBoneConfigurationsDragRotateDetent(XPlaneTestCase):
    #Case 1: The Classic
    def test_drag_rotate_detent_case_01(self):
        create_initial_test_setup()

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
 
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 2: Leaf not Animated
    def test_drag_rotate_detent_case_02(self):
        create_initial_test_setup()

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 3: No-op Bones
    def test_drag_rotate_detent_case_03(self):
        create_initial_test_setup()

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(C)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(D,T_2_FRAMES_1_X)
        set_manipulator_settings(D,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Case 4: Surrounding No-op Bones
    def test_drag_rotate_detent_case_04(self):
        create_initial_test_setup()

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))

        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(C,T_2_FRAMES_1_X)
        set_manipulator_settings(D,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

        # Case 5: Requiremets met, don't care about above it
    def test_drag_rotate_detent_case_05(self):
        create_initial_test_setup()

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(C,T_2_FRAMES_1_X)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

runTestCases([TestBoneConfigurationsDragRotateDetent]) 
