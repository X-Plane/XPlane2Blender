import array
import collections
import re
import time
from typing import List, Optional

import bpy
import mathutils

from io_xplane2blender import xplane_helpers

from ..xplane_config import getDebug
from ..xplane_constants import *
from ..xplane_helpers import floatToStr, logger
from .xplane_face import XPlaneFace
from .xplane_object import XPlaneObject


class XPlaneMesh:
    """
    Stores the data for the OBJ's mesh - its VT and IDX tables.

    Despite the name, there is only one XPlaneMesh per XPlaneFile,
    unlike the many XPlaneObjects per file
    """

    def __init__(self):
        # Contains all OBJ VT directives, data in the order as specified by the OBJ8 spec
        self.vertices = (
            []
        )  # type: List[Tuple[float, float, float, float, float, float, float, float]]
        # array - contains all face indices
        self.indices = array.array("i")  # type: List[int]
        # int - Stores the current global vertex index.
        self.globalindex = 0
        self.debug = []

    # Method: collectXPlaneObjects
    # Fills the <vertices> and <indices> from a list of <XPlaneObjects>.
    # This method works recursively on the children of each <XPlaneObject>.
    #
    # Parameters:
    #   list xplaneObjects - list of <XPlaneObjects>.
    def collectXPlaneObjects(self, xplaneObjects: List[XPlaneObject]) -> None:
        debug = getDebug()

        def getSortKey(xplaneObject):
            return xplaneObject.name

        # sort objects by name for consitent vertex and indices table output
        xplaneObjects = sorted(xplaneObjects, key=getSortKey)

        dg = bpy.context.evaluated_depsgraph_get()
        for xplaneObject in xplaneObjects:
            if (
                xplaneObject.type == "MESH"
                and xplaneObject.xplaneBone
                and not xplaneObject.export_animation_only
            ):
                xplaneObject.indices[0] = len(self.indices)
                first_vertice_of_this_xplaneObject = len(self.vertices)

                # This is the heart of the exporter turning object into VT/IDX table:
                # - Get the mesh of the object with its modifiers
                # and transformations applied, rotated and moved by the bake matrix
                #
                # After that, the mesh needs to have some of it's data refreshed
                # - Recalc normals split
                # - Recalc tessface (now called loop triangles)

                # create a copy of the xplaneObject mesh with modifiers applied and triangulated
                evaluated_obj = xplaneObject.blenderObject.evaluated_get(dg)
                mesh = evaluated_obj.to_mesh(
                    preserve_all_data_layers=False, depsgraph=dg
                )

                xplaneObject.bakeMatrix = (
                    xplaneObject.xplaneBone.getBakeMatrixForAttached()
                )
                mesh.transform(xplaneObject.bakeMatrix)

                if hasattr(mesh, "calc_normals_split"):
                    mesh.calc_normals_split()
                
                mesh.calc_loop_triangles()
                loop_triangles = mesh.loop_triangles
                try:
                    uv_layer = mesh.uv_layers[xplaneObject.material.uv_name]
                except (KeyError, TypeError) as e:
                    uv_layer = None

                TempFace = collections.namedtuple(
                    "TempFace",
                    field_names=[
                        "original_face",  # type: bpy.types.MeshLoopTriangle
                        "indices",  # type: Tuple[float, float, float]
                        "normal",  # type: Tuple[float, float, float]
                        "split_normals",  # type: Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]
                        "uvs",  # type: Tuple[mathutils.Vector, mathutils.Vector, mathutils.Vector]
                    ],
                )
                tmp_faces = []  # type: List[TempFace]
                for tri in mesh.loop_triangles:
                    tmp_face = TempFace(
                        original_face=tri,
                        # BAD NAME ALERT!
                        # mesh.vertices is the actual vertex table,
                        # tri.vertices is indices in that vertex table
                        indices=tri.vertices,
                        normal=tri.normal,
                        split_normals=tri.split_normals,
                        uvs=tuple(
                            uv_layer.data[loop_index].uv for loop_index in tri.loops
                        )
                        if uv_layer
                        else (mathutils.Vector((0.0, 0.0)),) * 3,
                    )
                    tmp_faces.append(tmp_face)

                vertices_dct = {}
                zero_normal_corners = 0
                for tmp_face in tmp_faces:
                    # To reverse the winding order for X-Plane from CCW to CW,
                    # we iterate backwards through the mesh data structures
                    for i in reversed(range(0, 3)):
                        index = tmp_face.indices[i]
                        vertex = xplane_helpers.vec_b_to_x(mesh.vertices[index].co)
                        normal_b = (
                            tmp_face.split_normals[i]
                            if tmp_face.original_face.use_smooth
                            else tmp_face.normal
                        )
                        if (
                            normal_b[0] == 0.0
                            and normal_b[1] == 0.0
                            and normal_b[2] == 0.0
                        ):
                            # Blender gives the corners of zero-area faces a zero
                            # corner normal (4.1+ when the corner angle is zero,
                            # 5.x whenever the face is degenerate). A zero normal
                            # is never valid in an OBJ, so use the vertex normal,
                            # which is what the smooth fan around that corner
                            # would have produced. A vertex with nothing but
                            # zero-area faces has no normal either; a face with
                            # no area cannot be seen, so any unit vector will do.
                            normal_b = mesh.vertices[index].normal
                            if normal_b.length == 0.0:
                                normal_b = mathutils.Vector((0.0, 0.0, 1.0))
                            zero_normal_corners += 1
                        normal = xplane_helpers.vec_b_to_x(normal_b)
                        uv = tmp_face.uvs[i]
                        vt_entry = tuple(vertex[:] + normal[:] + uv[:])

                        # Optimization Algorithm:
                        # Try to find a matching vt_entry's index in the mesh's index table
                        # If found, skip adding to global vertices list
                        # If not found (-1), append the new vert, save its vertex
                        if bpy.context.scene.xplane.optimize:
                            vindex = vertices_dct.get(vt_entry, -1)
                        else:
                            vindex = -1

                        if vindex == -1:
                            vindex = self.globalindex
                            self.vertices.append(vt_entry)
                            self.globalindex += 1

                        if bpy.context.scene.xplane.optimize:
                            vertices_dct[vt_entry] = vindex

                        self.indices.append(vindex)

                    # store the faces in the prim
                    xplaneObject.indices[1] = len(self.indices)

                if zero_normal_corners:
                    xplane_helpers.logger.warn(
                        f"{xplaneObject.name}: {zero_normal_corners} corners on zero-area"
                        " faces had no normal, used the vertex normal instead"
                    )
                evaluated_obj.to_mesh_clear()

    def writeVertices(self) -> str:
        """
        Turns the collected vertices into the OBJ's VT table
        """
        ######################################################################
        # WARNING! This is a hot path! So don't change it without profiling! #
        ######################################################################
        # print("Begin XPlaneMesh.writeVertices")
        # start = time.perf_counter()
        debug = getDebug()
        tab = f"\t"
        if debug:
            s = "".join(
                f"VT\t"
                f"{tab.join(floatToStr(component) for component in line)}"
                f"\t# {i}"
                f"\n"
                for i, line in enumerate(self.vertices)
            )
            # print("end XPlaneMesh.writeVertices " + str(time.perf_counter()-start))
            return s
        else:
            s = "".join(
                f"VT\t" f"{tab.join(floatToStr(component) for component in line)}" f"\n"
                for line in self.vertices
            )
            # print("end XPlaneMesh.writeVertices " + str(time.perf_counter()-start))
            return s

    def writeIndices(self) -> str:
        """
        Turns the collected indices into the OBJ's IDX10/IDX table
        """
        ######################################################################
        # WARNING! This is a hot path! So don't change it without profiling! #
        ######################################################################
        o = ""
        # print("Begin XPlaneMesh.writeIndices")
        # start = time.perf_counter()

        s_idx10 = "IDX10\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n"
        s_idx = "IDX\t%d\n"
        partition_point = len(self.indices) - (len(self.indices) % 10)

        if len(self.indices) >= 10:
            o += "".join(
                [
                    s_idx10 % (*self.indices[i : i + 10],)
                    for i in range(0, partition_point - 1, 10)
                ]
            )

        o += "".join(
            [
                s_idx % (self.indices[i])
                for i in range(partition_point, len(self.indices))
            ]
        )
        # print("End XPlaneMesh.writeIndices: " + str(time.perf_counter()-start))
        return o

    def write(self):
        o = ""
        debug = False

        verticesOut = self.writeVertices()
        o += verticesOut
        if len(verticesOut):
            o += "\n"
        o += self.writeIndices()

        return o
