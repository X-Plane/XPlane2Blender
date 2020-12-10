"""The starting point for the export process, the start of the addon"""
import dataclasses
import pathlib
import re
from pprint import pprint
from typing import Any, Callable, Dict, List, Tuple, Union

import bmesh
import bpy

from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_helpers import (
    ExportableRoot,
    floatToStr,
    logger,
    vec_b_to_x,
    vec_x_to_b,
)


class UnrecoverableParserError(Exception):
    pass


@dataclasses.dataclass
class _VT:
    """Where xyz, nxyz are in Blender coords"""

    x: float
    y: float
    z: float
    nx: float
    ny: float
    nz: float
    s: float
    t: float

    def __post_init__(self):
        for attr, factory in type(self).__annotations__.items():
            try:
                setattr(self, attr, factory(getattr(self, attr)))
            except ValueError:
                print(
                    f"Couldn't convert '{attr}''s value ({getattr(self, attr)}) with {factory}"
                )

    def __str__(self) -> str:
        def fmt(s):
            try:
                return floatToStr(float(s))
            except (TypeError, ValueError):
                return s

        return "\t".join(
            fmt(value)
            for attr, value in vars(self).items()
            if not attr.startswith("__")
        )


def _build_mesh(
    root_collection: ExportableRoot,
    vertices: List[_VT],
    faces: List[Tuple[int, int, int]],
) -> bpy.types.Mesh:
    # print("BUILD WITH")
    # pprint([f"VT {v}" for v in vertices])
    me = bpy.data.meshes.new(f"Mesh.{len(bpy.data.meshes):03}")
    ob = bpy.data.objects.new(me.name, me)
    ob.location = [0, 0, 0]
    # ob.show_name = True
    root_collection.objects.link(ob)
    me.from_pydata([(v.x, v.y, v.z) for v in vertices], [], faces)
    uv_layer = me.uv_layers.new()
    me.update(calc_edges=True)

    ret = me.validate(verbose=True)
    # print("validate says " , ret)
    if True:
        for i in range(len(me.vertices)):
            me.vertices[i].normal = vertices[i].nx, vertices[i].ny, vertices[i].nz
            uv_layer.data[i].uv = vertices[i].s, vertices[i].t
    else:
        logger.error("Mesh was not valid")

    return ob


def import_obj(filepath: Union[pathlib.Path, str]) -> str:
    """
    Attempts to import an OBJ, mutating the blender data of the current scene.
    The importer may
    - finish the whole import, returning "FINISHED"
    - stop early with partial results, returning "CANCELLED".
    - Raise an UnrecoverableParserError showing no results can be trusted
    """
    filepath = pathlib.Path(filepath)
    try:
        lines = pathlib.Path(filepath).read_text().splitlines()
    except OSError:
        raise OSError
    else:
        # pprint(lines)
        pass

    if lines[0:3] != ["I", "800", "OBJ"]:
        logger.error(
            ".obj file must start with exactly the OBJ header. Check filetype and content"
        )
        raise UnrecoverableParserError

    directives_white = {
        "VT",
        "IDX",
        "IDX10",
        "TRIS",
    }
    vertices = []
    idxs = []

    # TODO: This should be made later. We should start with our tree of intermediate structures then eventually make that into bpy structs when we know what is valid.
    # Otherwise, consider this a hack
    root_col = test_creation_helpers.create_datablock_collection(
        pathlib.Path(filepath).stem
    )
    root_col.xplane.is_exportable_collection = True
    pattern = re.compile("([^#]*)(#.*)?")
    for lineno, line in enumerate(map(str.strip, lines[3:]), start=1):
        to_parse, comment = re.match(pattern, line).groups()[0:2]
        if not to_parse:
            continue
        else:
            directive, *components = to_parse.split()
            # print(lineno, directive, components)

        # TODO: Rewrite using giant switch-ish table and functions so it is more neat
        # Need scanf solution
        # scan_int, scan_float, scan_vec2, scan_vec3tobl, scan_str, scan_enum (where it scans a limited number of choices and has a mapping of strings for it)
        # if fails we can fallback to default value and print warning or just print a logger warning that it is skipping
        # itr = enumerate()
        # def scan_(last=False, msg_missing=f"Could not convert parameter {lineno} _true, default=None)->value:
        # Throws parser error if needed
        # def _try to swallow all exceptions if the only thing that should happen is the line getting ignored on bad data. Otherwise we can go into more crazy exception hanlding cases
        if directive == "VT":
            components[:3] = vec_x_to_b(list(map(float, components[:3])))
            components[3:6] = vec_x_to_b(list(map(float, components[3:6])))
            components[6:8] = list(map(float, components[6:8]))
            vertices.append(_VT(*components[:8]))
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
                idxs.append(idx)
        elif directive == "IDX10":
            # idx error etc
            idxs.extend(map(int, components[:11]))
        elif directive == "TRIS":
            # TODO: idx error, can't convert error, idx doesn't have that many error, wrong index error
            start = int(components[0])
            count = int(components[1])
            all_idxs = idxs[start : start + count]
            _build_mesh(
                root_collection=root_col,
                vertices=[vertices[idx] for idx in all_idxs],
                faces=[all_idxs[i : i + 3] for i in range(0, len(all_idxs), 3)],
            )
        else:
            # print("SKIPPING directive", directive)
            pass

    return "FINISHED"
