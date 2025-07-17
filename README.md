# Blender

This Repository is a collection of scripts that use the python api to achieve different task. 

## Scripts
*Cad whisperer* - Takes as input a glb file (will be updated to more CAD files formats) and translates the hierarchy into a GNN. It also extracts all the necessary information about each Parts / Assembly to enable an accurate representation of the model in a Neural Network way. 
### Purpose 
3D Model give an exellent representation of machines in the engineering industry, in terms of position, size, relation, etc. of spare parts. Currently this capabilities are not being used in the industry, crucially as well in the current endeviours of AI. Once the models hierarchy is being matched with the rest of the metadata from the customers AI models can be trained more accurately and informations can be gathered more accuratly. 
### Features 


*depth_rendering.py* a script that generated depth images out of CAD files in PNG or EXR format.
### Features

- Joins all meshes into a single object
- Adjusts camera clipping automatically
- Outputs depth as PNG or EXR
- Supports orthographic or perspective cameras

### Usage

Run Blender in background:

```bash
blender yourscene.blend --background --python depth_renderer.py -- \
  --output /path/to/output.png \
  --format PNG 
