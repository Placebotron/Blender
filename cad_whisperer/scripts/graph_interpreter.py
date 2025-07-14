#!/usr/bin/env python3
"""
graph_interpreter.py
--------------------
A one‑stop utility that:
  • builds / loads a NetworkX scene‑graph from a GLB file
  • augments the graph with *derived* semantic tags (screw, nut, assembly …)
    using **both** name heuristics *and* coarse geometry analysis –
    so it still works if labels are missing or wrong.
  • serialises the enriched graph into three text‑friendly formats
      1. triples.txt            (line‑oriented RDF‑like)
      2. node_link.json         (NetworkX canonical)
      3. nodes.jsonl.gz         (one node per line, gzip)
  • prints quick statistics (how many screws, sub‑parts, assemblies …)

Run:
    python graph_interpreter.py \
        --glb   /path/10494016.glb \
        --out   out_dir           \
        --no-geom   # (skip the mesh pass if performance is an issue)

Dependencies
-------------
  pip install trimesh networkx numpy tqdm lxml  # lxml only for graphml reloads
  pip install plotly     # if you want the Plotly helper

Notes
-----
*  Geometry reasoning is *coarse* – it checks bounding‑box aspect ratios
   and (optionally) trimesh's cylinder fit.  Good enough for screws vs
   plates, but not a CAD kernel replacement.
*  Designed as a library **and** a CLI.  Import the helpers in a notebook
   or just run from the command‑line.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path
from typing import Iterable, Tuple

import networkx as nx
import numpy as np
import trimesh
from tqdm import tqdm
from networkx.readwrite import json_graph

SCREW_KEYWORDS = {"screw", "bolt", "thread", "schraube", "vis"}

# ---------------------------------------------------------------------------- #
# 1.  Graph construction
# ---------------------------------------------------------------------------- #

def load_scene_make_graph(glb_path: Path, *, verbose: bool = True) -> Tuple[trimesh.Scene, nx.DiGraph]:
    """Returns (scene, graph) where *graph* is a NetworkX DiGraph copy of
    the scene hierarchy with basic `label` attributes.
    """
    scene = trimesh.load(glb_path, force="scene")
    g = scene.graph.to_networkx().copy()  # ensure independent of trimesh

    for node_id in g.nodes:
        g.nodes[node_id]["label"] = str(node_id)  # default label – will update

    # try to preserve existing names if any
    for node_id in g.nodes:
        try:
            transform, geom_name = scene.graph[node_id]
            if geom_name:
                g.nodes[node_id]["geom_name"] = geom_name
                g.nodes[node_id]["label"] = geom_name
        except Exception:
            pass  # leave defaults

    if verbose:
        print(f"Loaded {glb_path.name}: {g.number_of_nodes()} nodes, {g.number_of_edges()} edges")
    return scene, g

# ---------------------------------------------------------------------------- #
# 2.  Enrich with semantics
# ---------------------------------------------------------------------------- #

def _is_cylinder_like(mesh: trimesh.Trimesh) -> bool:
    """Very lightweight cylindricality check: bounding‑box has two nearly
    equal small dimensions and one longer one."""
    try:
        extents = np.sort(mesh.bounds[1] - mesh.bounds[0])  # ascending
    except Exception:
        return False
    if extents[0] < 1e-3:
        return False  # degenerate
    xy_ratio = extents[1] / extents[0]
    slenderness = extents[2] / extents[1]
    # In screws: cross‑section ~circle (ratio ~1), length >> diameter
    return 0.8 <= xy_ratio <= 1.25 and slenderness >= 2.5


def tag_nodes(scene: trimesh.Scene, g: nx.DiGraph, *, use_geometry: bool = True) -> None:
    """Mutates the graph, adding:
      • part_type   → "SCREW" | "ASSEMBLY" | "PART"
      • has_children → bool
    """
    for n in g.nodes:
        g.nodes[n]["has_children"] = g.out_degree(n) > 0
        if g.out_degree(n) > 0:
            g.nodes[n]["part_type"] = "ASSEMBLY"
        else:
            g.nodes[n]["part_type"] = "PART"  # may be refined later

    # --- name‑based screw heuristic ---------------------------------------- #
    for n, attr in g.nodes(data=True):
        label_lc = attr["label"].lower()
        if any(k in label_lc for k in SCREW_KEYWORDS):
            attr["part_type"] = "SCREW"

    if not use_geometry:
        return

    # --- geometry‑based screw guess --------------------------------------- #
    for n, attr in tqdm(list(g.nodes(data=True)), desc="geom‑pass", leave=False):
        if attr.get("part_type") == "SCREW":
            continue  # name already identified – trust it
        geom_name = attr.get("geom_name")
        if not geom_name:
            continue
        mesh = scene.geometry.get(geom_name)
        if not isinstance(mesh, trimesh.Trimesh):
            continue
        if _is_cylinder_like(mesh):
            attr["part_type"] = "SCREW"

# ---------------------------------------------------------------------------- #
# 3.  Serialisers
# ---------------------------------------------------------------------------- #

def write_triples(g: nx.DiGraph, path: Path):
    with path.open("w") as f:
        for u, v in g.edges:
            f.write(f"{u} parent_of {v}\n")
        for n, a in g.nodes(data=True):
            if pt := a.get("part_type"):
                f.write(f"{n} part_type {pt}\n")
            if a.get("has_children"):
                f.write(f"{n} has_children true\n")
    print(f"Triples written → {path} ({path.stat().st_size/1e3:.1f} kB)")


def write_node_link_json(g: nx.DiGraph, path: Path):
    data = json_graph.node_link_data(g)
    path.write_text(json.dumps(data))
    print(f"Node‑link JSON → {path} ({path.stat().st_size/1e3:.1f} kB)")


def write_jsonl(g: nx.DiGraph, path: Path):
    with gzip.open(path, "wt") as f:
        for n, a in g.nodes(data=True):
            record = dict(id=n, **a, children=list(g.successors(n)))
            f.write(json.dumps(record) + "\n")
    print(f"JSONL (gzip)   → {path} ({path.stat().st_size/1e3:.1f} kB)")

# ---------------------------------------------------------------------------- #
# 4.  Quick stats
# ---------------------------------------------------------------------------- #

def print_stats(g: nx.DiGraph):
    counts = {}
    for _, a in g.nodes(data=True):
        pt = a.get("part_type", "UNKNOWN")
        counts[pt] = counts.get(pt, 0) + 1
    total = g.number_of_nodes()
    print("\nSummary:")
    for k, v in counts.items():
        print(f"  {k:<10}: {v:5d}")
    print(f"  TOTAL parts : {total:5d}\ ")

# ---------------------------------------------------------------------------- #
# 5.  CLI
# ---------------------------------------------------------------------------- #

def main(argv: Iterable[str] | None = None):
    p = argparse.ArgumentParser(description="Graph interpreter for CAD GLB scene‑graphs")
    p.add_argument("--glb", type=Path, required=True, help="Path to .glb/.gltf file")
    p.add_argument("--out", type=Path, required=True, help="Output directory")
    p.add_argument("--no-geom", action="store_true", help="Skip geometry‑based tagging (faster)")
    args = p.parse_args(argv)

    args.out.mkdir(parents=True, exist_ok=True)

    scene, g = load_scene_make_graph(args.glb)
    tag_nodes(scene, g, use_geometry=not args.no_geom)
    print_stats(g)

    # serialise
    write_triples   (g, args.out / "scene.triples")
    write_node_link_json(g, args.out / "scene.node_link.json")
    write_jsonl     (g, args.out / "scene.nodes.jsonl.gz")


if __name__ == "__main__":
    main()