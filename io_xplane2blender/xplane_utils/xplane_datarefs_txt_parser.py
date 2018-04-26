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

    def is_invalid(self)->str:
        '''Returns "" for no errors, or a string describing the issue'''
        if self.path == "":
            return "Dataref path must be one or more non-whitespace character"

        if re.match(r"^(int|float|double|byte)[\[\s]", self.type) is None:
            return "Dataref type '{}' is must be an int, float, double, byte".format(self.type)
        elif '[' in self.type:
            match = re.match(r"^(int|float|double|byte)(\[.*\])", self.type)
            if match is None:
                return "Dataref array type '{}' must formatted as 'datatype[index]', where datatype is an accepted type and index is one or more digits".format(self.type)
            else:
                match = re.match(r"\[\d+\]",match.groups()[1])
                if match is None:
                    return "Dataref array type index '{}' must be one or more digits".format(self.type)

        if self.is_writable not in {'y','n'}:
            return "Dataref 'is writable' '{}' must be 'y' or 'n'".format(self.is_writable)

        return ""

    def __repr__(self)->str:
        return """DatarefInfoStruct(path="{}",type="{}",is_writable="{}",units="{}",description="{}")""".format(self.path, self.type, self.is_writable, self.units, self.description)

_datarefs_txt_content = {} # type: Dict[str,List[DatarefInfoStruct]]

def parse_datarefs_txt(filepath: str)->Union[List[DatarefInfoStruct],str]:
    '''
    Returns a collection of DatarefInfoStruct representing the contents of or an error string
    '''
    try:
        with open(filepath) as dref_file:
            file_contents = []
            for i,line in enumerate(dref_file):
                print(line)
                if i == 0:
                    if re.match("^[0-9] [0-9]+",line):
                        continue
                    else:
                        return filepath + " does not have a valid file format line: {}".format(line)

                if i == 1:
                    if line == "\n":
                        continue
                    else:
                        return filepath + " does not have a blank line for its second line"


                segments = [segment.strip() for segment in line.strip().split(sep=None,maxsplit=4)]
                info_struct_params = [""] * 5
                info_struct_params[:len(segments)] = segments[:5]
                dataref_info_struct = DatarefInfoStruct(*info_struct_params)
                if not dataref_info_struct.is_invalid():
                    _datarefs_txt_content[filepath].append(dataref_info_struct)
                else:
                    return "Dataref {} on line {} is not valid: {}".format(line.strip(),i+1,dataref_info_struct.is_invalid())

            if len(_datarefs_txt_content[filepath]) == 0:
                return filepath + " had no datarefs in it"

            _datarefs_txt_content[filepath] = file_contents
            return _datarefs_txt_content[filepath]
    except Exception as e:
        return e.args[1]

def get_datarefs_txt_file_content(filepath:str)->Union[List[DatarefInfoStruct],str]:
    if filepath in _datarefs_txt_content:
        return _datarefs_txt_content[filepath]
    else:
        # Lazy parsing of file
        return parse_datarefs_txt(filepath)
