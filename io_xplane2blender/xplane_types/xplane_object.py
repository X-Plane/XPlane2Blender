import itertools
from typing import Dict, List, Optional

import bpy
import mathutils

from io_xplane2blender.xplane_config import getDebug
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_helpers import *
from io_xplane2blender.xplane_types import xplane_bone
from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute
from io_xplane2blender.xplane_types.xplane_attributes import XPlaneAttributes


class XPlaneObject:
    """
    An object in the XPlane2Blender collection tree,
    tied with the Blender Object it is based off.
    """

    def __init__(self, blenderObject: bpy.types.Object) -> None:
        # When true, keyframes and Custom Animation Properties
        # are included in OBJ
        # True for split parent feature or not visible
        self.export_animation_only = (
            blenderObject.hide_get() or blenderObject.hide_viewport
        )
        self.blenderObject = blenderObject

        # This is assigned and tied together in in XPlaneBone's constructor
        self.xplaneBone = None  # type: xplane_bone.XPlaneBone
        self.name = blenderObject.name  # type: str
        self.type = self.blenderObject.type  # type: str
        self.datarefs = {}  # type: Dict[str,str]
        self.bakeMatrix = None  # type: Optional[mathutils.Matrix]

        self.attributes = XPlaneAttributes()
        self.cockpitAttributes = XPlaneAttributes()
        self.animAttributes = XPlaneAttributes()
        self.conditions = (
            []
        )  # type: List[io_xplane2blender.xplane_props.XPlaneCondition]

        # This represents all specializations of lods, on this subject,
        # including it's parents. Set in XPlaneBone's constructor
        self.effective_buckets: Tuple[...] = (False,) * 4
        for i, dataref in self.blenderObject.xplane.datarefs.items():
            self.datarefs[dataref.path] = dataref

        self.setWeight()

    def __str__(self):
        return "\n".join(
            (
                f"Name: {self.name}",
                f"Type: {self.type}",
                f"Datarefs: {len(self.datarefs)}",
                f"Effective LOD buckets: {self.effective_buckets}",
                f"Weight: {self.weight}",
            )
        )

    def collect(self) -> None:
        assert self.xplaneBone is not None, "xplaneBone must not be None!"
        if self.export_animation_only:
            # add anim attributes from datarefs and custom anim attributes
            self.collectAnimAttributes()
            return

        # add custom attributes
        self.collectCustomAttributes()

        # add anim attributes from datarefs and custom anim attributes
        self.collectAnimAttributes()

        # add conditions
        self.collectConditions()

        self.attributes.order()
        self.animAttributes.order()
        self.cockpitAttributes.order()

    def collectCustomAttributes(self):
        xplaneFile = self.xplaneBone.xplaneFile
        commands = xplaneFile.commands

        for attr in self.blenderObject.xplane.customAttributes:
            if attr.reset:
                commands.addReseter(attr.name, attr.reset)
            self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

        if (
            hasattr(self.blenderObject, "data")
            and hasattr(self.blenderObject.data, "xplane")
            and hasattr(self.blenderObject.data.xplane, "customAttributes")
        ):
            for attr in self.blenderObject.data.xplane.customAttributes:
                if attr.reset:
                    commands.addReseter(attr.name, attr.reset)
                self.attributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

    def collectAnimAttributes(self):
        # add custom anim attributes
        for attr in self.blenderObject.xplane.customAnimAttributes:
            self.animAttributes.add(XPlaneAttribute(attr.name, attr.value, attr.weight))

        # add anim attributes from datarefs
        for dataref in self.blenderObject.xplane.datarefs:
            # show/hide animation
            if dataref.anim_type in (ANIM_TYPE_SHOW, ANIM_TYPE_HIDE):
                name = "ANIM_" + dataref.anim_type
                value = (dataref.show_hide_v1, dataref.show_hide_v2, dataref.path)
                self.animAttributes.add(XPlaneAttribute(name, value))

    def setWeight(self, defaultWeight: int = 0):
        """
        Sets the weight of the object, if overriden, based
        its weight and the weight of its attributes
        """
        weight = defaultWeight

        if (
            hasattr(self.blenderObject.xplane, "override_weight")
            and self.blenderObject.xplane.override_weight
        ):
            weight = self.blenderObject.xplane.weight
        else:
            try:
                weight += max(
                    [
                        attr.weight
                        for attr in itertools.chain(
                            self.attributes.values(), self.cockpitAttributes.values()
                        )
                    ]
                )
            except ValueError:
                pass

        self.weight = weight

    def collectConditions(self):
        if self.blenderObject.xplane.conditions:
            self.conditions = self.blenderObject.xplane.conditions

    # Returns OBJ code for this object
    def write(self) -> str:
        """
        Writes collected Blender and XPlane data as a \\n
        seperated string of OBJ directives.
        """
        if self.export_animation_only:
            return ""

        debug = getDebug()
        o = ""

        xplaneFile = self.xplaneBone.xplaneFile
        commands = xplaneFile.commands

        if debug:
            indent = self.xplaneBone.getIndent()
            o += f"{indent}# {self.type}: {self.name}\tweight: {self.weight}\n"

        o += commands.writeReseters(self)

        for attr in self.attributes:
            o += commands.writeAttribute(self.attributes[attr], self)

        # if the file is a cockpit file write all cockpit attributes
        if xplaneFile.options.export_type == EXPORT_TYPE_COCKPIT:
            for attr in self.cockpitAttributes:
                o += commands.writeAttribute(self.cockpitAttributes[attr], self)

        return o
