from collections import OrderedDict

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

    # Method: add
    # Adds an attribute to the dict.
    #
    # Parameters:
    #   attr - A <XPlaneAttribute>
    def add(self, attr):
        if attr.name in self:
            self[attr.name].addValues(attr.getValues())
        else:
            self[attr.name] = attr

    # Method: get
    # Returns an attribute.
    #
    # Parameters:
    #   string name - Name of the attribute
    #
    # Returns:
    #   a <XPlaneAttribute> or None
    def get(self, name):
        if name in self:
            return self[name]
        else:
            return None

    # Method: set
    # Overwrites an existing attribute.
    #
    # Paramters:
    #   attr - A <XPlaneAttribute>
    def set(self, attr):
        if attr.name in self:
            self[attr.name] = attr

    def __str__(self):
        o = ''
        for name in self:
            o += name + ': ' + self[name].getValuesAsString() + '\n'

        return o

