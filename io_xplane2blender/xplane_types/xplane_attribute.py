from ..xplane_helpers import floatToStr

# Class: XPlaneAttribute
# An Attribute
class XPlaneAttribute():
    name = ''
    value = None
    weight = 0

    # Constructor: __init__
    #
    # Parameters:
    #   string name - Name of the attribute
    #   mixed value - (default = None) Either a string or boolean
    #   int weight - (default = 0) The attribute weight. Bigger weight will write the attribute later in the OBJ file.
    def __init__(self, name, value = None, weight = 0):
        self.name = name
        self.value = [value]
        self.weight = weight

    # Method: addValue
    # Adds a value to the attribute.
    #
    # Parameters:
    #   mixed value - Either a string or boolean
    def addValue(self, value):
        if value not in self.values:
            self.value.append(value)

    # Method: addValues
    # Add multiple values at once to the attribute.
    #
    # Parameters:
    #   list values - A list of values.
    def addValues(self, values):
        for value in values:
            if value not in self.value:
                self.value.append(value)

    # Method: setValue
    # Overwrites the current attribute value.
    #
    # Parameters:
    #   mixed value - Either a string or boolean
    #   int i - (default = 0) The index of the value.
    def setValue(self, value, i = 0):
        self.value[i] =  value

    # Method: getValue
    # Return the current value of the attribute.
    #
    # Paramters:
    #   int i - (default = 0) The index of the value.
    #
    # Returns:
    #   mixed - The value
    def getValue(self, i = 0):
        return self.value[i]

    # Method: getValueAsString
    # Returns the current value of the attribute as a string
    #
    # Parameters:
    #   int i - (default = 0) The index of the value.
    #
    # Returns:
    #   string - The value as string
    def getValueAsString(self, i = 0):
        value = self.getValue(i)

        if value == None:
            return ''

        # convert floats to strings
        if isinstance(value, float):
            value = floatToStr(value)
        # convert lists to strings
        elif isinstance(value, list) or isinstance(value, tuple) and len(value) > 0:
            _value = []
            for i in range(0, len(value)):
                # convert floats to strings
                if isinstance(value[i], float):
                    _value.append(floatToStr(value[i]))
                else:
                    _value.append(str(value[i]))

            value = '\t'.join(_value)
        else:
            value = ''

        return value

    # Method: getValues
    #
    # Returns:
    #   list - All values of the attribute.
    def getValues(self):
        return self.value

    # Method: getValuesAsString
    #
    # Returns:
    #   str - All values of the attribute as a single string.
    def getValuesAsString(self):
        o = ''
        for i in range(0, len(self.value)):
            o += self.getValueAsString(i)

        return o
