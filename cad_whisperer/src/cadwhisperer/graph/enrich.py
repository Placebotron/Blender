# ─────────────────────────────────────────────────────────────────────────────
# cadwhisperer/graph/enrich.py
# ─────────────────────────────────────────────────────────────────────────────
"""Enrich a scene graph in‑place with part_type, rationale, etc."""
from typing import List
import networkx as nx
import trimesh
from cadwhisperer.shapes.heuristics import ALL_HEURISTIC_DETECTORS

CONF_THRESHOLD = 0.6  # accept detector if confidence ≥ this


def enrich_graph(scene: trimesh.Scene, g: nx.DiGraph, *, detectors=None):
    if detectors is None:
        detectors = ALL_HEURISTIC_DETECTORS

    for n in g.nodes:
        g.nodes[n].setdefault("part_type", "UNKNOWN")

    for n in g.nodes:
        geom_name = g.nodes[n].get("geom_name")
        mesh = scene.geometry.get(geom_name) if geom_name else None
        for det in detectors:
            res = det.detect(mesh, g.nodes[n]) if mesh is not None else None
            if res and res.confidence >= CONF_THRESHOLD:
                g.nodes[n]["part_type"] = res.label
                g.nodes[n]["detection_rationale"] = res.rationale
                break

