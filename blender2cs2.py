bl_info = {
    "name": "Blender to CS2 Exporter",
    "author": "JoshMakesStuff @ X",
    "version": (1, 0),
    "blender": (3, 0, 0),
    "location": "File > Export > CS2 Asset Exporter",
    "description": "Exports mesh + materials to CS2-compatible format",
    "category": "Import-Export"
}

import bpy
import os

SURFACE_TYPES = {
    'alienflesh', 'armorflesh', 'asphalt', 'audioblocker', 'balloon', 'beans', 'blockbullets',
    'bloodyflesh', 'boulder', 'brakingrubbertire', 'brass_bell_large', 'brass_bell_medium',
    'brass_bell_small', 'brass_bell_smallest', 'brick', 'canister', 'cardboard', 'carpet',
    'chain', 'chainlink', 'clay', 'cloth', 'computer', 'concrete', 'default', 'defuser', 'dirt',
    'flesh', 'foliage', 'fruit', 'glass', 'grass', 'grate', 'gravel', 'ice', 'item', 'ladder',
    'metal', 'metal_barrel', 'metal_box', 'metalgrate', 'metalpanel', 'mud', 'paintcan', 'paper',
    'plaster', 'plastic', 'player', 'popcan', 'porcelain', 'rock', 'rubber', 'sand', 'slime',
    'snow', 'tile', 'upholstery', 'water', 'weapon', 'wet', 'wood', 'wood_box', 'wood_crate'
}

def resize_image_to_multiple_of_4(img):
    width = max(img.size[0] - (img.size[0] % 4), 4)
    height = max(img.size[1] - (img.size[1] % 4), 4)
    if img.size[0] != width or img.size[1] != height:
        img.scale(width, height)

def save_image(img, filepath):
    resize_image_to_multiple_of_4(img)
    img.filepath_raw = filepath
    img.file_format = 'TARGA'
    img.save()

def extract_texture_path(mat, socket_name, output_dir, fallback):
    node = mat.node_tree.nodes.get("Principled BSDF")
    if node:
        input_socket = node.inputs.get(socket_name)
        if input_socket and input_socket.is_linked:
            tex_node = input_socket.links[0].from_node
            if tex_node.type == 'TEX_IMAGE' and tex_node.image:
                tex_path = os.path.join(output_dir, tex_node.image.name + ".tga")
                save_image(tex_node.image, tex_path)
                return f"materials/{tex_node.image.name}.tga"
    return fallback

def get_surface_type(mat_name):
    name = mat_name.lower()
    return next((s for s in SURFACE_TYPES if s in name), "default")

def export_material(mat, output_dir):
    mat_name = mat.name
    vmat_path = os.path.join(output_dir, mat_name.split("/")[-1] + ".vmat")

    color = extract_texture_path(mat, "Base Color", output_dir, "materials/default/default_color.tga")
    normal = extract_texture_path(mat, "Normal", output_dir, "materials/default/default_normal.tga")
    rough = extract_texture_path(mat, "Roughness", output_dir, "materials/default/default_rough.tga")
    surface_type = get_surface_type(mat_name)

    with open(vmat_path, "w") as f:
        f.write(f"""// THIS FILE IS AUTO-GENERATED

Layer0
{{
\tshader "csgo_complex.vfx"

\tTextureAmbientOcclusion "materials/default/default_ao.tga"
\tg_flModelTintAmount "1.000"
\tg_flTexCoordRotation "0.000"
\tg_nScaleTexCoordUByModelScaleAxis "0"
\tg_nScaleTexCoordVByModelScaleAxis "0"
\tg_vColorTint "[1.000000 1.000000 1.000000 0.000000]"
\tg_vTexCoordCenter "[0.500 0.500]"
\tg_vTexCoordOffset "[0.000 0.000]"
\tg_vTexCoordScale "[1.000 1.000]"
\tg_vTexCoordScrollSpeed "[0.000 0.000]"
\tTextureColor "{color}"
\tg_bFogEnabled "1"
\tg_flMetalness "0.000"
\tTextureRoughness "{rough}"
\tTextureNormal "{normal}"
\tg_nTextureAddressModeU "0"
\tg_nTextureAddressModeV "0"

\tSystemAttributes
\t{{
\t\tPhysicsSurfaceProperties "{surface_type}"
\t}}
}}""")

def prefix_material_names():
    for mat in bpy.data.materials:
        if not mat.name.startswith("materials/"):
            mat.name = f"materials/{mat.name}"

def export_object_fbx(obj, export_dir):
    models_dir = os.path.join(export_dir, "models")
    os.makedirs(models_dir, exist_ok=True)

    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=os.path.join(models_dir, f"{obj.name}.fbx"),
        use_selection=True,
        apply_scale_options='FBX_SCALE_UNITS',
        object_types={'MESH'},
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode='AUTO'
    )

    obj.select_set(False)

def export_combined_fbx(context, export_dir):
    filepath = os.path.join(export_dir, "combined.fbx")

    bpy.ops.object.select_all(action='DESELECT')
    for obj in context.scene.objects:
        if obj.type == 'MESH':
            obj.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=filepath,
        use_selection=True,
        apply_scale_options='FBX_SCALE_UNITS',
        object_types={'MESH'},
        bake_space_transform=True,
        axis_forward='-Z',
        axis_up='Y',
        mesh_smooth_type='FACE',
        use_mesh_modifiers=True,
        add_leaf_bones=False,
        path_mode='AUTO'
    )

    bpy.ops.object.select_all(action='DESELECT')

def export_all(context, export_dir):
    if not os.path.isdir(export_dir):
        print(f"Please select a valid directory. Got: {export_dir}")
        return

    prefix_material_names()

    materials_dir = os.path.join(export_dir, "materials")
    os.makedirs(materials_dir, exist_ok=True)

    for mat in bpy.data.materials:
        export_material(mat, materials_dir)

    for obj in context.scene.objects:
        if obj.type == 'MESH':
            export_object_fbx(obj, export_dir)

    export_combined_fbx(context, export_dir)

class ExportCS2(bpy.types.Operator):
    bl_idname = "export_scene.cs2_export"
    bl_label = "Export to CS2 Format"

    directory = bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        export_all(context, self.directory)
        self.report({'INFO'}, f"Exported CS2 assets to {self.directory}")
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator(ExportCS2.bl_idname, text="CS2 One-Click Exporter", icon='EXPORT')

def register():
    bpy.utils.register_class(ExportCS2)
    bpy.types.TOPBAR_MT_file_export.append(menu_func)

def unregister():
    bpy.utils.unregister_class(ExportCS2)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func)

if __name__ == "__main__":
    register()
