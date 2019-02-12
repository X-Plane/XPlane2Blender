"""
This is the entry point for the 249 converter. Before you start poking around
make sure you read the available documentation! Don't assume anything!
"""
import collections
import copy
import enum
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers,
                                                    xplane_249_layer_props_converter,
                                                    xplane_249_manip_decoder,
                                                    xplane_249_workflow_converter)

_runs = 0
def do_249_conversion(context: bpy.types.Context, workflow_type: xplane_249_constants.WorkflowType):
    # TODO: Create log, similar to updater log

    #TODO: When we integrate with the updater, (adding 2.49 as a legacy version)
    # We can use that. Until then, we have this hack to keep unit testing going
    # Also, we should put it in the operator call instead so we can force it
    # rather than in the API itself
    global _runs
    if _runs > 0:
        return
    _runs += 1

    for scene in bpy.data.scenes:
        # Global settings
        scene.xplane.debug = True

        new_roots = xplane_249_workflow_converter.convert_workflow(scene, workflow_type)

        #TODO: converting too much per export mode? Will certainly be bad with scenes
        # Make the default material for new objects to be assaigned
        for armature in filter(lambda obj: obj.type == "ARMATURE", scene.objects):
            xplane_249_dataref_decoder.convert_armature_animations(scene, armature)

        for obj in filter(lambda obj: obj.type == "MESH", bpy.data.objects):
            xplane_249_manip_decoder.convert_manipulators(scene, obj)

        #--- Layer Properties (LODs, Layer Groups, Requires Wet/Dry, etc) -----
        if workflow_type == xplane_249_constants.WorkflowType.SKIP:
            pass
        elif (workflow_type == xplane_249_constants.WorkflowType.REGULAR
              or workflow_type == xplane_249_constants.WorkflowType.BULK):
            xplane_249_layer_props_converter.do_convert_layer_properties(scene, workflow_type, new_roots)
        else:
            assert False, "Unknown workflow type"
        #----------------------------------------------------------------------


