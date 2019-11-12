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
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import bpy
from bpy.app.handlers import persistent

import io_xplane2blender
from io_xplane2blender import xplane_props, xplane_helpers, xplane_constants
from io_xplane2blender.xplane_constants import LOGGER_LEVEL_ERROR,\
    LOGGER_LEVEL_INFO, LOGGER_LEVEL_SUCCESS, BLEND_GLASS
from io_xplane2blender.xplane_helpers import XPlaneLogger


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

# This is basically a copy of EnumPropertyItem, with only the parts we care about
_EnumItem = collections.namedtuple("EnumItem", ["identifier", "name", "description"])
def _get_enum_item(prop_group: bpy.types.PropertyGroup, prop:bpy.types.Property)->_EnumItem:
    """
    Inspects a property group's enum property and return's
    throws KeyNotFound and typeError

    prop.type must be and ENUM found in prop_group
    """
    assert prop.identifier in prop_group.bl_rna.properties, f"{prop.identifier} is not a member of {prop_group.rna_type.name}'s properties"
    assert prop.type == "ENUM", f"{prop.identifier} is not an ENUM and cannot be used in this function"
    # We need get instead of getattr because only get
    # gives us the real unfiltered value including
    # "never changed" aka None
    prop_value: Optional[int] = prop_group.get(prop.identifier)
    if prop_value is None:
        enum_key:str = prop.default
    else:
        enum_key:str = prop.enum_items.keys()[prop_value]
    item:bpy.types.EnumPropertyItem = prop.enum_items[enum_key]
    return _EnumItem(item.identifier, item.name, item.description)


def update(last_version:xplane_helpers.VerStruct, logger:xplane_helpers.XPlaneLogger)->None:
    """
    Entry point for the updater, which may change or delete XPlane2Blender
    properties of this .blend file to match the data model of this version of XPlane2Blender.
    Adding new properties to the data model is done elsewhere.

    Re-running the updater should result in no changes
    """
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
                blend_v1000 = xplane_props.XPlaneMaterialSettings.bl_rna.properties['blend_v1000']
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

    if last_version < xplane_helpers.VerStruct.parse_version("3.5.1-dev.0+43.20190606030000"):
        # This helps us conveniently save the Cast shadow value for later after we delete it
        UsedLayerInfo = collections.namedtuple("UsedLayerInfo", ["options", "cast_shadow", "final_name"])
        def _update_potential_materials(potential_objects: bpy.types.Material, layer_options:'XPlaneLayer')->None:
            for mat in potential_materials:
                # Default for shadow was True. get can't find shadow == no explicit value give
                val = bool(layer_options.get("shadow", True))
                mat.xplane.shadow_local = val # Easy case #1

        def _delete_shadow(layer_options: 'XPlaneLayer')->None:
            try:
                del layer_options["shadow"]
            except KeyError:
                pass

        def _print_error_table(material_uses: Dict[bpy.types.Material, List[UsedLayerInfo]])->None:
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
            logger.info("'Cast shadows' has been replaced by the Material's 'Cast Shadows (Local)'."
                        " The above OBJs may have incorrect shadows unless 'Cast Shadows (Local)'"
                        " is manually made uniform again, which could involve making"
                        " duplicate materials for each OBJ")

        # This way we'll be able to map the usage (and shared-ness) of a material
        material_uses = collections.defaultdict(list) # type: Dict[bpy.types.Material, List[UsedLayerInfo]]

        for scene in bpy.data.scenes:
            # From this we get the potential objects in an
            for root_obj in xplane_helpers.get_root_objects_in_scene(scene):
                layer_options = root_obj.xplane.layer
                if layer_options.export_type in {xplane_constants.EXPORT_TYPE_AIRCRAFT, xplane_constants.EXPORT_TYPE_COCKPIT}:
                    layer_options["shadow"] = True
                potential_objects = xplane_helpers.get_potential_objects_in_root_object(root_obj)
                potential_materials = [slot.material for obj in potential_objects for slot in obj.material_slots]
                _update_potential_materials(potential_materials, layer_options)
                used_layer_info = UsedLayerInfo(
                                        options=layer_options,
                                        cast_shadow=bool(layer_options.get("shadow", True)),
                                        final_name=layer_options.name if layer_options.name else root_obj.name
                                    )
                for mat in potential_materials:
                    material_uses[mat].append(used_layer_info)

            # Attempt to find shared usage, print out a table displaying issues
            _print_error_table(material_uses)

        # They might not all be root objects, but all objects have a XPlaneLayer property group!
        for obj in bpy.data.objects:
            try:
                del obj.xplane.layer["shadow"]
            except KeyError:
                pass

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
        def check_property_group_has_non_default(prop_group:bpy.types.PropertyGroup, props_to_ignore={"index", "expanded"})->Dict[str, Union[bool, float, int, str]]:
            """
            Recursively searches a property group for any members of it that have different values than the default.
            Returns a dictionary of property names to values. Currently does not inspect PointerPropertys
            """
            def check_recursive(real_prop_group:bpy.types.PropertyGroup):
                nondefault_props = {}
                for prop in filter(lambda p: p.identifier not in (props_to_ignore | {"rna_type"}), real_prop_group.bl_rna.properties):
                    if prop.type == "POINTER":
                        #TODO: This can be followed, but for now we need to press on to other bugs
                        # and we don't have a test case that uses this
                        #check_recursive(prop_group)
                        continue
                    elif prop.type == "COLLECTION":
                        nondefaults = list(
                            filter(None,
                                   [check_recursive(m) for m in getattr(real_prop_group, prop.identifier)]
                               )
                            )
                        if nondefaults:
                            nondefault_props[prop.identifier] = nondefaults
                    else:
                        if prop.type == "ENUM":
                            # This is the enum's identifier, what getattr and get when unchanged
                            # or missing
                            real_value = _get_enum_item(real_prop_group, prop).identifier
                        else:
                            real_value = real_prop_group.get(prop.identifier, prop.default)
                        if real_value != prop.default:
                            nondefault_props[prop.identifier] = real_value
                return nondefault_props

            return check_recursive(prop_group)

        def copy_property_group(source_prop_group:bpy.types.PropertyGroup, dest_prop_group:bpy.types.PropertyGroup, props_to_ignore: Set[str]=None)->None:
            """
            Recursively copies values from one PropertyGroup to another, using setattr.

            Note:
            If your PropertyGroup has a "name" property with a non-empty str default, you must copy those
            yourself.

            To iterate, we use bl_rna.properties, whose "name" member actually refers to the partent type
            (bpy.types.PropertyGroup)'s "name" property which is

                (identifier="name",
                 name="Name",
                 description="Unique name used in the code and scripting",
                 default="")

            If your "name" property's default matches the parent's "name", then everything lines up by co-incidence.
            There does not appear to be a way to get around this.

            bl_rna.properties["rna_type"] is always ignored since that is Blender defined.
            """

            props_to_ignore = props_to_ignore if props_to_ignore else set()
            def copy_recursive(source_prop_group:bpy.types.PropertyGroup, dest_prop_group:bpy.types.PropertyGroup):
                assert source_prop_group.rna_type == dest_prop_group.rna_type
                for prop in filter(lambda p: p.identifier not in (props_to_ignore | {"rna_type"}), source_prop_group.bl_rna.properties):
                    if prop.type == "POINTER":
                        #TODO: When we have a case with an POINTER to worry about
                        # we'll fill this in
                        continue
                    elif prop.type == "COLLECTION":
                        source_members = getattr(source_prop_group, prop.identifier)
                        dest_members =   getattr(dest_prop_group, prop.identifier)
                        for source_member, dest_member in zip(source_members, dest_members):
                            copy_recursive(source_member, dest_member)
                    else:
                        source_value = source_prop_group.get(prop.identifier, prop.default)
                        if prop.type == "ENUM":
                            setattr(dest_prop_group, prop.identifier, _get_enum_item(source_prop_group, prop).identifier)
                        else:
                            setattr(dest_prop_group, prop.identifier, source_value)
            copy_recursive(source_prop_group, dest_prop_group)

        #--- Copy Layers to Collections ---------------------------------------
        for scene in bpy.data.scenes:
            # Match Layers with Collections
            # Rename everything from Collection or Collection 2...
            # to Layer 1, Layer 2
            try:
                bpy.data.collections["Collection"].name = "Collection 1"
            except KeyError:
                pass

            for layer in scene.xplane.layers:
                assert layer.index != -1, f"XPlaneLayer f{layer.name} was never actually initialized in 2.79"
                collection_name = f"Layer {layer.index + 1}"
                try:
                    coll = bpy.data.collections[f"Collection {layer.index + 1}"]
                except KeyError:
                    nondefaults = check_property_group_has_non_default(layer)
                    if nondefaults:
                        coll = bpy.data.collections.new(collection_name)
                        scene.collection.children.link(coll)
                    else:
                        continue
                else:
                    coll.name = collection_name
                    coll.xplane.is_exportable_collection = not coll.hide_render

                copy_property_group(layer, coll.xplane.layer, props_to_ignore={"index"})
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
