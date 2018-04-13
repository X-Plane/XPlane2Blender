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

class TestBoneConfigurationsDragAxisDetent(XPlaneTestCase):
    #Case 1: The Classic
    def test_drag_axis_detent_case_01(self):
        #print("def test_drag_axis_detent_case_01(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_Y)
        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
 
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 2: Leaf not Animated
    def test_drag_axis_detent_case_02(self):
        #print("def test_drag_axis_detent_case_02(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_Y)
        set_manipulator_settings(C,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 3: No-op Bones
    def test_drag_axis_detent_case_03(self):
        #print("def test_drag_axis_detent_case_03(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(C)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(D,T_2_FRAMES_1_Y)
        set_manipulator_settings(D,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Case 4: Surrounding No-op Bones
    def test_drag_axis_detent_case_04(self):
        #print("def test_drag_axis_detent_case_04(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))

        set_animation_data(B,T_2_FRAMES_1_X)
        set_animation_data(C,T_2_FRAMES_1_Y)
        set_manipulator_settings(D,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

        # Case 5: Requiremets met, don't care about above it
    def test_drag_axis_detent_case_05(self):
        #print("def test_drag_axis_detent_case_05(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_animation_data(C,T_2_FRAMES_1_Y)
        set_manipulator_settings(C,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    # Case 6: Has Show/Hide inbetween otherwise valid bones
    def test_drag_axis_detent_case_06(self):
        #print("def test_drag_axis_detent_case_06(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_sh",parent_info=ParentInfo(A)))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(B)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_H)
        set_animation_data(C,T_2_FRAMES_1_Y)

        set_manipulator_settings(C,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 7: Missing T, version 1
    def test_drag_axis_detent_case_07(self):
        #print("def test_drag_axis_detent_case_07(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(A)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)
    
    # Case 8: Missing T, version 2
    def test_drag_axis_detent_case_08(self):
        #print("def test_drag_axis_detent_case_08(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))

        set_animation_data(A,T_2_FRAMES_1_X)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 9: Missing T, version 3
    def test_drag_axis_detent_case_09(self):
        #print("def test_drag_axis_detent_case_09(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))

        set_animation_data(B,T_2_FRAMES_1_X)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 10: Missing T, version 4
    def test_drag_axis_detent_case_10(self):
        #print("def test_drag_axis_detent_case_10(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_t"))
        
        set_animation_data(A,T_2_FRAMES_1_X)

        set_manipulator_settings(A,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 11: Missing TT, version 1
    def test_drag_axis_detent_case_11(self):
        #print("def test_drag_axis_detent_case_11(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_n"))

        set_manipulator_settings(A,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 12: Missing TT, version 2
    def test_drag_axis_detent_case_12(self):
        #print("def test_drag_axis_detent_case_12(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_sh"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))

        set_animation_data(A,SHOW_ANIM_S)
        set_animation_data(A,SHOW_ANIM_H)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 13: Rotating Detent Bone
    def test_drag_axis_detent_case_13(self):
        #print("def test_drag_axis_detent_case_13(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_tr",parent_info=ParentInfo(A)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_Y)
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 14: Rotating Drag Axis Bone
    def test_drag_axis_detent_case_14(self):
        #print("def test_drag_axis_detent_case_14(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))

        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_X)

        set_manipulator_settings(B,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 15: R->T->T
    def test_drag_axis_detent_case_15(self):
        #print("def test_drag_axis_detent_case_15(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(A)))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(B,T_2_FRAMES_1_Y)
        set_animation_data(C,R_2_FRAMES_45_Y_AXIS)

        set_manipulator_settings(C,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    # Case 16: All requirements on same bone
    def test_drag_axis_detent_case_16(self):
        #print("def test_drag_axis_detent_case_16(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_tt"))

        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(A,T_2_FRAMES_1_Y)
        set_manipulator_settings(A,MANIP_DRAG_AXIS_DETENT,manip_props={'axis_detent_ranges':[AxisDetentRangeInfo(start=0.0,end=1.0,height=1.0)]})
 
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestBoneConfigurationsDragAxisDetent]) 
