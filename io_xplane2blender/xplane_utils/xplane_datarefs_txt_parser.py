import pathlib
import re
import sys
from collections import OrderedDict
from pathlib import Path

from typing import List, Optional

import xplane_helpers

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
description: Zero or more non-whitespace characters
"""
class DatarefInfoStruct():
    def __init__(self,path:str,type:str,is_writable:str,units:Optional[str],description:Optional[str]):
        #assert etc etc etc
        self.path = path
        self.type = type
        self.is_array_type = True if '[' in self.type and ']' in self.type else False
        if self.is_array_type:
            #TODO: Potential for error here
            self.array_size = int(self.type[self.type.find('[')+1:self.type.find(']')])
        else:
            self.array_size = 0
        self.is_writable = is_writable
        self.units = units if units else ""
        self.description = description if description else ""

        if not self.is_valid():
            assert False, "How did this happen?! {}".format(self)

    def is_valid(self)->bool:
        valid_path = self.path != ""
        valid_type = re.match(r"^(int|float|double|byte)(\[\d+\])?", self.type) is not None
        valid_is_writable = (self.is_writable == "y" or self.is_writable == "n")
        if self.is_array_type:
            valid_is_array_size = self.array_size >= 0
            return valid_path and valid_type and valid_is_writable and valid_is_array_size
        else:
            return valid_path and valid_type and valid_is_writable
    def __repr__(self):
        return """DatarefInfoStruct(path="{}",type="{}",is_writable="{}",units="{}",description="{}")""".format(self.path, self.type, self.is_writable, self.units, self.description)

_datarefs_txt_content = {} # type: Dict[str,List[DatarefInfoStruct]]

def parse_datarefs_txt(filepath: str)->Optional[List[DatarefInfoStruct]]:
    logger = xplane_helpers.logger
    try:
        with open(filepath) as dref_file:
            _datarefs_txt_content[filepath] = []
            for i,line in enumerate(dref_file):
                if i == 0:
                    if re.match("^[0-9] [0-9]+",line):
                        continue
                    else:
                        logger.error(filepath + " does not have a valid file format line: {}".format(line))
                        return None

                if i == 1:
                    if line == "\n":
                        continue
                    else:
                        logger.error(filepath + " does not have a blank line for its second line")
                

                segments = [segment.strip() for segment in line.strip().split(sep=None,maxsplit=4)]
                info_struct_params = [""] * 5
                info_struct_params[:len(segments)] = segments[:5]
                _datarefs_txt_content[filepath].append(DatarefInfoStruct(*info_struct_params))

            return _datarefs_txt_content[filepath]
    except:
        return None

def get_datarefs_txt_file_content(filepath:str):
    if filepath in _datarefs_txt_content:
        return _datarefs_txt_content[filepath]
    else:
        # Lazy parsing of file
        return parse_datarefs_txt(filepath)
