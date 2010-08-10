#!BPY
""" Registration info for Blender menus:
Name: 'Copy & Paste'
Blender: 235
Group: 'UV'
Tooltip: 'Copy selected texture assignment to other faces'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script duplicates a face's texture assignment across many faces.

Usage:<br>
  * Select a mesh.<br>
  * Enter UV Face Select mode.<br>
  * Select the face who's texture assignment you want to duplicate.<br>
  * Run this script from the UVs menu in the UV/Image Editor window.<br>
  * Select the face(s) that you want to change.<br>
  * Press the Copy button.<br>
"""

#------------------------------------------------------------------------
# UV Copy & Paste for blender 2.35 or above
#
# Copyright (c) 2004 Jonathan Harris
# 
# Mail: <x-plane@marginal.org.uk>
# Web:  http://marginal.org.uk/x-planescenery/
#
# See XPlane2Blender.html for usage.
#
# This software is licensed under a Creative Commons License
#   Attribution-Noncommercial-Share Alike 3.0:
#
#   You are free:
#    * to Share - to copy, distribute and transmit the work
#    * to Remix - to adapt the work
#
#   Under the following conditions:
#    * Attribution. You must attribute the work in the manner specified
#      by the author or licensor (but not in any way that suggests that
#      they endorse you or your use of the work).
#    * Noncommercial. You may not use this work for commercial purposes.
#    * Share Alike. If you alter, transform, or build upon this work,
#      you may distribute the resulting work only under the same or
#      similar license to this one.
#
#   For any reuse or distribution, you must make clear to others the
#   license terms of this work.
#
# This is a human-readable summary of the Legal Code (the full license):
#   http://creativecommons.org/licenses/by-nc-sa/3.0/
#
#
# 2004-09-02 v1.70
#  - New file
#
# 2004-09-10 v1.72
#  - Checks that in strip mode pasted faces are in same mesh.
#
# 2004-12-29 v1.86
#  - More helpful error message when no object selected.
#  - Don't try to copy texture to face with different number of vertices.
#
# 2004-12-29 v1.88
#  - Draw dialog in theme colours (requires Blender 235).
#

import Blender
from Blender import Object, NMesh, Draw, BGL

# Globals
face = 0
meshname = ""
copynorm = Draw.Create(1)
copystrp = Draw.Create(0)


# Are two vertices equal?
def veq (a, b):
    for i in range (3):
        if abs (a.co[i]-b.co[i]) > 0.01:
            return 0
    return 1


# O(n!) algorithm I think!
def mapstrip (oldface, faces):
    donefaces=[]
    n = len(oldface.v)
    for f in range (len (faces)):
        face=faces[f]
        if face and len(face.v)==n:
            # Do the faces have a common edge?
            for i in range (n):
                for j in range (n):
                    # Order of vertices is reversed in faces pointing same way
                    if (veq (face.v[i], oldface.v[j]) and
                        veq (face.v[(i+1)%n], oldface.v[(j-1)%n])):

                        # Copy the texture co-ords
                        for k in range (n):
                            face.uv[(i+k)%n] = oldface.uv[(j-k)%n]

                        # Both faces must have same flags to share in a strip
                        face.image  = oldface.image
                        face.mode   = oldface.mode
                        face.smooth = oldface.smooth
                        face.transp = oldface.transp

                        # Done this face - remove from list
                        faces[f]=0

                        # Recurse
                        mapstrip (face, faces)


# the function to handle Draw Button events
def bevent (evt):
    global face, meshname, copynorm, copystrp
    
    if evt == 1:
        Draw.Exit()

    elif evt == 3:
        copynorm.val = 1
        copystrp.val = 0
        Draw.Redraw()
        
    elif evt == 4:
        copynorm.val = 0
        copystrp.val = 1
        Draw.Redraw()
        
    elif evt == 2:
        if copystrp.val:	# Strip
            objects = Blender.Object.GetSelected()
            if (len(objects) != 1 or
                objects[0].getType() != "Mesh" or
                objects[0].name != meshname):
                print len(objects)
                Draw.PupMenu("Please select faces only in the same mesh - %s." % meshname)
                return
    
            mesh = objects[0].getData()
            faces = mesh.getSelectedFaces()
            if len(faces) > 1024:
                # 1024 takes a reasonable time due to inefficiency of this
                # algorithm and doesn't overflow Python's recursion limit
                Draw.PupMenu("Please select at most 1024 faces.")
                return
    
            Blender.Window.WaitCursor(1)
            mapstrip (face, faces)
            mesh.update()

        else:			# Just map
            n = len(face.v)
            for ob in Blender.Object.GetSelected():
                mesh = ob.getData()
                if ob.getType() == "Mesh":
                    for newface in mesh.getSelectedFaces():
                        if len(newface.v) == n:
                            newface.image  = face.image
                            newface.mode   = face.mode
                            newface.smooth = face.smooth
                            newface.transp = face.transp
                            for k in range (n):
                                newface.uv[k] = face.uv[k]
                mesh.update()
                
        Draw.Exit()
        Blender.Window.Redraw(-1)


# the function to handle input events
def event (evt, val):
    if evt == Draw.ESCKEY and not val:
        Draw.Exit()                 # exit when user presses ESC


# the function to draw the screen
def gui():
    global copynorm, copystrp
    
    size=BGL.Buffer(BGL.GL_FLOAT, 4)
    BGL.glGetFloatv(BGL.GL_SCISSOR_BOX, size)
    size=size.list
    x=int(size[2])
    y=int(size[3])

    # Default theme
    text   =[  0,   0,   0, 255]
    text_hi=[255, 255, 255, 255]
    header =[195, 195, 195, 255]
    panel  =[255, 255, 255,  40]
    back   =[180, 180, 180, 255]

    # Actual theme
    if Blender.Get('version') >= 235:
        theme=Blender.Window.Theme.Get()
        if theme:
            theme=theme[0]
            space=theme.get('buts')
            text=theme.get('ui').text
            text_hi=space.text_hi
            header=space.header
            panel=space.panel
            back=space.back

    BGL.glEnable (BGL.GL_BLEND)
    BGL.glBlendFunc (BGL.GL_SRC_ALPHA, BGL.GL_ONE_MINUS_SRC_ALPHA)
    BGL.glClearColor (float(back[0])/255, float(back[1])/255,
                      float(back[2])/255, 1)
    BGL.glClear (BGL.GL_COLOR_BUFFER_BIT)
    BGL.glColor4ub (max(header[0]-30, 0),	# 30 appears to be hard coded
                    max(header[1]-30, 0),
                    max(header[2]-30, 0),
                    header[3])
    BGL.glRectd(7, y-8, 295, y-28)
    BGL.glColor4ub (panel[0], panel[1], panel[2], panel[3])
    BGL.glRectd(7, y-28, 295, y-130)
    BGL.glColor4ub (text_hi[0], text_hi[1], text_hi[2], text_hi[3])
    BGL.glRasterPos2d(16, y-23)
    Draw.Text("UV Copy & Paste")
    BGL.glColor4ub (text[0], text[1], text[2], text[3])
    BGL.glRasterPos2d(16, y-48)
    Draw.Text("Select the faces to paint and then press Paste")
    BGL.glRasterPos2d(16, y-75)
    Draw.Text("Copy type:", "small")
    copynorm = Draw.Toggle("Normal", 3, 73, y-79, 51, 17, copynorm.val,
                           "Copy texture to selected faces in the same or a different mesh")
    copystrp = Draw.Toggle("Strip", 4, 124, y-79, 51, 17, copystrp.val,
                           "Reverse copied texture as necessary to make a strip in the same mesh")
    Draw.Button("Paste", 2, 14, y-120, 100, 26)
    Draw.Button("Cancel", 1, 187, y-120, 100, 26)
  

#------------------------------------------------------------------------
# main routine
#------------------------------------------------------------------------
class StripError(Exception):
    def __init__(self, msg):
        self.msg = msg

try:
    if Blender.Window.EditMode():
        raise StripError("Please enter UV Face Select mode first")
    
    objects = Blender.Object.GetSelected ()
    if len(objects) == 0:
        raise StripError("Please select a mesh in Object mode first")
    elif len(objects) != 1:
        raise StripError("Please select only one mesh in Object mode first")
                     
    ob = objects[0]
    if ob.getType() != "Mesh":
        raise StripError("Selected object is not a Mesh")

    mesh = ob.getData()
    meshname = ob.name
    faces = mesh.getSelectedFaces ()
    if len (faces) != 1:
        raise StripError("Please select exactly one face")

    face = faces[0]
    if not (mesh.hasFaceUV() or (face.mode & NMesh.FaceModes.TEX)):
        raise StripError("Selected face doesn't have a texture")

    # 'Hard' faces can't be in a strip
    face.mode |= NMesh.FaceModes.DYNAMIC
    mesh.update()

    Draw.Register (gui, event, bevent)

except StripError, e:
    Draw.PupMenu ("ERROR%%t|%s" % e.msg)
