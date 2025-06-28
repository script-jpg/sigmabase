import subprocess
from pathlib import Path
import importlib.util

from dash import Dash, dcc, html

BASE_DIR = Path(__file__).parent

spec = importlib.util.spec_from_file_location("graph3d", BASE_DIR / "3dgraph.py")
graph3d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph3d)
build_figure = graph3d.build_figure
CSV_FILE = graph3d.CSV_FILE
FACTS_FILES = [BASE_DIR / 'facts.pl', BASE_DIR / 'rules.pl', BASE_DIR / '_facts_demo.pl']

# Track modification times
mod_times = {f: f.stat().st_mtime for f in FACTS_FILES if f.exists()}

# Start Dash app
app = Dash(__name__)
current_fig = build_figure()

app.layout = html.Div([
    dcc.Graph(id='graph', figure=current_fig),
    dcc.Interval(id='poll', interval=2000)
])


def export_csv():
    """Run the Prolog exporter if SWI-Prolog is available."""
    try:
        subprocess.run(
            ['swipl', '-s', str(BASE_DIR / 'rules.pl'), '-g', f"export_rel_csv('{CSV_FILE}'),halt"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        # swipl not installed; skip regeneration
        pass


@app.callback('graph.figure', 'poll.n_intervals')
def reload_graph(_):
    global current_fig
    changed = False
    for f in FACTS_FILES:
        if not f.exists():
            continue
        new_mtime = f.stat().st_mtime
        if mod_times.get(f) != new_mtime:
            mod_times[f] = new_mtime
            changed = True
    if changed:
        export_csv()
        current_fig = build_figure()
    return current_fig


if __name__ == '__main__':
    app.run_server(debug=False)
