#!BPY
""" Registration info for Blender menus:
Name: 'Replace and fixup UV mapping...'
Blender: 243
Group: 'Image'
Tooltip: 'Adjust UV assignments to enlarged bitmap'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
This script fixes up selected meshes' texture assignments after increasing
the size of the image.

Usage:<br>
  * Double the size of the texture bitmap file in an image editor.<br>
  * Use Image->Reload to load the resized bitmap.<br>
  * Select a mesh or meshes.<br>
  * Run this script from the UVs menu in the UV/Image Editor<br>
    window.<br>
  * Choose the location of the textures in the bitmap file.<br>
  * Press the Resize button.<br>
"""

#------------------------------------------------------------------------
# UV Resize for blender 2.43 or above
#
# Copyright (c) 2005,2007 Jonathan Harris
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
# 2005-03-02 v2.00
#  - New file
#
# 2007-12-06 v3.03
#  - Generalise to handle cases where new image is multiple size of old
#  - Handle case where new image is not a multiple of the old
#

import Blender
from Blender import BGL, Draw, Image, NMesh, Scene, Window

# Constants
CANCEL=0
PANELPAD=7
PANELINDENT=8
PANELTOP=8
PANELHEAD=20
PANELWIDTH=304
CONTROLSIZE=19

# Globals
oldimage=None
newimage=None
oldsize=None
newsize=None
buttons=[]
offsets=[]
rows=0
cols=0

def dodialog(newname):
    global newimage, newsize, offsets, rows, cols

    try:
        newimage=Image.Load(newname)
        newsize=newimage.getSize()
    except:
        Draw.PupMenu("Can't read image %s" % newname)
        return

    if newsize[0]==oldsize[0] and newsize[1]==oldsize[1]:
        # same size, just replace
        doapply(0,0)
        return
    elif newsize[0]<oldsize[0] or newsize[1]<oldsize[1]:
        Draw.PupMenu("The new image must be larger than the old image")
        return
    else:
        if newsize[0]%oldsize[0]==0:
            xoffs=range(0,newsize[0],oldsize[0])
        else:
            xoffs=[0,newsize[0]-oldsize[0]]
        if newsize[1]%oldsize[1]==0:
            yoffs=range(newsize[1]-oldsize[1],-oldsize[1],-oldsize[1])
        else:
            yoffs=[newsize[1]-oldsize[1],0]
        for i in yoffs:
            for j in xoffs:
                offsets.append((j,i))
        cols=len(xoffs)
        rows=len(yoffs)
        Draw.Register(gui, event, bevent)

# the function to handle input events
def event (evt, val):
    if evt == Draw.ESCKEY and not val:
        Draw.Exit()                 # exit when user presses ESC

# the function to handle Draw Button events
def bevent (evt):
    if evt==CANCEL:
        Draw.Exit()
    else:
        doapply(*offsets[evt-CANCEL-1])
        Draw.Exit()

# the function to draw the screen
def gui():
    global buttons, offsets, rows, cols

    size=BGL.Buffer(BGL.GL_FLOAT, 4)
    BGL.glGetFloatv(BGL.GL_SCISSOR_BOX, size)
    size=size.list
    xoff=PANELPAD
    yoff=int(size[3])

    # Default theme
    text   =[  0,   0,   0, 255]
    text_hi=[255, 255, 255, 255]
    header =[165, 165, 165, 255]
    panel  =[255, 255, 255,  40]
    back   =[180, 180, 180, 255]

    # Actual theme
    if Blender.Get('version') >= 235:
        theme=Blender.Window.Theme.Get()
        if theme:
            theme=theme[0]
            text=theme.get('ui').text
            space=theme.get('buts')
            text_hi=space.text_hi
            header=space.header
            header=[max(header[0]-30, 0),	# 30 appears to be hard coded
                    max(header[1]-30, 0),
                    max(header[2]-30, 0),
                    header[3]]
            panel=space.panel
            back=space.back

    BGL.glEnable (BGL.GL_BLEND)
    BGL.glBlendFunc (BGL.GL_SRC_ALPHA, BGL.GL_ONE_MINUS_SRC_ALPHA)
    BGL.glClearColor(float(back[0])/255, float(back[1])/255, float(back[2])/255, 1)
    BGL.glClear (BGL.GL_COLOR_BUFFER_BIT)

    BGL.glColor4ub(*header)
    BGL.glRectd(xoff, yoff-PANELTOP, xoff-PANELINDENT+PANELWIDTH, yoff-PANELTOP-PANELHEAD)
    BGL.glColor4ub(*panel)
    BGL.glRectd(xoff, yoff-PANELTOP-PANELHEAD, xoff-PANELINDENT+PANELWIDTH, yoff-60-PANELINDENT-rows*CONTROLSIZE)
    BGL.glColor4ub(*text_hi)
    BGL.glRasterPos2d(xoff+PANELINDENT, yoff-23)
    Draw.Text("Fixup UV mapping")

    BGL.glColor4ub(*text)
    BGL.glRasterPos2d(xoff+PANELINDENT, yoff-48)
    Draw.Text("Select where the old image is located in the new:")

    buttons=[]
    for i in range(rows):
        for j in range(cols):
            buttons.append(Draw.Button('', len(buttons)+CANCEL+1, xoff+PANELINDENT+j*CONTROLSIZE, yoff-80-i*CONTROLSIZE,  CONTROLSIZE, CONTROLSIZE))

    buttons.append(Draw.Button("Cancel", CANCEL, xoff-PANELINDENT*2+PANELWIDTH-4*CONTROLSIZE, yoff-60-rows*CONTROLSIZE, 4*CONTROLSIZE, CONTROLSIZE))


def doapply(xoff,yoff):
    xscale=oldsize[0]/float(newsize[0])
    yscale=oldsize[1]/float(newsize[1])
    xoff/=float(newsize[0])
    yoff/=float(newsize[1])

    Draw.Exit()
    for ob in Scene.GetCurrent().objects:
        if ob.getType() == "Mesh":
            mesh = ob.getData()
            if mesh.hasFaceUV():
                for face in mesh.faces:
                    if face.mode & NMesh.FaceModes.TEX and face.image==oldimage:
                        for i in range(len(face.uv)):
                            (s,t)=face.uv[i]
                            face.uv[i]=(xoff+s*xscale, yoff+t*yscale)
                            face.image=newimage
                mesh.update()

    newimage.makeCurrent()
    Window.RedrawAll()


#---------------------------------------------------------------------------
oldimage=Image.GetCurrent()
if oldimage:
    try:
        oldsize=oldimage.getSize()
    except:
        Draw.PupMenu("Can't read image %s" % oldimage.name)
    else:
        #Window.ImageSelector(dodialog, 'Replace image', oldimage.filename)
        Window.FileSelector(dodialog, 'Replace image', oldimage.filename)
