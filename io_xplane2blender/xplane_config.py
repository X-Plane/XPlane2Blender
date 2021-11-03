# File: xplane_config.py
# Holds config variables that are used throughout the addon.
from typing import Tuple

import bpy

from io_xplane2blender import bl_info, xplane_constants

# We make a copy here so as not to cause a circular dependency in xplane_props and other places
CURRENT_ADDON_VERSION: Tuple[int, int, int] = bl_info["version"]

# The current build type, must be a member of XPlane2BlenderVersion.BUILD_TYPE
CURRENT_BUILD_TYPE = xplane_constants.BUILD_TYPE_ALPHA

# The current build type version, must be > 0
# if not BUILD_TYPE_DEV or BULD_TYPE_LEGACY
CURRENT_BUILD_TYPE_VERSION = 1

# The current data model version, incrementing every time xplane_constants, xplane_props, or xplane_updater
# changes. Builds earlier than 3.4.0-beta.5 have and a version of 0.
# When merging, take the higher data model version of the two branches and add one
CURRENT_DATA_MODEL_VERSION = 101

# The build number, hardcoded by the build script when there is one, otherwise it is xplane_constants.BUILD_NUMBER_NONE
CURRENT_BUILD_NUMBER = xplane_constants.BUILD_NUMBER_NONE


def getDebug() -> bool:
    return bpy.context.scene.xplane.debug


def setDebug(debug: bool) -> None:
    bpy.context.scene.xplane.debug = debug
