"""
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
"""
import collections
import enum
import functools
import pprint
import re

from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy
from bpy.app.handlers import persistent

import io_xplane2blender
from io_xplane2blender import xplane_props, xplane_helpers, xplane_constants
from io_xplane2blender.xplane_constants import LOGGER_LEVEL_ERROR,\
    LOGGER_LEVEL_INFO, LOGGER_LEVEL_SUCCESS, BLEND_GLASS
from io_xplane2blender.xplane_helpers import XPlaneLogger
from io_xplane2blender.xplane_utils import xplane_updater_helpers

def _layers_to_collection(logger:xplane_helpers.XPlaneLogger)->None:
    """
    Side Effects: Collections may be created, properties changed; Deletes scene.xplane.layers

    - Renames all collections to the familiar and unambiguious "Layer N"
    - Copies any XPLaneLayers from scene.xplane.layers
    - Creates Collections for non-default XPlaneLayers w/o content
    - Sets visibility and exportablity
    - and finally deletes scene.xplane.layers
    """
    #--- Copy Layers to Collections ---------------------------------------
    def prepare_collections_for_renaming():
        for coll in bpy.data.collections:
            full_match = re.fullmatch("Collection(\.\d{3}|$)", coll.name)
            if full_match:
                coll.name = f"Collection 1{full_match.group(1)}"

            # Making this regular with the rest is better,
            # we're just going to replace all this anyway
            if "." not in coll.name:
                coll.name += ".000"

    prepare_collections_for_renaming()
    for i, scene in enumerate(bpy.data.scenes):
        if not scene.xplane.layers:
            for j, coll in enumerate(scene.collection.children, start=1):
                coll.name = f"Layer {j}" if i == 0 else f"Layer {j}_{scene.name}"
        else:
            # We rename everything from Collection {number} to Layer {number}_{scene.name}
            # 1. Correct any named "Collection$" to "Collection 1.000" (why Blender?!),
            #    keeping any trailing evidence of a name collision (.001, .002, etc)
            # 2. If our scene has a collection pre-made for the layer*, great! Use that!
            #    If our scene has a layer with non-default values but Blender didn't
            #    make a Collection for us (no Blender Data on it), make one ourselves
            #    Otherwise, go to the next layer
            #
            #    * We need to actually check every Collection N, Collection N.001 incase
            #      a previous scene didn't make that collection and Blender hasn't needed to
            #      make it unique by appending the .000 business
            # 3. Rename to match the pattern,
            #    copy the XPlaneLayer from scene.xplane.layers to coll.xplane.layer
            for layer in scene.xplane.layers:
                assert layer.index != -1, f"XPlaneLayer f{layer.name} was never actually initialized in 2.79"
                collection_new_name = f"Layer {layer.index + 1}" + (f"_{scene.name}" if i else f"")
                for suffix in (f"{j:03}" for j in range(0, i+1)):
                    try_this = f"Collection {layer.index + 1}.{suffix}"
                    try:
                        coll = scene.collection.children[try_this]
                    except KeyError:
                        continue
                    else:
                        coll.name = collection_new_name
                        # 0 used to mean "layers" (default), 1 used to mean "root_objects"
                        coll.xplane.is_exportable_collection = not coll.hide_viewport if scene.xplane.get("exportMode", 0) == 0 else False
                        scene.view_layers[0].layer_collection.children[coll.name].hide_viewport = coll.hide_viewport # Change eyeball
                        coll.hide_viewport = False
                    break
                else: # no break, no matching collection found
                    nondefaults = xplane_updater_helpers.check_property_group_has_non_default(layer)
                    if nondefaults:
                        coll = bpy.data.collections.new(collection_new_name)
                        scene.collection.children.link(coll)
                        coll.xplane.is_exportable_collection = False
                        scene.view_layers[0].layer_collection.children[coll.name].hide_viewport = True
                        coll.hide_viewport = False
                    else:
                        continue
                xplane_updater_helpers.copy_property_group(layer, coll.xplane.layer, props_to_ignore={"index"})

def _change_pre_3_3_0_properties(logger:xplane_helpers.XPlaneLogger)->None:
    """
    Side Effects: scene.xplane.compositeTextures, scene.xplane.autodetectTextures,
                  layer.exportType may change
    The purpose of this is (I think) to get pre 3_3_0 files up to speed.
    Or something.
    """
    for scene in bpy.data.scenes:
        # set compositeTextures to False
        scene.xplane.compositeTextures = False
        for layer in [coll.xplane.layer for coll in scene.collection.children]:
            # set autodetectTextures to False
            layer.autodetectTextures = False

            # set export mode to cockpit, if cockpit was previously enabled
            prev_export_type = layer.export_type
            if layer.cockpit:
                layer.export_type = 'cockpit'
                logger.info('Changed layer "%s"\'s Export Type from "%s" to "%s"' % (layer.name, prev_export_type, layer.export_type))
            else:
                layer.export_type = 'aircraft'

    logger.info("Unless otherwise noted, changed every layer's Export Type to 'Aircraft'")
    logger.info("For all layers, in all scenes, set 'Composite Textures' and 'Autodetect Textures' to false")

def _update_LocRot(has_datarefs:Union[bpy.types.Object, bpy.types.Bone],logger:XPlaneLogger)->None:
    """
    Side Effects: has_datarefs/bone's datarefs' anim_type may change
    from Loc/Rot/LocRot->Transform

    Loc and Rot and LocRot options were combined in the enum,
    and the enum needed to be adjusted
    """

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

    # Returned string is the new enum_type to be used and assaigned
    def convert_old_to_new(old_anim_type:int)->str:
        if old_anim_type >= 0 and old_anim_type < len(conversion_table):
            return conversion_table[old_anim_type][1]
        else:
            msg = "%s was not found in conversion table" % old_anim_type
            logger.error(msg)
            raise Exception(msg)

    for d in has_datarefs.xplane.datarefs:
        old_anim_type = d.get('anim_type')
        if old_anim_type is None:
            old_anim_type = 0 # If anim_type was never set in the first place, it's value is the default, aka 0 for the old anim_type

        new_anim_type = convert_old_to_new(old_anim_type)
        d.anim_type = new_anim_type
        logger.info("Updated %s's animation dataref (%s)'s animation type from %s to %s" %
              (has_datarefs.name,
               d.path,
               conversion_table[old_anim_type][0].capitalize(),
               new_anim_type.capitalize()
               )
              )


def _rollback_blend_glass(logger:XPlaneLogger)->None:
    """
    Side Effects: mat.xplane.blend_glass may change, mat.xplane.blend_v1100 deleted

    There was a mistake in creating Blend Glass as a member of blend_v1100,
    instead of as a BoolProperty.

    This saves Blend Glass (if needed) before blend_v1100 is deleted
    """
    for mat in bpy.data.materials:
        v10 = mat.xplane.get('blend_v1000')
        v11 = mat.xplane.get('blend_v1100')

        if v11 == 3: #Aka, where BLEND_GLASS was in the enum
            mat.xplane.blend_glass = True

            # This bit of code reachs around Blender's magic EnumProperty
            # stuff and get at the RNA behind it, all to find the name.
            # If the default for blend_v1000 ever changes, we'll be covered.
            blend_v1000 = xplane_props.XPlaneMaterialSettings.bl_rna.properties['blend_v1000']
            enum_items = blend_v1000.enum_items

            if v10 is None:
                v10_mode = enum_items[enum_items.find(blend_v1000.default)].name
            else:
                v10_mode = enum_items[v10].name
            logger.info(
                    "Set material \"{name}\"'s Blend Glass property to true and its Blend Mode to {v10_mode}"
                    .format(name=mat.name, v10_mode=v10_mode))

        #TODO: Replace with API
        if v11 is not None:
            # It appears when get returns None, del throws an error,
            # which is not how normal python works
            del mat.xplane['blend_v1100']

def _set_shadow_local_and_delete_global_shadow(logger:xplane_helpers.XPlaneLogger)->None:
    """
    Side Effects: mat.xplane.shadow_local may be set, based on the value of the root's
    global shadow if that mat was used in that root, layer.shadow is deleted

    To implement ATTR_shadow we needed material level shadow control, and if that was
    the case, we could use that to make the "uniform shadow->promote to GLOBAL_shadow"
    rule we like. We wanted to preserve people's shadow choice as best as possible,
    however, so this was used to populate people material's cast_local
    """

    # This helps us conveniently save the Cast shadow value for later after we delete it
    UsedLayerInfo = collections.namedtuple("UsedLayerInfo", ["options", "cast_shadow", "final_name"])
    def _update_potential_materials(potential_materials: List[bpy.types.Material], layer_options:'XPlaneLayer')->None:
        for mat in potential_materials:
            # Default for shadow was True. get can't find shadow == no explicit value give
            val = bool(layer_options.get("shadow", True))
            mat.xplane.shadow_local = val # Easy case #1

    def _print_error_table(material_uses: Dict[bpy.types.Material, List[UsedLayerInfo]])->None:
        error_count = len(logger.findErrors())
        for mat, layers_used_in in material_uses.items():
            if (len(layers_used_in) > 1
                and any(layers_used_in[0].cast_shadow != l.cast_shadow for l in layers_used_in)): # Checks for mixed use of Cast Shadow (Global)
                pad = max([len(final_name) for _, _, final_name in layers_used_in])
                logger.error(
                        "\n".join(
                            ["Material '{}' is used across OBJs with different 'Cast Shadow (Global)' values:".format(mat.name),
                             "Ambiguous OBJs".ljust(pad) + "| Cast Shadow (Global)",
                             "-" * pad +                   "|---------------------",
                             "\n".join("{}| {}".format(final_name.ljust(pad), "On" if cast_shadow else "Off")
                                       for options, cast_shadow, final_name in layers_used_in),
                             "",
                            ]
                        )
                    )
        if len(logger.findErrors()) > error_count:
            logger.info("'Cast shadows' has been replaced by the Material's 'Cast Shadows (Local)'."
                        " The above OBJs may have incorrect shadows unless 'Cast Shadows (Local)'"
                        " is manually made uniform again, which could involve making"
                        " duplicate materials for each OBJ")

    # This way we'll be able to map the usage (and shared-ness) of a material
    material_uses = collections.defaultdict(list) # type: Dict[bpy.types.Material, List[UsedLayerInfo]]

    for scene in bpy.data.scenes[:1]:
        for exportable_root in xplane_helpers.get_exportable_roots_in_scene(scene):
            layer_options = exportable_root.xplane.layer
            if layer_options.export_type in {xplane_constants.EXPORT_TYPE_AIRCRAFT, xplane_constants.EXPORT_TYPE_COCKPIT}:
                layer_options["shadow"] = True
            potential_objects = xplane_helpers.get_potential_objects_in_root_object(exportable_root)
            potential_materials = [slot.material for obj in potential_objects for slot in obj.material_slots if slot.material]
            _update_potential_materials(potential_materials, layer_options)
            used_layer_info = UsedLayerInfo(
                                    options=layer_options,
                                    cast_shadow=bool(layer_options.get("shadow", True)),
                                    final_name=layer_options.name if layer_options.name else exportable_root.name
                                )
            xplane_updater_helpers.delete_property_from_datablock(layer_options, "shadow")
            for mat in potential_materials:
                material_uses[mat].append(used_layer_info)

    _print_error_table(material_uses)

    # They might not all be root objects, but all objects have a XPlaneLayer property group!
    for obj in bpy.data.objects:
        xplane_updater_helpers.delete_property_from_datablock(obj.xplane.layer, "shadow")

def update(last_version:xplane_helpers.VerStruct, logger:xplane_helpers.XPlaneLogger)->None:
    """
    Entry point for the updater, which may change or delete XPlane2Blender
    properties of this .blend file to match the data model of this version of XPlane2Blender.
    Adding new properties to the data model is done elsewhere.

    Re-running the updater should result in no changes
    """
    if last_version < xplane_helpers.VerStruct.parse_version("4.0.0"):
        _layers_to_collection(logger)

    if last_version < xplane_helpers.VerStruct.parse_version('3.3.0'):
        _change_pre_3_3_0_properties(logger)

    if last_version < xplane_helpers.VerStruct.parse_version('3.4.0'):
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                #Thanks to Python's duck typing and Blender's PointerProperties, this works
                _update_LocRot(bone,logger)

        for obj in bpy.data.objects:
            _update_LocRot(obj,logger)

    if last_version < xplane_helpers.VerStruct.parse_version('3.5.0-beta.2+32.20180725010500'):
        _rollback_blend_glass(logger)

    if last_version < xplane_helpers.VerStruct.parse_version("3.5.1-dev.0+43.20190606030000"):
        _set_shadow_local_and_delete_global_shadow(logger)

    #TODO: Move the prop_group copying code before all this. The rest of the code will depend on it
    if last_version < xplane_helpers.VerStruct.parse_version("4.0.0"):
        #--- Delete "exportMode" ----------------------------------------------
        for scene in bpy.data.scenes:
            #TODO: Unit test for this
            #del scene.xplane["exportMode"]
            pass
        #----------------------------------------------------------------------

        #--- Disable Autodetect Textures --------------------------------------
        for scene in bpy.data.scenes:
            #TODO: Unit test for this. Default should be changed so new collections
            # automatically have it
            for layer_props in [obj.xplane.layer for obj in scene.objects]:
                layer_props.autodetectTextures = False
        #----------------------------------------------------------------------

        #----------------------------------------------------------------------


@persistent
def load_handler(dummy):
    filepath = bpy.context.blend_data.filepath

    for layer_props in [has_layer_props.xplane.layer for has_layer_props in bpy.data.objects[:] + bpy.data.collections[:]]:
        # Since someone could add lods/cockpit_regions just before export, export needs to be the one
        # to validate the size of the collection
        while len(layer_props.lod) < xplane_constants.MAX_LODS - 1:
            layer_props.lod.add()
        while len(layer_props.cockpit_region) < xplane_constants.MAX_COCKPIT_REGIONS:
            layer_props.cockpit_region.add()

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
