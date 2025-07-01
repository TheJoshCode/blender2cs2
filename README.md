# Overview
This Blender add-on streamlines the export process for meshes and materials into a format compatible with Source 2. It automatically generates .fbx models, .vmat material definitions, and .tga textures, organizing them for quick integration into the CS2 editor.

# Features
- Exports individual mesh objects and a combined scene FBX

- Extracts and resizes texture maps (Base Color, Normal, Roughness)

- Auto-generates Source 2-compatible .vmat files

- Detects and applies physics surface types from material names

- Automatically prefixes material names with materials/

# Installation
## 1. Download or clone this repository.

## 2. In Blender:

- Go to Edit > Preferences > Add-ons

- Click Install..., then select the blender2cs2.py file

- Enable Blender to CS2 Exporter in the add-ons list

# Usage
1. Set up your material(s) using the Principled BSDF shader.

2. Navigate to File > Export > CS2 Asset Exporter.

3. Export

# Output structure:
```bash
your_export_directory/
├── models/
│   └── object_name.fbx
├── materials/
│   ├── material_name.vmat
│   └── texture_name.tga
└── combined.fbx
```
