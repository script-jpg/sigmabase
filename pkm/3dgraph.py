#!/usr/bin/env python
"""
3-D note-graph viewer – updated defaults
——————————————————————————————
• Spacing slider: 0.25, 0.5, 1, 2
• Repulsive-force slider: 0.2, 0.4, 0.8, 1.6
• Toggles (one button each):
      ⚲ edge-labels     (off by default)
      ⇢ arrowheads      (off by default)
      🔤 node-labels    (ON  by default)
• Nodes themselves start hidden (can be revealed by editing the code if needed)
• All performance tweaks preserved (cached layout, uirevision, no cones)
"""

import json, pathlib, pandas as pd, networkx as nx, numpy as np, plotly.graph_objects as go
import re

# ── CONFIG ────────────────────────────────────────────────────────
CSV_FILE       = "relations.csv"
ITERATIONS     = 100
SPACING_VALUES = [0.25, 0.5, 1, 2, 4, 8]     # ← updated
REPEL_VALUES   = [0.5, 1, 2, 4, 8, 16]  # ← new slider values
ARROW_FRAC     = 0.12

# ── NOTE FILE LOOKUP ─────────────────────────────────────────────-
FACTS_FILE     = "facts.pl"
note_files = {}
note_re = re.compile(r"note\(([^,]+),\s*'([^']+)'\)")
try:
    with open(FACTS_FILE) as f:
        for line in f:
            m = note_re.search(line)
            if m:
                note_files[m.group(1)] = m.group(2)
except FileNotFoundError:
    pass

# ── LOAD GRAPH ────────────────────────────────────────────────────
df = pd.read_csv(CSV_FILE)
G  = nx.from_pandas_edgelist(df, "Source", "Target",
                             edge_attr="Label", create_using=nx.DiGraph())

# ── LAYOUTS PER REPULSIVE VALUE (cached) ─────────────────────────
layouts = {}
for k in REPEL_VALUES:
    cf = pathlib.Path(f"layout_{k}.json")
    if cf.exists():
        layouts[k] = {n: np.array(p) for n, p in json.load(cf.open()).items()}
    else:
        layouts[k] = nx.spring_layout(G, dim=3, seed=42, iterations=ITERATIONS, k=k)
        json.dump({n: layouts[k][n].tolist() for n in G}, cf.open("w"))

DEFAULT_K = REPEL_VALUES[1]
pos0 = layouts[DEFAULT_K]

comp_id  = {n: i for i, c in enumerate(nx.connected_components(G.to_undirected()))
            for n in c}
centroid = {cid: np.mean([pos0[n] for n in G if comp_id[n]==cid], axis=0)
            for cid in set(comp_id.values())}

node_text_plain = list(G.nodes())
node_text_bold  = [f"<b>{t}</b>" for t in node_text_plain]
node_files      = [note_files.get(n, "") for n in G]

# ── COORD ARRAYS PER SPACING ─────────────────────────────────────
def arrays_for(pos_base, sp):
    pos = {n: pos_base[n] + (sp-1)*centroid[comp_id[n]] for n in G}
    node_xyz = np.array([pos[n] for n in G]).T

    edge = [[], [], []]; arrow = [[], [], []]
    for u, v in G.edges():
        p0, p1 = pos[u], pos[v]
        edge[0] += [p0[0], p1[0], None]
        edge[1] += [p0[1], p1[1], None]
        edge[2] += [p0[2], p1[2], None]

        head = p1 - ARROW_FRAC*(p1-p0)
        arrow[0] += [head[0], p1[0], None]
        arrow[1] += [head[1], p1[1], None]
        arrow[2] += [head[2], p1[2], None]

    lx, ly, lz, ltxt = [], [], [], []
    for u, v, d in G.edges(data=True):
        p0, p1 = pos[u], pos[v]
        lx.append((p0[0]+p1[0])/2)
        ly.append((p0[1]+p1[1])/2)
        lz.append((p0[2]+p1[2])/2)
        ltxt.append(d["Label"])

    return dict(node=node_xyz,
                edge=edge,
                arrow=arrow,
                edge_lbl=(lx, ly, lz, ltxt),
                node_lbl=node_xyz)

arrays = {k: {s: arrays_for(layouts[k], s) for s in SPACING_VALUES}
          for k in REPEL_VALUES}

# ── TRACE FACTORY ────────────────────────────────────────────────
def sc3d(x, y, z, **kw):
    t = go.Scatter3d(x=x, y=y, z=z, **kw); t.uirevision = "static"; return t

a1 = arrays[DEFAULT_K][1]

edge_t  = sc3d(*a1["edge"],  mode="lines", line=dict(width=1), hoverinfo="none")
arrow_t = sc3d(*a1["arrow"], mode="lines", line=dict(width=4),
               hoverinfo="none", visible=False)
lx,ly,lz,lt = a1["edge_lbl"]
edge_lbl_t = sc3d(lx,ly,lz, mode="text", text=lt,
                  hoverinfo="none", visible=False)

# Node-label trace (ON by default)
node_lbl_t = sc3d(*a1["node_lbl"],
    mode="markers+text",
    marker=dict(size=12, symbol="square", color="#fff7b2", line=dict(width=0)),
    text=node_text_bold,
    textfont=dict(color="black"),
    hoverinfo="none",
    customdata=node_files,
    visible=True)                      # ← now visible by default

# Node spheres (OFF by default)
node_t = sc3d(*a1["node"], mode="markers",
              marker=dict(size=6, opacity=0.85),
              hovertext=node_text_plain,
              customdata=node_files,
              visible=False)           # ← now hidden by default

fig = go.Figure(data=[edge_t, arrow_t, edge_lbl_t, node_lbl_t, node_t])

# ── SLIDER (restyle) ─────────────────────────────────────────────
# Create a JavaScript variable to store the arrays data
arrays_js = json.dumps({
    str(k): {
        str(s): {
            "edge": [arrays[k][s]["edge"][i] for i in range(3)],
            "arrow": [arrays[k][s]["arrow"][i] for i in range(3)],
            "edge_lbl": [arrays[k][s]["edge_lbl"][i] for i in range(4)],
            "node_lbl": [arrays[k][s]["node_lbl"][i].tolist() for i in range(3)],
            "node": [arrays[k][s]["node"][i].tolist() for i in range(3)]
        } for s in SPACING_VALUES
    } for k in REPEL_VALUES
})

# Create dummy steps that will be handled by JavaScript
steps = []
for i, s in enumerate(SPACING_VALUES):
    steps.append(dict(
        label=str(s),
        method="relayout",
        args=[{}]  # Empty args, will be handled by JS
    ))

repel_steps = []
for j, k in enumerate(REPEL_VALUES):
    repel_steps.append(dict(
        label=str(k),
        method="relayout",
        args=[{}]  # Empty args, will be handled by JS
    ))

fig.update_layout(
    sliders=[
        dict(steps=steps, active=SPACING_VALUES.index(1),
             x=0.02, y=-0.05, xanchor="left", len=0.45,
             currentvalue=dict(visible=False)),
        dict(steps=repel_steps, active=REPEL_VALUES.index(DEFAULT_K),
             x=0.55, y=-0.05, xanchor="left", len=0.4,
             currentvalue=dict(visible=False))
    ],

    # ── SINGLE-TOGGLE BUTTONS ────────────────────────────────────
    updatemenus=[dict(
        type="buttons", x=1.05, y=0.8,
        buttons=[
            dict(label="⚲ Edge labels",
                 method="restyle",
                 args=[{"visible":[True]}, [2]],
                 args2=[{"visible":[False]}, [2]]),

            dict(label="⇢ Arrowheads",
                 method="restyle",
                 args=[{"visible":[True]}, [1]],
                 args2=[{"visible":[False]}, [1]]),

            dict(label="🔤 Node labels",
                 method="restyle",
                 args=[{"visible":[True]}, [3]],
                 args2=[{"visible":[False]}, [3]])
        ]
    )],

    scene=dict(xaxis_visible=False, yaxis_visible=False, zaxis_visible=False, dragmode='orbit'),
    margin=dict(l=0, r=0, t=0, b=0),
    clickmode="event+select"
)

CLICK_JS = f"""
var SPACING_VALUES = {json.dumps(SPACING_VALUES)};
var REPEL_VALUES = {json.dumps(REPEL_VALUES)};
var arrays = {arrays_js};
var node_text_bold = {json.dumps(node_text_bold)};
var node_text_plain = {json.dumps(node_text_plain)};
var node_files = {json.dumps(node_files)};

// Initialize current values
var current_spacing_idx = {SPACING_VALUES.index(1)};
var current_repel_idx = {REPEL_VALUES.index(DEFAULT_K)};

var plot = document.getElementsByClassName('plotly-graph-div')[0];

// Create search input
var searchContainer = document.createElement('div');
searchContainer.style.cssText = 'position: absolute; top: 10px; left: 10px; z-index: 1000;';
searchContainer.innerHTML = `
    <input type="text" id="nodeSearch" placeholder="Search nodes..." 
           style="padding: 8px 12px; font-size: 14px; border: 1px solid #ccc; 
                  border-radius: 4px; width: 200px;">
    <button id="clearSearch" style="padding: 8px 12px; margin-left: 5px; 
            font-size: 14px; border: 1px solid #ccc; border-radius: 4px; 
            background: #f0f0f0; cursor: pointer;">Clear</button>
`;
plot.parentElement.appendChild(searchContainer);

// Search functionality
var searchInput = document.getElementById('nodeSearch');
var clearButton = document.getElementById('clearSearch');

function filterNodes() {{
    var searchTerm = searchInput.value.toLowerCase();
    
    if (searchTerm === '') {{
        // Show all nodes
        var allVisible = new Array(node_text_plain.length).fill(true);
        updateNodeVisibility(allVisible);
    }} else {{
        // Filter nodes
        var visibility = node_text_plain.map(function(text) {{
            return text.toLowerCase().includes(searchTerm);
        }});
        updateNodeVisibility(visibility);
    }}
}}

function updateNodeVisibility(visibility) {{
    var k = REPEL_VALUES[current_repel_idx];
    var s = SPACING_VALUES[current_spacing_idx];
    var a = arrays[k][s];
    
    // Filter coordinates and text based on visibility
    var filtered_x = [];
    var filtered_y = [];
    var filtered_z = [];
    var filtered_text = [];
    var filtered_customdata = [];
    
    for (var i = 0; i < visibility.length; i++) {{
        if (visibility[i]) {{
            filtered_x.push(a.node_lbl[0][i]);
            filtered_y.push(a.node_lbl[1][i]);
            filtered_z.push(a.node_lbl[2][i]);
            filtered_text.push(node_text_bold[i]);
            filtered_customdata.push(node_files[i]);
        }}
    }}
    
    // Update only the node label trace
    Plotly.restyle(plot, {{
        'x': [filtered_x],
        'y': [filtered_y],
        'z': [filtered_z],
        'text': [filtered_text],
        'customdata': [filtered_customdata]
    }}, [3]);
}}

// Event listeners
searchInput.addEventListener('input', filterNodes);
clearButton.addEventListener('click', function() {{
    searchInput.value = '';
    filterNodes();
}});

// Handle clicks
plot.on('plotly_click', function(data){{
    var c = data.points[0].curveNumber;
    if(c===3 || c===4){{
        var url = data.points[0].customdata;
        if(url){{window.open(url);}}
    }}
}});

// Handle slider changes
plot.on('plotly_sliderchange', function(eventdata){{
    // Determine which slider changed
    if(eventdata.slider.x === 0.02){{
        // Spacing slider
        current_spacing_idx = eventdata.slider.active;
    }} else {{
        // Repel slider
        current_repel_idx = eventdata.slider.active;
    }}
    
    // Apply search filter when sliders change
    filterNodes();
}});
"""

# --- write the updated file ---
fig.write_html("graph.html", include_plotlyjs="cdn",
               auto_open=False, post_script=CLICK_JS)

# --- bring/reload the page in the browser ---
import webbrowser
webbrowser.open("http://localhost:8000/graph.html", new=0, autoraise=True)
