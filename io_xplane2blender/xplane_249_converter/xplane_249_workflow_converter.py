'''
This module handles converting a .blend contents that were set up
for use with Bulk Export or Export v8/v9 (aka Regular Export), so that
all necissary Root Objects are created with their properties filled in.
'''

import enum
import os
from typing import Callable, Dict, List, Optional, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter.xplane_249_constants import WorkflowType


def convert_workflow(scene: bpy.types.Scene, workflow_type: WorkflowType)->bool:
    print("Converting {} workflow for scene '{}'".format(workflow_type.name, scene.name))
    scene.xplane.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

    if workflow_type == WorkflowType.SKIP:
        return True
    elif workflow_type == WorkflowType.REGULAR:
        new_root = test_creation_helpers.create_datablock_empty(
            test_creation_helpers.DatablockInfo("EMPTY", "249_CONVERSION_ROOT")
        )
        new_root.xplane.layer.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        new_root.xplane.layer.isExportableRoot = True
        for ob in filter(lambda ob: ob.parent is None and ob != new_root, bpy.context.scene.objects):
            ob.parent = new_root
    elif workflow_type == WorkflowType.BULK:
        assert False, workflow_type.name + "Not implemented yet"
    else:
        assert False, workflow_type.name + "Not implemented yet"
    return True

