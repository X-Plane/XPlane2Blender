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
        KeyframeInfo(1, "sim/cockpit2/engine/actuators/throttle_ratio_all",
            0.0,
            rotation=(0,0,0)),
        KeyframeInfo(2, "sim/cockpit2/engine/actuators/throttle_ratio_all",
            1.0,
            rotation=(0,45,0)))

T_2_FRAMES_1_X = (
        KeyframeInfo(1,"sim/cockpit2/engine/actuators/throttle_ratio_all",
            0.0,
            location=(0,0,0)),
        KeyframeInfo(2,"sim/cockpit2/engine/actuators/throttle_ratio_all",
            1.0,
            location=(1,0,0)))

SHOW_ANIM_S = (
        KeyframeInfo(1,"show_hide_dataref", 0.0, xplane_constants.ANIM_TYPE_SHOW),
        )

SHOW_ANIM_FAKE_T = (
        KeyframeInfo(1,"none", 0.0, location=(0,0,0)),
        KeyframeInfo(2,"none", 1.0, location=(0,0,0)),
        )
  
class TestBoneConfigurationsDragRotate(XPlaneTestCase):
    '''
    #case 1: The Classic 
    def test_drag_rotate_case_1(self):
        create_initial_test_setup()

        #This is also the only bone
        bone_r = create_datablock_mesh(DatablockInfo("MESH",name="bone_r"))
        set_manipulator_settings(bone_r,MANIP_DRAG_ROTATE)
        set_animation_data(bone_r,R_2_FRAMES_45_Y_AXIS)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")

    #Case 2: Leaf Not Animated
    def test_drag_rotate_case_2(self):
        create_initial_test_setup()
        tests.test_creation_helpers.create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(A)))
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")
        #B = make_bone("n")
        #link_parents([B,A])
        pass

    #Case 3: No-op Bones
    def test_drag_rotate_case_3(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(A)))
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("r")
        #B = make_bone("n")
        #C = make_bone("n")
        #D = make_bone("n")
        #link_parents([D,CB,A])

    #Case 4: Surrounding No-op bones
    def test_drag_rotate_case_4(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n"))
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_empty(DatablockInfo("EMPTY",name="bone_n",parent_info=ParentInfo(B)))
        D = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(C)))
        set_manipulator_settings(D,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("n")
        #B = make_bone("r")
        #C = make_bone("n")
        #D = make_bone("n")
        #link_parents([D,C,B,A])

    #Case 5: Requirements Met
    def test_drag_rotate_case_5(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_rt"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,T_2_FRAMES_1_X)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(0)
        #A = make_bone("rt")
        #B = make_bone("r")
        #C = make_bone("n")
        #link_parents([C,B,A])
#
    #Failure
    #Case 6: N->SH->R
    def test_drag_rotate_case_6(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        B = create_datablock_empty(DatablockInfo("EMPTY",name="bone_s",parent_info=ParentInfo(A)))
        set_animation_data(B,SHOW_ANIM_S)
        set_animation_data(B,SHOW_ANIM_FAKE_T)
        C = create_datablock_mesh(DatablockInfo("MESH",name="bone_n",parent_info=ParentInfo(B)))
        set_manipulator_settings(C,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("s")
        #C = make_bone("n")
        #link_parents([C,B,A])

    #Case 7: Wrong Order T->R
    def test_drag_rotate_case_7(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_t",parent_info=ParentInfo(A)))
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("t")
        #link_parents([B,A])

    #Case 8: Wrong Order, version 2
    def test_drag_rotate_case_8(self):
        create_initial_test_setup()
        A = create_datablock_empty(DatablockInfo("EMPTY",name="bone_r"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)

        B = create_datablock_mesh(DatablockInfo("MESH",name="bone_rt",parent_info=ParentInfo(A)))
        set_animation_data(B,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(B,T_2_FRAMES_1_X)
        set_manipulator_settings(B,MANIP_DRAG_ROTATE)

        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("r")
        #B = make_bone("rt")
        #link_parents([B,A])

        #'''
    #Case 9: R,S
    def test_drag_rotate_case_9(self):
        create_initial_test_setup()
        A = create_datablock_mesh(DatablockInfo("MESH",name="bone_rs"))
        set_animation_data(A,R_2_FRAMES_45_Y_AXIS)
        set_animation_data(A,SHOW_ANIM_S)
        set_animation_data(A,SHOW_ANIM_FAKE_T)
        set_manipulator_settings(A,MANIP_DRAG_ROTATE)
        bpy.ops.wm.save_mainfile(filepath=__dirname__+"/config_blends/{}.blend".format(inspect.stack()[0][3]))
        out  = self.exportLayer(0)
        self.assertLoggerErrors(2)
        #A = make_bone("rs")

    '''
    #Case 10: Missing R, version 1
    def test_drag_rotate_case_10(self):
        A = make_bone("t")
        B = make_bone("n")
        link_parents([B,A])

    #Case 11: Missing R, version 2
    def test_drag_rotate_case_11(self):
        A = make_bone("n")
        B = make_bone("s")
        link_parents([B,A])

    #Case 12: Missing R, version 3
    def test_drag_rotate_case_12(self):
        A = make_bone("n")
        B = make_bone("n")
        link_parents([B,A])

    def test_usually_the_file_name_snake_case(self):
        #TI Example of whitebox testing
        #from io_xplane2blender.xplane_types import xplane_
        #access object using bpy.data.objects
        # use constructor for xplane_type, use methods
        #TI
        #TI Testing the results of an export without a fixture
        #out  = self.exportLayer(0)

        #TI Example of expecting a failure
        #self.assertLoggerErrors(1)

        #TI Test layer against fixture
        # Note, I would recommend layout out your layers, tests, and names so they are all in order.
        # It makes everything much easier
        #
        #filename = inspect.stack()[0][3]

        #self.assertLayerExportEqualsFixture(
        #    0, os.path.join(__dirname__, 'fixtures', filename + '.obj'),
        #    filename,
        #    filterLines
        #)

#TI Class name above
'''
runTestCases([TestBoneConfigurationsDragRotate])
