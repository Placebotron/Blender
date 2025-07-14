"""
cadwhisperer.io.scene_loader
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Utility for turning a GLB/GLTF file into a (scene, NetworkX‐DiGraph) pair.

Usage
-----
from cadwhisperer.io.scene_loader import load_scene_make_graph
scene, g = load_scene_make_graph("my_part.glb")
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Tuple

import networkx as nx
import numpy as np
import trimesh


def _default_cache_path(glb_path: Path) -> Path:
    """`.glb`  →  `.scene.graphml` in the same folder (hashed by mtime+size)."""
    stamp = f"{glb_path.stat().st_mtime_ns}_{glb_path.stat().st_size}"
    digest = hashlib.sha1(stamp.encode()).hexdigest()[:8]
    return glb_path.with_suffix(f".{digest}.graphml")


def load_scene_make_graph(
    glb_file: str | Path,
    *,
    cache: bool = True,
    cache_path: Path | None = None,
    verbose: bool = False,
) -> Tuple[trimesh.Scene, nx.DiGraph]:
    """
    Parameters
    ----------
    glb_file : str | Path
        Path to .glb / .gltf file (tri-mesh Scene is forced).
    cache : bool
        If True, write/read a GraphML file so repeated loads are instant.
    cache_path : Path | None
        Override where the cache is stored; otherwise next to input file.
    verbose : bool
        Print a short summary.

    Returns
    -------
    scene : trimesh.Scene
    g     : networkx.DiGraph
    """
    glb_path = Path(glb_file)
    if not glb_path.exists():
        raise FileNotFoundError(glb_path)

    cache_path = cache_path or _default_cache_path(glb_path)

    # try fast-path ----------------------------------------------------------------
    if cache and cache_path.exists():
        g = nx.read_graphml(cache_path)
        scene = trimesh.load(glb_path, force="scene")
        if verbose:
            print(f"[scene_loader] loaded graph cache → {cache_path.name}")
        return scene, g

    # slow path: build graph -------------------------------------------------------
    scene: trimesh.Scene = trimesh.load(glb_path, force="scene")
    g = scene.graph.to_networkx().copy()

    # add simple attributes
    for node_id in g.nodes:
        g.nodes[node_id]["label"] = str(node_id)
        try:
            transform, geom_name = scene.graph[node_id]
            g.nodes[node_id]["geom_name"] = geom_name or ""
            g.nodes[node_id]["matrix"] = np.asarray(transform).tolist()
            if geom_name:
                g.nodes[node_id]["label"] = geom_name
        except Exception:
            pass

    # optional cache write
    if cache:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            nx.write_graphml(g, cache_path)
            if verbose:
                print(f"[scene_loader] wrote graph cache → {cache_path.name}")
        except Exception as e:
            if verbose:
                print(f"[scene_loader] cache write failed: {e}")

    if verbose:
        print(
            f"[scene_loader] GLB: {glb_path.name} → "
            f"{g.number_of_nodes()} nodes / {g.number_of_edges()} edges"
        )

    return scene, g
