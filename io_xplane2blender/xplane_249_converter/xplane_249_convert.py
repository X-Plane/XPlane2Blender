"""
This is the entry point for the 249 converter. Before you start poking around
make sure you read the available documentation! Don't assume anything!
"""
import ast
import collections
import copy
import enum
import os
import re
import sys
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy

from io_xplane2blender import xplane_constants, xplane_helpers
from io_xplane2blender.xplane_helpers import logger
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_249_converter import (xplane_249_constants,
                                                    xplane_249_dataref_decoder,
                                                    xplane_249_helpers,
                                                    xplane_249_layer_props_converter,
                                                    xplane_249_light_converter,
                                                    xplane_249_manip_decoder,
                                                    xplane_249_material_converter,
                                                    xplane_249_texture_converter,
                                                    xplane_249_workflow_converter)

_converted_objects = set() # type: Set[bpy.types.Object]
_runs = 0
def do_249_conversion(
        context: bpy.types.Context,
        project_type: xplane_249_constants.ProjectType,
        workflow_type: xplane_249_constants.WorkflowType):
    # Since the updater adds the version on load (because
    # we want to save that vital information ASAP,
    # possible - the potential level of bugs makes it immediatly
    # we can't use it here.
    #
    # Instead we check if the file hasn't been saved
    # and re-opened in 2.79.0 yet, and prevent it from
    # re-running multiple times after it is open.
    #
    # - If you never save it, you'll have to convert again.
    # - If you save it without converting it, you've destroyed the ability to
    # convert it.
    # - If you converter it and try to run it again, even in the same session, it'll fail
    # (except by changing _runs or the source code - and only those smart enough
    # to know what danger their in will do that. Right, dear reader?)
    global _runs
    if bpy.data.version == (2, 49, 2) and _runs:
        print("File already converted, will not convert twice")
        return
    _runs += 1


    def run_pre_convert_fixes()->bool:
        """
        Returns True if fixes were run, regardless of any actual effect
        """
        logger.clear()
        logger.addTransport(
            xplane_helpers.XPlaneLogger.InternalTextTransport(
                xplane_249_constants.LOG_NAME +", Pre-Convert Fixes"),
                xplane_constants.LOGGER_LEVELS_ALL
            )
        logger.addTransport(xplane_helpers.XPlaneLogger.ConsoleTransport())
        #--- FixDroppedActions -----------------------------------------------
        logger.info("", "raw")
        logger.info(
                "Fix Dropped Actions\n"
                "--------------------------------------------------",
                context="raw")
        try:
            text_block = bpy.data.texts["FixDroppedActions.py"]
        except KeyError:
            logger.info("No FixDroppedActions.py text block found, no fixes applied")
            return False
        else:
            logger.info("Fixing Dropped Actions recorded in FixDroppedActions.py")

            script = "".join([
                    line.body
                    for line in filter(lambda l: not l.body.startswith("#"), text_block.lines)
                    ])

            try:
                actions_and_users = ast.literal_eval(script)
            except (IndexError, SyntaxError, ValueError) as e:
                logger.warn("Contents of {} improperly formatted.".format(xplane_249_constants.FIX_SCRIPT_DROPPED_ACTIONS)
                            + "Run 'X-Plane Pre-Conversion Fixes' again and be careful if editing")
            else:
                actions_will_fix = {
                        action_name: users
                        for action_name, users in actions_and_users.items()
                        if action_name in bpy.data.actions
                    }
                unknown_actions = actions_and_users.keys() - actions_will_fix.keys()
                if unknown_actions:
                    logger.warn("Found unknown Actions '{}', re-run {}".format(unknown_actions, xplane_249_constants.FIX_SCRIPT))
                else:
                    for action_name, users in actions_will_fix.items():
                        action = bpy.data.actions[action_name]
                        users_will_fix = {name for name in users if name in bpy.data.objects}
                        unknown_users = set(users) - users_will_fix
                        if unknown_users:
                            logger.warn("Found unknown Users '{}', re-run {}".format(unknown_users, xplane_249_constants.FIX_SCRIPT))
                            continue
                        for user in users_will_fix:
                            user_obj = bpy.data.objects[user]
                            if not user_obj.animation_data:
                                user_obj.animation_data_create()
                            user_obj.animation_data.action = action
            # TODO: If we ever get more fix scripts,
            # we'll change this to a set of script names ran
            # - Ted 9/18/2019
            return True
        #----------------------------------------------------------------------
    ran_fixes = run_pre_convert_fixes()

    for i, scene in enumerate(bpy.data.scenes, start=1):
        logger.clear()
        logger.addTransport(xplane_helpers.XPlaneLogger.InternalTextTransport(xplane_249_constants.LOG_NAME + ", " + scene.name), xplane_constants.LOGGER_LEVELS_ALL)
        logger.addTransport(xplane_helpers.XPlaneLogger.ConsoleTransport())
        logger.info("", context="raw")
        logger.info("Converting scene '{}' using a {} workflow"
                    .format(scene.name, workflow_type.name))
        # This line will NOT WORK when the GUI is open,
        # TODO: I sure as hell hope it works on Mac/Linux too!
        bpy.context.window.screen.scene = scene
        # Global settings
        scene.xplane.debug = True

        #--- Making New Roots-------------------------------------------------
        new_roots = xplane_249_workflow_converter.convert_workflow(scene, project_type, workflow_type)
        if workflow_type == xplane_249_constants.WorkflowType.REGULAR:
            new_roots[0].name += "_{:02d}".format(i)
        if new_roots:
            logger.info("New Root Object{}: {}"
                    .format(
                        "s" if len(new_roots) > 1 else "",
                        ", ".join(root.name for root in sorted(new_roots, key=lambda r: r.name))))
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
                    "--------------------------------------------------".format(scene.name),
                    context="raw")
        # Make the default material for new objects to be assaigned
        for armature in filter(lambda obj: obj not in _converted_objects and obj.type == "ARMATURE", scene.objects):
            _converted_objects.update(xplane_249_dataref_decoder.convert_armature_animations(scene, armature))

        logger.info(
            "NEXT STEPS: Check for missing or incorrect animations"
            + "" if ran_fixes else ", especially since FixDroppedActions.py was not run."
            + "\n"
            + "If many are missing, check that io_xplane2blender/resources/DataRefs.txt is the same as what was used with this file in Blender 2.49")
        #print("Converted objects", _converted_objects)

        #print("Converting Any Manipulators In Scene '{}'".format(scene.name))
        for obj in scene.objects:
            converted_manipulator = xplane_249_manip_decoder.convert_manipulators(scene, obj)
            if converted_manipulator:
                try:
                    #TODO: Slow! It would be better to do this at the end, starting from the
                    # top down, searching so we don't waste time on things without a root object!
                    root_object = xplane_249_helpers.find_parent_root_object(obj)
                except Exception as e:
                    #print(e)
                    pass
                else:
                    root_object.xplane.layer.export_type = xplane_constants.EXPORT_TYPE_COCKPIT

        logger.info("", "raw")
        logger.info("Converting Any Lights In Scene '{}'\n"
                    "--------------------------------------------------".format(scene.name),
                    context="raw")
        for root in new_roots:
            #TODO: ALSO! This breaks if there are no new roots becaues of SKIP. SKIP should only affect workflow
            xplane_249_light_converter.convert_lights(scene, workflow_type, root)
            xplane_249_material_converter.convert_materials(scene, workflow_type, root)
            xplane_249_texture_converter.convert_textures(scene, workflow_type, root)


        logger.info("", "raw")
        logger.warn("NEXT-STEPS: Check the Export Type of {}".format(", ".join([root.name for root in new_roots])))
