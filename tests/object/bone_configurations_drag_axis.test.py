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

class TestBoneConfigurationsDragAxis(XPlaneTestCase):
    #Case 1: The Classic 
    def test_drag_axis_case_01(self):
        #print("def test_drag_axis_case_01(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_t"))
        set_manipulator_settings(A,MANIP_DRAG_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 2: Leaf Not Animated
    def test_drag_axis_case_02(self):
        #print("def test_drag_axis_case_02(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_AXIS)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 3: No-op Bones
    def test_drag_axis_case_03(self):
        #print("def test_drag_axis_case_03(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_AXIS)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 4: Surrounding No-op bones
    def test_drag_axis_case_04(self):
        #print("def test_drag_axis_case_04(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        set_animation_data(B,T_2_FRAMES_1_X)
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_AXIS)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 5: Requirements Met
    def test_drag_axis_case_05(self):
        #print("def test_drag_axis_case_05(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t",parent_info=ParentInfo(A)))
        set_animation_data(B,T_2_FRAMES_1_X)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_AXIS)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Failure
    #Case 6: N->SH->T
    def test_drag_axis_case_06(self):
        #print("def test_drag_axis_case_06(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1) #currently show/hide misses "specific parent" error

    #Case 7: Wrong Order R->T
    def test_drag_axis_case_07(self):
        #print("def test_drag_axis_case_07(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_manipulator_settings(B,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 8: Rotate and Translation
    def test_drag_axis_case_08(self):
        #print("def test_drag_axis_case_08(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        set_manipulator_settings(A,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 9: T,S/H
    def test_drag_axis_case_09(self):
        #print("def test_drag_axis_case_09(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_tsh"))
        set_animation_data(A,T_2_FRAMES_1_X)
        set_animation_data(A,SHOW_ANIM_S)
        set_animation_data(A,SHOW_ANIM_H)
        set_manipulator_settings(A,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 10: Missing T, version 1
    def test_drag_axis_case_10(self):
        #print("def test_drag_axis_case_10(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 11: Missing T, version 2
    def test_drag_axis_case_11(self):
        #print("def test_drag_axis_case_11(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_sh",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_H)
        set_manipulator_settings(B,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 12: Missing T, version 3
    def test_drag_axis_case_12(self):
        #print("def test_drag_axis_case_12(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_nn"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_AXIS,manip_props={'autodetect_settings_opt_in':True})
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestBoneConfigurationsDragAxis])
