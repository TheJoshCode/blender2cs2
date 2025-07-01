bl_info = {
    "name": "Blender to CS2 Exporter",
    "author": "JoshMakesStuff",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "File > Export > CS2 Exporter",
    "description": "Export objects and materials as CS2-ready assets with .fbx and .vmat",
    "category": "Import-Export",
}

import bpy
import os

# Full Valve surface types list (lowercase)
SURFACE_TYPES = {
    "alienflesh", "armorflesh", "asphalt", "audioblocker", "balloon", "beans", "blockbullets",
    "bloodyflesh", "boulder", "brakingrubbertire", "brass_bell_large", "brass_bell_medium",
    "brass_bell_small", "brass_bell_smallest", "brass_bell_smallest_g", "brick", "canister",
    "cardboard", "cardboard_smallbox", "carpet", "cieling_tile", "chain", "chainlink", "clay",
    "cloth", "computer", "concrete", "concrete_block", "concrete_polished", "default",
    "default_silent", "defuser", "dirt", "dufflebag_survivalcase", "flesh", "floating_metal_barrel",
    "floatingstandable", "foliage", "fruit", "glass", "glassbottle", "glassfloor", "grass",
    "grate", "gravel", "grenade", "ice", "item", "jalopy", "jalopytire", "jeeptire", "ladder",
    "metal", "metal_barrel", "metal_barrel_explodingsurvival", "metal_barrelsoundoverride",
    "metal_bouncy", "metal_box", "metal_dumpster", "metal_sand_barrel", "metal_sheetmetal",
    "metal_shield", "metal_survivalcase", "metal_survivalcase_unpunchable",
    "metal_vehiclesoundoverride", "metal_ventslat", "metaldogtags", "metalgrate", "metalpanel",
    "metalrailing", "metalvehicle", "metalvent", "mud", "no_decal", "paintcan", "paper",
    "papercup", "papertowel", "plaster", "plaster_drywall", "plastic", "plastic_autocover",
    "plastic_barrel", "plastic_barrel_buoyant", "plastic_box", "plastic_dumpster",
    "plastic_milkcrate", "plastic_solid", "plastic_survivalcase", "plastic_tape", "plasticbottle",
    "player", "player_control_clip", "playerflesh", "popcan", "porcelain", "pottery",
    "potterylarge", "puddle", "quicksand", "rock", "roller", "rubber", "rubbertire", "sand",
    "sheetrock", "slidingrubbertire", "slidingrubbertire_front", "slidingrubbertire_jalopyfront",
    "slidingrubbertire_jalopyrear", "slidingrubbertire_rear", "slime", "slipperymetal",
    "slipperyslide", "slipperyslime", "slowgrass", "snow", "soccerball", "solidmetal",
    "strongman_bell", "stucco", "sugarcane", "tile", "tile_survivalcase", "tile_survivalcase_gib",
    "upholstery", "wade", "water", "watermelon", "weapon", "weapon_magazine", "weaponc4",
    "weaponflashbang", "weaponheavy", "weaponhegrenade", "weaponincendiary", "weaponknife",
    "weaponmagazine", "weaponmolotov", "weaponpistol", "weaponrifle", "weaponshotgun",
    "weaponsmg", "weaponsniper", "wet", "wet_sand", "wood", "wood_basket", "wood_box",
    "wood_crate", "wood_dense", "wood_furniture", "wood_ladder", "wood_lowdensity", "wood_panel",
    "wood_plank", "wood_solid", "wood_tree"
}

def detect_surface_type(material_name):
    name = material_name.lower()
    for surface in SURFACE_TYPES:
        if surface in name:
            return surface
    return "default"

def export_image(img, target_path):
    if not img:
        return None
    try:
        # Force save as .tga
        img.filepath_raw = target_path
        img.file_format = 'TARGA'
        img.save_render(filepath=target_path)
        return os.path.basename(target_path)
    except Exception as e:
        print(f"Error exporting image {img.name}: {e}")
        return None

def get_image_from_slot(mat, slot_name):
    # Search in nodes or slots for the image connected to the given property
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            # Check if the node is connected to the right socket by name or by property
            # For simplicity, we match slot_name in the node label or node name
            if slot_name.lower() in node.name.lower() or slot_name.lower() in node.label.lower():
                return node.image
    # Fallback: try searching all images in nodes
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE':
            return node.image
    return None

def build_vmat_content(mat, basecolor_tex, roughness_tex, normal_tex):
    lines = []
    lines.append("// THIS FILE IS AUTO-GENERATED\n")
    lines.append("Layer0\n{")
    lines.append('\tshader "csgo_complex.vfx"\n')

    # AO (empty as example, could be extended)
    lines.append('\t//---- Ambient Occlusion ----')
    lines.append('\tTextureAmbientOcclusion ""\n')

    # Color
    lines.append('\t//---- Color ----')
    lines.append('\tg_flModelTintAmount "1.000"')
    lines.append('\tg_flTexCoordRotation "0.000"')
    lines.append('\tg_nScaleTexCoordUByModelScaleAxis "0"')
    lines.append('\tg_nScaleTexCoordVByModelScaleAxis "0"')
    lines.append('\tg_vColorTint "[1.000000 1.000000 1.000000 0.000000]"')
    lines.append('\tg_vTexCoordCenter "[0.500 0.500]"')
    lines.append('\tg_vTexCoordOffset "[0.000 0.000]"')
    lines.append('\tg_vTexCoordScale "[1.000 1.000]"')
    lines.append('\tg_vTexCoordScrollSpeed "[0.000 0.000]"')
    basecolor_path = f"materials/{basecolor_tex}" if basecolor_tex else ""
    lines.append(f'\tTextureColor "{basecolor_path}"\n')

    # Fog
    lines.append('\t//---- Fog ----')
    lines.append('\tg_bFogEnabled "1"\n')

    # Lighting
    lines.append('\t//---- Lighting ----')
    lines.append('\tg_flMetalness "0.000"')
    roughness_path = f"materials/{roughness_tex}" if roughness_tex else ""
    lines.append(f'\tTextureRoughness "{roughness_path}"\n')

    # Normal
    lines.append('\t//---- Normal Map ----')
    normal_path = f"materials/{normal_tex}" if normal_tex else ""
    lines.append(f'\tTextureNormal "{normal_path}"\n')

    # Texture address mode
    lines.append('\t//---- Texture Address Mode ----')
    lines.append('\tg_nTextureAddressModeU "0"')
    lines.append('\tg_nTextureAddressModeV "0"')

    # SystemAttributes with PhysicsSurfaceProperties
    surface_type = detect_surface_type(mat.name)
    lines.append('\nSystemAttributes\n{')
    lines.append(f'\tPhysicsSurfaceProperties "{surface_type}"')
    lines.append('}')
    lines.append("}")

    return "\n".join(lines)

def export_material(material, materials_dir):
    # Make sure material name starts with "materials/"
    mat_name = material.name
    if not mat_name.lower().startswith("materials/"):
        mat_name = "materials/" + mat_name

    # Get images
    # Try to find basecolor, roughness, normal from principled BSDF node if exists
    basecolor_img = None
    roughness_img = None
    normal_img = None
    if material.use_nodes:
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                # BaseColor
                if 'Base Color' in node.inputs and node.inputs['Base Color'].is_linked:
                    basecolor_img = node.inputs['Base Color'].links[0].from_node.image
                # Roughness
                if 'Roughness' in node.inputs and node.inputs['Roughness'].is_linked:
                    roughness_img = node.inputs['Roughness'].links[0].from_node.image
                # Normal Map
                if 'Normal' in node.inputs and node.inputs['Normal'].is_linked:
                    normal_map_node = node.inputs['Normal'].links[0].from_node
                    if normal_map_node.type == 'NORMAL_MAP' and normal_map_node.inputs['Color'].is_linked:
                        normal_img = normal_map_node.inputs['Color'].links[0].from_node.image
                    elif normal_map_node.type == 'TEX_IMAGE':
                        normal_img = normal_map_node.image
                break

    # Export images
    basecolor_filename = None
    roughness_filename = None
    normal_filename = None

    if basecolor_img:
        basecolor_filename = f"{material.name}_basecolor.tga"
        basecolor_path = os.path.join(materials_dir, basecolor_filename)
        export_image(basecolor_img, basecolor_path)

    if roughness_img:
        roughness_filename = f"{material.name}_roughness.tga"
        roughness_path = os.path.join(materials_dir, roughness_filename)
        export_image(roughness_img, roughness_path)

    if normal_img:
        normal_filename = f"{material.name}_normal.tga"
        normal_path = os.path.join(materials_dir, normal_filename)
        export_image(normal_img, normal_path)

    # Write .vmat file
    vmat_content = build_vmat_content(material, basecolor_filename, roughness_filename, normal_filename)
    vmat_filename = os.path.join(materials_dir, f"{material.name}.vmat")
    with open(vmat_filename, 'w') as f:
        f.write(vmat_content)

def export_object_fbx(obj, export_root):
    # Ensure models directory exists
    models_dir = os.path.join(export_root, "models")
    os.makedirs(models_dir, exist_ok=True)

    # Select only this object
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    fbx_path = os.path.join(models_dir, f"{obj.name}.fbx")

    bpy.ops.export_scene.fbx(
        filepath=fbx_path,
        use_selection=True,
        apply_scale_options='FBX_SCALE_UNITS',
        object_types={'MESH', 'EMPTY', 'ARMATURE'},
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode='COPY',
        embed_textures=False
    )

def export_all(context, export_root):
    # Create materials directory
    materials_dir = os.path.join(export_root, "materials")
    os.makedirs(materials_dir, exist_ok=True)

    # Export materials
    for mat in bpy.data.materials:
        export_material(mat, materials_dir)

    # Export each mesh object as individual FBX inside models folder
    for obj in context.scene.objects:
        if obj.type == 'MESH':
            export_object_fbx(obj, export_root)

class ExportCS2Operator(bpy.types.Operator):
    bl_idname = "export_scene.cs2_export"
    bl_label = "Export CS2 Assets"
    bl_description = "Export each object as FBX and create CS2-ready material folder"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        export_root = self.filepath
        print(f"Selected export folder: '{export_root}'")  # Debug print
        if not export_root or not os.path.isdir(export_root):
            self.report({'ERROR'}, f"Please select a valid directory. Got: {export_root!r}")
            return {'CANCELLED'}

        export_all(context, export_root)
        self.report({'INFO'}, f"Exported CS2 assets to {export_root}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func_export(self, context):
    self.layout.operator(ExportCS2Operator.bl_idname, text="CS2 One-Click Export",)

def register():
    bpy.utils.register_class(ExportCS2Operator)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ExportCS2Operator)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()
