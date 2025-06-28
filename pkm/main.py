import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

df = pd.read_csv("relations.csv")
G = nx.DiGraph()
for _, row in df.iterrows():
    G.add_edge(row['Source'], row['Target'], label=row['Label'])

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray')
edge_labels = nx.get_edge_attributes(G, 'label')
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
plt.show()
