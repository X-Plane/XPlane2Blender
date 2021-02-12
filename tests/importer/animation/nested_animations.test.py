import inspect
import os
import sys
from itertools import product
from pathlib import Path
from typing import Tuple

import bpy

from io_xplane2blender import xplane_constants, xplane_import
from io_xplane2blender.importer import xplane_imp_parser
from io_xplane2blender.importer.xplane_imp_parser import import_obj
from io_xplane2blender.tests import *
from io_xplane2blender.tests.test_creation_helpers import (
    DatablockInfo,
    KeyframeInfo,
    ParentInfo,
)

__dirname__ = os.path.dirname(__file__)


def make_blend_file():
    """To be run from inside Blender"""
    test_creation_helpers.delete_everything(preserve_text_files=[Path(__file__).name])

    def make_root_collection(root_name: str) -> bpy.types.Collection:
        file_name = "test_" + root_name
        root_collection = test_creation_helpers.create_datablock_collection(
            root_name,
            bpy.context.scene,
        )
        root_collection.xplane.is_exportable_collection = True
        root_collection.xplane.layer.name = file_name
        return root_collection

    def make_db_ob(
        datablock_type: str,
        name: str,
        parent_info: Optional[ParentInfo],
        root_collection: bpy.types.Collection,
        location: Vector,
        animated: bool,
    ):
        assert datablock_type in {"MESH", "EMPTY"}

        db = DatablockInfo(
            datablock_type=datablock_type,
            name=f"{name}_" + ("Anim" if animated else "NonAnim"),
            parent_info=parent_info,
            collection=root_collection,
            location=location,
        )
        if datablock_type == "MESH":
            ob = test_creation_helpers.create_datablock_mesh(db, "eq-tri")
        elif datablock_type == "EMPTY":
            ob = test_creation_helpers.create_datablock_empty(db)

        if animated:
            test_creation_helpers.set_animation_data(
                ob,
                [
                    KeyframeInfo(
                        idx=i + 1,
                        dataref_path="sim/graphics/animation/sin_wave_2",
                        dataref_value=i,
                        location=location + Vector((0, i, 0)),
                    )
                    for i in range(2)
                ],
            )

    def nesting_test():
        """
        For the level tests we
        1 levels A_Anim->B_Anim
        2 levels A_Anim->B_Anim->C_Anim
        3 levels A_Anim->B_Anim->C_Anim->D_anim
        """
        leaf_anim = True
        for level_count in range(1, 4):
            root_collection = make_root_collection(
                f"{level_count}_level_nested_anim_leaf{'_anim' if leaf_anim else ''}",
            )
            for i, letter in enumerate(["A", "B", "C", "D"][: level_count + 1]):
                make_db_ob(
                    datablock_type="MESH",
                    name=letter,
                    parent_info=ParentInfo(root_collection.objects[-1])
                    if root_collection.objects
                    else None,
                    root_collection=root_collection,
                    location=Vector(
                        (level_count * 2 + (i * 3), level_count * 2 + (i * 3), 0)
                    ),
                    animated=True,
                )

    nesting_test()


make_blend_file()


class TestBlendFileNameCamelCaseNoPunctuation(XPlaneTestCase):
    def test_nested_files(self) -> None:
        files = [
            "test_1_level_nested_anim_leaf_anim",
            "test_2_level_nested_anim_leaf_anim",
            "test_3_level_nested_anim_leaf_anim",
        ]
        for filepath in [
            Path(__dirname__, "fixtures", f"{filename}") for filename in files
        ]:
            with self.subTest(filepath=filepath):
                import_obj(filepath)
        out = self.exportExportableRoot("")

        # TI Example of expecting a failure
        # TI (Note: This doesn't test specific errors)
        # self.assertLoggerErrors(1)

        # TI Example testing root object against fixture

        # TI or, with a set of OBJ directives
        # self.assertExportableRootExportEqualsFixture(
        #    filename[5:],
        #    os.path.join(__dirname__, "fixtures", f"{filename}.obj"),
        #    {""},
        #    filename,
        # )


# TI Same class name above, we only support one TestCase in runTestCases
# runTestCases([TestBlendFileNameCamelCaseNoPunctuation])
