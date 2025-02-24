from wikimap import WikiMap, WikiLanguage, WikiGraphFormat, WikiSanityCheckMode
from datetime import datetime
import matplotlib.pyplot as plt
import networkx as nx
from igraph import Graph, plot
import time

# Recombine all pages, current versions only
# frwiki-20241101-pages-meta-current.xml.bz2
# https://dumps.wikimedia.org/frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2


# Nom du fichier                                        Contenu                                         Taille relative     Usage principal
# frwiki-20241101-pages-meta-current.xml.bz2            Pages actuelles + métadonnées                   Moyenne             Étude des articles et métadonnées actuels
# frwiki-20241101-pages-articles.xml.bz2                Texte brut des articles                         Faible              Travail sur le contenu brut des articles
# frwiki-20241101-pages-meta-history1.xml-p1p1209.7z    Historique complet pour une sélection de pages  Très élevée         Analyse des révisions et de l’évolution


# wm = WikiMap("wikimap_fr_20241101.gexf")
# wm = WikiMap("https://dumps.wikimedia.org/frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2")
# wm = WikiMap("frwiki/20241101/frwiki-20241101-pages-meta-current.xml.bz2")
# wm = WikiMap("fr/20241101/pages-meta-current.xml.bz2")
# wm = WikiMap(date=datetime(2020, 5, 17), language="en", with_history=False)

wm = WikiMap(date="latest", language=WikiLanguage.EL)

wm.load()

wm.parse()

wm.save_graph(WikiGraphFormat.CSV, "./tmp/el_save")

graph = wm.get_graph()

# Measure execution time for PageRank
start_time = time.time()
page_ranks = graph.pagerank()
top_10_page_ranks = sorted([(graph.vs[i]["title"], page_ranks[i]) for i in range(len(page_ranks))], key=lambda x: x[1], reverse=True)[:10]
print(f"Top 10 Page Ranks: {top_10_page_ranks}")
print(f"PageRank execution time: {time.time() - start_time} seconds")

# Measure execution time for out degrees and in degrees
start_time = time.time()
out_degrees = graph.outdegree()
in_degrees = graph.indegree()
top_10_out_degrees = sorted([(graph.vs[i]["title"], out_degrees[i]) for i in range(len(out_degrees))], key=lambda x: x[1], reverse=True)[:10]
top_10_in_degrees = sorted([(graph.vs[i]["title"], in_degrees[i]) for i in range(len(in_degrees))], key=lambda x: x[1], reverse=True)[:10]
print(f"Top 10 Out Degrees: {top_10_out_degrees}")
print(f"Top 10 In Degrees: {top_10_in_degrees}")
print(f"Out/In Degrees execution time: {time.time() - start_time} seconds")

# Measure execution time for Louvain community detection on directed graph
start_time = time.time()
undirected_graph = graph.as_undirected()
communities = undirected_graph.community_multilevel()
print(f"Number of communities: {len(communities)}")
print(f"Louvain community detection execution time: {time.time() - start_time} seconds")

# # get graph diameter and on which nodes it is reached
# start_time = time.time()
# diameter = graph.diameter(directed=True)
# print(f"Graph diameter: {diameter}")
# futher_nodes = graph.farthest_points()
# further_nodes_titles = [(graph.vs[node]["title"] for node in futher_nodes)]
# print(f"Further nodes: {further_nodes_titles}")
# print(f"Diameter execution time: {time.time() - start_time} seconds")

# Pour NetworkX
# print(f"Le graphe contient {graph.number_of_nodes()} nœuds et {graph.number_of_edges()} arêtes.")
# # save a picture of the node with title = "512" with adjacent nodes
# node = [x for x,y in graph.nodes(data=True) if y['title']=="512"][0]
# adjacent_nodes = list(graph.successors(node)) + list(graph.predecessors(node))
# # Create a subgraph with the node and its adjacent nodes
# subgraph_nodes = [node] + adjacent_nodes
# subgraph = graph.subgraph(subgraph_nodes)
# # Draw the subgraph
# pos = nx.spring_layout(subgraph)
# labels = {n: d['title'] for n, d in subgraph.nodes(data=True)}
# nx.draw(subgraph, pos, labels=labels, with_labels=True, node_color='lightblue', edge_color='gray', node_size=500, font_size=10)
# # Save the picture
# plt.savefig("image.png")
# plt.show()

# wm.graph.save("gexf", "wikimap_fr_20241101.gexf")
# wm.save("512", "png", "wikimap_fr_20241101.png")

# total_pages, total_links, missing_pages = wm.stats()

# wm.save_graph(WikiGraphFormat.GRAPHML, "./tmp/fr_test_save")
# wm.save_graph(WikiGraphFormat.GRAPHML, "./tmp/fr_test_save", True)
# wm.save_graph(WikiGraphFormat.CSV, "./tmp/fr_test_save", compression=True)
# wm.save_graph(WikiGraphFormat.CSV, "./tmp/fr_test_save")

# Measure execution time for displaying "United States"
# start_time = time.time()
# wm.display("United States", 1)
# print(f"Display execution time: {time.time() - start_time} seconds")

wm.sanity_check(WikiSanityCheckMode.NODES_SELECTION, 0.01)

# wm.display_html("Άρης (πλανήτης)", 2, "wikimap_el_latest.html")
# wm.display("Άρης (πλανήτης)", 2)

# check Αθλητισμός
# Ντέιβιντ Σάνσον
# ou
# ντέιβιντ σάνσον