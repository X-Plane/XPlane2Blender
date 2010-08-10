#!BPY
""" Registration info for Blender menus:
Name: 'X-Plane Animation'
Blender: 245
Group: 'Object'
Tooltip: 'Edit X-Plane animation'
"""
__author__ = "Jonathan Harris"
__email__ = "Jonathan Harris, Jonathan Harris <x-plane:marginal*org*uk>"
__url__ = "XPlane2Blender, http://marginal.org.uk/x-planescenery/"
__version__ = "3.09"
__bpydoc__ = """\
Edit X-Plane animation properties.
"""

#------------------------------------------------------------------------
#
# Copyright (c) 2007 Jonathan Harris
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
# 2007-12-03 v3.01
#  - New file
#
# 2007-12-05 v3.01
#  - Fix for when no action associated with armature
#  - Fix for setting multiple "hide" entries
#
# 2007-12-05 v3.02
#  - Bones in the same armature can have different frame counts
#  - Middle button pans
#
# 2007-12-06 v3.03
#  - Fix for missing first dataref menu entries
#
# 2007-12-11 v3.04
#  - Disambiguate all similar bones/hideshow in armature when editing one
#
# 2008-01-20 v3.07
#  - Limit data input to +/-10000 - this is the limit in the properties panel.
#
# 2010-03-21 v3.08
#  - Support manipulator functionality

import Blender
from Blender import BGL, Draw, Object, Scene, Window

from XPlaneUtils import Vertex, getDatarefs, getManipulators, make_short_name

theobject=None

# Globals
lookup={}
hierarchy={}
firstlevel=[]
has_sim=False
armature=None
bonecount=0	# number of parent bones
bones=[]	# all bones in armature
datarefs=[]
indices=[]
vals=[]
loops=[]
hideshow=[]
hideorshow=[]
hideshowindices=[]
hideshowfrom=[]
hideshowto=[]

manipulator_dict={}
manipulatorList=[]
cursorList=[]
manipulators=[]
manipulatorVals={}
cursors=[]

# Layout
vertical=False
mousex=0
mousey=0
anchor=None
offset=(0,0)

PANELPAD=7
PANELINDENT=8
PANELTOP=8
PANELHEAD=20
PANELWIDTH=304
CONTROLSIZE=19

# max value for dataref value fields
# >=1000 -> 1 decimal place precision (Method_Number in python\api2_2x\Draw.c)
# 10000 is largest number supported by properties UI
NUMBERMAX=10000

# Shared buttons. Indices<bonecount are for bones, >=bonecount are for hideshow
dataref_m=[]
dataref_b=[]
indices_b=[]
indices_t=[]
manipulator_m=[]
manipulator_b=[]

# Value buttons
vals_b=[]
clear_b=None
loops_b=[]

# Hide/Show buttons
hideshow_m=[]
from_b=[]
to_b=[]
up_b=[]
down_b=[]
delete_b=[]
addhs_b=None
cancel_b=None
apply_b=None

# Event IDs
DONTCARE=0
DATAREF_B=1
INDICES_B=2
INDICES_T=3
DELETE_B=4
LOOPS_B=5	# LOOPS must be 2nd last
VALS_B=6	# VALS must be last
HIDEORSHOW_M=7
FROM_B=8
TO_B=9
UP_B=10
DOWN_B=11
ADD_B=12
CANCEL_B=13
APPLY_B=14
EVENTMAX=256


def getparents():
    global lookup, hierarchy, firstlevel, has_sim, armature, bones, theobject

    if Window.EditMode():
        objects=[Scene.GetCurrent().objects.active]
    else:
        objects = Object.GetSelected()
    for theobject in objects:
        parent=theobject.parent
        if not parent or parent.getType()!='Armature':
            Draw.PupMenu('Object "%s" is not a child of a bone.' % theobject.name)
            return None
        bonename=theobject.getParentBoneName()
        if not bonename:
            Draw.PupMenu('Object "%s" is the child of an armature. It should be the child of a bone.' % theobject.name)
            return None
        thisbones=parent.getData().bones
        if bonename in thisbones.keys():
            bone=thisbones[bonename]
        else:
            Draw.PupMenu('Object "%s" has a deleted bone as its parent.' % theobject.name)
            return None
        if armature and (parent!=armature or bone!=bones[0]):
            Draw.PupMenu('You have selected multiple objects with different parents.')
            return None
        else:
            armature=parent
            bones=[bone]

    if not bones: return
    bone=bones[0]
    while bone.parent:
        bones.append(bone.parent)
        bone=bone.parent

    try:
        has_sim=False
        (lookup, hierarchy)=getDatarefs()
        firstlevel=[]
        for key in lookup:
            if lookup[key]:
                (path,n)=lookup[key]
                ref=path.split('/')
                if not ref[0] in firstlevel:
                   firstlevel.append(ref[0])
        if len(firstlevel) == 1:
            firstlevel=hierarchy['sim'].keys()
            has_sim=True
        firstlevel.sort(lambda x,y: -cmp(x.lower(), y.lower()))

    except IOError, e:
        Draw.PupMenu(str(e))
        return None

    return True


# populate vals array and loop value
def getvals(bonename, dataref, index):

    props=armature.getAllProperties()

    fullref=""
    if dataref in lookup and lookup[dataref]:
        (path, n)=lookup[dataref]
        fullref=path
    else:
        for prop in props:
            if prop.name.strip()==dataref and prop.type=='STRING' and prop.data:
                if prop.data.endswith('/'):
                    fullref=prop.data+dataref
                else:
                    fullref=prop.data+'/'+dataref




    # find last frame
    framecount=2    # zero based
    action=armature.getAction()
    if action and bonename in action.getChannelNames():
        ipo=action.getChannelIpo(bonename)
        for icu in ipo:
            for bez in icu.bezierPoints:
                f=bez.pt[0]
                if f>100:
                    pass    # silently stop
                elif f>int(f):
                    framecount=max(framecount,int(f)+1) # like math.ceil()
                else:
                    framecount=max(framecount,int(f))
    vals=[0.0]+[1.0 for i in range(framecount-1)]
    loop=0.0

    sname=make_short_name(fullref)
    seq=[dataref]
    seq.append(sname)
    if index: seq.append('%s[%d]' % (dataref, index))
    if index: seq.append('%s[%d]' % (sname, index))

    for tmpref in seq:
        for val in range(framecount):
            valstr="%s_v%d" % (tmpref, val+1)
            for prop in props:
                if prop.name.strip()==valstr:
                    if prop.type=='INT':
                        vals[val]=float(prop.data)
                    elif prop.type=='FLOAT':
                        vals[val]=round(prop.data, Vertex.ROUND)
        valstr="%s_loop" % tmpref
        for prop in props:
            if prop.name.strip()==valstr:
                if prop.type=='INT':
                    loop=float(prop.data)
                elif prop.type=='FLOAT':
                    loop=round(prop.data, Vertex.ROUND)
            if prop.name.strip()==dataref and prop.type=='STRING' and prop.data:
                if prop.data.endswith('/'):
                    fullref=prop.data+dataref
                else:
                    fullref=prop.data+'/'+dataref

    return (fullref,vals,loop)

# Scan the armature properties for manipulator entries
def getmanipulatorvals():

    # Default manipulator values
    manipulator = 'ATTR_manip_none'
    cursor = 'hand'

    props = armature.getAllProperties()
    for prop in props:
        if prop.name == 'manipulator_type':
            manipulator = prop.data

        if prop.name.startswith(manipulator) and prop.name.endswith('cursor'):
            cursor = prop.data

    # This is butt-ugly. Used a dictionary for the mainpulator data
    # this should get changed to a 2D array
    keys = sorted(manipulator_dict[manipulator].keys())
    for prop in props:
        if prop.name.startswith(manipulator) and not prop.name.endswith('cursor'):
            tmp = prop.name.split('_')
            key = tmp[len(tmp)-1]

            for dict_key in keys:
                if dict_key.find(key) > 0:
                    key = dict_key
                    break

            manipulator_dict[manipulator][key] = prop.data

    return (manipulator, cursor)


def gethideshow():
    props=armature.getAllProperties()

    for prop in props:
        propname=prop.name
        for suffix in ['_hide_v', '_show_v']:
            if not (suffix) in propname: continue
            digit=propname[propname.index(suffix)+7:]
            if not digit.isdigit() or not int(digit)&1: continue
            dataref=propname[:propname.index(suffix)]
            if prop.type=='INT':
                fr=float(prop.data)
            elif prop.type=='FLOAT':
                fr=round(prop.data, Vertex.ROUND)
            else:
                continue

            # look for matching pair
            valstr='%s%s%d' % (dataref, suffix, int(digit)+1)
            for prop in props:
                if prop.name==valstr:
                    if prop.type=='INT':
                        to=float(prop.data)
                        break
                    elif prop.type=='FLOAT':
                        to=round(prop.data, Vertex.ROUND)
                        break
            else:
                continue

            # split off index
            index=None
            l=dataref.find('[')
            if l!=-1:
                i=dataref[l+1:-1]
                if dataref[-1]==']':
                    try:
                        index=int(i)
                    except:
                        pass
                dataref=dataref[:l]

            if dataref in lookup and lookup[dataref]:
                (path, n)=lookup[dataref]
                fullref=path
            else:
                # look for full name
                fullref=dataref
                seq=[dataref]
                if index: seq.append('%s[%d]' % (dataref, index))
                for tmpref in seq:
                    for prop in props:
                        if prop.name.strip()==dataref and prop.type=='STRING' and prop.data:
                            if prop.data.endswith('/'):
                                fullref=prop.data+dataref
                            else:
                                fullref=prop.data+'/'+dataref

            hideshow.append(fullref)
            if suffix=='_hide_v':
                hideorshow.append(0)
            else:
                hideorshow.append(1)
            hideshowindices.append(index)
            hideshowfrom.append(fr)
            hideshowto.append(to)


def swaphideshow(a,b):
    t=hideshow[a]
    hideshow[a]=hideshow[b]
    hideshow[b]=t
    t=hideorshow[a]
    hideorshow[a]=hideorshow[b]
    hideorshow[b]=t
    t=hideshowindices[a]
    hideshowindices[a]=hideshowindices[b]
    hideshowindices[b]=t
    t=hideshowfrom[a]
    hideshowfrom[a]=hideshowfrom[b]
    hideshowfrom[b]=t
    t=hideshowto[a]
    hideshowto[a]=hideshowto[b]
    hideshowto[b]=t


# apply settings
def doapply(evt,val):
    global bonecount

    editmode=Window.EditMode()
    if editmode: Window.EditMode(0)
    armobj=armature.getData()
    armobj.makeEditable()
    armbones=armobj.bones

    # rescan object's parents - hope that the user hasn't reparented
    bone=armbones[theobject.getParentBoneName()]
    editbones=[bone]
    while bone.parent:
        editbones.append(bone.parent)
        bone=bone.parent
    bonecount=min(bonecount, len(editbones))	# in case user has reparented

    # Rename bones - see armature_bone_rename in editarmature.c
    oldnames=[bone.name for bone in editbones]
    othernames=armbones.keys()
    for name in oldnames: othernames.remove(name)
    newnames=[]

    action=armature.getAction()
    if action:
        for boneno in range(bonecount):
            # rename this Action's channels to prevent error on dupes
            if oldnames[boneno] in action.getChannelNames():
                action.renameChannel(oldnames[boneno], 'TmpChannel%d' % boneno)

    for boneno in range(bonecount-1,-1,-1):
        # do in reverse order in case of duplicate names
        name=datarefs[boneno].split('/')[-1]
		# bone name getting up toward trouble?  use PT name.  We'd rather be ambiguous - and readable.
        if len(name) > 26:
            name=make_short_name(datarefs[boneno])
        if indices[boneno]!=None: name='%s[%d]' % (name, indices[boneno])
        # Have to manually avoid duplicate names
        i=0
        base=name
        while True:
            if name in othernames:
                i+=1
                name='%s.%03d' % (base, i)
            else:
                break

        editbones[boneno].name=name
        othernames.append(name)
        newnames.insert(0, name)

        # Update this Action's channels
        if action:
            oldchannel='TmpChannel%d' % boneno
            if oldchannel in action.getChannelNames():
                # Delete keys
                ipo=action.getChannelIpo(oldchannel)
                for icu in ipo:
                    i=0
                    while i<len(icu.bezierPoints):
                        if icu.bezierPoints[i].pt[0]>len(vals[boneno]):
                            icu.delBezier(i)
                        else:
                            i+=1
                # Rename
                action.renameChannel(oldchannel, name)
        # Update any other Actions' channels?

    armobj.update()    # apply new bone names

    # Reparent children - have to do this after new bone names are applied
    for obj in Scene.GetCurrent().objects:
        if obj.parent==armature and obj.parentbonename in oldnames:
            obj.parentbonename=newnames[oldnames.index(obj.parentbonename)]

    # Now do properties
    props={}

    # First do dataref paths for datarefs and hide/show
    for dataref in datarefs+hideshow:
        ref=dataref.split('/')
        if len(ref)>1 and (ref[-1] not in lookup or not lookup[ref[-1]]):
            # not a standard dataref
            props[ref[-1]]='/'.join(ref[:-1])

    # datarefs values
    for boneno in range(len(datarefs)):
        ref=datarefs[boneno].split('/')
        name=make_short_name(datarefs[boneno])
        #name=ref[-1]
        if indices[boneno]!=None: name='%s[%d]' % (name, indices[boneno])
        if len(ref)>1 or name in lookup:
            # write vals for ambiguous and unusable datarefs, but not invalid
            for frameno in range(len(vals[boneno])):
                if not ((frameno==0 and vals[boneno][frameno]==0) or
                        (frameno==(len(vals[boneno])-1) and vals[boneno][frameno]==1)):
                    props['%s_v%d' % (name, frameno+1)]=vals[boneno][frameno]
                if loops[boneno]:
                    props[name+'_loop']=loops[boneno]

    # Apply
    armature.removeAllProperties()
    keys=props.keys()
    keys.sort()
    for key in keys:
        armature.addProperty(key, props[key])

    # Create properties for the manipulators
    manipulator = manipulators[0]
    sub_dict = sorted(manipulator_dict[manipulator].keys())
    armature.addProperty('manipulator_type', manipulator )

    for field_id in sub_dict:
        field_name = field_id.split('@')[1]
        field_val = manipulator_dict[manipulator][field_id]
        property_name = manipulator + '_' + field_name
        if field_name == 'cursor':
            armature.addProperty(property_name, cursors[0])
        else:
            armature.addProperty(property_name, field_val)

    # Hide/Show - order is significant
    h=1
    s=1
    for hs in range(len(hideshow)):
        name=hideshow[hs].split('/')[-1]
        if hideshowindices[hs]!=None: name='%s[%d]' % (name, hideshowindices[hs])
        if hideorshow[hs]:
            armature.addProperty('%s_show_v%d' % (name, s), hideshowfrom[hs])
            armature.addProperty('%s_show_v%d' % (name, s+1), hideshowto[hs])
            s+=2
        else:
            armature.addProperty('%s_hide_v%d' % (name, h), hideshowfrom[hs])
            armature.addProperty('%s_hide_v%d' % (name, h+1), hideshowto[hs])
            h+=2

    Draw.Exit()
    if editmode: Window.EditMode(1)
    Window.RedrawAll()    # in case bone names have changed
    return


# the function to handle input events
def event (evt, val):
    global vertical, mousex, mousey, anchor, offset

    if evt == Draw.ESCKEY and not val:
        if anchor:
            anchor=None
        else:
            Draw.Exit()                 # exit when user releases ESC
    elif evt==Draw.MOUSEX:
        mousex=val
        if anchor:
            offset=(max(0,anchor[0]-mousex), offset[1])
            Draw.Redraw()
    elif evt==Draw.MOUSEY:
        mousey=val
        if anchor:
            offset=(offset[0], min(0,anchor[1]-mousey))
            Draw.Redraw()
    elif evt == Draw.MIDDLEMOUSE and val:
        anchor=(mousex+offset[0], mousey+offset[1])
    elif evt == Draw.MIDDLEMOUSE and not val:
        anchor=None
    elif anchor:
        pass    # suppress other activity while panning
    elif evt == Draw.RIGHTMOUSE and val:
        r=Draw.PupMenu('Panel Alignment%t|Horizontal|Vertical')
        if r==1:
            vertical=False
        elif r==2:
            vertical=True
        else:
            return
        Draw.Redraw()


# the function to handle Draw Button events
def bevent (evt):
    if anchor: return	# suppress other activity while panning
    boneno=evt/EVENTMAX
    event=evt-boneno*EVENTMAX
    if boneno>=bonecount:
        # hide/show
        hs=boneno-bonecount
        if event==DATAREF_B:
            hideshow[hs]=dataref_b[boneno].val
            ref=hideshow[hs].split('/')
            if len(ref)==1:
                # lookup
                if hideshow[hs] in lookup and lookup[hideshow[hs]]:
                    (path, n)=lookup[hideshow[hs]]
                    hideshow[hs]=path
        elif event==INDICES_B:
            hideshowindices[hs]=indices_b[boneno].val
        elif event==INDICES_T:
            if indices_t[boneno].val and hideshowindices[hs]==None:
                hideshowindices[hs]=0
            elif not indices_t[boneno].val:
                hideshowindices[hs]=None
        elif event==HIDEORSHOW_M:
            hideorshow[hs]=hideshow_m[hs].val
        elif event==FROM_B:
            hideshowfrom[hs]=from_b[hs].val
        elif event==TO_B:
            hideshowto[hs]=to_b[hs].val
        elif event==DELETE_B:
            hideshow.pop(hs)
            hideorshow.pop(hs)
            hideshowindices.pop(hs)
            hideshowfrom.pop(hs)
            hideshowto.pop(hs)
        elif event==UP_B and hs:
            swaphideshow(hs-1, hs)
        elif event==DOWN_B and hs<len(hideshow)-1:
            swaphideshow(hs, hs+1)
        elif event==ADD_B:
            hideshow.append('')
            hideorshow.append(0)
            hideshowindices.append(None)
            hideshowfrom.append(0.0)
            hideshowto.append(1.0)
        elif event==CANCEL_B:
            Draw.Exit()
        else:
            return	# eh?
    else:
        if event==DATAREF_B:
            datarefs[boneno]=dataref_b[boneno].val
            ref=datarefs[boneno].split('/')
            if len(ref)==1:
                # lookup
                if datarefs[boneno] in lookup and lookup[datarefs[boneno]]:
                    (path, n)=lookup[datarefs[boneno]]
                    datarefs[boneno]=path
        elif event==INDICES_B:
            indices[boneno]=indices_b[boneno].val
        elif event==INDICES_T:
            if indices_t[boneno].val and indices[boneno]==None:
                indices[boneno]=0
            elif not indices_t[boneno].val:
                indices[boneno]=None
        elif event==DELETE_B:
            vals[boneno].pop()
        elif event>=LOOPS_B:
            if event==LOOPS_B:
                loops[boneno]=loops_b[boneno].val
            else:
                vals[boneno][event-VALS_B]=vals_b[boneno][event-VALS_B].val
            # Update other bones with same name & index for consistency
            framecount=len(vals[boneno])
            for i in range(len(bones)):
                if datarefs[i]==datarefs[boneno] and indices[i]==indices[boneno]:
                    loops[i]=loops[boneno]
                    for j in range(min(framecount,len(vals[i]))):
                        vals[i][j]=vals[boneno][j]
        else:
            return	# eh?
    Draw.Redraw()


def datarefmenucallback(event, val):
    if val==-1: return
    rows=Window.GetScreenSize()[1]/20-1		# 16 point plus space
    boneno=event/EVENTMAX
    if has_sim:
        ref=['sim',firstlevel[val-1]]
        this=hierarchy['sim'][firstlevel[val-1]]
    else:
        ref=[firstlevel[val-1]]
        this=hierarchy[firstlevel[val-1]]
    while True:
        keys=this.keys()
        keys.sort(lambda x,y: cmp(x.lower(), y.lower()))
        opts=[]
        for i in range(len(keys)):
            key=keys[i]
            if isinstance(this[key], dict):
                opts.append('%s/...' % key)
            elif this[key]:	# not illegal
                opts.append('%s' % key)
        val=Draw.PupMenu('/'.join(ref)+'/%t|'+'|'.join(opts), rows)
        if val==-1: return
        ref.append(keys[val-1])
        this=this[keys[val-1]]
        if not isinstance(this, dict):
            if boneno>=bonecount:
                hideshow[boneno-bonecount]='/'.join(ref)
            else:
                datarefs[boneno]='/'.join(ref)
            # disambiguate all similar bones/hideshow in armature
            for i in range(len(datarefs)):
                if datarefs[i]==ref[-1]: datarefs[i]='/'.join(ref)
            for i in range(len(hideshow)):
                if hideshow[i]==ref[-1]: hideshow[i]='/'.join(ref)
            Draw.Redraw()
            return

# User changed manipulator drop down. Update manipulator GUI
def manipulatormenucallback(event, val):
    if val==-1: return
    boneno=event/EVENTMAX
    manipulators[boneno] = manipulatorList[val-1]
    Draw.Redraw()
    return

# User changed cursor drop down. Update GUI
def cursormenucallback(event, val):
    if val==-1: return
    boneno=event/EVENTMAX
    cursors[boneno] = cursorList[val-1]
    Draw.Redraw()
    return

def manipulatordatacallback(event, val):
    event -= 1000

    # This is a bug. Manipulator only works on the parent bone
    manipulator = manipulators[0]
    key = sorted(manipulator_dict[manipulator].keys())[event]
    manipulator_dict[manipulator][key] = val
    return

# the function to draw the screen
def gui():
    global dataref_m, dataref_b, indices_b, indices_t, vals_b, clear_b, loops_b
    global hideshow_m, from_b, to_b, up_b, down_b, delete_b, addhs_b
    global cancel_b, apply_b
    global manipulator_m, manipulator_b, cursor_m, cursor_b

    dataref_m=[]
    dataref_b=[]
    indices_b=[]
    indices_t=[]
    vals_b=[]
    clear_b=None
    loops_b=[]
    hideshow_m=[]
    from_b=[]
    to_b=[]
    up_b=[]
    down_b=[]
    delete_b=[]
    addhs_b=None
    cancel_b=None
    apply_b=None


    # Default theme
    text   =[  0,   0,   0, 255]
    text_hi=[255, 255, 255, 255]
    header =[165, 165, 165, 255]
    panel  =[255, 255, 255,  40]
    back   =[180, 180, 180, 255]
    error  =[255,  80,  80, 255]	# where's the theme value for this?

    # Actual theme
    if Blender.Get('version') >= 235:
        theme=Blender.Window.Theme.Get()
        if theme:
            theme=theme[0]
            space=theme.get('buts')
            text=theme.get('ui').text
            text_hi=space.text_hi
            header=space.header
            header=[max(header[0]-30, 0),	# 30 appears to be hard coded
                    max(header[1]-30, 0),
                    max(header[2]-30, 0),
                    header[3]]
            panel=space.panel
            back=space.back

    size=BGL.Buffer(BGL.GL_FLOAT, 4)
    BGL.glGetFloatv(BGL.GL_SCISSOR_BOX, size)
    size=size.list
    x=int(size[2])
    y=int(size[3])

    BGL.glEnable(BGL.GL_BLEND)
    BGL.glBlendFunc(BGL.GL_SRC_ALPHA, BGL.GL_ONE_MINUS_SRC_ALPHA)
    BGL.glClearColor(float(back[0])/255, float(back[1])/255, float(back[2])/255, 1)
    BGL.glClear(BGL.GL_COLOR_BUFFER_BIT)

    yoff=y-offset[1]
    if vertical:
        xoff=PANELPAD+PANELINDENT-offset[0]

    for boneno in range(bonecount):
        eventbase=boneno*EVENTMAX
        framecount=len(vals[boneno])
        if not vertical:
            xoff=PANELPAD+boneno*(PANELWIDTH+PANELPAD)+PANELINDENT-offset[0]
        BGL.glColor4ub(*header)
        BGL.glRectd(xoff-PANELINDENT, yoff-PANELTOP, xoff-PANELINDENT+PANELWIDTH, yoff-PANELTOP-PANELHEAD)
        BGL.glColor4ub(*panel)
        BGL.glRectd(xoff-PANELINDENT, yoff-PANELTOP-PANELHEAD, xoff-PANELINDENT+PANELWIDTH, yoff-170-(CONTROLSIZE-1)*framecount)

        txt='parent bone'
        if boneno: txt='grand'+txt
        txt='great-'*(boneno-1)+txt
        txt=txt[0].upper()+txt[1:]
        BGL.glColor4ub(*text_hi)
        BGL.glRasterPos2d(xoff, yoff-23)
        Draw.Text(txt)

        Draw.Label("Dataref:", xoff-4, yoff-54, 100, CONTROLSIZE)
        BGL.glColor4ub(*error)	# For errors
        (valid,mbutton,bbutton,ibutton,tbutton)=drawdataref(datarefs, indices, eventbase, boneno, xoff-4, yoff-80)
        dataref_m.append(mbutton)
        dataref_b.append(bbutton)
        indices_b.append(ibutton)
        indices_t.append(tbutton)

        vals_b.append([])
        if valid:
            # is a valid or custom dataref
            Draw.Label("Dataref values:", xoff-4, yoff-132, 150, CONTROLSIZE)
            for i in range(framecount):
                Draw.Label("Frame #%d:" % (i+1), xoff-4+CONTROLSIZE, yoff-152-(CONTROLSIZE-1)*i, 100, CONTROLSIZE)
                if i>1:
                    v9='v9: '
                else:
                    v9=''
                vals_b[-1].append(Draw.Number('', i+VALS_B+eventbase, xoff+104, yoff-152-(CONTROLSIZE-1)*i, 80, CONTROLSIZE, vals[boneno][i], -NUMBERMAX, NUMBERMAX, v9+'The dataref value that corresponds to the pose in frame %d' % (i+1)))
            if framecount>2:
                clear_b=Draw.Button('Delete', DELETE_B+eventbase, xoff+208, yoff-152-(CONTROLSIZE-1)*(framecount-1), 80, CONTROLSIZE, 'Clear animation keys from this frame')
            Draw.Label("Loop:", xoff-4+CONTROLSIZE, yoff-160-(CONTROLSIZE-1)*framecount, 100, CONTROLSIZE)
            loops_b.append(Draw.Number('', LOOPS_B+eventbase, xoff+104, yoff-160-(CONTROLSIZE-1)*framecount, 80, CONTROLSIZE, loops[boneno], -NUMBERMAX, NUMBERMAX, 'v9: The animation will loop back to frame 1 when the dataref value exceeds this number. Enter 0 for no loop.'))
        else:
            loops_b.append(None)

        if vertical:
            yoff-=(170+(CONTROLSIZE-1)*framecount)

        #Draw Manipulator GUI
        if valid:
            Draw.Label("Manipulator:", xoff-4, yoff-220-(CONTROLSIZE-1)*i, 100, CONTROLSIZE)
            drawmanipulator(manipulators, indices, eventbase, boneno, xoff-4, yoff-250-(CONTROLSIZE-1)*i)



    if not vertical:
        xoff=PANELPAD+bonecount*(PANELWIDTH+PANELPAD)+PANELINDENT-offset[0]
    BGL.glColor4ub(*header)
    BGL.glRectd(xoff-PANELINDENT, yoff-PANELTOP, xoff-PANELINDENT+PANELWIDTH, yoff-PANELTOP-PANELHEAD)
    BGL.glColor4ub(*panel)
    BGL.glRectd(xoff-PANELINDENT, yoff-PANELTOP-PANELHEAD, xoff-PANELINDENT+PANELWIDTH, yoff-64-len(hideshow)*82)

    BGL.glColor4ub(*text_hi)
    BGL.glRasterPos2d(xoff, yoff-23)
    Draw.Text("Hide/Show for all children of %s" % armature.name)

    for hs in range(len(hideshow)):
        eventbase=(bonecount+hs)*EVENTMAX
        BGL.glColor4ub(*panel)
        BGL.glRectd(xoff-4, yoff-PANELTOP-PANELHEAD-4-hs*82, xoff-13+PANELWIDTH, yoff-PANELTOP-101-hs*82)
        BGL.glColor4ub(*error)	# For errors
        (valid,mbutton,bbutton,ibutton,tbutton)=drawdataref(hideshow, hideshowindices, eventbase, hs, xoff-4, yoff-54-hs*82)
        dataref_m.append(mbutton)
        dataref_b.append(bbutton)
        indices_b.append(ibutton)
        indices_t.append(tbutton)
        if hs:
            up_b.append(Draw.Button('^', UP_B+eventbase, xoff+217, yoff-80-hs*82, CONTROLSIZE, CONTROLSIZE, 'Move this entry up'))
        else:
            up_b.append(None)
        if hs!=len(hideshow)-1:
            down_b.append(Draw.Button('v', DOWN_B+eventbase, xoff+237, yoff-80-hs*82, CONTROLSIZE, CONTROLSIZE, 'Move this entry down'))
        else:
            down_b.append(None)
        delete_b.append(Draw.Button('X', DELETE_B+eventbase, xoff+267, yoff-80-hs*82, CONTROLSIZE, CONTROLSIZE, 'Delete this entry'))
        if valid:
            # is a valid or custom dataref
            hideshow_m.append(Draw.Menu('Hide%x0|Show%x1', HIDEORSHOW_M+eventbase, xoff, yoff-106-hs*82, 62, CONTROLSIZE, hideorshow[hs], 'Choose Hide or Show'))
            Draw.Label("when", xoff+63, yoff-106-hs*82, 60, CONTROLSIZE)
            from_b.append(Draw.Number('', FROM_B+eventbase, xoff+104, yoff-106-hs*82, 80, CONTROLSIZE, hideshowfrom[hs], -NUMBERMAX, NUMBERMAX, 'The dataref value above which the animation will be hidden or shown'))
            Draw.Label("to", xoff+187, yoff-106-hs*82, 60, CONTROLSIZE)
            to_b.append(Draw.Number('', TO_B+eventbase, xoff+207, yoff-106-hs*82, 80, CONTROLSIZE, hideshowto[hs], -NUMBERMAX, NUMBERMAX, 'The dataref value below which the animation will be hidden or shown'))
        else:
            hideshow_m.append(None)
            from_b.append(None)
            to_b.append(None)
    addhs_b=Draw.Button('Add New', ADD_B+bonecount*EVENTMAX, xoff+217, yoff-54-len(hideshow)*82, 70, CONTROLSIZE, 'Add a new Hide or Show entry')

    if vertical:
        xoff=PANELPAD-offset[0]
        yoff-=(64+len(hideshow)*82)
    else:
        xoff=PANELPAD+(bonecount+1)*(PANELWIDTH+PANELPAD)-offset[0]
    apply_b=Draw.Button('Apply', APPLY_B+bonecount*EVENTMAX, xoff, yoff-PANELTOP-CONTROLSIZE*2, 80, CONTROLSIZE*2, 'Apply these settings', doapply)
    if vertical:
        cancel_b=Draw.Button('Cancel', CANCEL_B+bonecount*EVENTMAX, xoff+80+PANELPAD, yoff-PANELTOP-CONTROLSIZE*2, 80, CONTROLSIZE*2, 'Retain existing settings')
    else:
        cancel_b=Draw.Button('Cancel', CANCEL_B+bonecount*EVENTMAX, xoff, yoff-PANELTOP-CONTROLSIZE*4-PANELPAD, 80, CONTROLSIZE*2, 'Retain existing settings')



def drawdataref(datarefs, indices, eventbase, boneno, x, y):

    dataref=datarefs[boneno]
    valid=True

    mbutton=Draw.Menu('sim/%t|'+'/...|'.join(firstlevel)+'/...', DONTCARE+eventbase, x+4, y, CONTROLSIZE, CONTROLSIZE, -1, 'Pick the dataref from a list', datarefmenucallback)
    bbutton=Draw.String('', DATAREF_B+eventbase, x+4+CONTROLSIZE, y, PANELWIDTH-2*PANELINDENT-CONTROLSIZE, CONTROLSIZE, dataref, 100, 'Full name of the dataref used to animate this object')

    ibutton=None
    tbutton=None
    ref=dataref.split('/')
    if len(ref)<=1 or ref[0]=='sim':
        if len(ref)==1 and ref[0] in lookup and not lookup[ref[0]]:
            BGL.glRasterPos2d(x+4, y-21)
            Draw.Text('This dataref name is ambiguous')
            valid=False
        else:
            try:
                thing=hierarchy
                for i in range(len(ref)):
                    thing=thing[ref[i]]
                n=thing+0	# check is a leaf - ie numeric
                if not n:
                    BGL.glRasterPos2d(x+4, y-21)
                    Draw.Text("This dataref can't be used for animation")
                    valid=False
                elif n==1:
                    indices[boneno]=None
                else:
                    if indices[boneno]==None or indices[boneno]>=n:
                        indices[boneno]=0
                    Draw.Label("Part number:", x, y-26, 120, CONTROLSIZE)
                    ibutton=Draw.Number('', INDICES_B+eventbase, x+108, y-26, 50, CONTROLSIZE, indices[boneno], 0, n-1, 'The part number / array index')
            except:
                BGL.glRasterPos2d(x+4, y-21)
                Draw.Text("This is not a valid dataref")
                valid=False
    else:
        if indices[boneno]!=None:
            val=1
        else:
            val=0
        tbutton=Draw.Toggle('Part number', INDICES_T+eventbase, x+4, y-26, 104, CONTROLSIZE, val, 'Whether this is an array dataref')
        if val:
            ibutton=Draw.Number('', INDICES_B+eventbase, x+108, y-26, 50, CONTROLSIZE, indices[boneno], 0, 729, 'The part number / array index')

    return (valid, mbutton,bbutton,ibutton,tbutton)


# Draw the GUI for the manipulator entry area.
# Selection of the manipulator will determine that fields that are displayed
# See XPlaneUtils.py::getManipulators() for the manipluator definitions
#
# The data gets stored utilizing the manipulatordatacallback function
# The event_id (starting at 1000 to not interfere with Marginal's events)
# is an ugly hack to determine which field is being modified.
def drawmanipulator(manipulators, indices, eventbase, boneno, x, y):

    # See Blender Python Docs
    # http://www.blender.org/documentation/248PythonDoc/Draw-module.html

    manipulator = manipulators[boneno]
    cursor = cursors[boneno]
    valid = True

    Draw.Menu('|'.join(manipulatorList), DONTCARE+eventbase, x+4, y, CONTROLSIZE, CONTROLSIZE, -1, 'Pick the manipulator from a list', manipulatormenucallback)
    Draw.String('', DATAREF_B+eventbase, x+4+CONTROLSIZE, y, PANELWIDTH-2*PANELINDENT-CONTROLSIZE, CONTROLSIZE, manipulator, 100, 'Full name of the manipulator used to control this animation')
    y -= 30
    event_id = 1000
    sub_dict = sorted(manipulator_dict[manipulator].keys())

    for field_id in sub_dict:
        field_name = field_id.split('@')[1]
        field_val = manipulator_dict[manipulator][field_id]

        if field_name == 'cursor':
            Draw.Label("Cursor Type:", x, y, 100, CONTROLSIZE)
            Draw.Menu('|'.join(cursorList), DONTCARE+eventbase, x+4, y, CONTROLSIZE, CONTROLSIZE, -1, 'Pick the cursor type from a list', cursormenucallback)
            Draw.String('', DATAREF_B+eventbase, x+4+CONTROLSIZE, y, PANELWIDTH-2*PANELINDENT-CONTROLSIZE, CONTROLSIZE, cursor, 100, 'Full name of the manipulator used to control this animation')
            y -= 30
            event_id += 1
        elif field_name != 'NULL':
            Draw.Label(field_name + ':', x, y, 120, CONTROLSIZE)

            if type(field_val).__name__ == 'str':
                Draw.String('', event_id, x+100, y, 180, CONTROLSIZE, field_val, 100, '', manipulatordatacallback)

            if type(field_val).__name__ == 'float':
                Draw.Number('', event_id, x+100, y, 80, CONTROLSIZE, field_val, -50000.0,50000.0, '', manipulatordatacallback)

            if type(field_val).__name__ == 'int':
                Draw.Number('', event_id, x+100, y, 80, CONTROLSIZE, int(field_val), -50000,50000, '', manipulatordatacallback)

            y -= 20
            event_id += 1

    return valid


if __name__=='__main__' and getparents():

    # Init manipulator data
    manipulator_dict,cursorList = getManipulators()
    for ii in manipulator_dict.keys():
        manipulatorList.append(ii)

    (manipulator, cursor) = getmanipulatorvals()
    manipulators.append(manipulator)
    cursors.append(cursor)

    bonecount=len(bones)
    # Get values for other bones in armature too
    for bone in armature.getData().bones.values():
        if bone not in bones:
            bones.append(bone)

    for bone in bones:
        dataref=bone.name.split('.')[0]

        # split off index
        index=None
        l=dataref.find('[')
        if l!=-1:
            i=dataref[l+1:-1]
            if dataref[-1]==']':
                try:
                    index=int(i)
                except:
                    pass
            dataref=dataref[:l]

        # Data INIT here
        (dataref,v,l)=getvals(bone.name, dataref, index)
        datarefs.append(dataref)
        indices.append(index)
        vals.append(v)
        loops.append(l)

    gethideshow()


    #print armature, bones, bonecount, datarefs, indices, vals, loops
    #print hideshow, hideorshow, hideshowindices, hideshowfrom, hideshowto

    vertical=(Window.GetAreaSize()[1]>Window.GetAreaSize()[0])
    Draw.Register (gui, event, bevent)
