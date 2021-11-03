"""The starting point for the export process, the start of the addon.
Its purpose is to read strings and break them into chunks, filtering out
comments and deprecated OBJ directives.

It also gives prints errors to the logger
"""

import collections
import itertools
import math
import pathlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from pprint import pprint
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import bmesh
import bpy
from mathutils import Euler, Vector

from io_xplane2blender.importer.xplane_imp_cmd_builder import VT, ImpCommandBuilder
from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_constants import (
    ANIM_TYPE_HIDE,
    ANIM_TYPE_SHOW,
    ANIM_TYPE_TRANSFORM,
)
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    floatToStr,
    logger,
    vec_b_to_x,
    vec_x_to_b,
)


class UnrecoverableParserError(Exception):
    pass


def import_obj(filepath: Union[pathlib.Path, str]) -> str:
    """
    Attempts to import an OBJ, mutating the blender data of the current scene.
    The importer may
    - finish the whole import, returning "FINISHED"
    - stop early with partial results, returning "CANCELLED".
    - Raise an UnrecoverableParserError showing no results can be trusted
    """
    filepath = pathlib.Path(filepath)
    builder = ImpCommandBuilder(filepath)
    try:
        lines = pathlib.Path(filepath).read_text().splitlines()
    except OSError:
        raise OSError
    else:
        # pprint(lines)
        pass

    if not lines or not (lines[0] in {"A", "I"} and lines[1:3] == ["800", "OBJ"]):
        logger.error(
            ".obj file must start with exactly the OBJ header. Check filetype and content"
        )
        raise UnrecoverableParserError

    directives_white = {
        "VT",
        "IDX",
        "IDX10",
        "TRIS",
        "ANIM_begin",
        "ANIM_end",
        "ANIM_trans_begin",
        "ANIM_trans_key",
        "ANIM_trans_end",
        "ANIM_rotate_begin",
        "ANIM_rotate_key",
        "ANIM_rotate_end",
        "ANIM_keyframe_loop",
    }

    # TODO: This should be made later. We should start with our tree of intermediate structures then eventually make that into bpy structs when we know what is valid.
    # Otherwise, consider this a hack
    root_col = test_creation_helpers.create_datablock_collection(
        pathlib.Path(filepath).stem
    )
    root_col.xplane.is_exportable_collection = True

    pattern = re.compile("([^#]*)(#.*)?")

    last_axis = None
    name_hint = ""
    skip = False
    for lineno, line in enumerate(map(str.strip, lines[3:]), start=1):
        to_parse, comment = re.match(pattern, line).groups()[0:2]
        try:
            if comment.startswith("# name_hint:"):
                name_hint = comment[12:].strip()
            elif comment.startswith(("# 1", "# 2", "# 3", "# 4")):
                name_hint = comment[2:].strip()
        except AttributeError:
            pass

        if not to_parse:
            continue
        else:
            directive, *components = to_parse.split()

        if directive == "SKIP":
            skip = not skip
        if directive == "STOP":
            break

        if skip:
            continue

        # print(lineno, directive, components)

        # TODO: Rewrite using giant switch-ish table and functions so it is more neat
        # Need scanf solution
        # scan_int, scan_float, scan_vec2, scan_vec3tobl, scan_str, scan_enum (where it scans a limited number of choices and has a mapping of strings for it)
        """
        def scan_int(s_itr:iter_of_enum, default=None, error_msg=None):
            s = ""
            try:
                i, c = next(s_itr)
            except StopIteration:
                return "expected, str, found end of line"
            while c in "-0123456789":
                s += c
                c = next(s_itr)
            try:
                return int(s)
            except ValueError:
                if default is not None:
                    return default

        def scan_float(s_itr:iter)
            pass
        """

        # if fails we can fallback to default value and print warning or just print a logger warning that it is skipping
        # itr = enumerate()
        # def scan_(last=False, msg_missing=f"Could not convert parameter {lineno} _true, default=None)->value:
        # Throws parser error if needed
        # def _try to swallow all exceptions if the only thing that should happen is the line getting ignored on bad data. Otherwise we can go into more crazy exception hanlding cases
        if directive == "TEXTURE":
            try:
                texture_path = (filepath.parent / Path(components[0])).resolve()
            except IndexError:
                logger.warn(f"TEXTURE directive given but was empty")
            else:
                if texture_path.exists():
                    builder.texture = texture_path
                else:
                    logger.warn(f"'{str(texture_path)}' is not a real file")
        elif directive == "VT":
            components[:3] = vec_x_to_b(list(map(float, components[:3])))
            components[3:6] = vec_x_to_b(list(map(float, components[3:6])))
            components[6:8] = list(map(float, components[6:8]))
            builder.build_cmd(directive, *components[:8])
        elif directive == "IDX":
            try:
                idx = int(*components[:1])
                if idx < -1:
                    raise ValueError(
                        f"IDX on line {lineno}'s is less than 0"
                    )  # Also, must be less than POINT_COUNTS reports?  # TODO yes?
            except ValueError:
                logger.warn(f"IDX table messed up, {idx} is not an int")
                print("what")
            except IndexError:
                # should have been at least 1
                print("index error")
                pass
            else:
                builder.build_cmd(directive, idx)
        elif directive == "IDX10":
            # idx error etc
            builder.build_cmd(directive, *map(int, components[:11]))
        elif directive == "TRIS":
            start_idx = int(components[0])
            count = int(components[1])
            builder.build_cmd(directive, start_idx, count, name_hint=name_hint)
            name_hint = ""

        elif directive == "ANIM_begin":
            builder.build_cmd("ANIM_begin", name_hint=name_hint)
        elif directive == "ANIM_end":
            builder.build_cmd("ANIM_end")
        elif directive == "ANIM_trans_begin":
            dataref_path = components[0]
            builder.build_cmd("ANIM_trans_begin", dataref_path, name_hint=name_hint)
        elif directive == "ANIM_trans_key":
            value = float(components[0])
            location = vec_x_to_b(list(map(float, components[1:4])))
            builder.build_cmd(directive, value, location)
        elif directive == "ANIM_trans_end":
            pass
        elif directive in {"ANIM_hide", "ANIM_show"}:
            v1, v2 = map(float, components[:2])
            dataref_path = components[2]
            builder.build_cmd(directive, v1, v2, dataref_path)
        elif directive == "ANIM_rotate_begin":
            axis = vec_x_to_b(list(map(float, components[0:3])))
            dataref_path = components[3]
            builder.build_cmd(directive, axis, dataref_path, name_hint=name_hint)
        elif directive == "ANIM_rotate_key":
            value = float(components[0])
            degrees = float(components[1])
            builder.build_cmd(directive, value, degrees)
        elif directive == "ANIM_rotate_end":
            builder.build_cmd(directive)
        elif directive == "ANIM_keyframe_loop":
            loop = float(components[0])
            builder.build_cmd(directive, loop)
        elif directive == "ANIM_trans":
            xyz1 = vec_x_to_b(list(map(float, components[:3])))
            xyz2 = vec_x_to_b(list(map(float, components[3:6])))
            v1, v2 = (0, 0)
            path = "none"

            try:
                v1 = float(components[6])
                v2 = float(components[7])
                path = components[8]
            except IndexError as e:
                pass
            builder.build_cmd(directive, xyz1, xyz2, v1, v2, path, name_hint=name_hint)
        elif directive == "ANIM_rotate":
            dxyz = vec_x_to_b(list(map(float, components[:3])))
            r1, r2 = map(float, components[3:5])
            v1, v2 = (0, 0)
            path = "none"

            try:
                v1 = float(components[5])
                v2 = float(components[6])
                path = components[7]
            except IndexError:
                pass
            builder.build_cmd(
                directive, dxyz, r1, r2, v1, v2, path, name_hint=name_hint
            )
        else:
            # print(f"{directive} is not implemted yet")
            pass

    builder.finalize_intermediate_blocks()
    return "FINISHED"
