'''Contains constants that the converter uses'''
import enum

WORKFLOW_REGULAR_NEW_ROOT_NAME = "249_CONVERSION_ROOT"

class WorkflowType(enum.Enum):
    '''
    What type of script or process was used to
    export the 2.49 file
    '''
    SKIP = 0
    REGULAR = 1
    BULK = 2
