import argparse
import os
import re
import shutil
import sys
from typing import List, Optional, Tuple

from collections import namedtuple

#from io_xplane2blender.xplane_constants import *

def _make_parser()->argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Creates a clean zip build with any arbitrary build info.'\
            ' It can also change xplane_config.py, create git tags, and incorporate the test suite.\n'\
            'To run the test you\'ll need to have "another addon" called io_xplane2blender_build available to Blender.')

    version_group = parser.add_argument_group("Addon Version")
    version_group.add_argument("--major",
            type=int,
            help="Override the Blender major version (very unused!)")
    version_group.add_argument("--minor",
            type=int,
            help="Override the Blender minor version")
    version_group.add_argument("--revision",
            type=int,
            help="Override the Blender revision version")

    build_metadata_group = parser.add_argument_group("Build Metadata")
    build_metadata_group.add_argument("--build-type",
            type=str,
            choices=["dev","alpha","beta","rc"],
            help="Override CURRENT_BUILD_TYPE")
    build_metadata_group.add_argument("--data-model-number",
            type=int,
            help="Override CURRENT_DATA_MODEL_VERSION with an arbitrary number (dangerous, only increment!)")
    build_metadata_group.add_argument("--build-number",
            type=int,
            help="Overrides use of current time in UTC")

    parser.add_argument("--make-overrides-permanent",
            help="Changes source files to match inputs")

    parser.add_argument("--clean",
            action="store_true",
            help="Cleans files and folders created during the build process")

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

    parser.add_argument("--build_folder",
            type=str,
            default="./builds",
            help="Destination for the zip file. Folders will be created if it does not exist, files will be overwritten")

    parser.add_argument("TEST_ARGS",
            default="",
            help="Arguments to pass into test suite")

    return parser

#parser.parse_args()

class VerData():
    '''A small completely mutable version of XPlaneHelper's VerStruct class (so we don't have to worry about importing bpy without Blender'''
    def __init__(self,
            addon_version:Optional[Tuple[int,int,int]]=None,
            build_type:Optional[str]=None,
            build_type_version:Optional[int]=None,
            data_model_version:Optional[int]=None,
            build_number:Optional[str]=None):
        self.addon_version      = (addon_version)  #if addon_version      is not None else [0,0,0]
        self.build_type         = build_type           #if build_type         is not None else xplane_constants.BUILD_TYPE_DEV
        self.build_type_version = build_type_version   #if build_type_version is not None else 0
        self.data_model_version = data_model_version   #if data_model_version is not None else 0
        self.build_number       = build_number         #if build_number       is not None else xplane_constants.BUILD_NUMBER_NONE

def change_version_info(new_version:VerData)->Optional[VerData]:
    src_folder = os.path.join(os.path.dirname(__file__),"io_xplane2blender")
    build_folder = src_folder + "_build"

    old_version = VerData()

    #TODO: Do init first
    init_file = os.path.join(build_folder,"__init__.py")
    xplane_config_file = os.path.join(src_folder,"xplane_config.py")
    
    try:
        out_config_file = []
        with open(xplane_config_file, 'r') as in_config_file:
            build_types = { "alpha":"BUILD_TYPE_ALPHA",
                            "beta": "BUILD_TYPE_BETA",
                            "dev":  "BUILD_TYPE_DEV",
                            "rc":   "BUILD_TYPE_RC"}

            for line in in_config_file:
                o_line = line
                if re.match("^CURRENT_BUILD_TYPE ",line):
                    old_version.build_type = re.search("\.(BUILD_TYPE_.*)",line).group(1)
                    if new_version.build_type:
                        line = re.sub(r"\..+",".BUILD_TYPE_"+new_version.build_type.capitalize(),line)

                if re.match("^CURRENT_BUILD_TYPE_VERSION ",line):
                    old_version.build_type_version = re.search(r"\d+",line).group(0)
                    if new_version.build_type_version:
                        line = re.sub(r"\d+",new_version.build_type_version,line)

                if re.match("^CURRENT_DATA_MODEL_VERSION ",line):
                    old_version.data_model_version = re.search(r"\d+",line).group(0)
                    if new_version.data_model_version:
                        line = re.sub(r"\d+",new_version.data_model_version,line)

                if re.match("^CURRENT_BUILD_NUMBER ",line):
                    old_version.build_number = re.search(r"xplane_constants.*",line).group(0)
                    if new_version.build_number:
                        line = re.sub(r"xplane_constants.BUILD_NUMBER_NONE",\
                            "'{}'".format(str(new_version.build_number)),\
                            line)

                if line != o_line:
                    print("o_line " + o_line)
                    print("line " + line)
                out_config_file += line

        #with open(xplane_config_file, 'w') as out_config_file:
        #    for line in out_config_file:
        #        out_config_file.write(line)
    except OSError as e:
        print(e)
        return e
    else:
        print(old_version)
        return old_version

def main(argv=None):
    exit_code = 0
    if argv is None:
        argv = _make_parser().parse_args()

    print(argv)
    src_folder = os.path.join(os.path.dirname(__file__),"io_xplane2blender")
    build_folder = src_folder + "_build"

    # 1. Delete the old build folder, if present
    # 2. Parse __init__.py and xplane_config.py for version info, swap new for old
    # 3. Run any tests desired
    # 4. Copy the source to create a new build folder
    # 5. Delete temporary files, gitignore files, and (optionally) untracked files
    # 6. Zip up folder, rename it, move to ./builds folder
    # 7. (if desired, which is almost always), replace old values for __init__.py and xplane_config.
    # This should always be able to happen, no matter what happens between 2 and 7
    try:
        if os.path.isdir(build_folder):
            shutil.rmtree(build_folder)
    except shutil.Error as e:
        print(e)
        return 1

    if argv.clean:
        return 1

    old_version = change_version_info(VerData(build_number="20180727043920"))
    try:
        shutil.copytree(src_folder,build_folder)
    except shutil.Error as e:
        print(e)
        return 1

    """
    try:
        shutil.rmtree(src_folder)
    except shutil.Error as e:
        print(e)
    else:
        try:
            os.rename(bak_folder,src_folder)
        except Exception as e:
            print(e)
            return 1
            """

    return exit_code

if __name__ == "__main__":
    sys.exit(main())
