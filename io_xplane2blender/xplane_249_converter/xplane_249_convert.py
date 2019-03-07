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
from xplane_helpers import logger
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers,
                                                    xplane_249_layer_props_converter,
                                                    xplane_249_manip_decoder,
                                                    xplane_249_workflow_converter)

_converted_objects = set() # type: Set[bpy.types.Object]
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

    logger.clear()
    logger.addTransport(xplane_helpers.XPlaneLogger.InternalTextTransport('Converter Log'), xplane_constants.LOGGER_LEVELS_ALL)
    logger.addTransport(xplane_helpers.XPlaneLogger.ConsoleTransport())

    for i, scene in enumerate(bpy.data.scenes, start=1):
        logger.info("Converting scene '{}' using a {} workflow"
                    .format(scene.name, workflow_type.name))
        bpy.context.window.screen.scene = scene
        # Global settings
        scene.xplane.debug = True

        #--- Making New Roots-------------------------------------------------
        new_roots = xplane_249_workflow_converter.convert_workflow(scene, workflow_type)

        if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
            new_roots[0].name += "_{:02d}".format(i)
        #---------------------------------------------------------------------

        #--- Layer Properties (LODs, Layer Groups, Requires Wet/Dry, etc) -----
        if workflow_type == xplane_249_constants.WorkflowType.SKIP:
            logger.warn("Skipping converting global OBJ settings, project may not export correctly\n"
                        "NEXT STEP: Set up .blend file for Layers or Root Objects mode and fill out OBJ settings")
        elif (workflow_type == xplane_249_constants.WorkflowType.REGULAR
              or workflow_type == xplane_249_constants.WorkflowType.BULK):
            xplane_249_layer_props_converter.do_convert_layer_properties(scene, workflow_type, new_roots)
        else:
            assert False, "Unknown workflow type"
        #----------------------------------------------------------------------

        logger.info("", "raw")
        logger.info("Converting Any Animations In Scene '{}'\n"
                    "--------------------------------------------------".format(scene.name))
        # Make the default material for new objects to be assaigned
        for armature in filter(lambda obj: obj not in _converted_objects and obj.type == "ARMATURE", scene.objects):
            _converted_objects.update(xplane_249_dataref_decoder.convert_armature_animations(scene, armature))

        if _converted_objects:
            logger.info("\nNEXT STEP: Check for missing or incorrect animations. See XPlaneDuplicateActionDatablocks.py for more")
        #print("Converted objects", _converted_objects)


        logger.info("", "raw")
        logger.info("Converting Any Manipulators In Scene '{}'\n"
                    "--------------------------------------------------".format(scene.name))
        for obj in scene.objects:
            converted_manipulator = xplane_249_manip_decoder.convert_manipulators(scene, obj)
            #if converted_manipulator:
                #print("root hint: COCKPIT")

        logger.info("", "raw")
        logger.warn("NEXT-STEPS: Check the Export Type of {}".format(','.join([root.name for root in new_roots])))
