# ─────────────────────────────────────────────────────────────────────────────
# scripts/shape_finder.py  (thin CLI)
# ─────────────────────────────────────────────────────────────────────────────

import networkx as nx

"""CLI to tag parts and print a part‑type histogram."""
import numpy as np
import argparse, json
from pathlib import Path
from cadwhisperer.io.scene_loader import load_scene_make_graph
from cadwhisperer.graph.enrich import enrich_graph

def _prepare_for_graphml(g):
    """Make sure all attrs are GraphML-legal."""
    for _, a in g.nodes(data=True):
        for k, v in list(a.items()):
            if isinstance(v, (list, tuple, np.ndarray)):
                # ---- Pick ONE of the next two lines ----
                # a.pop(k)                                # A.  drop it
                a[k] = json.dumps(v)                     # B.  keep as str
    for u, v, a in g.edges(data=True):                   # (edges just in case)
        for k, vv in list(a.items()):
            if isinstance(vv, (list, tuple, np.ndarray)):
                # a.pop(k)                               # or drop
                a[k] = json.dumps(vv)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--glb", type=Path, required=True)
    p.add_argument("--out", type=Path, required=False)
    args = p.parse_args()

    scene, g = load_scene_make_graph(args.glb)
    enrich_graph(scene, g)

    counts = {}
    for _, a in g.nodes(data=True):
        counts[a["part_type"]] = counts.get(a["part_type"], 0) + 1
    print(json.dumps(counts, indent=2))

    if args.out:
        args.out.mkdir(parents=True, exist_ok=True)
        _prepare_for_graphml(g)      
        nx.write_graphml(g, args.out / "scene_tagged.graphml")
        print("Tagged GraphML saved →", args.out / "scene_tagged.graphml")

if __name__ == "__main__":
    main()
