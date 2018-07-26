# File: xplane_updater.py
# Automagically updates blend data created with older XPlane2Blender Versions

import bpy
from bpy.app.handlers import persistent

import io_xplane2blender
from io_xplane2blender import xplane_props, xplane_helpers, xplane_constants
from io_xplane2blender.xplane_constants import LOGGER_LEVEL_ERROR,\
    LOGGER_LEVEL_INFO, LOGGER_LEVEL_SUCCESS, BLEND_GLASS
from io_xplane2blender.xplane_helpers import XPlaneLogger


'''
 #####     ##   ##  ##   ####  ####  ####  #    ### ##  ####  ####  ####    ####  ####    #####   ####    ##    ####   ###   ##  ##   ###  # 
  #   #   # #    #  #   ##  #  ## #  #  #  #     #  #   ## #  #  #  ## #    #  #  ## #     #   #  #  #   # #   ##  #  #   #   #  #   #  #  # 
 ##   #   # #   # # #  ##      ###   ###   #    #####   ###   ###   ###     ###   ###     ##   #  ###    # #  ##     ##   #  # # #   ##    # 
 ##   #  ####   # # #  #  ###  #     # #   #    #  ##   #     # #   #       # #   #       ##   #  # #   ####  #  ### #    #  # # #    ##   # 
 #   #   #  #   #  ##  ##  #   # #   # #        #  #    # #   # #   # #     # ##  # #     #   #   # #   #  #  ##  #  #   #   #  ##  #  #     
#####   ##  ## ##  #    ####  ####  ## ## #    ## ###  ####  ## ## ####    ####  ####    #####   ## ## ##  ##  ####   ###   ##  #   ####  #  

BEFORE CHANGING THIS FILE have you:
1. Fully understood what parts of the data model you are changing?
2. Written a spec and documented it?
3. Reviewed existing unit tests for correctness?
4. Created unit tests __before__ you start?
5. Quadruple checked every character, even the ones you didn't write?
6. Tested it with all versions of Blender people could be using?
7. Cross tested loading and unloading between different versions of XPlane2Blender?
8. Immediately went into a beta cycle?

Put this in your mind:
    A poor defenseless .blend file, with big watery wobbly eyes is lying on the operating table, eyeing the sharp text editors and esoteric command line commands
    about to be used on the codebase that supports it. It says
            
            Will it hurt to change the update function? Is it necessary?
            Is it deterministic and fulfills the "Only update what's needed, when needed" contract?
            Do you remember the 3.4.0 loc/rot/locrot fiasco of Aug. 2017?
    
    You hold the anesthesia mask in one hand, and a terminal prompt in the other. Are you ready to take responsibility for this data model and
    the artists who depend on it? Are you ready to make a change to this file? Or are you another wanna-be console cowboy who is poking their mouse
    in the wrong part of the codebase again?
    ...
    ...
    ...
    
You may now proceed to the rest of the file.
'''

def __updateLocRot(obj,logger):

    #In int
    #Out string enum
    #Recreate the pre_34 animation types enum
    ANIM_TYPE_TRANSLATE = "translate"
    ANIM_TYPE_ROTATE = "rotate"

    conversion_table = [
            #pre_34_anim_types  : post_34_anim_types
            (xplane_constants.ANIM_TYPE_TRANSFORM, xplane_constants.ANIM_TYPE_TRANSFORM),
            (                 ANIM_TYPE_TRANSLATE, xplane_constants.ANIM_TYPE_TRANSFORM),
            (                 ANIM_TYPE_ROTATE,    xplane_constants.ANIM_TYPE_TRANSFORM),
            (xplane_constants.ANIM_TYPE_SHOW,      xplane_constants.ANIM_TYPE_SHOW),
            (xplane_constants.ANIM_TYPE_HIDE,      xplane_constants.ANIM_TYPE_HIDE)
        ]

    def convert_old_to_new(old_anim_type):
        if old_anim_type >= 0 and old_anim_type < len(conversion_table):
            return conversion_table[old_anim_type][1]
        else:
            msg = "%s was not found in conversion table" % old_anim_type
            logger.error(msg)
            raise Exception(msg)

    for d in obj.xplane.datarefs:
        old_anim_type = d.get('anim_type')
        if old_anim_type is None:
            old_anim_type = 0 # If anim_type was never set in the first place, it's value is the default, aka 0 for the old anim_type

        new_anim_type = convert_old_to_new(old_anim_type)
        d.anim_type = new_anim_type 
        logger.info("Updated %s's animation dataref (%s)'s animation type from %s to %s" %
              (obj.name,\
               d.path,\
               conversion_table[old_anim_type][0].capitalize(),
               new_anim_type.capitalize()
               )
              )

# Function: update
# Updates parts of the data model to ensure forward
# compatability between versions of XPlane2Blender.
#
# Important: Running the updater on an already updated file
# should result in no changes to it
#
# Parameters:
#     fromVersion - The old version of the blender file
def update(last_version:xplane_helpers.VerStruct,logger:xplane_helpers.XPlaneLogger):
    if last_version < xplane_helpers.VerStruct.parse_version('3.3.0'):
        for scene in bpy.data.scenes:
            # set compositeTextures to False
            scene.xplane.compositeTextures = False
            logger.info('Set "Composite Textures" to False')

            if scene.xplane and scene.xplane.layers and len(scene.xplane.layers) > 0:
                for layer in scene.xplane.layers:
                    # set autodetectTextures to False
                    layer.autodetectTextures = False
                    logger.info('Turned layer "%s"\'s Autodetect Textures property to off' % layer.name)

                    # set export mode to cockpit, if cockpit was previously enabled
                    # TODO: Have users actually exported scenery objects before?
                    # Do we need to care about non-aircraft export types?
                    prev_export_type = layer.export_type
                    if layer.cockpit:
                        layer.export_type = 'cockpit'
                    else:
                        layer.export_type = 'aircraft'

                    logger.info('Changed layer "%s"\'s Export Type from "%s" to "%s"' % (layer.name, prev_export_type, layer.export_type))

    if last_version < xplane_helpers.VerStruct.parse_version('3.4.0'):
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                #Thanks to Python's duck typing and Blender's PointerProperties, this works
                __updateLocRot(bone,logger)

        for obj in bpy.data.objects:
            __updateLocRot(obj,logger)

    if last_version < xplane_helpers.VerStruct.parse_version('3.5.0-beta.2+32.20180725010500'):
        for mat in bpy.data.materials:
            v10 = mat.xplane.get('blend_v1000')
            v11 = mat.xplane.get('blend_v1100')

            if v11 == 3: #Aka, where BLEND_GLASS was in the enum
                mat.xplane.blend_glass = True

                # This bit of code reachs around Blender's magic EnumProperty
                # stuff and get at the RNA behind it, all to find the name.
                # If the default for blend_v1000 ever changes, we'll be covered.
                blend_v1000 = bpy.types.XPlaneMaterialSettings.bl_rna.properties['blend_v1000']
                enum_items = blend_v1000.enum_items
                
                if v10 is None:
                    v10_mode = enum_items[enum_items.find(blend_v1000.default)].name
                else:
                    v10_mode = enum_items[v10].name
                logger.info(
                        "Set material \"{name}\"'s Blend Glass property to true and its Blend Mode to {v10_mode}"
                        .format(name=mat.name, v10_mode=v10_mode))

            if v11 is not None:
                # It appears when get returns None, del throws an error,
                # which is not how normal python works
                del mat.xplane['blend_v1100']


@persistent
def load_handler(dummy):
    filepath = bpy.context.blend_data.filepath

    # do not update newly created files
    if not filepath:
        return

    scene = bpy.context.scene
    current_version = xplane_helpers.VerStruct.current()
    ver_history = scene.xplane.xplane2blender_ver_history
    logger = xplane_helpers.logger
    logger.clear()
    logger.addTransport(xplane_helpers.XPlaneLogger.InternalTextTransport('Updater Log'), xplane_constants.LOGGER_LEVELS_ALL)
    logger.addTransport(XPlaneLogger.ConsoleTransport())

    # Test if we're coming from a legacy build
    # Caveats:
    #    - New "modern" files don't touch this
    #    - Edge case: If someone takes a modern file and saves it in a legacy version
    #    the history will be updated (if the legacy version found is valid),
    #    but update won't be re-run. User is on their own if they made real changes to the
    #    data model
    legacy_build_number_w_history = False
    if scene.get('xplane2blender_version') != xplane_constants.DEPRECATED_XP2B_VER:
        # "3.2.0 was the last version without an updater, so default to that."
        # 3.20 was a mistake. If we get to a real version 3.20, we'll deprecate support for 3.2.0
        legacy_version_str = scene.get('xplane2blender_version','3.2.0').replace('20','2')
        legacy_version = xplane_helpers.VerStruct.parse_version(legacy_version_str)
        if legacy_version is not None:
            # Edge case: If someone creates a modern file and saves it with a legacy version
            # (no protection against real breaking edits, however)
            if len(ver_history) > 0:
                logger.info("Legacy build number, %s, found %d entries in version history. Not updating, still adding new version numbers" % (str(legacy_version),len(ver_history)))
                legacy_build_number_w_history = True
                # Since we changed the data of this file, we still need to save the version,
                # even if no updating gets done
                xplane_helpers.VerStruct.add_to_version_history(legacy_version)
                logger.info("Added %s to version history" % str(legacy_version))

                xplane_helpers.VerStruct.add_to_version_history(current_version)
                logger.info("Added %s to version history" % str(current_version))
            else:
                xplane_helpers.VerStruct.add_to_version_history(legacy_version)
                logger.info("Added %s to version history" % str(legacy_version))

            scene['xplane2blender_version'] = xplane_constants.DEPRECATED_XP2B_VER
        else:
            invalid_version_error_msg = "pre-3.4.0-beta.5 file has invalid xplane2blender_version: %s."\
                            " " "Re-open file in a previous version and/or fix manually in Scene->Custom Properties" % legacy_version_str

            logger.error(invalid_version_error_msg)
            logger.error("Update not performed")
            raise Exception(invalid_version_error_msg)

    #We don't have to worry about ver_history for 3.4.0-beta.5 >= files since we save that on first save or it'll already be deprecated!

    # Get the old_version (end of list, which by now is guaranteed to have something in it)
    last_version = ver_history[-1]
    
    # L:Compare last vs current
    # If the version is out of date
    #     L:Run update
    if last_version.make_struct() < current_version and legacy_build_number_w_history is False:
        logger.info("This file was created with an older XPlane2Blender version (%s) less than or equal to (%s) "
              "and will now be updated" % (str(last_version),str(current_version)))
        update(last_version.make_struct(),logger)

        logger.success('Your file was successfully updated to XPlane2Blender %s' % str(current_version))
    elif last_version.make_struct() > current_version:
        logger.warn('This file was last edited by a more advanced version, %s, than the current version %s.'\
        ' Changes may be lost or corrupt your work!' % (last_version,current_version))

    # Add the current version to the history, no matter what. Just in case it means something
    xplane_helpers.VerStruct.add_to_version_history(current_version)
    logger.info("Added %s to version history" % str(current_version))

bpy.app.handlers.load_post.append(load_handler)

@persistent
def save_handler(dummy):
    scene = bpy.context.scene
    if len(scene.xplane.xplane2blender_ver_history) == 0:
        xplane_helpers.VerStruct.add_to_version_history(xplane_helpers.VerStruct.current())
        scene['xplane2blender_version'] = xplane_constants.DEPRECATED_XP2B_VER

bpy.app.handlers.save_pre.append(save_handler)
