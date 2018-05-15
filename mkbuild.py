import argparse
import os
import sys

import re


#from io_xplane2blender.xplane_helpers import VerStruct

def _make_parser()->argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Change the version number information of XPlane2Blender and automatically tests and packages the folder')
    version_group = parser.add_argument_group("Addon Version")
    version_group.add_argument("--major",
            type=int,
            help="Set the major version (very unlikely you need this). Actually changes xplane_config.py file")
    version_group.add_argument("-m","--minor",
            type=int,
            help="Set the minor version")
    version_group.add_argument("-r","--revision",
            type=int,
            help="Set the revision version")
    build_metadata_group = parser.add_argument_group("Build Metadata")
    build_metadata_group.add_argument("-t","--build-type",
            type=str,
            choices=["dev","alpha","beta","rc"],
            help="Set the build type")
    build_metadata_group.add_argument("--data-model-number",
            type=int,
            help="Sets the data model number to a number of your choice (which is not recommended!)"\
                 " Overrides auto-increment from use of version flags")
    build_metadata_group.add_argument("--build-number",
            type=int,
            help="Sets the build number to a number of your choice, instead of the current time in UTC."\
                 " Overrides auto-increment from use of version flags")
    parser.add_argument("--save-version-information",
            help="MutateInstead of ")

    test_args_group = parser.add_argument_group(
            "Options related to running the test suite before saving the build."\
            " The build number string is always tested. When conflicted, more tests are chosen over less")
    test_args_group.add_argument("--test-level",
            type=str,
            default = "all",
            choices = ["none","fast","all"],
            help="What parts of the test suite to run. --filter in --test-args will overwrite this")

    test_args_group.add_argument("--no-zip",
            action="store_true",
            help="Does not write zip. Useful for changing version numbers easily")

    parser.add_argument("DESTINATION",
            type=str,
            default="./builds",
            help="Destination for the zip file. Folders will be created if it does not exist, files will be overwritten")
    parser.add_argument("TEST_ARGS",
            help="Arguments to pass into test suite")

    return parser

#parser.parse_args()

def main(argv=None):
    exit_code = 0
    if argv is None:
        argv = _make_parser().parse_args()

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
