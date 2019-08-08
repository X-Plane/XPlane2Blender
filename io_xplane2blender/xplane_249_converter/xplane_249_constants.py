'''Contains constants that the converter uses'''
import enum

# Per Scene, a "_01", "_02", "_03" gets appended
WORKFLOW_DEFAULT_ROOT_NAME = "249_ROOT"
DEFAULT_MATERIAL_NAME = "249"

# These are used by the material converter when making
# unique and derivative names during conversion
# and to "Hint" the user as to what happened
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
HINT_TF_LIT_LEVEL      = "LIT_LEVEL"
HINT_TF_SHADOW         = "SHADOW"
HINT_TF_TEX            = "TEX"
HINT_TF_TILES          = "TILES"

class WorkflowType(enum.Enum):
    '''
    What type of script or process was used to
    export the 2.49 file
    '''
    SKIP = 0
    REGULAR = 1
    BULK = 2
