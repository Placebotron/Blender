import bpy 
import mathutils
import logging
import argparse
from pathlib import Path

'''This script produces depth renderings'''

# Configure module-level logger
logger = logging.getLogger("CameraClipper")

scene = bpy.context.scene

def set_camera_clipping_to_scene(camera_obj: bpy.types.Object, margin:float = 0.1) -> None:
    """
    Sets the clipping range of the given camera object to focuse all visible meshes in the given scene.
    
    Args:
        camera_obj (bpy.type.Object): The camera whose clipping distance will be adjusted.
        margin (float): Extra margin added before and after the min max distance.
    """
    
    
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    min_distance = float('inf')
    max_distance = float('-inf')
    
    cam_matrix_inv = camera_obj.matrix_world.inverted()
    
    for obj in scene.objects:
        if obj.type != 'MESH' or not obj.visible_get():
            logging.error(f"Object:{obj.name} is not a mesh or does not have any visible objects.")
            continue
        
        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        
        if mesh is None:
            logging.error(f"Mesh {mesh} is None")
            continue
        
        for vertex in mesh.vertices:
            world_co = eval_obj.matrix_world @ vertex.co
            cam_co = cam_matrix_inv @ world_co
            z = -cam_co.z
            
            min_distance = min(min_distance, z)
            max_distance = max(max_distance, z)
            
        eval_obj.to_mesh_clear()
        
        # Ensure positive non-zero distances
        min_distance = max(min_distance - margin, 0.001)
        max_distance = max(max_distance + margin, min_distance + 0.01)
        
        # Apply the calucalted clipping distsances to the camera
        camera_data = camera_obj.data
        camera_data.clip_start = min_distance 
        camera_data.clip_end = max_distance 
        
        logger.info("Camera clipping set to: start=%.4f, end=%.4f", min_distance, max_distance)
        
def set_orthographi_camera(camera_obj: bpy.types.Object) -> None:
    """
    Configures the camera to orthogprahic projection.
    
    Args:
        camera_obj (bpy.type.Object): The camera whose clipping distance will be adjusted.
    """
    
    camera_data = camera_obj.data
    camera_data.type = 'ORTHO'
    logger.info("Camera set to orthographic.")
    
def scene_preparation()->None:
    """
    Prepares the Blender scene to handle depth map renderings.
    """
    scene.render.image_settings.color_depth = '16'
    scene.view_layers["ViewLayer"].use_pass_z = True
    
    # B-est output format for depth maps
    scene.render.image_settings.file_format = 'OPEN_EXR'
    scene.render.image_settings.color_mode = 'BW'
    
    logging.info("Scene settings for depth rendering prepared.")

def join_all_meshes() -> bpy.types.Object:
    """
    Joins all mesh objects in the scene into a single mesh and selects it.

    Returns:
        bpy.types.Object: The joined mesh object.
    """
    # Deselect everything
    bpy.ops.object.select_all(action='DESELECT')

    # Collect all mesh objects
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

    if not mesh_objects:
        logger.error("No mesh objects found to join.")
        return None

    # Make the first mesh the active object
    active_obj = mesh_objects[0]
    bpy.context.view_layer.objects.active = active_obj

    # Select all meshes
    for obj in mesh_objects:
        obj.select_set(True)

    # Join them
    bpy.ops.object.join()

    # After join, active_obj is now the joined mesh
    logger.info("All meshes joined into: %s", active_obj.name)

    # Ensure it's selected
    bpy.ops.object.select_all(action='DESELECT')
    active_obj.select_set(True)

    return active_obj


def node_setup()->None:
    """
    Setup the necessary nodes for renderings depth maps. 
    """
    # Ensure compositor nodes are enabled
    
    scene.use_nodes = True
    tree = scene.node_tree

   # Get or create Render Layers node
    render_layers = None
    for node in tree.nodes:
        if node.type == 'R_LAYERS':
            render_layers = node
            break

    if render_layers is None:
        render_layers = tree.nodes.new('CompositorNodeRLayers')

    # Create Normalize node
    normalize_node = tree.nodes.new('CompositorNodeNormalize')

    # Create Invert node
    invert_node = tree.nodes.new('CompositorNodeInvert')

    # Get or create Composite node
    composite_node = None
    for node in tree.nodes:
        if node.type == 'COMPOSITE':
            composite_node = node
            break

    if composite_node is None:
        composite_node = tree.nodes.new('CompositorNodeComposite')

    # Link nodes
    tree.links.new(
        render_layers.outputs['Depth'],
        normalize_node.inputs[0]
    )
    tree.links.new(
        normalize_node.outputs[0],
        invert_node.inputs[1]
    )
    tree.links.new(
        invert_node.outputs[0],
        composite_node.inputs[0]
    )

    logging.info("Node chain for depth rendering created.")

def render(output_path:Path, file_format:str) -> None:
    """
    Render the deth map and store it.
    """
    # Set output filepath
    scene.render.filepath = str(output_path / file_format.lower())
    # Render still image
    bpy.ops.render.render(write_still=True)

def main(output_path: Path, image_format:str) -> None:
    """
    Main function orchestrating the rendering.
    """
    scene_preparation()
    node_setup()
    
    active_object = join_all_meshes()
    if active_object:
        # Select the joined mesh
        active_object.select_set(True)
    else:
        logger.error("No active object to work with.")
        return

    # Make sure there's an active camera
    camera = bpy.context.scene.camera
    if camera is None:
        logger.error("No active camera found in the scene.")
        return

    # Set camera to orthographic
    set_orthographi_camera(camera)
    bpy.ops.view3d.camera_to_view_selected()
    # Adjust clipping
    set_camera_clipping_to_scene(camera)
    # Render to specified output path
    render(output_path, args.format)
    
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s"
    )
    parser = argparse.ArgumentParser(description="Render depth maps from a Blender scene.")
    parser.add_argument("--output", required=True, help="Output file path (e.g., /tmp/depth.png)")
    parser.add_argument("--format", default="PNG", choices=["PNG", "EXR"], help="Output image format.")

    args = parser.parse_args()
    output = Path(args.output)
    main(output, args.format)

    