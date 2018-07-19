import math

import bpy
from io_xplane2blender import xplane_config
from io_xplane2blender import xplane_helpers
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

        #TODO: Change 'empty' becaues it is too vauge? Def.
        empty = self.blenderObject.xplane.empty
        o = ''

        if (int(bpy.context.scene.xplane.version) >= 1130 and
                (empty.special_type == EMPTY_USAGE_EMITTER_PARTICLE or
                empty.special_type == EMPTY_USAGE_EMITTER_SOUND)):
            bake_matrix = self.xplaneBone.getBakeMatrixForAttached()
            print(bake_matrix)
            translation = bake_matrix.to_translation()
            print(translation)
            em_location = xplane_helpers.vec_b_to_x(translation)
            #yaw,pitch,roll
            theta,psi,phi = [math.degrees(comp) for comp in bake_matrix.to_euler()[:]]
            o += 'EMITTER {name} {x} {y} {z} {phi} {theta} {psi}'.format(
                    name=empty.emitter_props.name,
                    x=em_location.x,
                    y=em_location.y,
                    z=em_location.z,
                    phi=-phi, #yaw right
                    theta=theta, #pitch up
                    psi=psi) #roll right

            if empty.emitter_props.index > 0:
                o += ' {}'.format(empty.emitter_props.index)
            print(o)

            o +='\n'

        return o

