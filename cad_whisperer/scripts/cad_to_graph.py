import argparse
from pathlib import Path
import numpy as np
import networkx as nx
import trimesh
from pyvis.network import Network
import torch
from torch_geometric.utils import from_networkx
import json
import plotly.graph_objects as go



# ------------------------------------------------------------------ #
def load_scene_make_nx(glb_path: Path) -> nx.DiGraph:
    """Load GLB/GLTF and return a NetworkX DiGraph of the scene graph."""
    scene = trimesh.load(glb_path, force="scene")
    g_nx  = scene.graph.to_networkx()

    # decorate every node with a label and (optionally) a transform matrix
    for node_id in g_nx.nodes:
        # ----- label --------------------------------------------------------
        g_nx.nodes[node_id]["label"] = str(node_id)

        # ----- transform ----------------------------------------------------
        try:
            # scene.graph[node_id] → (4×4 matrix, geometry_name) OR raises
            transform_tuple = scene.graph[node_id]
            if isinstance(transform_tuple, (list, tuple, np.ndarray)):
                matrix = np.asarray(transform_tuple[0]  # first item
                                    if isinstance(transform_tuple, tuple)
                                    else transform_tuple)
                g_nx.nodes[node_id]["matrix"] = matrix.tolist()
        except KeyError:
            # node might be purely organisational (no transform)
            pass

    return g_nx


def make_pyg_data(g_nx: nx.DiGraph):
    # -------- strip edge attributes so every edge is equal --------
    for u, v in g_nx.edges:
        g_nx[u][v].clear()

    data = from_networkx(g_nx)          # safe now
    if data.x is None:                  # add dummy node-feature matrix
        data.x = torch.ones(
            (g_nx.number_of_nodes(), 1), dtype=torch.float32)
    return data

def export_plotly(g_nx: nx.DiGraph, html_path):
    """
    Save an interactive Plotly graph (pan / zoom / hover) to `html_path`.
    """
    # -- 2-D layout ---------------------------------------------------------
    pos = nx.spring_layout(g_nx, dim=2, k=0.5)   # ⟺ force-directed

    # -- edge traces --------------------------------------------------------
    edge_x, edge_y = [], []
    for u, v in g_nx.edges():
        edge_x += [pos[u][0], pos[v][0], None]   # None -> segment break
        edge_y += [pos[u][1], pos[v][1], None]
    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        mode='lines',
        line=dict(width=1),
        hoverinfo='none'
    )

    # -- node traces --------------------------------------------------------
    x_nodes, y_nodes = zip(*[pos[n] for n in g_nx])
    labels = [g_nx.nodes[n].get('label', str(n)) for n in g_nx]
    node_trace = go.Scatter(
        x=x_nodes, y=y_nodes,
        mode='markers+text',
        text=[f" {lbl}" for lbl in labels],   # tiny space before label
        textposition='top center',
        hovertext=labels,
        hoverinfo='text',
        marker=dict(size=8)
    )

    # -- figure & save ------------------------------------------------------
    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title="Scene Graph",
            hovermode='closest',
            showlegend=False,
            margin=dict(l=0, r=0, t=40, b=0),
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
    )
    fig.write_html(str(html_path), include_plotlyjs='cdn')
    print(f"Plotly interactive HTML saved → {html_path}")


def export_graphml(g_nx: nx.DiGraph, out_path):
    """
    Write GraphML after coercing non-scalar attrs to strings.
    GraphML spec allows only str, int, float, bool.
    """
    for _, attr in g_nx.nodes(data=True):
        for key, value in list(attr.items()):
            if isinstance(value, (list, tuple, np.ndarray)):
                # Option A: drop it → uncomment next line
                # attr.pop(key)

                # Option B: keep as JSON string  (default below)
                attr[key] = json.dumps(value)

    for u, v, attr in g_nx.edges(data=True):
        # our edges are already empty after the earlier .clear(),
        # but this keeps the function generic
        for key, value in list(attr.items()):
            if isinstance(value, (list, tuple, np.ndarray)):
                attr[key] = json.dumps(value)

    nx.write_graphml(g_nx, out_path)
    print(f"GraphML saved → {out_path}")


def export_pyvis(g_nx: nx.DiGraph, html_path: Path):
    try:
        from pyvis.network import Network
        net = Network(height="800px", directed=True)
        net.from_nx(g_nx)
        for n in net.nodes:
            n["title"] = n.get("label", n["id"])
        net.show(str(html_path))
        print(f"Interactive HTML saved → {html_path}")
    except Exception as e:
        print(f"[warn] pyvis export skipped ({e})")


def plot_matplotlib(g_nx: nx.DiGraph):
    import matplotlib.pyplot as plt
    pos = nx.spring_layout(g_nx, k=0.5)
    nx.draw(g_nx, pos, with_labels=True, node_size=300, arrowsize=12)
    plt.title("Scene graph (spring layout)")
    plt.show()


# ------------------------------------------------------------------ #
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--glb",  required=True, type=Path)
    p.add_argument("--out",  required=True, type=Path)
    p.add_argument("--matplot", action="store_true")
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    g_nx = load_scene_make_nx(args.glb)

    # save PyG
    pyg_data = make_pyg_data(g_nx)
    torch.save(pyg_data, args.out / "scene_pyg_data.pt")
    print(f"PyG Data saved → {args.out/'scene_pyg_data.pt'}")

    # exports
    export_graphml(g_nx, args.out / "scene.graphml")
    export_pyvis(g_nx,  args.out / "scene_graph.html")
    export_plotly(g_nx, args.out / "scene_plotly.html")

    if args.matplot:
        plot_matplotlib(g_nx)


if __name__ == "__main__":
    main()