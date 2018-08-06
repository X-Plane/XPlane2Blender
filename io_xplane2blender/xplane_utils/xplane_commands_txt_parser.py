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
Commands.txt file format spec
-----------------------------
The file is one or more commands, followed by whitespace,
and a description. While there is no formal spec I've found,
here is my best guess as to the rules.

file ::= {<command> [<whitespace> <description>] \n}

command: Same as the dataref: one or more non-whitespace characters,
usually in the form of sim/subcatagory/etc
whitepace: At least one space, enough space characters to
align all the descriptions (currently column 52) if there is a description
description ::= A short description of the command's purpose
using any characters, followed by a new line. It is right aligned
"""

class CommandInfoStruct():
    def __init__(self,command:str,description:Optional[str]):
        self.command = command
        self.description = description

    def is_invalid(self)->str:
        '''Returns "" for no errors or a string describing the issue'''
        if self.command == "":
            return "Command must be one or more non-whitespace characters"

_commands_txt_content = {} # type: Dict[str,List[CommandInfoStruct]]
def parse_commands_txt(filepath:str)->Union[List[CommandInfoStruct],str]:
    try:
        with open(filepath) as commands_file:
            file_contents = [] # type: List[Any]
            for i,line in enumerate(commands_file):
                match = re.match("^(\S+)\s+([\S ]*)")
                if match:
                    file_contents.append(CommandInfoStruct(match.group(1), match.group(2)))

            _commands_txt_content[filepath] = file_contents
            return _commands_txt_content[filepath]

    except Exception as e:
        return e.args[1]

def get_commands_txt_file_content(filepath:str)->Union[List[CommandInfoStruct],str]:
    if filepath in _commands_txt_content:
        return _commands_txt_content[filepath]
    else:
        # Lazy parsing of file
        return parse_commands_txt(filepath)

