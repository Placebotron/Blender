import json, networkx as nx, dash, dash_cytoscape as cyto
from dash import dcc, html, Input, Output, State
from pathlib import Path

def nx_to_cyto(g: nx.DiGraph):
    nodes = [{"data": {"id": n, "label": g.nodes[n]["label"]},
              "classes": g.nodes[n].get("part_type", "UNKNOWN").lower()}
             for n in g]
    edges = [{"data": {"source": u, "target": v}} for u, v in g.edges]
    return nodes + edges

def load_graph(path: Path):
    g = nx.read_graphml(path)
    return g

g = load_graph(Path("output_kone/scene_tagged.graphml"))
elements = nx_to_cyto(g)

app = dash.Dash(__name__)
app.layout = html.Div([
    dcc.Input(id="search", type="text", placeholder="type part name…"),
    html.Button("Find", id="btn"),
    cyto.Cytoscape(id='cy', elements=elements,
        layout={'name': 'breadthfirst'},
        style={'width':'100%', 'height':'800px'},
        stylesheet=[
            {'selector':'node','style':{'label':'data(label)','font-size':'8px'}},
            {'selector':'.screw','style':{'background-color':'orange'}},
            {'selector':'.plate','style':{'background-color':'lightblue'}},
        ]),
])

@app.callback(Output('cy', 'elements'),
              Input('btn', 'n_clicks'),
              State('search', 'value'))
def search(n_clicks, query):
    if not query:
        return elements
    hits = [n for n in g if query.lower() in g.nodes[n]['label'].lower()]
    sub = g.subgraph(hits + [v for n in hits for v in g.successors(n)] +
                             [u for n in hits for u in g.predecessors(n)])
    return nx_to_cyto(sub)

if __name__ == "__main__":
    app.run(debug=True)
