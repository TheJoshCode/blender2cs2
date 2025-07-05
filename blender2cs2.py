bl_info = {
    "name": "CS2 Asset Exporter",
    "author": "JoshMakesStuff",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "File > Export > CS2 Asset Exporter",
    "description": "Exports meshes and materials to Counter-Strike 2 compatible format",
    "category": "Import-Export"
}

import bpy
import os
from pathlib import Path

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

def resize_image_to_multiple_of_4(image):
    """Resize image to nearest multiple of 4, ensuring minimum size of 4x4."""
    width = max(4, image.size[0] - (image.size[0] % 4))
    height = max(4, image.size[1] - (image.size[1] % 4))
    if image.size != (width, height):
        image.scale(width, height)

def save_image(image, filepath):
    """Save image as TGA format after resizing."""
    resize_image_to_multiple_of_4(image)
    image.filepath_raw = str(filepath)
    image.file_format = 'TARGA'
    image.save()

def get_texture_path(material, socket_name, output_dir):
    """Extract texture path from material node, return default if not found."""
    node = material.node_tree.nodes.get("Principled BSDF")
    if node and (input_socket := node.inputs.get(socket_name)) and input_socket.is_linked:
        tex_node = input_socket.links[0].from_node
        if tex_node.type == 'TEX_IMAGE' and tex_node.image:
            tex_path = Path(output_dir) / f"{tex_node.image.name}.tga"
            save_image(tex_node.image, tex_path)
            return f"materials/{tex_node.image.name}.tga"
    
    # Handle default texture fallback
    if socket_name == "Roughness":
        return "materials/default/default_rough.tga"
    return f"materials/default/default_{socket_name.lower()}.tga"


def get_surface_type(material_name):
    """Determine surface type from material name."""
    return next((surface for surface in SURFACE_TYPES if surface in material_name.lower()), "default")

def export_material(material, output_dir):
    """Export material to VMAT format."""
    vmat_path = Path(output_dir) / f"{material.name.split('/')[-1]}.vmat"
    color = get_texture_path(material, "Base Color", output_dir)
    normal = get_texture_path(material, "Normal", output_dir)
    roughness = get_texture_path(material, "Roughness", output_dir)
    surface_type = get_surface_type(material.name)

    vmat_content = f"""// Auto-generated VMAT file
Layer0
{{
    shader "csgo_complex.vfx"
    TextureColor "{color}"
    TextureNormal "{normal}"
    TextureRoughness "{roughness}"
    TextureAmbientOcclusion "materials/default/default_ao.tga"
    g_flMetalness "0.000"
    g_vColorTint "[1.000000 1.000000 1.000000 0.000000]"
    g_vTexCoordCenter "[0.500 0.500]"
    g_vTexCoordOffset "[0.000 0.000]"
    g_vTexCoordScale "[1.000 1.000]"
    g_nTextureAddressModeU "0"
    g_nTextureAddressModeV "0"
    g_bFogEnabled "1"
    SystemAttributes
    {{
        PhysicsSurfaceProperties "{surface_type}"
    }}
}}
"""
    vmat_path.write_text(vmat_content)

def export_fbx(context, filepath, objects):
    """Export selected objects to FBX format."""
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=str(filepath),
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

def export_assets(context, export_dir):
    """Export all assets to CS2 format."""
    export_path = Path(export_dir)
    if not export_path.is_dir():
        raise ValueError(f"Invalid directory: {export_dir}")

    # Ensure material names are prefixed
    for material in bpy.data.materials:
        if not material.name.startswith("materials/"):
            material.name = f"materials/{material.name}"

    # Create directories
    materials_dir = export_path / "materials"
    models_dir = export_path / "models"
    materials_dir.mkdir(exist_ok=True)
    models_dir.mkdir(exist_ok=True)

    # Export materials
    for material in bpy.data.materials:
        export_material(material, materials_dir)

    # Export individual objects
    mesh_objects = [obj for obj in context.scene.objects if obj.type == 'MESH']
    for obj in mesh_objects:
        export_fbx(context, models_dir / f"{obj.name}.fbx", [obj])

    # Export combined FBX
    export_fbx(context, export_path / "combined.fbx", mesh_objects)

class ExportCS2(bpy.types.Operator):
    """Operator to export assets to CS2 format."""
    bl_idname = "export_scene.cs2_export"
    bl_label = "Export to CS2 Format"
    bl_options = {'REGISTER', 'UNDO'}

    directory: bpy.props.StringProperty(subtype='DIR_PATH')

    def execute(self, context):
        try:
            export_assets(context, self.directory)
            self.report({'INFO'}, f"Successfully exported CS2 assets to {self.directory}")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_func_export(self, context):
    """Add export operator to the File > Export menu."""
    self.layout.operator(ExportCS2.bl_idname, text="CS2 Asset Exporter", icon='EXPORT')

def register():
    """Register the operator and menu item."""
    bpy.utils.register_class(ExportCS2)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    """Unregister the operator and menu item."""
    bpy.utils.unregister_class(ExportCS2)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()