from collections import OrderedDict
from typing import Optional

from io_xplane2blender.xplane_types.xplane_attribute import XPlaneAttribute


# Class: XPlaneAttributes
# A Wrapper for OrderedDict that stores a collection of <XPlaneAttribute>.
class XPlaneAttributes(OrderedDict):
    def __init__(self):
        super(XPlaneAttributes, self).__init__()

    # Method: order
    # Sorts items by weight.
    def order(self):
        max_weight = 0

        # this prevents the OrderedDict to be mutated during iteration
        names = []
        for name in self:
            names.append(name)

        for name in names:
            if self[name].weight > max_weight:
                self.move_to_end(name, True)
                max_weight = self[name].weight

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
