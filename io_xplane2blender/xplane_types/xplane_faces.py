# Class: XPlaneFaces
# A collection of <XPlaneFace>.
class XPlaneFaces():
    # Property: faces
    # list - List of <XPlaneFace>.
    faces = []

    # Constructor: __init__
    def __init__(self):
        pass

    # Method: append
    # Adds a <XPlaneFace> to <faces>.
    #
    # Parameters:
    #   XPlaneFace face - A <XPlaneFace>
    def append(self,face):
        self.faces.append(face)

    # Method: remove
    # Removes a <XPlaneFace> from <faces>.
    #
    # Parameters:
    #   XPlaneFace face - A <XPlaneFace>
    def remove(self,face):
        del self.faces[face]

    # Method: get
    # Returns a <XPlaneFace> from <faces>.
    #
    # Parameters:
    #   int i - Index of the face
    #
    # Returns:
    #   XPlaneFace - A <XPlaneFace>
    def get(self,i):
        if len(self.faces)-1>=i:
            return self.faces[i]
        else:
            return None
