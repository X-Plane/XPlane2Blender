'''Contains constants that the converter uses'''
import enum

# Per Scene, a "_01", "_02", "_03" gets appended
WORKFLOW_DEFAULT_ROOT_NAME = "249_ROOT"

class WorkflowType(enum.Enum):
    '''
    What type of script or process was used to
    export the 2.49 file
    '''
    SKIP = 0
    REGULAR = 1
    BULK = 2
