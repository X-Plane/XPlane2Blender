import os

import bpy
from mathutils import Vector

from io_xplane2blender import xplane_config
from io_xplane2blender.tests import *
from io_xplane2blender.tests.test_creation_helpers import *

__dirname__ = os.path.dirname(__file__)


class TestBoneRemoveDatarefFCurve(XPlaneTestCase):
    def test_remove_dataref_removes_fcurve_and_renumbers(self):
        create_initial_test_setup()
        armature = create_datablock_armature(DatablockInfo("ARMATURE", "Armature"))
        bone = armature.data.bones[0]

        # Two datarefs on one bone, each with a keyframed value. Bone dataref
        # values are keyframed on the Armature *data* block
        for dataref_path in ["sim/test/first", "sim/test/second"]:
            set_animation_data(
                bone,
                [
                    KeyframeInfo(
                        idx=1,
                        dataref_path=dataref_path,
                        dataref_value=0.0,
                        location=Vector((0, 0, 0)),
                    ),
                    KeyframeInfo(
                        idx=2,
                        dataref_path=dataref_path,
                        dataref_value=1.0,
                        location=Vector((0, 0, 1)),
                    ),
                ],
                parent_armature=armature,
            )

        def dataref_fcurve_paths():
            return sorted(
                fcurve.data_path
                for fcurve in armature.data.animation_data.action.fcurves
                if ".xplane.datarefs[" in fcurve.data_path
            )

        self.assertEqual(
            dataref_fcurve_paths(),
            [
                'bones["Bone"].xplane.datarefs[0].value',
                'bones["Bone"].xplane.datarefs[1].value',
            ],
        )

        bpy.context.view_layer.objects.active = armature
        armature.data.bones.active = bone
        with bpy.context.temp_override(object=armature, bone=bone):
            self.assertEqual(bpy.ops.bone.remove_xplane_dataref(index=0), {"FINISHED"})

        self.assertEqual(
            [dref.path for dref in bone.xplane.datarefs], ["sim/test/second"]
        )
        # The removed dataref's F-Curve is gone, and the survivor was renumbered
        # to match its new position in the collection. Before, the F-Curve was
        # searched for on the Object's action and never found, so it stayed
        # behind as an orphan that XPlaneBone.collectAnimations trips over.
        self.assertEqual(
            dataref_fcurve_paths(), ['bones["Bone"].xplane.datarefs[0].value']
        )
        survivor = armature.data.animation_data.action.fcurves.find(
            'bones["Bone"].xplane.datarefs[0].value'
        )
        self.assertEqual(len(survivor.keyframe_points), 2)


runTestCases([TestBoneRemoveDatarefFCurve])
