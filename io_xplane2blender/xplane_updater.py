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
import itertools
import pprint
import re
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union

import bpy
from bpy.app.handlers import persistent

import io_xplane2blender
from io_xplane2blender import xplane_constants, xplane_helpers, xplane_props
from io_xplane2blender.xplane_constants import (
    BLEND_GLASS,
    LOGGER_LEVEL_ERROR,
    LOGGER_LEVEL_INFO,
    LOGGER_LEVEL_SUCCESS,
)
from io_xplane2blender.xplane_helpers import XPlaneLogger
from io_xplane2blender.xplane_utils import xplane_updater_helpers


def _layers_to_collection(logger: xplane_helpers.XPlaneLogger) -> None:
    """
    Side Effects: Collections may be created, properties changed; Deletes scene.xplane.layers

    - Renames all collections to the familiar and unambiguious "Layer N"
    - Copies any XPLaneLayers from scene.xplane.layers
    - Creates Collections for non-default XPlaneLayers w/o content
    - Sets visibility and exportablity
    - and finally deletes scene.xplane.layers
    """
    # --- Copy Layers to Collections ---------------------------------------
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
        if "layers" in scene.xplane and not scene.xplane["layers"]:
            for j, coll in enumerate(scene.collection.children, start=1):
                coll.name = f"Layer {j}" if i == 0 else f"Layer {j}_{scene.name}"
        elif "layers" in scene.xplane:
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
            for layer in scene.xplane["layers"]:
                assert (
                    layer["index"] != -1
                ), f"XPlaneLayer f{layer.name} was never actually initialized in 2.79"
                collection_new_name = f"Layer {layer['index'] + 1}" + (
                    f"_{scene.name}" if i else f""
                )
                for suffix in (f"{j:03}" for j in range(0, i + 1)):
                    try_this = f"Collection {layer['index'] + 1}.{suffix}"
                    try:
                        coll = scene.collection.children[try_this]
                    except KeyError:
                        continue
                    else:
                        coll.name = collection_new_name
                        # 0 used to mean "layers" (default), 1 used to mean "root_objects"
                        coll.xplane.is_exportable_collection = (
                            not coll.hide_viewport
                            if scene.xplane.get("exportMode", 0) == 0
                            else False
                        )
                        scene.view_layers[0].layer_collection.children[
                            coll.name
                        ].hide_viewport = coll.hide_viewport  # Change eyeball
                        coll.hide_viewport = False
                    break
                else:  # no break, no matching collection found

                    def flatten(items: Dict[str, Any]):
                        """
                        Returns all the real values (except 'index') used in 'layer'
                        """
                        output = []

                        def f(item):
                            # No, it isn't perfect. I'm just sick of this API
                            if item == [] or item == dict():
                                return
                            if isinstance(item, list):
                                for v in item:
                                    f(v)
                            elif isinstance(item, dict):
                                for k, v in item.items():
                                    # - index will always be not None,
                                    # - expanded isn't impressive enough to matter
                                    # - no point collecting a change of "" for name, common mistake
                                    if (k not in {"expanded", "index"}) and (k, v) != (
                                        "name",
                                        "",
                                    ):
                                        f(v)
                            else:
                                output.append(item)

                        f(items)
                        return output

                    nondefaults = flatten(layer.to_dict())
                    if nondefaults:
                        coll = bpy.data.collections.new(collection_new_name)
                        scene.collection.children.link(coll)
                        coll.xplane.is_exportable_collection = False
                        scene.view_layers[0].layer_collection.children[
                            coll.name
                        ].hide_viewport = True
                        coll.hide_viewport = False
                    else:
                        continue

                def copy_layer_idprop_to_property(coll: bpy.types.Collection):
                    try:
                        coll.xplane["layer"]
                    except KeyError:
                        coll.xplane["layer"] = {}
                    finally:
                        coll.xplane["layer"].update(layer)

                copy_layer_idprop_to_property(coll)
        xplane_updater_helpers.delete_property_from_datablock(scene["xplane"], "layers")


def _change_pre_3_3_0_properties(logger: xplane_helpers.XPlaneLogger) -> None:
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
                layer.export_type = "cockpit"
                logger.info(
                    'Changed layer "%s"\'s Export Type from "%s" to "%s"'
                    % (layer.name, prev_export_type, layer.export_type)
                )
            else:
                layer.export_type = "aircraft"

    logger.info(
        "Unless otherwise noted, changed every layer's Export Type to 'Aircraft'"
    )
    logger.info(
        "For all layers, in all scenes, set 'Composite Textures' and 'Autodetect Textures' to false"
    )


def _update_LocRot(
    has_datarefs: Union[bpy.types.Object, bpy.types.Bone], logger: XPlaneLogger
) -> None:
    """
    Side Effects: has_datarefs/bone's datarefs' anim_type may change
    from Loc/Rot/LocRot->Transform

    Loc and Rot and LocRot options were combined in the enum,
    and the enum needed to be adjusted
    """

    # Recreate the pre_34 animation types enum
    ANIM_TYPE_TRANSLATE = "translate"
    ANIM_TYPE_ROTATE = "rotate"

    # fmt: off
    conversion_table = [
            #pre_34_anim_types  : post_34_anim_types
            (xplane_constants.ANIM_TYPE_TRANSFORM, xplane_constants.ANIM_TYPE_TRANSFORM),
            (                 ANIM_TYPE_TRANSLATE, xplane_constants.ANIM_TYPE_TRANSFORM),
            (                 ANIM_TYPE_ROTATE,    xplane_constants.ANIM_TYPE_TRANSFORM),
            (xplane_constants.ANIM_TYPE_SHOW,      xplane_constants.ANIM_TYPE_SHOW),
            (xplane_constants.ANIM_TYPE_HIDE,      xplane_constants.ANIM_TYPE_HIDE)
        ]
    # fmt: on

    # Returned string is the new enum_type to be used and assaigned
    def convert_old_to_new(old_anim_type: int) -> str:
        if old_anim_type >= 0 and old_anim_type < len(conversion_table):
            return conversion_table[old_anim_type][1]
        else:
            msg = "%s was not found in conversion table" % old_anim_type
            logger.error(msg)
            raise Exception(msg)

    for d in has_datarefs.xplane.datarefs:
        old_anim_type = d.get("anim_type")
        if old_anim_type is None:
            old_anim_type = 0  # If anim_type was never set in the first place, it's value is the default, aka 0 for the old anim_type

        new_anim_type = convert_old_to_new(old_anim_type)
        d.anim_type = new_anim_type
        logger.info(
            "Updated %s's animation dataref (%s)'s animation type from %s to %s"
            % (
                has_datarefs.name,
                d.path,
                conversion_table[old_anim_type][0].capitalize(),
                new_anim_type.capitalize(),
            )
        )


def _rollback_blend_glass(logger: XPlaneLogger) -> None:
    """
    Side Effects: mat.xplane.blend_glass may change, mat.xplane.blend_v1100 deleted

    There was a mistake in creating Blend Glass as a member of blend_v1100,
    instead of as a BoolProperty.

    This saves Blend Glass (if needed) before blend_v1100 is deleted
    """
    for mat in bpy.data.materials:
        v10 = mat.xplane.get("blend_v1000")
        v11 = mat.xplane.get("blend_v1100")

        if v11 == 3:  # Aka, where BLEND_GLASS was in the enum
            # v4.1.0 note - we've moved blend_glass to the header
            # but I don't want to change the rest of this function
            # So... we fake it to match later expectations!
            mat["xplane"]["blend_glass"] = True

            # This bit of code reachs around Blender's magic EnumProperty
            # stuff and get at the RNA behind it, all to find the name.
            # If the default for blend_v1000 ever changes, we'll be covered.
            blend_v1000 = xplane_props.XPlaneMaterialSettings.bl_rna.properties[
                "blend_v1000"
            ]
            enum_items = blend_v1000.enum_items

            if v10 is None:
                v10_mode = enum_items[enum_items.find(blend_v1000.default)].name
            else:
                v10_mode = enum_items[v10].name
            logger.info(
                'Set material "{name}"\'s Blend Glass property to true and its Blend Mode to {v10_mode}'.format(
                    name=mat.name, v10_mode=v10_mode
                )
            )

        xplane_updater_helpers.delete_property_from_datablock(mat.xplane, "blend_v1100")


def _set_shadow_local_and_delete_global_shadow(
    logger: xplane_helpers.XPlaneLogger,
) -> None:
    """
    Side Effects: mat.xplane.shadow_local may be set, based on the value of the root's
    global shadow if that mat was used in that root, layer.shadow is deleted

    To implement ATTR_shadow we needed material level shadow control, and if that was
    the case, we could use that to make the "uniform shadow->promote to GLOBAL_shadow"
    rule we like. We wanted to preserve people's shadow choice as best as possible,
    however, so this was used to populate people material's cast_local
    """

    # This helps us conveniently save the Cast shadow value for later after we delete it
    UsedLayerInfo = collections.namedtuple(
        "UsedLayerInfo", ["options", "cast_shadow", "final_name"]
    )

    def _update_potential_materials(
        potential_materials: List[bpy.types.Material], layer_options: "XPlaneLayer"
    ) -> None:
        for mat in potential_materials:
            # Default for shadow was True. get can't find shadow == no explicit value give
            val = bool(layer_options.get("shadow", True))
            mat.xplane.shadow_local = val  # Easy case #1

    def _print_error_table(
        material_uses: Dict[bpy.types.Material, List[UsedLayerInfo]]
    ) -> None:
        error_count = len(logger.findErrors())
        for mat, layers_used_in in material_uses.items():
            if len(layers_used_in) > 1 and any(
                layers_used_in[0].cast_shadow != l.cast_shadow for l in layers_used_in
            ):  # Checks for mixed use of Cast Shadow (Global)
                pad = max([len(final_name) for _, _, final_name in layers_used_in])
                logger.error(
                    "\n".join(
                        [
                            "Material '{}' is used across OBJs with different 'Cast Shadow (Global)' values:".format(
                                mat.name
                            ),
                            "Ambiguous OBJs".ljust(pad) + "| Cast Shadow (Global)",
                            "-" * pad + "|---------------------",
                            "\n".join(
                                "{}| {}".format(
                                    final_name.ljust(pad),
                                    "On" if cast_shadow else "Off",
                                )
                                for options, cast_shadow, final_name in layers_used_in
                            ),
                            "",
                        ]
                    )
                )
        if len(logger.findErrors()) > error_count:
            logger.info(
                "'Cast shadows' has been replaced by the Material's 'Cast Shadows (Local)'."
                " The above OBJs may have incorrect shadows unless 'Cast Shadows (Local)'"
                " is manually made uniform again, which could involve making"
                " duplicate materials for each OBJ"
            )

    # This way we'll be able to map the usage (and shared-ness) of a material
    material_uses = collections.defaultdict(
        list
    )  # type: Dict[bpy.types.Material, List[UsedLayerInfo]]

    for scene in bpy.data.scenes:
        for exportable_root in xplane_helpers.get_exportable_roots_in_scene(
            scene, scene.view_layers[0]
        ):  # Don't worry, we'll always have only 1 view layer
            layer_options = exportable_root.xplane.layer
            if layer_options.export_type in {
                xplane_constants.EXPORT_TYPE_AIRCRAFT,
                xplane_constants.EXPORT_TYPE_COCKPIT,
            }:
                layer_options["shadow"] = True

            potential_objects = xplane_helpers.get_potential_objects_in_exportable_root(
                exportable_root
            )
            potential_materials = [
                slot.material
                for obj in potential_objects
                for slot in obj.material_slots
                if slot.material
            ]
            _update_potential_materials(potential_materials, layer_options)
            used_layer_info = UsedLayerInfo(
                options=layer_options,
                cast_shadow=bool(layer_options.get("shadow", True)),
                final_name=layer_options.name
                if layer_options.name
                else exportable_root.name,
            )
            xplane_updater_helpers.delete_property_from_datablock(
                layer_options, "shadow"
            )
            for mat in potential_materials:
                material_uses[mat].append(used_layer_info)

    _print_error_table(material_uses)

    # They might not all be root objects, but all objects have a XPlaneLayer property group!
    for obj in bpy.data.objects:
        xplane_updater_helpers.delete_property_from_datablock(
            obj.xplane.layer, "shadow"
        )


def _move_global_material_props(
    logger: xplane_helpers.XPlaneLogger,
):
    """
    Because it was deemed horribly annoying and bad semantics,
    NORMAL_METALNESS, BLEND_GLASS, and GLOBAL_tint are
    going to be moved to the OBJ settings instead.

    Side Effects: The value of `Normal Metalness`, `Blend Glass`,
    `Tint`, `Tint Albedo`, `Tint Emissive` are copied to the OBJ
    settings with a very liberal dumb heuristic for solving
    ambiguities and defaults given. No old data is deleted.

    On Accidental Re-run: Pre-v4.1.0-alpha.1 choices would be re-applied,
    overwriting new choices
    """
    default_blend_glass = False
    default_normal_metalness = False
    default_tint = False
    default_tint_albedo = 0.0
    default_tint_emissive = 0.0

    for scene in bpy.data.scenes:
        exp_collections = [
            col
            for col in xplane_helpers.get_collections_in_scene(scene)
            if col.xplane.is_exportable_collection
        ]
        exp_objects = [o for o in scene.objects if o.xplane.isExportableRoot]

        for exp in itertools.chain(exp_collections, exp_objects):

            if isinstance(exp, bpy.types.Collection):
                all_objects = exp.all_objects
            else:

                def recurse_obj_tree(obj: bpy.types.Collection):
                    yield obj
                    for c in obj.children:
                        yield from recurse_obj_tree(c)

                all_objects = [*recurse_obj_tree(exp)]

            exp.xplane.layer.blend_glass = default_blend_glass
            exp.xplane.layer.normal_metalness = default_normal_metalness

            for m in [
                slot.material
                for o in all_objects
                for slot in o.material_slots
                if slot.material
            ]:
                exp.xplane.layer.blend_glass |= bool(
                    m.xplane.get("blend_glass", default_blend_glass)
                )
                old_normal_metalness = bool(
                    m.xplane.get("normal_metalness", default_normal_metalness)
                )
                if m.xplane.draped:
                    exp.xplane.layer.normal_metalness_draped |= old_normal_metalness
                else:
                    exp.xplane.layer.normal_metalness |= old_normal_metalness

                # Copying only the 1st material we see is a heuristic -
                # Since we had no error we have no definitive answer. I'm hoping this choice
                # which mimics picking the 1st reference material
                # is good enough. If not... well... its a one time fix of only so many clicks.
                # ...
                # Right?
                if exp.xplane.layer.get("tint") == None:
                    exp.xplane.layer.tint = bool(m.xplane.get("tint", default_tint))
                    exp.xplane.layer.tint_albedo = m.xplane.get(
                        "tint_albedo", default_tint_albedo
                    )
                    exp.xplane.layer.tint_emissive = m.xplane.get(
                        "tint_emissive", default_tint_emissive
                    )


def _panel_to_cockpit_feature(logger: xplane_helpers.XPlaneLogger):
    for mat in bpy.data.materials:
        mat.xplane.cockpit_feature = (
            xplane_constants.COCKPIT_FEATURE_PANEL
            if mat.xplane.get("panel", False)
            else xplane_constants.COCKPIT_FEATURE_NONE
        )


def _regions_change_panel_mode(logger: xplane_helpers.XPlaneLogger):
    for col in bpy.data.collections:
        col.xplane.layer.cockpit_panel_mode = (
            xplane_constants.PANEL_COCKPIT_REGION
            if int(col.xplane.layer.cockpit_regions)
            else col.xplane.layer.cockpit_panel_mode
        )


def update(
    last_version: xplane_helpers.VerStruct, logger: xplane_helpers.XPlaneLogger
) -> None:
    """
    Entry point for the updater, which may change or delete XPlane2Blender
    properties of this .blend file to match the data model of this version of XPlane2Blender.
    Adding new properties to the data model is done elsewhere.

    Re-running the updater should result in no changes
    """
    if last_version < xplane_helpers.VerStruct.parse_version("4.0.0"):
        _layers_to_collection(logger)

    if last_version < xplane_helpers.VerStruct.parse_version("3.3.0"):
        _change_pre_3_3_0_properties(logger)

    if last_version < xplane_helpers.VerStruct.parse_version("3.4.0"):
        for arm in bpy.data.armatures:
            for bone in arm.bones:
                # Thanks to Python's duck typing and Blender's PointerProperties, this works
                _update_LocRot(bone, logger)

        for obj in bpy.data.objects:
            _update_LocRot(obj, logger)

    if last_version < xplane_helpers.VerStruct.parse_version(
        "3.5.0-beta.2+32.20180725010500"
    ):
        _rollback_blend_glass(logger)

    if last_version < xplane_helpers.VerStruct.parse_version(
        "3.5.1-dev.0+43.20190606030000"
    ):
        _set_shadow_local_and_delete_global_shadow(logger)

    if last_version < xplane_helpers.VerStruct.parse_version(
        "4.0.0-alpha.6+71.20200207171400"
    ):
        # --- Disable autodetect textures --------------------------------------

        # I acknowledge that the 3_3_0 updater already has code like this,
        # however it doesn't matter much since most people aren't coming from
        # that anymore /s
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            has_layer.xplane.layer.autodetectTextures = False
        # --- Delete "exportMode" ----------------------------------------------
        for scene in bpy.data.scenes:
            xplane_updater_helpers.delete_property_from_datablock(
                scene.xplane, "exportMode"
            )
        # ----------------------------------------------------------------------
        # --- Delete index -----------------------------------------------------
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            xplane_updater_helpers.delete_property_from_datablock(
                has_layer.xplane.layer, "index"
            )
        # ----------------------------------------------------------------------
        # --- Delete XPlaneObjectSettings.export_mesh---------------------------
        for obj in bpy.data.objects:
            xplane_updater_helpers.delete_property_from_datablock(
                obj.xplane, "export_mesh"
            )
        # ----------------------------------------------------------------------
        # --- Delete all XPlaneLayer's "Include in Export" ---------------------
        for has_layer in bpy.data.collections[:] + bpy.data.objects[:]:
            xplane_updater_helpers.delete_property_from_datablock(
                has_layer.xplane.layer, "export"
            )
        # ----------------------------------------------------------------------

    if last_version < xplane_helpers.VerStruct.parse_version(
        "4.0.0-beta.2+88.20200622133200"
    ):
        # Remember, get returning 0 and return None means something different
        for light in filter(lambda l: l.xplane.get("type") is None, bpy.data.lights):
            light.xplane.type = xplane_constants.LIGHT_DEFAULT

    if last_version < xplane_helpers.VerStruct.parse_version(
        "4.1.0-alpha.1+92.20201020151500"
    ):
        _move_global_material_props(logger)
    if last_version < xplane_helpers.VerStruct.parse_version(
        "4.1.0-alpha.1+97.20201109172400"
    ):
        _panel_to_cockpit_feature(logger)
    if last_version < xplane_helpers.VerStruct.parse_version(
        "4.1.0-beta.1+100.20201117112800"
    ):
        _regions_change_panel_mode(logger)


def _synchronize_last_version_across_histories(last_version: xplane_helpers.VerStruct):
    assert last_version.is_valid(), f"last_version {last_version} isn't valid"

    for scene in bpy.data.scenes:
        xplane_helpers.VerStruct.add_to_version_history(scene, last_version)


@persistent
def load_handler(dummy):
    from io_xplane2blender.xplane_utils import xplane_lights_txt_parser

    # --- Setup logger (Startup) ----------------------------------------------
    logger = xplane_helpers.logger
    logger.clear()
    logger.addTransport(
        xplane_helpers.XPlaneLogger.InternalTextTransport("Startup Log"),
        xplane_constants.LOGGER_LEVELS_ALL,
    )
    logger.addTransport(XPlaneLogger.ConsoleTransport())
    # -------------------------------------------------------------------------
    # --- Parse lights.txt file -----------------------------------------------
    try:
        xplane_lights_txt_parser.parse_lights_file()
    except (FileNotFoundError, OSError) as oe:

        def draw(self, context):
            self.layout.label(
                text="Some lighting features may not work. Read the internal text block 'Startup Log' for more details"
            )
            self.layout.label(
                text="Check for a missing or broken lights.txt file or re-install addon"
            )
            self.layout.label(text=str(oe))

        bpy.context.window_manager.popup_menu(
            draw,
            title="Could not read io_xplane2blender/resources/lights.txt",
            icon="ERROR",
        )
    except xplane_lights_txt_parser.LightsTxtFileParsingError as pe:

        def draw(self, context):
            self.layout.label(
                text="Some lighting features may not work. Read the internal text block 'Startup Log' for more details"
            )
            self.layout.label(
                text="Check replace lights.txt from X-Plane or re-install addon"
            )
            self.layout.label(text=str(pe))

        bpy.context.window_manager.popup_menu(
            draw,
            title="io_xplane2blender/resources/lights.txt had invalid content",
            icon="ERROR",
        )
    # -------------------------------------------------------------------------

    # --- Add/Correct Layer Props ---------------------------------------------
    for layer_props in [
        has_layer_props.xplane.layer
        for has_layer_props in bpy.data.objects[:] + bpy.data.collections[:]
    ]:
        # Since someone could add lods/cockpit_regions just before export, export needs to be the one
        # to validate the size of the collection
        while len(layer_props.lod) < xplane_constants.MAX_LODS - 1:
            layer_props.lod.add()
        while len(layer_props.cockpit_region) < xplane_constants.MAX_COCKPIT_REGIONS:
            layer_props.cockpit_region.add()
    # -------------------------------------------------------------------------

    # do not update newly created files
    if not bpy.context.blend_data.filepath:
        return

    assert bpy.data.filepath, "We've missed the new file check"
    # --- Setup logger (Updater) ----------------------------------------------
    logger.clear()
    logger.addTransport(
        xplane_helpers.XPlaneLogger.InternalTextTransport("Updater Log"),
        xplane_constants.LOGGER_LEVELS_ALL,
    )
    logger.addTransport(XPlaneLogger.ConsoleTransport())
    # -------------------------------------------------------------------------

    current_version = xplane_helpers.VerStruct.current()

    def handle_legacy_idprop(scene: bpy.types.Scene):
        if scene.get("xplane2blender_version") != xplane_constants.DEPRECATED_XP2B_VER:
            # "3.2.0 was the last version without an updater, so default to that."
            # 3.20 was a mistake
            legacy_version_str = scene.get("xplane2blender_version", "3.2.0").replace(
                "20", "2"
            )
            legacy_version = xplane_helpers.VerStruct.parse_version(legacy_version_str)
            if legacy_version is not None:
                xplane_helpers.VerStruct.add_to_version_history(scene, legacy_version)
                logger.info(f"Added {legacy_version} to version history")

                scene["xplane2blender_version"] = xplane_constants.DEPRECATED_XP2B_VER
            else:
                logger.warn(
                    f"pre-3.4.0-beta.5 file has invalid xplane2blender_version: {legacy_version_str}.\n"
                    f"Re-open file in a previous version and/or fix manually in Scene->Custom Properties"
                )

    for scene in bpy.data.scenes:
        handle_legacy_idprop(scene)

    latest_versions = sorted(
        (
            xplane_helpers.VerStruct.from_version_entry(
                scene.xplane.xplane2blender_ver_history[-1]
            )
            for scene in bpy.data.scenes
            if scene.xplane.xplane2blender_ver_history
        ),
    )
    assert latest_versions, "Non-newly created file has no scene with version history"
    last_version = latest_versions[-1]

    if last_version < current_version:
        logger.info(
            f"The current addon version, '{current_version}', is greater than the previous version, '{last_version}'. The updater will run as needed."
        )
        update(last_version, logger)

        logger.success(
            f"Your file was successfully updated to XPlane2Blender {current_version}"
        )
    elif last_version > current_version:
        logger.warn(
            f"DANGER: VERSION ISSUE MAY CORRUPT WORK! CHECK BLENDER AND ADDON VERSION. You have opened this file in an older version of XPlane2Blender."
            f" If saved and opened with a later version, the updater may re-run and overwrite data."
        )

    # Add the current version to the history, no matter what. Just in case it means something
    _synchronize_last_version_across_histories(current_version)
    logger.info(f"Added '{current_version}' to version history")


bpy.app.handlers.load_post.append(load_handler)


@persistent
def save_handler(dummy):
    for scene in bpy.data.scenes:
        scene["xplane2blender_version"] = xplane_constants.DEPRECATED_XP2B_VER
    # For if you append or make a new scene
    _synchronize_last_version_across_histories(xplane_helpers.VerStruct.current())


bpy.app.handlers.save_pre.append(save_handler)
