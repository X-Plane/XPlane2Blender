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
        #print("def test_drag_rotate_detent_case_01(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 2: Leaf not Animated
    def test_drag_rotate_detent_case_02(self):
        #print("def test_drag_rotate_detent_case_02(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 3: No-op Bones
    def test_drag_rotate_detent_case_03(self):
        #print("def test_drag_rotate_detent_case_03(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B),collection="Layer 1"))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(C),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(D,T_2_FRAMES_1_X)
        set_manipulator_settings(D,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Case 4: Surrounding No-op Bones
    def test_drag_rotate_detent_case_04(self):
        #print("def test_drag_rotate_detent_case_04(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(B),collection="Layer 1"))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C),collection="Layer 1"))

        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(C,T_2_FRAMES_1_X)
        set_manipulator_settings(D,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

        # Case 5: Requiremets met, don't care about above it
    def test_drag_rotate_detent_case_05(self):
        #print("def test_drag_rotate_detent_case_05(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(C,T_2_FRAMES_1_X)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Case 6: Has Show/Hide inbetween otherwise valid bones
    def test_drag_rotate_detent_case_06(self):
        #print("def test_drag_rotate_detent_case_06(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_sh",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_H)
        set_animation_data(C,T_2_FRAMES_1_X)

        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Failures
    # Case 7: Wrong order
    def test_drag_rotate_detent_case_07(self):
        #print("def test_drag_rotate_detent_case_07(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 8: Missing T, version 1
    def test_drag_rotate_detent_case_08(self):
        #print("def test_drag_rotate_detent_case_08(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 9: Missing T, version 2
    def test_drag_rotate_detent_case_09(self):
        #print("def test_drag_rotate_detent_case_09(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 10: Missing T, version 3
    def test_drag_rotate_detent_case_10(self):
        #print("def test_drag_rotate_detent_case_10(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(A,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 11: Missing R, version 1
    def test_drag_rotate_detent_case_11(self):
        #print("def test_drag_rotate_detent_case_11(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,T_2_FRAMES_1_X)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 12: Missing R, version 2
    def test_drag_rotate_detent_case_12(self):
        #print("def test_drag_rotate_detent_case_12(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(B,T_2_FRAMES_1_X)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 13: Missing R, version 3
    def test_drag_rotate_detent_case_13(self):
        #print("def test_drag_rotate_detent_case_13(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",collection="Layer 1"))

        set_animation_data(A,T_2_FRAMES_1_X)

        set_manipulator_settings(A,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 14: Missing RT, version 1
    def test_drag_rotate_detent_case_14(self):
        #print("def test_drag_rotate_detent_case_14(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",collection="Layer 1"))
        set_manipulator_settings(A,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 15: Missing RT, version 2
    def test_drag_rotate_detent_case_15(self):
        #print("def test_drag_rotate_detent_case_15(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_s",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,SHOW_ANIM_S)
        set_animation_data(A,SHOW_ANIM_H)

        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 16: Rotating Detent Bone
    def test_drag_rotate_detent_case_16(self):
        #print("def test_drag_rotate_detent_case_16(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 17: Translating Rotate Bone
    def test_drag_rotate_detent_case_17(self):
        #print("def test_drag_rotate_detent_case_17(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt",collection="Layer 1"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 18: T-T-R
    def test_drag_rotate_detent_case_18(self):
        #print("def test_drag_rotate_detent_case_18(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_animation_data(C,T_2_FRAMES_1_X)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 19: R-T-R
    def test_drag_rotate_detent_case_19(self):
        #print("def test_drag_rotate_detent_case_19(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",collection="Layer 1"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A),collection="Layer 1"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(B),collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_animation_data(C,R_2_FRAMES_45_Y_AXIS)
        set_manipulator_settings(C,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 20: All requirements on the same bone
    def test_drag_rotate_detent_case_20(self):
        #print("def test_drag_rotate_detent_case_20(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt",collection="Layer 1"))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        set_manipulator_settings(A,MANIP_DRAG_ROTATE_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestBoneConfigurationsDragRotateDetent])
