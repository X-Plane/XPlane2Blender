# Function: register
# Registers the addon with all its classes and the menu function.
def register():
    from io_xplane2blender.xplane_249_converter import (xplane_249_ops,
                                                        xplane_249_ui)
    xplane_249_ops.register()
    xplane_249_ui.register()

# Function: unregister
# Unregisters the addon and all its classes and removes the entry from the menu.
def unregister():
    from io_xplane2blender.xplane_249_converter import (xplane_249_ops,
                                                        xplane_249_ui)
    xplane_249_ops.unregister()
    xplane_249_ui.unregister()
