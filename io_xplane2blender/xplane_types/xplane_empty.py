import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender.xplane_constants import *
from io_xplane2blender.xplane_types import XPlaneObject


class XPlaneEmpty(XPlaneObject):
    def __init__(self,blenderObject):
        assert blenderObject.type == 'EMPTY'
        super().__init__(blenderObject)
        self.type = 'EMPTY'

    def collect(self):
        pass

    def write(self):
        debug = xplane_config.getDebug()
        indent = self.xplaneBone.getIndent()

        #TODO: Change 'emppy' becaues it is too vauge? Def.
        empty = self.blenderObject.xplane.empty
        o = ''

        if (empty.special_type == EMPTY_USAGE_EMITTER_PARTICLE or
            empty.special_type == EMPTY_USAGE_EMITTER_SOUND):
            o += 'EMITTER {name} {x} {y} {z} {phi} {theta} {psi}'.format(
                    name=empty.emitter_props.name,
                    x=self.blenderObject.location.x,
                    y=self.blenderObject.location.y,
                    z=self.blenderObject.location.z,
                    phi=empty.emitter_props.phi,
                    theta=empty.emitter_props.theta,
                    psi=empty.emitter_props.psi)

            if empty.emitter_props.index > 0:
                o += ' {}'.format(empty.emitter_props.index)

            o +='\n'

        return o
