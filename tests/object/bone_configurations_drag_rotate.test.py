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

#def filterLines(line):
    #return isinstance(line[0],str) and\
            #("OBJ_DIRECTIVE" in line[0] or\


R_2_FRAMES_45_Y_AXIS = (
        KeyframeInfo(
            idx=1,
            dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
            dataref_value=0.0,
            rotation=(0,0,0)),
        KeyframeInfo(
            idx=2,
            dataref_path="sim/cockpit2/engine/actuators/throttle_ratio_all",
            dataref_value=1.0,
            rotation=(0,45,0)))

T_2_FRAMES_1_X = (
        KeyframeInfo(
            idx=1,
            dataref_path="sim/graphics/animation/sin_wave_2",
            dataref_value=0.0,
            location=(0,0,0)),
        KeyframeInfo(
            idx=2,
            dataref_path="sim/graphics/animation/sin_wave_2",
            dataref_value=1.0,
            location=(1,0,0)))

SHOW_ANIM_S = (
        KeyframeInfo(
            idx=1,
            dataref_path="show_hide_dataref",
            dataref_show_hide_value_1=0.0,
            dataref_show_hide_value_2=100.0,
            dataref_anim_type=ANIM_TYPE_SHOW),
        )

SHOW_ANIM_H = (
        KeyframeInfo(
            idx=1,
            dataref_path="show_hide_dataref",
            dataref_show_hide_value_1=100.0,
            dataref_show_hide_value_2=200.0,
            dataref_anim_type=ANIM_TYPE_SHOW),
        )

SHOW_ANIM_FAKE_T = (
        KeyframeInfo(
            idx=1,
            dataref_path="none",
            dataref_value=0.0,
            location=(0,0,0)),
        KeyframeInfo(
            idx=2,
            dataref_path="none",
            dataref_value=1.0,
            location=(0,0,0)),
        )
  
class TestBoneConfigurationsDragRotate(XPlaneTestCase):
    #case 1: The Classic 
    def test_drag_rotate_case_01(self):
        create_initial_test_setup()

        #This is also the only bone
        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_r"))
        set_manipulator_settings(A,MANIP_DRAG_ROTATE)
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")

    #Case 2: Leaf Not Animated
    def test_drag_rotate_case_02(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")
        #B = make_bone("n")
        #link_parents([B,A])
        pass

    #Case 3: No-op Bones
    def test_drag_rotate_case_03(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")
        #B = make_bone("n")
        #C = make_bone("n")
        #D = make_bone("n")
        #link_parents([D,CB,A])

    #Case 4: Surrounding No-op bones
    def test_drag_rotate_case_04(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("n")
        #B = make_bone("r")
        #C = make_bone("n")
        #D = make_bone("n")
        #link_parents([D,C,B,A])

    #Case 5: Requirements Met
    def test_drag_rotate_case_05(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("rt")
        #B = make_bone("r")
        #C = make_bone("n")
        #link_parents([C,B,A])

    #Failure
    #Case 6: N->SH->R
    def test_drag_rotate_case_06(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        #set_animation_data(B,SHOW_ANIM_FAKE_T)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("s")
        #C = make_bone("n")
        #link_parents([C,B,A])

    #Case 7: Wrong Order T->R
    def test_drag_rotate_case_07(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("t")
        #link_parents([B,A])

    #Case 8: Wrong Order, version 2
    def test_drag_rotate_case_08(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("rt")
        #link_parents([B,A])

    #Case 9: R,S
    def test_drag_rotate_case_09(self):
        create_initial_test_setup()
        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_rs"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,SHOW_ANIM_S)
        #set_animation_data(A,SHOW_ANIM_FAKE_T)
        set_manipulator_settings(A,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("rs")

    #Case 10: Missing R, version 1
    def test_drag_rotate_case_10(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_t"))
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("t")
        #B = make_bone("n")
        #link_parents([B,A])

    #Case 11: Missing R, version 2
    def test_drag_rotate_case_11(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_H)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("n")
        #B = make_bone("s")
        #link_parents([B,A])

    #Case 12: Missing R, version 3
    def test_drag_rotate_case_12(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_nn"))
        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("n")
        #B = make_bone("n")
        #link_parents([B,A])

runTestCases([TestBoneConfigurationsDragRotate])
