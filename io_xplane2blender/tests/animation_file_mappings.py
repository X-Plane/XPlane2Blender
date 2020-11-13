"""
Contains the mapping between .blend files
and what is supposed to be tested in them
"""
from typing import Dict, Set

# A set of .blend file names to a dictionary of
# the .blend file's layer indexes and their fixtures to test
mappings: Set[Dict[str, Dict[int, str]]] = {
    "TestCase1": {
        0: "./fixtures/TestCase1/armature_rotation_arbitrary_axis.obj",
        1: "./fixtures/TestCase1/armature_rotation_twoaxis_3keys.obj",
        2: "./fixtures/TestCase1/armature_translation_arbitrary.obj",
        3: "./fixtures/TestCase1/object_translation.obj",
        4: "./fixtures/TestCase1/object_rotation_X_axis_angle.obj",
        5: "./fixtures/TestCase1/object_rotation_X_zyx_euler.obj",
        6: "./fixtures/TestCase1/object_rotation_X_zxy_euler.obj",
        7: "./fixtures/TestCase1/object_rotation_X_yzx_euler.obj",
        8: "./fixtures/TestCase1/object_rotation_X_yxz_euler.obj",
        9: "./fixtures/TestCase1/object_rotation_X_xzy_euler.obj",
        10: "./fixtures/TestCase1/object_rotation_X_xyz_euler.obj",
        11: "./fixtures/TestCase1/object_rotation_X_quaternion.obj",
        12: "./fixtures/TestCase1/object_rotation_Y_axis_angle.obj",
        13: "./fixtures/TestCase1/object_rotation_Y_zyx_euler.obj",
        14: "./fixtures/TestCase1/object_rotation_Y_zxy_euler.obj",
        15: "./fixtures/TestCase1/object_rotation_Y_yzx_euler.obj",
        16: "./fixtures/TestCase1/object_rotation_Y_yxz_euler.obj",
        17: "./fixtures/TestCase1/object_rotation_Y_xzy_euler.obj",
        18: "./fixtures/TestCase1/object_rotation_Y_xyz_euler.obj",
        19: "./fixtures/TestCase1/object_rotation_Y_quaternion.obj",
    },
    "TestCase2": {
        0: "./fixtures/TestCase2/object_rotation_Z_axis_angle.obj",
        1: "./fixtures/TestCase2/object_rotation_Z_zyx_euler.obj",
        2: "./fixtures/TestCase2/object_rotation_Z_zxy_euler.obj",
        3: "./fixtures/TestCase2/object_rotation_Z_yzx_euler.obj",
        4: "./fixtures/TestCase2/object_rotation_Z_yxz_euler.obj",
        5: "./fixtures/TestCase2/object_rotation_Z_xzy_euler.obj",
        6: "./fixtures/TestCase2/object_rotation_Z_xyz_euler.obj",
        7: "./fixtures/TestCase2/object_rotation_Z_quaternion.obj",
        8: "./fixtures/TestCase2/object_rotation_arbitrary_3key_axis_angle.obj",
        9: "./fixtures/TestCase2/object_rotation_arbitrary_3key_zyx_euler.obj",
        10: "./fixtures/TestCase2/object_rotation_arbitrary_3key_zxy_euler.obj",
        11: "./fixtures/TestCase2/object_rotation_arbitrary_3key_yzx_euler.obj",
        12: "./fixtures/TestCase2/object_rotation_arbitrary_3key_yxz_euler.obj",
        13: "./fixtures/TestCase2/object_rotation_arbitrary_3key_xzy_euler.obj",
        14: "./fixtures/TestCase2/object_rotation_arbitrary_3key_xyz_euler.obj",
        15: "./fixtures/TestCase2/object_rotation_arbitrary_3key_quaternion.obj",
    },
    "TestCase3": {
        0: "./fixtures/TestCase3/object_rotation_translation_arbitrary_yxz_euler.obj",
        1: "./fixtures/TestCase3/object_rotation_translation_arbitrary_xzy_euler.obj",
        2: "./fixtures/TestCase3/object_rotation_translation_arbitrary_xyz_euler.obj",
        3: "./fixtures/TestCase3/object_rotation_translation_arbitrary_quaternion.obj",
        16: "./fixtures/TestCase3/object_rotation_translation_arbitrary_axis_angle.obj",
        17: "./fixtures/TestCase3/object_rotation_translation_arbitrary_zyx_euler.obj",
        18: "./fixtures/TestCase3/object_rotation_translation_arbitrary_zxy_euler.obj",
        19: "./fixtures/TestCase3/object_rotation_translation_arbitrary_yzx_euler.obj",
    },
    "TestCase4": {
        0: "./fixtures/TestCase4/object_rotation_translation_orthogonal.obj",
        1: "./fixtures/TestCase4/armature_combined_rotation_translation.obj",
        2: "./fixtures/TestCase4/object_orthogonal_3keys.obj",
        10: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_axis_angle.obj",
        11: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_zyx_euler.obj",
        12: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_zxy_euler.obj",
        13: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_yzx_euler.obj",
        14: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_yxz_euler.obj",
        15: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_xzy_euler.obj",
        16: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_xyz_euler.obj",
        17: "./fixtures/TestCase4/object_orthagonal_2axis_3keys_quaternion.obj",
    },
    "TestCase5_nested_sets": {
        0: "./fixtures/TestCase5_nested_sets/armature_rot_nested_armature_rot.obj",
        1: "./fixtures/TestCase5_nested_sets/armature_rot_nested_armature_rot_3keys.obj",
        2: "./fixtures/TestCase5_nested_sets/armature_locrot_nested_armature_locrot.obj",
        3: "./fixtures/TestCase5_nested_sets/object_trans_ortho_nested_object_trans_ortho.obj",
        4: "./fixtures/TestCase5_nested_sets/object_trans_arbitrary_nested_object_trans_arbitrary.obj",
        5: "./fixtures/TestCase5_nested_sets/armature_locrot_whereOBJ_trans_rotation_single_axis.obj",
        6: "./fixtures/TestCase5_nested_sets/armature_locrot_whereOBJ_trans_rotation_arbitrary.obj",
        7: "./fixtures/TestCase5_nested_sets/mega_nested_mega.obj",
    },
    "TestCase6_scaling_rot": {
        0: "./fixtures/TestCase6_scaling_rot/TestCase6_scaling_rot.obj"
    },
    "TestCase7_scaling_rotloc": {
        0: "./fixtures/TestCase7_scaling_rotloc/TestCase7_scaling_rotloc.obj"
    },
    "TestCase8_bone_optimization": {
        0: "./fixtures/TestCase8_bone_optimization/TestCase8_rot.obj",
        1: "./fixtures/TestCase8_bone_optimization/TestCase8_loc.obj",
        2: "./fixtures/TestCase8_bone_optimization/TestCase8_rot_loc.obj",
        3: "./fixtures/TestCase8_bone_optimization/TestCase8_static.obj",
    },
    "TestCase9_keyframe_loops": {
        0: "./fixtures/TestCase9_keyframe_loops/TestCase9_loop_bone.obj",
        1: "./fixtures/TestCase9_keyframe_loops/TestCase9_loop_arm.obj",
        2: "./fixtures/TestCase9_keyframe_loops/TestCase9_loop_arm_bone.obj",
        3: "./fixtures/TestCase9_keyframe_loops/TestCase9_loop_none.obj",
    },
}
