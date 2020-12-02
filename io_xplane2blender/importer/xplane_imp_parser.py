"""The starting point for the export process, the start of the addon"""
import dataclasses
import pathlib
from pprint import pprint
from typing import Any, Callable, Dict, List, Tuple, Union

import bmesh
import bpy

from io_xplane2blender.tests import test_creation_helpers
from io_xplane2blender.xplane_helpers import floatToStr, logger, vec_b_to_x, vec_x_to_b


class UnrecoverableParseError(Exception):
    pass


@dataclasses.dataclass
class _VT:
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
    vertices: List[_VT], faces: List[Tuple[int, int, int]]
) -> bpy.types.Mesh:
    print("BUILD WITH")
    # pprint([f"VT {v}" for v in vertices])
    me = bpy.data.meshes.new(name="asdf")
    ob = bpy.data.objects.new(me.name, me)
    ob.location = [0, 0, 0]
    ob.show_name = True
    bpy.context.scene.collection.objects.link(ob)
    me.from_pydata([(v.x, v.y, v.z) for v in vertices], [], faces)
    me.validate()
    me.update(calc_edges=True)

    return ob


def import_obj(path: pathlib.Path) -> str:
    """
    Attempts to import an OBJ, mutating the blender data of the current scene.
    The importer may
    - finish the whole import, returning "FINISHED"
    - stop early with partial results, returning "CANCELLED".
    - Raise an UnrecoverableParserError showing no results can be trusted
    """
    try:
        lines = pathlib.Path(path).read_text().splitlines()
    except OSError:
        raise OSError
    else:
        pass
        # pprint(lines)

    if lines[0:3] != ["I", "800", "OBJ"]:
        logger.error(
            ".obj file must start with exactly OBJ header. Check filetype and content"
        )
        raise UnrecoverableParseError

    directives_white = {
        "VT",
        "IDX",
        "IDX10",
        "TRIS",
    }
    vertices = []
    idxs = []

    for lineno, line in filter(
        lambda l: l[1] and not l[1].startswith("#"),
        enumerate(map(str.strip, lines), start=1),
    ):
        directive, *components = line.split()
        # print(lineno, directive, components)

        # TODO: Rewrite using giant switch-ish table and functions so it is more neat
        if directive == "VT":
            components[:3] = vec_x_to_b(list(map(float, components[:3])))
            components[3:6] = vec_x_to_b(list(map(float, components[3:6])))
            components[6:8] = list(map(float, components[6:8]))
            vertices.append(_VT(*components))
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
                vertices=[vertices[idx] for idx in all_idxs],
                faces=[
                    (
                        all_idxs[i],
                        all_idxs[i + 1],
                        all_idxs[i + 2],
                    )
                    for i in range(0, len(all_idxs), 3)
                ],
            )
        else:
            print("SKIPPING directive", directive)
    # pprint([f"VT {v}" for v in vertices])
    # pprint([f"IDX {i}" for i in idxs])
