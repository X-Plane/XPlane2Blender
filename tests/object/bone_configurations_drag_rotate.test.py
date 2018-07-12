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

class TestBoneConfigurationsDragRotate(XPlaneTestCase):
    #Case 1: The Classic 
    def test_drag_rotate_case_01(self):
        #print("def test_drag_rotate_case_01(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_r"))
        set_manipulator_settings(A,MANIP_DRAG_ROTATE)
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 2: Leaf Not Animated
    def test_drag_rotate_case_02(self):
        #print("def test_drag_rotate_case_02(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 3: No-op Bones
    def test_drag_rotate_case_03(self):
        #print("def test_drag_rotate_case_03(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 4: Surrounding No-op bones
    def test_drag_rotate_case_04(self):
        #print("def test_drag_rotate_case_04(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Case 5: Requirements Met
    def test_drag_rotate_case_05(self):
        #print("def test_drag_rotate_case_05(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)

    #Failure
    #Case 6: N->SH->R
    def test_drag_rotate_case_06(self):
        #print("def test_drag_rotate_case_06(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 7: Wrong Order T->R
    def test_drag_rotate_case_07(self):
        #print("def test_drag_rotate_case_07(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 8: Wrong Order, version 2
    def test_drag_rotate_case_08(self):
        #print("def test_drag_rotate_case_08(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 9: R,S
    def test_drag_rotate_case_09(self):
        #print("def test_drag_rotate_case_09(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_rs"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,SHOW_ANIM_S)
        set_manipulator_settings(A,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 10: Missing R, version 1
    def test_drag_rotate_case_10(self):
        #print("def test_drag_rotate_case_10(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 11: Missing R, version 2
    def test_drag_rotate_case_11(self):
        #print("def test_drag_rotate_case_11(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_H)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

    #Case 12: Missing R, version 3
    def test_drag_rotate_case_12(self):
        #print("def test_drag_rotate_case_12(self):")
        create_initial_test_setup()
        set_xplane_layer(0,{'export_type':'cockpit'})

        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_nn"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        #bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(1)

runTestCases([TestBoneConfigurationsDragRotate])
