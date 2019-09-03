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


def convert_workflow(scene: bpy.types.Scene,
        project_type: xplane_249_constants.ProjectType,
        workflow_type: xplane_249_constants.WorkflowType)->List[bpy.types.Object]:
    """
    Converts 2.49 workflow to 2.7x workflow, automatically filling in XPlaneLayer data.

    Returns by WorkflowType:
    Skip:
        An Empty List
    Regular:
        A list of one containing new all encompessing new parent root
    Bulk:
        A list of identified root objects
    """
    #print("Converting {} workflow for scene '{}'".format(workflow_type.name, scene.name))
    scene.xplane.exportMode = xplane_constants.EXPORT_MODE_ROOT_OBJECTS

    if workflow_type == xplane_249_constants.WorkflowType.SKIP:
        return []
    elif workflow_type == xplane_249_constants.WorkflowType.REGULAR:
        new_root = test_creation_helpers.create_datablock_empty(
            test_creation_helpers.DatablockInfo("EMPTY",
                                                xplane_249_constants.WORKFLOW_DEFAULT_ROOT_NAME)
        )
        new_root.xplane.layer.export_type = project_type.name.lower()
        if len(bpy.data.scenes) == 1:
            new_root.xplane.layer.name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        else:
            new_root.xplane.layer.name = scene.name
        new_root.xplane.isExportableRoot = True
        for ob in filter(lambda ob: ob.parent is None and ob != new_root,
                         scene.objects):
            ob.parent = new_root
        return [new_root]
    elif workflow_type == xplane_249_constants.WorkflowType.BULK:
        new_roots = list(filter(lambda ob: ob.parent is None
                                           and ob.type == "EMPTY"
                                           and ob.name.startswith("OBJ"),
                                scene.objects))
        for ob in new_roots:
            ob.xplane.isExportableRoot = True
            try:
                layer_name  = ob.game.properties["rname"].value
            except KeyError:
                layer_name = ob.name[3:]
            try:
                layer_name = ob.game.properties["path"].value + "/" + layer_name
            except KeyError:
                pass
            ob.xplane.layer.export_type = project_type.name.lower()
            ob.xplane.layer.name = layer_name

        return new_roots
    else:
        assert False, workflow_type.name + "Not implemented yet"
