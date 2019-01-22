'''Contains constants that the converter uses'''
import enum


class WorkflowType(enum.Enum):
    '''
    What type of script or process was used to
    export the 2.49 file
    '''
    SKIP = 0
    REGULAR = 1
    BULK    = 2
