'''
This module handles converting a .blend contents that were set up
for use with Bulk Export or Export v8/v9 (aka Regular Export), so that
all necissary Root Objects are created with their properties filled in.
'''

import os
from typing import Callable, Dict, List, Optional, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import xplane_249_constants


def convert_workflow(scene: bpy.types.Scene, workflow_type: xplane_249_constants.WorkflowType)->bool:
    print("Converting {} workflow for scene '{}'".format(workflow_type.name, scene.name))
    scene.xplane.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

    if workflow_type == xplane_249_constants.WorkflowType.SKIP:
        return True
    elif workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        new_root = test_creation_helpers.create_datablock_empty(
            test_creation_helpers.DatablockInfo("EMPTY",
                                                xplane_249_constants.WORKFLOW_REGULAR_NEW_ROOT_NAME)
        )
        new_root.xplane.layer.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        new_root.xplane.layer.isExportableRoot = True
        for ob in filter(lambda ob: ob.parent is None and ob != new_root,
                         scene.objects):
            ob.parent = new_root
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        new_root = test_creation_helpers.create_datablock_empty(
            test_creation_helpers.DatablockInfo("EMPTY",
                                                xplane_249_constants.WORKFLOW_REGULAR_NEW_ROOT_NAME)
        )

        for ob in filter(lambda ob: ob.parent is None
                                    and ob.type == "EMPTY"
                                    and ob != new_root
                                    and ob.name.startswith("OBJ"),
                         scene.objects):
            ob.xplane.isExportableRoot = True
            try:
                ob.xplane.layer.name = ob.game.properties["rname"].value
            except KeyError:
                ob.xplane.layer.name = ob.name[3:]
    else:
        assert False, workflow_type.name + "Not implemented yet"
    return True
