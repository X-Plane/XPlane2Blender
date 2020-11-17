# Class: XPlaneFace
# A mesh face. This class is just a data wrapper used by <XPlaneFaces>.
class XPlaneFace:
    # Property: vertices
    # list of vectors - [v1,v2,v3] The vertices forming the face.

    # Property: normals
    # list of vectors - [n1,n2,n3] The normals of each vertice in <vertices>.

    # Property: indices
    # list - [i1,i2,i3] The indices for each vertice in <vertices>.

    # Property: uvs
    # list of vectors - [(u1,v1),(u2,v2),(u3,v3)] With UV coordinates for each vertice in <vertices>.

    # Property: smooth
    # bool - (default=False) True if face is smooth shaded, False if it is flat shaded.

    def __init__(self):
        self.vertices = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        self.normals = [(0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)]
        self.indices = [0, 0, 0]
        self.uvs = [(0.0, 0.0), (0.0, 0.0), (0.0, 0.0)]
        self.smooth = False
