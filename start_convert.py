import argparse
import os
import sys

import bpy

# We can tell if we're launched with Blender or with CLI from sys.argv?
def _make_argparser():
    parser = argparse.ArgumentParser(
        description="Launches the XPlane2Blender Converter before the GUI loads",
        epilog="Invoke as blender my_file.blend -P start_convert.py -- --workflow-type {BULK or REGULAR} --project-type {AIRCRAFT or SCENERY}"
    )

    parser.add_argument(
        "--workflow-type",
        help="Tells the 2.49 converter which export script you used in 2.49",
        default="",
        nargs="?",
        choices={"BULK", "REGULAR"})

    parser.add_argument(
        "--project-type",
        help="Tells the 2.49 converter what type of project this is",
        default="AIRCRAFT",
        nargs="?",
        choices={"AIRCRAFT", "SCENERY"}
        )

    return parser


def main(argv=None) -> int:
    '''
    Return is exit code, 0 for good, anything else is an error
    '''

    exit_code = 0
    if argv is None:
        if "--" in sys.argv:
            argv = _make_argparser().parse_args(sys.argv[sys.argv.index("--")+1:])
        else:
            argv = _make_argparser().parse_args("")


    if argv.workflow_type:
        bpy.ops.xplane.do_249_conversion(
                project_type=argv.project_type,
                workflow_type=argv.workflow_type)

if __name__ == "__main__":
    main()
