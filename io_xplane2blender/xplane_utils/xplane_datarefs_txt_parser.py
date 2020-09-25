import os
import pathlib
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List, Optional, Union

from io_xplane2blender import xplane_helpers
from io_xplane2blender.xplane_export import showLogDialog


"""
Datarefs.txt file format spec
-----------------------------
First Line: FORMAT_VERSION WED_VERSION DATE(ignored)
Ex: 2 950 Tue Feb 23 22:39:40 2010
Second Line: New Line

Rest of file: A whitespace (\t used here for emphasis) seperated csv with exactly 5 columns
path\ttype\twritable\tunits\tdescription

path: One or more non-whitespace character, usually in the form of sim/subcatagory/etc
type: The word int, float, double, or btye optionally followed by [#] making it an array of that type.
      For instance int[24] is ``an array of 24 ints``
writable: A single y or n
units: Zero or more non-whitespace characters
description: Zero or more characters
"""


class DatarefInfoStruct:
    def __init__(
        self,
        path: str,
        type: str,
        is_writable: str,
        units: Optional[str],
        description: Optional[str],
    ):
        # assert etc etc etc
        self.path = path
        self.type = type
        self.is_array_type = True if "[" in self.type and "]" in self.type else False
        try:
            if self.is_array_type:
                # TODO: Potential for error here
                self.array_size = int(
                    self.type[self.type.find("[") + 1 : self.type.find("]")]
                )
            else:
                self.array_size = 0
        except:
            self.array_size = 0

        self.is_writable = is_writable
        self.units = units if units else ""
        self.description = description if description else ""

    def is_invalid(self) -> str:
        """Returns "" for no errors, or a string describing the issue"""
        if self.path == "":
            return "Path must be one or more non-whitespace character"

        if re.match(r"^(int|float|double|byte)", self.type) is None:
            return "Type '{}' must be an int, float, double, or byte".format(self.type)
        if "[" in self.type:
            match = re.match(r"^(int|float|double|byte)(\[.*\])", self.type)
            if match is None:
                return "Array type '{}' must be formatted as 'datatype[index]', where datatype is a valid type and index is one or more digits".format(
                    self.type
                )
            else:
                match = re.match(r"\[\d+\]", match.groups()[1])
                if match is None:
                    return "Array index '{}' must be one or more digits".format(
                        self.type
                    )

        if self.is_writable not in {"y", "n"}:
            return "Path is writable '{}' must be 'y' or 'n'".format(self.is_writable)

        return ""

    def __repr__(self) -> str:
        return """DatarefInfoStruct(path="{}",type="{}",is_writable="{}",units="{}",description="{}")""".format(
            self.path, self.type, self.is_writable, self.units, self.description
        )


_datarefs_txt_content = {}  # type: Dict[str,List[DatarefInfoStruct]]


def parse_datarefs_txt(filepath: str) -> Union[List[DatarefInfoStruct], str]:
    """
    Returns a collection of DatarefInfoStruct representing the contents of or an error string
    """

    def shorten_path(filepath):
        return "..." + os.path.sep.join(pathlib.Path(filepath).parts[-3:])

    try:
        with open(filepath) as dref_file:
            file_contents = []
            for i, line in enumerate(dref_file):
                if i == 0:
                    match = re.match("^([0-9]) [0-9]+(\s+|$)", line)
                    if match:
                        if match.group(1) != "2":
                            return "File version number '{}' is not 2".format(
                                match.group(1)
                            )
                        continue
                    else:
                        return "File format line is invalid: '{}'".format(line)

                if i == 1:
                    if line == "\n":
                        continue
                    else:
                        return "Does not have a blank line for its second line"

                if re.match("^\s+", line):
                    return "Line {} cannot start with whitespace".format(i)

                segments = [
                    segment.strip()
                    for segment in line.strip().split(sep=None, maxsplit=4)
                ]
                info_struct_params = [""] * 5
                info_struct_params[: len(segments)] = segments[:5]
                dataref_info_struct = DatarefInfoStruct(*info_struct_params)
                if not dataref_info_struct.is_invalid():
                    file_contents.append(dataref_info_struct)
                else:
                    return "Line {}, '{}' is invalid: {}".format(
                        i + 1,
                        line.strip().replace("\t", "    "),
                        dataref_info_struct.is_invalid(),
                    )

            if len(file_contents) == 0:
                return "File has no datarefs in it"

            _datarefs_txt_content[filepath] = file_contents
            return _datarefs_txt_content[filepath]
    except Exception as e:
        return e.args[1]


def get_datarefs_txt_file_content(filepath: str) -> Union[List[DatarefInfoStruct], str]:
    if filepath in _datarefs_txt_content:
        return _datarefs_txt_content[filepath]
    else:
        # Lazy parsing of file
        return parse_datarefs_txt(filepath)
