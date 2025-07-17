# Blender

This Repository is a collection of scripts that use the python api to achieve different task. 


## Features

- Joins all meshes into a single object
- Adjusts camera clipping automatically
- Outputs depth as PNG or EXR
- Supports orthographic or perspective cameras

## Usage

Run Blender in background:

```bash
blender yourscene.blend --background --python depth_renderer.py -- \
  --output /path/to/output.png \
  --format PNG 
