from collections import OrderedDict
from typing import Optional

from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute


# Class: XPlaneAttributes
# A Wrapper for OrderedDict that stores a collection of <XPlaneAttribute>.
class XPlaneAttributes(OrderedDict):
    def __init__(self):
        super(XPlaneAttributes, self).__init__()

    def order(self):
        """Sorts dict by attribute weight"""
        for k, v in dict(sorted(self.items(), key=lambda item: item[1].weight)).items():
            self[k] = v
        return

    def add(self, attr: XPlaneAttribute):
        if attr.name in self:
            self[attr.name].addValues(attr.getValues())
        else:
            self[attr.name] = attr

    def get(self, name: str) -> Optional[XPlaneAttribute]:
        if name in self:
            return self[name]
        else:
            return None

    def set(self, attr: XPlaneAttribute) -> None:
        if attr.name in self:
            self[attr.name] = attr

    def __str__(self) -> str:
        o = ""
        for name in self:
            o += name + ": " + self[name].getValuesAsString() + "\n"

        return o
