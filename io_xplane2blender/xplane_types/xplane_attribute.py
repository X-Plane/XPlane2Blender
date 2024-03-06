from typing import Any, Dict, List, Optional, Union, Callable
from functools import total_ordering

from io_xplane2blender.xplane_helpers import floatToStr

# TODO: This API is either redundent or self.value should be private.

AttributeValueType = Union[bool, float, int, str, List["AttributeValueType"]]
AttributeValueTypeList = List[AttributeValueType]

"""
Lord forgive me for what I'm about to do
"""
@total_ordering
class XPlaneAttributeName(str):
    def __new__(
        cls, name: str, instance: int = 0
    ):
        attribute_name = super().__new__(cls, name)
        attribute_name.instance = instance

        return attribute_name
    
    def __eq__(
        self, other
    ):
        if type(other) == str:
            return self.__str__() == other and self.instance == 0
        else:
            return self.__str__() == other.__str__() and self.instance == other.instance
        
    def __lt__(
        self, other
    ):
        if type(other) == str:
            return self.__str__() < other.__str__()
        else:
            if self.__str__() == other.__str__():
                return self.instance < other.instance
            else:
                return self.__str__() < other.__str__()
    
    def __hash__(
        self
    ):
        if self.instance == 0:
            return hash(self.__str__())
        else:
            return hash((self.__str__(), self.instance))

class XPlaneAttribute:
    """
    XPlaneAttributes are the data class for what will eventually be written as commands in the
    OBJ. Names usually start with "ATTR_"
    """

    def __init__(
        self, name: Union[XPlaneAttributeName, str], value: Optional[AttributeValueType] = None, weight: int = 0
    ):
        """
        name - OBJ directive name, usually starts with 'ATTR_'
        value - Directive value, False and None prevent the atttribute from writing. Use "True"/"False" as a str if needed
        weight - Indicates where the attribute should be in the OBJ File
        """
        self.name = name
        self.value: AttributeValueTypeList = [value]
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

        None -> ""
        bool (True) -> ""
        float -> floatToStr(value)
        int -> str(value)
        list -> for each member, bool->int(bool), float and int see above
        str -> str

        XPlaneAttribute.setValue(True/False) is used to indicate to activate
        this or not, boolean values in a sub-list are treated as OBJ 0 or 1
        """
        fmt_type:Dict[Union[bool, float, int, str], Callable] = {
                type(None): lambda v: "",
                bool: lambda v: str(int(v)), # Used in list convertion only
                float: lambda v: floatToStr(v),
                int: lambda v: str(int(v)),
                str: lambda v: v,
            }
        value = self.getValue(i)

        if isinstance(value, bool):
            # setValue(True/False) is used as activation, not a value
            value = ""
        elif isinstance(value, (list, tuple)):
            try:
                value = "\t".join(fmt_type[type(v)](v) for v in value)
            except KeyError:
                assert False, f"{self.name}, {self.value}: Has value that cannot be convereted to string"
        else:
            try:
                value = fmt_type[type(value)](value)
            except KeyError:
                assert False, f"{self.name}, {self.value}: Has value that cannot be converted to a string"

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
