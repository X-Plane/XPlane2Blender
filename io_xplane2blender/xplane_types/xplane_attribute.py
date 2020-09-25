from typing import Any, List, Optional, Union

from io_xplane2blender.xplane_helpers import floatToStr

# TODO: This API is either redundent or self.value should be private.

AttributeValueType = Union[bool, float, int, str]
AttributeValueTypeList = List[Optional[AttributeValueType]]


class XPlaneAttribute:
    """
    XPlaneAttributes are the data class for what will eventually be written as commands in the
    OBJ. Names usually start with "ATTR_"
    """

    def __init__(
        self, name: str, value: Optional[AttributeValueType] = None, weight: int = 0
    ):
        """
        weight indicates where the attribute should be in the OBJ File
        """
        self.name = name
        self.value = [value]  # type: AttributeValueTypeList
        self.weight = weight

    def addValue(self, value: Optional[AttributeValueType]) -> None:
        """
        Appends a value to the XPlaneAttribute's value list
        """
        if value not in self.value:
            self.value.append(value)

    def addValues(self, values: AttributeValueTypeList):
        """
        Extends the XPlaneAttribute's value list with another list of values,
        excluding duplicates
        """
        for value in values:
            if value not in self.value:
                self.value.append(value)

    def setValue(self, value: AttributeValueType, i: int = 0):
        """Overwrites the current attribute value. Will throw is i is out of bounds"""
        self.value[i] = value

    def getValue(self, i: int = 0) -> Optional[AttributeValueType]:
        """
        Return value from the value list at a certain index i
        (because, remember, value is a list of values...)
        """
        return self.value[i]

    def getValueAsString(self, i: int = 0) -> str:
        """
        Gets the value of value[i] as a formatted string.
        If self.value[i] is a list, the list's string representation
        will be seperated with '\t's instead of ','s
        """
        value = self.getValue(i)

        if value is None:
            return ""

        # convert floats to strings
        if isinstance(value, float):
            value = floatToStr(value)
        # convert ints to strings
        elif isinstance(value, int):
            value = str(value)
        # convert lists to strings
        elif isinstance(value, list) or isinstance(value, tuple) and len(value) > 0:
            value = tuple(value)  # satisfies pylint "value is unsubscriptable"
            _value = []
            for i in range(0, len(value)):
                # convert floats to strings
                if isinstance(value[i], float):
                    _value.append(floatToStr(value[i]))
                else:
                    _value.append(str(value[i]))

            value = "\t".join(_value)
        elif not isinstance(value, str):
            value = ""

        return value

    # Method: getValues
    #
    # Returns:
    #   list - All values of the attribute.
    def getValues(self) -> AttributeValueTypeList:
        return self.value

    # Method: getValuesAsString
    #
    # Returns:
    #   str - All values of the attribute as a single string.
    def getValuesAsString(self) -> str:
        o = ""
        for i in range(0, len(self.value)):
            o += self.getValueAsString(i)

        return o

    def removeValues(self):
        self.value = []
