import json
import re
import pathlib

import pandas as pd
import networkx as nx
import numpy as np
import plotly.graph_objects as go
import dash
from dash import html, dcc
from dash.dependencies import Input, Output

CSV_FILE = "relations.csv"
PL_FILES = ["facts.pl", "_facts_demo.pl"]
ITERATIONS = 30
SPACING_VALUES = [0.25, 0.5, 1, 2]
ARROW_FRAC = 0.12


def parse_pl(path):
    notes = {}
    tags = {}
    edges = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith('%'):
            continue
        m = re.match(r"note\(([^,]+),\s*'([^']+)'\)", line)
        if m:
            notes[m.group(1)] = m.group(2)
            continue
        m = re.match(r"tag\(([^,]+),\s*([^)]+)\)", line)
        if m:
            node = m.group(1)
            tag = m.group(2).rstrip('.').strip()
            tags.setdefault(node, set()).add(tag)
            continue
        m = re.match(r"rel\(([^,]+),\s*([^,]+),\s*'([^']+)'\)", line)
        if m:
            edges.append((m.group(1), m.group(2), m.group(3)))
    return notes, tags, edges


def load_data():
    df = pd.read_csv(CSV_FILE)
    edges = [(row.Source, row.Target, row.Label) for row in df.itertuples()]
    notes = {}
    tags = {}
    for pl in PL_FILES:
        p = pathlib.Path(pl)
        if not p.exists():
            continue
        n, t, _ = parse_pl(p)
        notes.update(n)
        for k, v in t.items():
            tags.setdefault(k, set()).update(v)
    return edges, notes, tags


def build_graph(edges, notes, tags):
    G = nx.DiGraph()
    for u, v, lbl in edges:
        G.add_edge(u, v, label=lbl)
    for n in G:
        G.nodes[n]["tags"] = list(tags.get(n, []))
        G.nodes[n]["filename"] = notes.get(n)
        G.nodes[n]["metadata"] = bool(notes.get(n) or tags.get(n))
    return G


def layout_graph(G):
    pos0 = nx.spring_layout(G, dim=3, seed=42, iterations=ITERATIONS)
    comp_id = {n: i for i, c in enumerate(nx.connected_components(G.to_undirected())) for n in c}
    centroid = {cid: np.mean([pos0[n] for n in G if comp_id[n] == cid], axis=0) for cid in set(comp_id.values())}
    return pos0, comp_id, centroid


def arrays_for(G_sub, sp, pos0, comp_id, centroid):
    if len(G_sub) == 0:
        return dict(node=np.empty((3, 0)), edge=[[], [], []], arrow=[[], [], []], edge_lbl=([], [], [], []), node_lbl=np.empty((3, 0)))
    pos = {n: pos0[n] + (sp - 1) * centroid[comp_id[n]] for n in G_sub}
    node_xyz = np.array([pos[n] for n in G_sub]).T
    edge = [[], [], []]
    arrow = [[], [], []]
    lx = []
    ly = []
    lz = []
    ltxt = []
    for u, v, d in G_sub.edges(data=True):
        p0, p1 = pos[u], pos[v]
        edge[0] += [p0[0], p1[0], None]
        edge[1] += [p0[1], p1[1], None]
        edge[2] += [p0[2], p1[2], None]
        head = p1 - ARROW_FRAC * (p1 - p0)
        arrow[0] += [head[0], p1[0], None]
        arrow[1] += [head[1], p1[1], None]
        arrow[2] += [head[2], p1[2], None]
        lx.append((p0[0] + p1[0]) / 2)
        ly.append((p0[1] + p1[1]) / 2)
        lz.append((p0[2] + p1[2]) / 2)
        ltxt.append(d["label"])
    return dict(node=node_xyz, edge=edge, arrow=arrow, edge_lbl=(lx, ly, lz, ltxt), node_lbl=node_xyz)


def figure_for(G_sub, sp, pos0, comp_id, centroid, show_edge_lbl, show_arrow, show_node_lbl, show_nodes):
    arr = arrays_for(G_sub, sp, pos0, comp_id, centroid)
    node_text_plain = list(G_sub.nodes())
    node_text_bold = [f"<b>{t}</b>" for t in node_text_plain]

    def sc3d(x, y, z, **kw):
        return go.Scatter3d(x=x, y=y, z=z, **kw)

    t_edge = sc3d(*arr["edge"], mode="lines", line=dict(width=1), hoverinfo="none")
    t_arrow = sc3d(*arr["arrow"], mode="lines", line=dict(width=4), hoverinfo="none", visible=show_arrow)
    lx, ly, lz, lt = arr["edge_lbl"]
    t_edge_lbl = sc3d(lx, ly, lz, mode="text", text=lt, hoverinfo="none", visible=show_edge_lbl)
    t_node_lbl = sc3d(*arr["node_lbl"], mode="markers+text", marker=dict(size=12, symbol="square", color="#fff7b2", line=dict(width=0)), text=node_text_bold, textfont=dict(color="black"), hoverinfo="none", visible=show_node_lbl)
    t_node = sc3d(*arr["node"], mode="markers", marker=dict(size=6, opacity=0.85), hovertext=node_text_plain, visible=show_nodes)

    fig = go.Figure(data=[t_edge, t_arrow, t_edge_lbl, t_node_lbl, t_node])
    fig.update_layout(scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False), margin=dict(l=0, r=0, t=0, b=0))
    return fig


def filter_graph(G, require_tags, exclude_tags, include_labels, exclude_labels, substr, exclude_substr, meta_filter):
    nodes = set(G.nodes())
    if require_tags:
        nodes &= {n for n in G if set(G.nodes[n]["tags"]).intersection(require_tags)}
    if exclude_tags:
        nodes -= {n for n in G if set(G.nodes[n]["tags"]).intersection(exclude_tags)}
    if substr:
        s = substr.lower()
        nodes &= {n for n in nodes if s in n.lower() or s in str(G.nodes[n]["filename"]).lower()}
    if exclude_substr:
        s = exclude_substr.lower()
        nodes -= {n for n in nodes if s in n.lower() or s in str(G.nodes[n]["filename"]).lower()}
    if meta_filter == "with":
        nodes &= {n for n in nodes if G.nodes[n]["metadata"]}
    elif meta_filter == "without":
        nodes &= {n for n in nodes if not G.nodes[n]["metadata"]}

    G_sub = nx.DiGraph()
    G_sub.add_nodes_from(nodes)
    for u, v, d in G.edges(data=True):
        if u not in nodes or v not in nodes:
            continue
        lbl = d["label"]
        if include_labels and lbl not in include_labels:
            continue
        if exclude_labels and lbl in exclude_labels:
            continue
        G_sub.add_edge(u, v, label=lbl)
    return G_sub


def make_app():
    edges, notes, tags = load_data()
    G = build_graph(edges, notes, tags)
    pos0, comp_id, centroid = layout_graph(G)

    all_tags = sorted({t for ts in tags.values() for t in ts})
    all_labels = sorted({lbl for _, _, lbl in edges})

    app = dash.Dash(__name__)
    app.layout = html.Div([
        html.Div([
            html.Label("Require tags"),
            dcc.Dropdown(options=[{"label": t, "value": t} for t in all_tags], id="req-tags", multi=True),
            html.Label("Exclude tags"),
            dcc.Dropdown(options=[{"label": t, "value": t} for t in all_tags], id="exc-tags", multi=True),
            html.Label("Include rel labels"),
            dcc.Dropdown(options=[{"label": l, "value": l} for l in all_labels], id="inc-lbls", multi=True),
            html.Label("Exclude rel labels"),
            dcc.Dropdown(options=[{"label": l, "value": l} for l in all_labels], id="exc-lbls", multi=True),
            html.Label("Name substring"),
            dcc.Input(id="substr", type="text"),
            html.Label("Exclude substring"),
            dcc.Input(id="exc-substr", type="text"),
            html.Label("Metadata"),
            dcc.Dropdown(options=[{"label": "Any", "value": "any"}, {"label": "With metadata", "value": "with"}, {"label": "Without metadata", "value": "without"}], value="any", id="meta"),
            html.Label("Spacing"),
            dcc.Slider(id="sp", min=0, max=len(SPACING_VALUES) - 1, step=1, value=SPACING_VALUES.index(1), marks={i: str(v) for i, v in enumerate(SPACING_VALUES)}),
            html.Label("Display"),
            dcc.Checklist(options=[{"label": "Edge labels", "value": "edge"}, {"label": "Arrowheads", "value": "arrow"}, {"label": "Node labels", "value": "node_lbl"}, {"label": "Nodes", "value": "nodes"}], value=["node_lbl"], id="disp")
        ], style={"width": "25%", "display": "inline-block", "verticalAlign": "top"}),
        html.Div([
            dcc.Graph(id="graph")
        ], style={"width": "74%", "display": "inline-block"})
    ])

    @app.callback(Output("graph", "figure"),
                  [Input("req-tags", "value"), Input("exc-tags", "value"), Input("inc-lbls", "value"), Input("exc-lbls", "value"), Input("substr", "value"), Input("exc-substr", "value"), Input("meta", "value"), Input("sp", "value"), Input("disp", "value")])
    def update_graph(req_tags, exc_tags, inc_lbls, exc_lbls, substr, exc_substr, meta, sp_idx, disp):
        G_sub = filter_graph(G, req_tags or [], exc_tags or [], inc_lbls or [], exc_lbls or [], substr or "", exc_substr or "", meta)
        fig = figure_for(G_sub, SPACING_VALUES[sp_idx], pos0, comp_id, centroid,
                         show_edge_lbl="edge" in disp, show_arrow="arrow" in disp,
                         show_node_lbl="node_lbl" in disp, show_nodes="nodes" in disp)
        return fig

    return app


if __name__ == "__main__":
    app = make_app()
    app.run_server(debug=True)
