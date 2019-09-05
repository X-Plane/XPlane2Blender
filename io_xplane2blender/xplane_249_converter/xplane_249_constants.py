'''Contains constants that the converter uses'''
import enum

# Per Scene, a "_01", "_02", "_03" gets appended
WORKFLOW_DEFAULT_ROOT_NAME = "249_ROOT"
DEFAULT_MATERIAL_NAME = "249"

# These are used by the material converter when making
# unique and derivative names during conversion
# and to "Hint" the user as to what happened

# Since all materials must have a different name,
# our algorithm's record keeping must eventually become a unique name.
#
# While it would have been great to develop some kind of global dictionary of
# converted materials and make the names at the end, we slid into
# stringification and testing for "_" + HINT_* in material names
# Therefore these must all be unique!
HINT_GLOBAL_BLEND_GLASS  = "bg"
HINT_GLOBAL_CKPIT_LIT    = "ck"
HINT_GLOBAL_NORM_MET     = "nm"
HINT_GLOBAL_NO_BLEND     = "nb"
HINT_GLOBAL_SHADOW_BLEND = "sb"
HINT_GLOBAL_SPECULAR     = "sp"
HINT_GLOBAL_TINT         = "tn"

HINT_TF_COLL           = "COLL"
HINT_PROP_SOLID_CAM    = "SOLID_CAM"

HINT_TF_INVIS          = "INVIS"
HINT_PROP_DRAW_DISABLE = "DRAW_DISABLE"

HINT_TF_LIGHT          = "LIGHT"

# Since LIT_LEVEL is not bool or enumeration
# we need to create seperate names for each unique material
# to prevent overwriting
# LIT_LEVEL may have an int immediately afterwards, starting at 1
# Ex: 249_COLL_LIT_LEVEL, 249_COLL_LIT_LEVEL1, 249_COLL_LIT_LEVEL2
# A .blend file has 3 materials with Solid Camera and 3 unique LIT_LEVEL values
HINT_PROP_LIT_LEVEL    = "LIT_LEVEL"

HINT_TF_SHADOW         = "SHADOW"

#TEX is always joined by _ALPHA or _CLIP
HINT_TF_TEX            = "TEX"
HINT_TF_TILES          = "TILES"

# Used to enable splitting by ".panel"
HINT_UV_PANEL          = "pn"

class ProjectType(enum.Enum):
    """
    What type of project this is, which sets the default
    export type in each root object.

    We don't support mixed Aircraft/Scenery project (if they ever existed)
    """
    AIRCRAFT = 0
    SCENERY = 1

class WorkflowType(enum.Enum):
    """
    What type of script or process was used to
    export the 2.49 file
    """
    SKIP = 0
    REGULAR = 1
    BULK = 2
